from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
import yaml

from qs_dmss.deployment import public_deployment_provenance

REPO_ROOT = Path(__file__).resolve().parents[1]
VERIFIER_PATH = REPO_ROOT / ".github" / "scripts" / "verify_public_deployment.py"


def _load_verifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "verify_public_deployment",
        VERIFIER_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_public_deployment_provenance_rejects_untrusted_values() -> None:
    payload = public_deployment_provenance(
        {
            "RENDER": "true",
            "RENDER_GIT_COMMIT": "not-a-commit",
            "RENDER_GIT_BRANCH": "main\ninternal-detail",
            "RENDER_SERVICE_ID": "private-service-id",
        }
    )

    assert payload == {
        "provider": "render",
        "git_commit": None,
        "git_branch": None,
    }


def test_production_verification_runs_for_every_main_push() -> None:
    workflow_path = (
        REPO_ROOT / ".github" / "workflows" / "verify-production-deploy.yml"
    )
    workflow = yaml.load(
        workflow_path.read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    push_trigger = workflow["on"]["push"]

    assert push_trigger["branches"] == ["main"]
    assert "paths" not in push_trigger
    assert "paths-ignore" not in push_trigger


def test_public_verifier_requires_matching_render_provenance(monkeypatch) -> None:
    verifier = _load_verifier()
    portal_commit = "c" * 40
    app_commit = "d" * 40
    headers = {
        "content-security-policy": "default-src 'self'",
        "x-frame-options": "DENY",
        "x-content-type-options": "nosniff",
        "referrer-policy": "strict-origin-when-cross-origin",
        "strict-transport-security": "max-age=63072000",
        "permissions-policy": "camera=()",
    }
    portal = {
        "version": "0.13.2",
        "deployment": {
            "provider": "render",
            "git_commit": portal_commit,
            "git_branch": "main",
        },
    }
    app = {
        "status": "ok",
        "version": "0.13.2",
        "deployment": {
            "provider": "render",
            "git_commit": app_commit,
            "git_branch": "main",
        },
    }

    def fetch(url: str, expected_commit: str):
        if "deployment.json" in url:
            assert expected_commit == portal_commit
        else:
            assert expected_commit == app_commit
        return (portal if "deployment.json" in url else app), headers

    monkeypatch.setattr(verifier, "_fetch_json", fetch)

    verifier.verify_once(
        portal_url="https://portal.example/deployment.json",
        app_health_url="https://app.example/api/health",
        expected_portal_commit=portal_commit,
        expected_app_commit=app_commit,
        expected_version="0.13.2",
    )

    app["deployment"]["git_commit"] = "e" * 40
    with pytest.raises(ValueError, match="app commit"):
        verifier.verify_once(
            portal_url="https://portal.example/deployment.json",
            app_health_url="https://app.example/api/health",
            expected_portal_commit=portal_commit,
            expected_app_commit=app_commit,
            expected_version="0.13.2",
        )
