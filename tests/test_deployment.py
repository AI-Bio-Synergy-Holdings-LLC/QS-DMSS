from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

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


def test_public_verifier_requires_matching_render_provenance(monkeypatch) -> None:
    verifier = _load_verifier()
    commit = "c" * 40
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
            "git_commit": commit,
            "git_branch": "main",
        },
    }
    app = {
        "status": "ok",
        "version": "0.13.2",
        "deployment": {
            "provider": "render",
            "git_commit": commit,
            "git_branch": "main",
        },
    }

    def fetch(url: str, expected_commit: str):
        assert expected_commit == commit
        return (portal if "deployment.json" in url else app), headers

    monkeypatch.setattr(verifier, "_fetch_json", fetch)

    verifier.verify_once(
        portal_url="https://portal.example/deployment.json",
        app_health_url="https://app.example/api/health",
        expected_commit=commit,
        expected_version="0.13.2",
    )

    app["deployment"]["git_commit"] = "d" * 40
    with pytest.raises(ValueError, match="app commit"):
        verifier.verify_once(
            portal_url="https://portal.example/deployment.json",
            app_health_url="https://app.example/api/health",
            expected_commit=commit,
            expected_version="0.13.2",
        )
