from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from qs_dmss import ai as ai_module
from qs_dmss.ai import (
    AIConfigurationError,
    AIGeneration,
    AIProviderSettings,
    AIResponseValidationError,
    OpenAICompatibleProvider,
    ai_interaction_bundle_path,
    build_ai_runtime,
    load_ai_interaction,
    make_ai_artifact,
    persist_ai_interaction,
    review_ai_interaction,
    validate_ai_response,
)


def _context() -> dict:
    return {
        "schema_version": 1,
        "intent": "summary",
        "artifacts": [
            make_ai_artifact(
                "run/example/metrics",
                "run_metrics",
                {"energy_drift": 1.25, "verification_success": True},
            )
        ],
    }


def _response(*, statement: str = "Energy drift is recorded as 1.25.") -> dict:
    return {
        "schema_version": 1,
        "title": "Evidence summary",
        "draft": "The recorded workflow evidence remains bounded to the packaged run.",
        "findings": [
            {
                "statement": statement,
                "artifact_ids": ["run/example/metrics"],
            }
        ],
        "limitations": ["This is not physical validation."],
        "proposed_actions": ["Ask a researcher to review the recorded evidence."],
    }


def test_ai_response_requires_known_artifact_citations_and_recorded_numbers() -> None:
    context = _context()
    validated = validate_ai_response(
        _response(),
        context=context,
        allowed_artifact_ids={"run/example/metrics"},
    )
    assert validated["findings"][0]["artifact_ids"] == ["run/example/metrics"]

    unknown_citation = _response()
    unknown_citation["findings"][0]["artifact_ids"] = ["outside/context"]
    with pytest.raises(AIResponseValidationError, match="outside the approved context"):
        validate_ai_response(
            unknown_citation,
            context=context,
            allowed_artifact_ids={"run/example/metrics"},
        )

    with pytest.raises(AIResponseValidationError, match="numerical values absent"):
        validate_ai_response(
            _response(statement="Energy drift is recorded as 9.75."),
            context=context,
            allowed_artifact_ids={"run/example/metrics"},
        )

    unsupported_field = _response()
    unsupported_field["hidden_reasoning"] = "must not persist"
    with pytest.raises(AIResponseValidationError, match="unsupported fields"):
        validate_ai_response(
            unsupported_field,
            context=context,
            allowed_artifact_ids={"run/example/metrics"},
        )


def test_ai_response_checks_proposed_actions_and_ignores_identifier_numbers() -> None:
    context = _context()
    context["artifacts"][0]["id"] = "run/975/metrics"
    context["artifacts"][0]["data"].update(
        {
            "run_id": "run-975",
            "created_at": "2026-07-22T01:19:45Z",
            "bundle_sha256": "975" + ("a" * 61),
        }
    )
    allowed_artifact_ids = {"run/975/metrics"}

    unsupported_action = _response()
    unsupported_action["findings"][0]["artifact_ids"] = ["run/975/metrics"]
    unsupported_action["proposed_actions"] = ["Repeat the workflow 975 times."]
    with pytest.raises(AIResponseValidationError, match="numerical values absent"):
        validate_ai_response(
            unsupported_action,
            context=context,
            allowed_artifact_ids=allowed_artifact_ids,
        )

    supported_action = _response()
    supported_action["findings"][0]["artifact_ids"] = ["run/975/metrics"]
    supported_action["proposed_actions"] = ["Review the recorded drift of 1.25."]
    validated = validate_ai_response(
        supported_action,
        context=context,
        allowed_artifact_ids=allowed_artifact_ids,
    )
    assert validated["proposed_actions"] == ["Review the recorded drift of 1.25."]


def test_ai_provider_requires_https_and_explicit_remote_authorization() -> None:
    with pytest.raises(AIConfigurationError, match="must use HTTPS"):
        OpenAICompatibleProvider(
            AIProviderSettings(
                enabled=True,
                base_url="http://models.example.test/v1",
                model="research-model",
                allow_remote=True,
            )
        )

    with pytest.raises(AIConfigurationError, match="ALLOW_REMOTE"):
        OpenAICompatibleProvider(
            AIProviderSettings(
                enabled=True,
                base_url="https://models.example.test/v1",
                model="research-model",
            )
        )

    with pytest.raises(AIConfigurationError, match="query or fragment"):
        OpenAICompatibleProvider(
            AIProviderSettings(
                enabled=True,
                base_url="http://127.0.0.1:11434/v1?redirect=https://example.test",
                model="local-research-model",
            )
        )

    provider = OpenAICompatibleProvider(
        AIProviderSettings(
            enabled=True,
            base_url="http://127.0.0.1:11434/v1",
            model="local-research-model",
        )
    )
    assert provider.endpoint_scope == "local"


def test_disabled_ai_ignores_inactive_provider_settings(monkeypatch) -> None:
    monkeypatch.delenv("QS_DMSS_AI_ENABLED", raising=False)
    monkeypatch.setenv("QS_DMSS_AI_TIMEOUT_SECONDS", "not-active")
    runtime = build_ai_runtime()
    assert runtime.provider is None
    assert runtime.status["enabled"] is False
    assert runtime.status["availability"] == "disabled"


def test_injected_remote_ai_provider_requires_explicit_authorization(
    monkeypatch,
) -> None:
    class RemoteProvider:
        provider_id = "remote-test-provider"
        model = "remote-test-model"
        endpoint_scope = "remote"

    provider = RemoteProvider()
    monkeypatch.delenv("QS_DMSS_AI_ALLOW_REMOTE", raising=False)
    monkeypatch.delenv("QS_DMSS_AI_HOSTED_ENABLED", raising=False)
    blocked = build_ai_runtime(provider)
    assert blocked.provider is None
    assert blocked.status["availability"] == "configuration_error"
    assert blocked.status["remote_allowed"] is False
    assert blocked.status["hosted_enabled"] is False
    assert "QS_DMSS_AI_ALLOW_REMOTE=1" in blocked.status["message"]

    monkeypatch.setenv("QS_DMSS_AI_ALLOW_REMOTE", "1")
    authorized = build_ai_runtime(provider)
    assert authorized.provider is provider
    assert authorized.status["availability"] == "ready"
    assert authorized.status["remote_allowed"] is True


def test_openai_compatible_adapter_uses_structured_bounded_contract(monkeypatch) -> None:
    response_body = json.dumps(
        {
            "id": "provider-request-1",
            "choices": [{"message": {"content": json.dumps(_response())}}],
            "usage": {
                "prompt_tokens": True,
                "completion_tokens": -1,
                "total_tokens": 30,
                "cached_tokens": 12,
            },
        }
    ).encode("utf-8")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, maximum_bytes: int) -> bytes:
            assert maximum_bytes == ai_module.MAX_AI_PROVIDER_RESPONSE_BYTES + 1
            return response_body

    class FakeOpener:
        request = None

        def open(self, request, timeout):
            self.request = request
            assert timeout == 12
            return FakeResponse()

    opener = FakeOpener()
    monkeypatch.setattr(ai_module, "build_opener", lambda handler: opener)
    provider = OpenAICompatibleProvider(
        AIProviderSettings(
            enabled=True,
            base_url="http://127.0.0.1:11434/v1",
            model="local-research-model",
            api_key="test-secret",
            timeout_seconds=12,
        )
    )

    generation = provider.generate(
        intent="summary",
        context=_context(),
        allowed_artifact_ids={"run/example/metrics"},
    )

    assert opener.request.full_url == "http://127.0.0.1:11434/v1/chat/completions"
    assert opener.request.get_header("Authorization") == "Bearer test-secret"
    request_payload = json.loads(opener.request.data)
    assert request_payload["model"] == "local-research-model"
    assert request_payload["temperature"] == 0
    assert request_payload["response_format"] == {"type": "json_object"}
    assert generation.response["findings"][0]["artifact_ids"] == [
        "run/example/metrics"
    ]
    assert generation.provenance["usage"] == {"total_tokens": 30}
    assert "test-secret" not in json.dumps(generation.provenance)


def test_ai_interaction_is_separate_manifested_artifact_with_human_review(
    tmp_path: Path,
) -> None:
    context = _context()
    generation = AIGeneration(
        response=_response(),
        provenance={
            "provider": "test-provider",
            "model": "test-model",
            "endpoint_scope": "local",
            "context_sha256": "a" * 64,
            "tool_calls": [],
            "api_key": "must-not-persist",
        },
    )
    record = persist_ai_interaction(
        tmp_path,
        intent="summary",
        subject={"scenario_name": "canonical-simulation", "run_id": "example"},
        context=context,
        generation=generation,
    )
    interaction_id = record["interaction_id"]
    interaction_dir = tmp_path / "ai-interactions" / interaction_id
    assert record["human_review"]["status"] == "pending"
    assert not (interaction_dir / "context.json").exists()

    reviewed = review_ai_interaction(
        tmp_path,
        interaction_id,
        status="edited",
        reviewer="Research lead",
        edited_draft="Human-reviewed evidence summary.",
    )
    assert reviewed["human_review"]["status"] == "edited"
    assert reviewed["human_review"]["reviewer"] == "Research lead"
    assert reviewed["review_history"] == [reviewed["human_review"]]
    assert reviewed["provenance"]["context_sha256"] == hashlib.sha256(
        json.dumps(context, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert "must-not-persist" not in json.dumps(reviewed)
    assert load_ai_interaction(tmp_path, interaction_id) == reviewed

    manifest = json.loads(
        (interaction_dir / "manifest.sha256.json").read_text(encoding="utf-8")
    )
    record_entry = next(
        entry for entry in manifest["files"] if entry["path"] == "interaction.json"
    )
    record_bytes = (interaction_dir / "interaction.json").read_bytes()
    assert record_entry["sha256"] == hashlib.sha256(record_bytes).hexdigest()

    bundle_path = ai_interaction_bundle_path(tmp_path, interaction_id)
    with zipfile.ZipFile(bundle_path) as archive:
        names = set(archive.namelist())
    assert f"{interaction_id}/interaction.json" in names
    assert f"{interaction_id}/manifest.sha256.json" in names
    assert str(tmp_path) not in json.dumps(reviewed)


def test_ai_interaction_retries_an_identifier_collision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    colliding_id = "ai-20260722T011945Z-aaaaaaaa"
    replacement_id = "ai-20260722T011945Z-bbbbbbbb"
    colliding_dir = tmp_path / "ai-interactions" / colliding_id
    colliding_dir.mkdir(parents=True)
    marker = colliding_dir / "existing-artifact.txt"
    marker.write_text("preserve", encoding="utf-8")
    generated_ids = iter((colliding_id, replacement_id))
    monkeypatch.setattr(
        ai_module,
        "create_ai_interaction_id",
        lambda: next(generated_ids),
    )

    record = persist_ai_interaction(
        tmp_path,
        intent="summary",
        subject={"scenario_name": "canonical-simulation"},
        context=_context(),
        generation=AIGeneration(
            response=_response(),
            provenance={
                "provider": "test-provider",
                "model": "test-model",
                "endpoint_scope": "local",
                "tool_calls": [],
            },
        ),
    )

    assert record["interaction_id"] == replacement_id
    assert marker.read_text(encoding="utf-8") == "preserve"
    assert load_ai_interaction(tmp_path, replacement_id) == record


def test_ai_edited_review_requires_human_wording(tmp_path: Path) -> None:
    record = persist_ai_interaction(
        tmp_path,
        intent="summary",
        subject={"scenario_name": "canonical-simulation"},
        context=_context(),
        generation=AIGeneration(
            response=_response(),
            provenance={
                "provider": "test-provider",
                "model": "test-model",
                "endpoint_scope": "local",
                "tool_calls": [],
            },
        ),
    )
    with pytest.raises(AIResponseValidationError, match="edited_draft is required"):
        review_ai_interaction(
            tmp_path,
            record["interaction_id"],
            status="edited",
            reviewer="Research lead",
        )


def test_ai_rejects_tool_provenance_before_creating_an_artifact(
    tmp_path: Path,
) -> None:
    with pytest.raises(AIResponseValidationError, match="must not expose tool calls"):
        persist_ai_interaction(
            tmp_path,
            intent="next",
            subject={"scenario_name": "canonical-simulation"},
            context=_context(),
            generation=AIGeneration(
                response=_response(),
                provenance={
                    "provider": "unsafe-provider",
                    "model": "unsafe-model",
                    "endpoint_scope": "local",
                    "tool_calls": [{"name": "launch_run"}],
                },
            ),
        )
    assert not (tmp_path / "ai-interactions").exists()
