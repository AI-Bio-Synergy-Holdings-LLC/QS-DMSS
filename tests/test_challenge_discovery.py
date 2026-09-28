"""Read-only discovery generation, package serving and intake boundaries."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from qs_dmss.cockpit.api import create_app

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "src/qs_dmss/cockpit/static"


@pytest.fixture
def builder():
    spec = importlib.util.spec_from_file_location("build_discovery", ROOT / "research/challenges/build_discovery.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_surfaces_are_identical_and_derived_from_validated_evidence(builder):
    expected = builder.render_assets()
    assert len(expected) == 6
    for path, data in expected.items():
        assert (ROOT / path).read_bytes() == data
    registry = json.loads((ROOT / "research/challenges/registry-v1.json").read_text(encoding="utf-8"))
    data = (STATIC / "scientific-challenges.json").read_bytes()
    assert json.loads(data) == registry
    script = (STATIC / "scientific-challenges.js").read_text(encoding="utf-8")
    assert hashlib.sha256(data).hexdigest() in script
    assert "__REGISTRY_SHA256__" not in script
    assert b"\r" not in data  # Must remain identical across Windows and Linux.


def test_generation_refuses_invalid_evidence_before_writing(builder, monkeypatch):
    original = builder.importlib.util.module_from_spec

    def load(spec):
        module = original(spec)
        loader = spec.loader.exec_module

        def invalid(target):
            loader(target)
            target.validate_registry = lambda *_: (_ for _ in ()).throw(ValueError("Evidence mismatch"))
        spec.loader.exec_module = invalid
        return module
    monkeypatch.setattr(builder.importlib.util, "module_from_spec", load)
    with pytest.raises(ValueError, match="Evidence mismatch"):
        builder.render_assets()


def test_check_mode_detects_stale_and_missing_files_without_writes(builder, monkeypatch, tmp_path):
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    monkeypatch.setattr(builder, "render_assets", lambda: {Path("catalog.json"): b"expected"})
    monkeypatch.setattr("sys.argv", ["build_discovery.py", "--check"])
    with pytest.raises(SystemExit, match="Regenerate"):
        builder.main()
    assert not (tmp_path / "catalog.json").exists()
    (tmp_path / "catalog.json").write_bytes(b"stale")
    with pytest.raises(SystemExit, match="Regenerate"):
        builder.main()
    assert (tmp_path / "catalog.json").read_bytes() == b"stale"


def test_discovery_never_renders_untrusted_html_or_calls_ai_or_compute():
    script = (STATIC / "scientific-challenges.js").read_text(encoding="utf-8")
    for forbidden in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write",
                      "eval(", "/api/ai", "/api/runs", "/api/sweeps", "localStorage"):
        assert forbidden not in script
    assert "element.textContent = String(text)" in script
    assert script.index('actual !== EXPECTED_SHA256') < script.index('JSON.parse')
    assert script.index('JSON.parse') < script.index('render(registry);')
    assert 'redirect: "error"' in script and 'cache: "no-cache"' in script
    assert 'url.origin !== window.location.origin' in script
    assert "controller.abort()" in script
    assert "No scientific status can be inferred" in script
    assert 'url.searchParams.set("template", "scientific_review.yml")' in script
    prefill_keys = re.findall(r'url.searchParams.set\("([^"]+)"', script)
    assert prefill_keys == ["template", "title", "focus"]  # No fabricated reviewer/result/hash.
    assert "same AI-assisted maintainer workflow" in script
    assert "Original candidate wheel SHA-256" in script


@pytest.mark.parametrize("hosted", [False, True])
def test_discovery_assets_are_served_with_guards_and_ai_stays_disabled(tmp_path, monkeypatch, hosted):
    monkeypatch.setenv("QS_DMSS_HOSTED_DEMO", "1" if hosted else "0")
    monkeypatch.delenv("QS_DMSS_AI_ENABLED", raising=False)
    app = create_app(repo_root=ROOT, output_root=tmp_path / "runs")
    client = TestClient(app)
    page = client.get("/")
    assert page.status_code == 200
    assert 'data-scientific-challenges="/static/scientific-challenges.json"' in page.text
    assert 'data-challenge-assistant' in page.text
    for suffix in ("js", "css", "json"):
        response = client.get("/static/scientific-challenges." + suffix)
        assert response.status_code == 200
        assert response.content == (STATIC / ("scientific-challenges." + suffix)).read_bytes()
        assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
        assert response.headers["x-content-type-options"] == "nosniff"
    assert client.get("/api/ai/status").json()["enabled"] is False
    if hosted:
        assert client.get("/api/health").json()["capabilities"]["hosted_custom_compute"] is False
    assert not list((tmp_path / "runs").glob("*/manifest.json"))


def test_discovery_assets_participate_in_shell_cache_revision(tmp_path):
    # The revision method needs no service state beyond the static directory.
    from qs_dmss.cockpit.api import CockpitService
    service = SimpleNamespace(static_root=tmp_path / "static")
    service.static_root.mkdir()
    names = ("styles.css", "app.js", "scientific-challenges.js",
             "scientific-challenges.css", "scientific-challenges.json")
    for name in names:
        (service.static_root / name).write_bytes((STATIC / name).read_bytes())
    baseline = CockpitService.static_asset_revision(service)
    for name in names[2:]:
        path = service.static_root / name
        original = path.read_bytes()
        path.write_bytes(original + b" ")
        assert CockpitService.static_asset_revision(service) != baseline
        path.write_bytes(original)


def test_both_shells_have_accessible_unavailable_and_no_javascript_handoffs():
    for path in (ROOT / "site/index.html", STATIC / "index.html"):
        html = path.read_text(encoding="utf-8")
        assert 'id="scientific-challenges"' in html
        assert 'aria-labelledby="scientific-challenges-title"' in html
        assert 'data-challenge-status role="status"' in html
        assert 'data-challenge-retry hidden' in html
        assert '<noscript>' in html and "Source reviewer guide" in html
        assert "/issues/183" in html
    css = (STATIC / "scientific-challenges.css").read_text(encoding="utf-8")
    assert ":focus-visible" in css
    assert "forced-colors: active" in css
    assert "min-height: 44px" in css
    assert "overflow-wrap: anywhere" in css
