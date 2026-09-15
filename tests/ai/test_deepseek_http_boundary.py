"""HTTP boundary tests for DeepSeekProvider using pytest-httpserver.

These tests verify that the real DeepSeek HTTP client (urllib.request) can:
- send a POST to /chat/completions with correct headers and body
- receive and parse a valid DeepSeek-compatible response
- classify invalid JSON content as INVALID_RESPONSE
- classify HTTP 500 as PROVIDER_UNAVAILABLE
- be exercised through the canonical runtime execute() path

NO real AI is called. NO real API key is used. All traffic stays on localhost.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from werkzeug.wrappers import Response as WerkzeugResponse

from pytest_httpserver import HTTPServer

from src.ai.contracts import ExecutionRequest, ExecutionStatus, InputArtifact
from src.ai.execution import execute
from src.ai.providers.deepseek import DeepSeekProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_KEY = "test-key"
FAKE_MODEL = "deepseek-chat"
CAPABILITY = "B5_I2_SEMANTIC_AUDITOR"
SKILL_ID = "skill_http_boundary"
SKILL_VERSION = "1.0.0"
AUDITOR_ROLE = "SCRIPT_PRODUCT_AUDITOR"


def _valid_deepseek_response(content: dict) -> dict:
    """Build a DeepSeek-compatible chat completion response."""
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1700000000,
        "model": FAKE_MODEL,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": json.dumps(content)},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }


def _provider_request(
    base_url: str,
    *,
    prompt: str = "instruccion de test",
    model: str | None = FAKE_MODEL,
) -> ExecutionRequest:
    """Build an ExecutionRequest targeting DeepSeekProvider."""
    return ExecutionRequest(
        capability_id=CAPABILITY,
        skill_id=SKILL_ID,
        skill_version=SKILL_VERSION,
        input_artifacts=[],
        output_schema="topic_belonging_assessment",
        provider="deepseek",
        model=model,
        execution_mode="deepseek",
        config={
            "base_url": base_url,
            "api_key_env": "DEEPSEEK_API_KEY",
            "model_env": "DEEPSEEK_MODEL",
            "prompt": prompt,
            "local_available": False,
        },
    )


def _sha256(p: Path) -> str:
    import hashlib
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _setup_governed_env(root: Path) -> None:
    """Set up the minimal governed environment for execute() path."""
    (root / "config").mkdir(exist_ok=True)
    (root / "output").mkdir(exist_ok=True)

    # Capability registry
    (root / "config" / "capability_registry.json").write_text(
        json.dumps({
            "registry_version": "1.0.0",
            "authority": "CAPABILITY_FUNCTIONAL_AUTHORITY",
            "routing_consumer": "HTTP_BOUNDARY_TEST",
            "compatibility_tokens": {
                "maturity": {}, "availability": {}, "assurance": {},
                "approval": {}, "evidence": {},
            },
            "capabilities": [
                {
                    "capability_id": CAPABILITY,
                    "domain": "SCRIPT_PRODUCT",
                    "functional_authority_domain": "SCRIPT_PRODUCT",
                    "purpose": "HTTP boundary test fixture.",
                    "functional_requirements": [],
                    "implementation_kind": "DETERMINISTIC",
                    "maturity_status": "DEFINED",
                    "assigned_role": [AUDITOR_ROLE],
                    "routing_required": False,
                }
            ],
        }),
        encoding="utf-8",
    )

    # Context resolution policy
    shutil.copy(
        Path(__file__).resolve().parents[2] / "config" / "context_resolution_policy.json",
        root / "config" / "context_resolution_policy.json",
    )
    shutil.copy(
        Path(__file__).resolve().parents[2] / "config" / "agent_execution_profiles.json",
        root / "config" / "agent_execution_profiles.json",
    )
    (root / "config" / "execution-family-selection.json").write_text(
        json.dumps({
            "selection_version": "1.0.0",
            "families": {
                "AGENT_HARNESS": False,
                "API_PROVIDER": True,
                "LOCAL_MODEL": False,
            },
        }),
        encoding="utf-8",
    )

    # Control state
    (root / "control.md").write_text(
        "CURRENT_MISSION: HTTP_BOUNDARY_TEST\n",
        encoding="utf-8",
    )

    state_sha = _sha256(root / "control.md")

    # Scope & authorization
    from src.core.mission_authorization import scope_checksum

    scope = {
        "mission_id": "HTTP_BOUNDARY_TEST",
        "capability_ids": [CAPABILITY],
        "role_ids": [AUDITOR_ROLE],
        "execution_profile_ids": ["ANY"],
        "execution_interface": "ANY",
        "allowed_operations": ["EXECUTE_CAPABILITY"],
        "allowed_paths": ["output/"],
        "allowed_routes": ["api_model"],
        "execution_mode": "ANY",
        "live_state_sha256": state_sha,
        "contains_material_repair": False,
        "repair_integrity_evidence_path": "repair.json",
    }
    decision = root / "authority-decision.json"
    decision.write_text(
        json.dumps({
            "mission_id": "HTTP_BOUNDARY_TEST",
            "decision": "APPROVE",
            "artifact_version": "1.0.0",
            "authorized_scope_sha256": scope_checksum(scope),
        }),
        encoding="utf-8",
    )
    (root / "mission-authorization.json").write_text(
        json.dumps({
            "mission_id": "HTTP_BOUNDARY_TEST",
            "authorization": {
                "live_state_path": "control.md",
                "live_state_sha256": state_sha,
                "capability_ids": [CAPABILITY],
                "role_ids": [AUDITOR_ROLE],
                "execution_profile_ids": ["ANY"],
                "execution_interface": "ANY",
                "allowed_operations": ["EXECUTE_CAPABILITY"],
                "allowed_paths": ["output/"],
                "allowed_routes": ["api_model"],
                "execution_mode": "ANY",
                "single_use": False,
                "authority_ref": "authority-decision.json",
                "authority_sha256": _sha256(decision),
                "authorized_scope_sha256": scope_checksum(scope),
                "executor_substitution_policy": "COMPATIBLE_INTERFACE_ONLY",
                "contains_material_repair": False,
                "repair_integrity_evidence_path": "repair.json",
            },
        }),
        encoding="utf-8",
    )

    # Routing policy
    (root / "routing.yaml").write_text(
        "capabilities:\n"
        "  B5_I2_SEMANTIC_AUDITOR:\n"
        "    routing:\n"
        "      allow_external_api: true\n",
        encoding="utf-8",
    )


def _governed_runtime_request(
    tmp_path: Path,
    base_url: str,
) -> ExecutionRequest:
    """Build a governed ExecutionRequest for the canonical execute() path.

    Finding 02 correction: provider is NOT set explicitly. The runtime must
    resolve DeepSeek through the REAL execution profile and routing
    infrastructure, matching the product path.
    """
    _setup_governed_env(tmp_path)
    return ExecutionRequest(
        capability_id=CAPABILITY,
        skill_id=SKILL_ID,
        skill_version=SKILL_VERSION,
        input_artifacts=[],
        output_schema="topic_belonging_assessment",
        provider=None,  # <-- NOT explicitly forced; routing must resolve it
        execution_mode="REAL",
        execution_route="api_model",
        execution_profile="deepseek_chat",
        model=FAKE_MODEL,
        role=AUDITOR_ROLE,
        config={
            "base_url": base_url,
            "api_key_env": "DEEPSEEK_API_KEY",
            "model_env": "DEEPSEEK_MODEL",
            "prompt": "instruccion de test",
            "repository_root": str(tmp_path),
            "mission_authorization_path": "mission-authorization.json",
            "context_policy_path": "config/context_resolution_policy.json",
            "routing_policy_path": tmp_path / "routing.yaml",
            "execution_profiles_path": tmp_path / "config" / "agent_execution_profiles.json",
            "execution_family_selection_path": "config/execution-family-selection.json",
            "paid_cost_approved": True,
            "local_available": False,
        },
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDirectProviderValidResponse:
    """A. Provider + valid HTTP response -> PASS"""

    def test_valid_json_content_is_parsed(self, httpserver: HTTPServer, monkeypatch: pytest.MonkeyPatch) -> None:
        expected_content = {"topic": "ciencia", "belongs": True, "confidence": 0.95}
        httpserver.expect_oneshot_request(
            "/chat/completions",
            method="POST",
        ).respond_with_json(_valid_deepseek_response(expected_content))

        monkeypatch.setenv("DEEPSEEK_API_KEY", FAKE_KEY)
        monkeypatch.setenv("DEEPSEEK_MODEL", FAKE_MODEL)

        provider = DeepSeekProvider()
        request = _provider_request(httpserver.url_for(""))

        parsed, usage = provider.execute(request)

        assert parsed == expected_content
        assert usage["provider_or_adapter"] == "deepseek"
        assert usage["model_or_evaluator"] == FAKE_MODEL
        assert "prompt_tokens" in usage
        httpserver.check()

    def test_request_contains_correct_method_path_headers_and_body(
        self, httpserver: HTTPServer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured_requests: list[dict] = []

        def handler(request):
            captured_requests.append({
                "method": request.method,
                "path": request.path,
                "headers": {k: v for k, v in request.headers if k.lower() in ("authorization", "content-type")},
                "body": json.loads(request.data.decode("utf-8")),
            })
            return WerkzeugResponse(
                response=json.dumps(_valid_deepseek_response({"ok": True})),
                status=200,
                content_type="application/json",
            )

        httpserver.expect_request("/chat/completions", method="POST").respond_with_handler(handler)

        monkeypatch.setenv("DEEPSEEK_API_KEY", FAKE_KEY)
        monkeypatch.setenv("DEEPSEEK_MODEL", FAKE_MODEL)

        prompt_text = "evalua este contenido"
        provider = DeepSeekProvider()
        request = _provider_request(httpserver.url_for(""), prompt=prompt_text)

        parsed, _ = provider.execute(request)

        assert len(captured_requests) == 1
        req = captured_requests[0]

        # Method and path
        assert req["method"] == "POST"
        assert req["path"] == "/chat/completions"

        # Auth header
        assert req["headers"]["Authorization"] == f"Bearer {FAKE_KEY}"
        assert req["headers"]["Content-Type"] == "application/json"

        # Body contract
        body = req["body"]
        assert body["model"] == FAKE_MODEL
        assert isinstance(body["messages"], list)
        assert len(body["messages"]) == 1
        assert body["messages"][0]["role"] == "user"
        assert body["messages"][0]["content"] == prompt_text
        assert body["response_format"] == {"type": "json_object"}

        assert parsed == {"ok": True}
        httpserver.check()


class TestDirectProviderInvalidContent:
    """B. Provider + HTTP 200 but non-JSON content -> INVALID_RESPONSE"""

    def test_non_json_content_raises_invalid_response(
        self, httpserver: HTTPServer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        bad_response = {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1700000000,
            "model": FAKE_MODEL,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "esto no es JSON valido"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }
        httpserver.expect_oneshot_request(
            "/chat/completions",
            method="POST",
        ).respond_with_json(bad_response)

        monkeypatch.setenv("DEEPSEEK_API_KEY", FAKE_KEY)
        monkeypatch.setenv("DEEPSEEK_MODEL", FAKE_MODEL)

        provider = DeepSeekProvider()
        request = _provider_request(httpserver.url_for(""))

        with pytest.raises(ValueError, match="INVALID_RESPONSE"):
            provider.execute(request)

        httpserver.check()

    def test_missing_choices_raises_invalid_response(
        self, httpserver: HTTPServer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        httpserver.expect_oneshot_request(
            "/chat/completions",
            method="POST",
        ).respond_with_json({"id": "chatcmpl-test", "usage": {}})

        monkeypatch.setenv("DEEPSEEK_API_KEY", FAKE_KEY)
        monkeypatch.setenv("DEEPSEEK_MODEL", FAKE_MODEL)

        provider = DeepSeekProvider()
        request = _provider_request(httpserver.url_for(""))

        with pytest.raises(ValueError, match="INVALID_RESPONSE"):
            provider.execute(request)

        httpserver.check()


class TestDirectProviderHttpError:
    """C. Provider + HTTP 500 -> PROVIDER_UNAVAILABLE"""

    def test_http_500_classified_as_provider_unavailable(
        self, httpserver: HTTPServer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        httpserver.expect_oneshot_request(
            "/chat/completions",
            method="POST",
        ).respond_with_data(
            b"Internal Server Error",
            status=500,
            content_type="text/plain",
        )

        monkeypatch.setenv("DEEPSEEK_API_KEY", FAKE_KEY)
        monkeypatch.setenv("DEEPSEEK_MODEL", FAKE_MODEL)

        provider = DeepSeekProvider()
        request = _provider_request(httpserver.url_for(""))

        with pytest.raises(RuntimeError, match="PROVIDER_UNAVAILABLE"):
            provider.execute(request)

        httpserver.check()

    def test_http_401_classified_as_provider_unavailable(
        self, httpserver: HTTPServer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        httpserver.expect_oneshot_request(
            "/chat/completions",
            method="POST",
        ).respond_with_data(
            b"Unauthorized",
            status=401,
            content_type="text/plain",
        )

        monkeypatch.setenv("DEEPSEEK_API_KEY", FAKE_KEY)
        monkeypatch.setenv("DEEPSEEK_MODEL", FAKE_MODEL)

        provider = DeepSeekProvider()
        request = _provider_request(httpserver.url_for(""))

        with pytest.raises(RuntimeError, match="PROVIDER_UNAVAILABLE"):
            provider.execute(request)

        httpserver.check()


_TOPIC_TRIGGERS = {key: False for key in [
    "political_partisan_sensitivity", "high_sensitivity", "audience_matrix_change",
    "excluded_boundary_reinterpretation", "new_personal_exposure", "voice_or_author_persona_change",
    "positioning_expansion", "permanent_effect", "high_precedent_risk", "experimental_territory",
]}
_VALID_CHECKSUM = "a" * 64


def _valid_topic_belonging_assessment() -> dict:
    """Build a valid topic_belonging_assessment matching the schema."""
    return {
        "assessment_id": "TBA-HTTP-001",
        "producer_actor_id": "producer-http",
        "producer_run_id": "run-http",
        "producer_role_id": "CHANNEL_INTELLIGENCE_PRODUCER",
        "profile_id": "mas_alla_del_guion",
        "profile_version": "1.2.2",
        "profile_checksum": _VALID_CHECKSUM,
        "topic": "Tema de test HTTP",
        "topic_input_id": "TBI-HTTP-001",
        "entry_mode": "ANCHOR_WORK_FIRST",
        "central_question": "Pregunta de test",
        "proposed_angle": "Angulo de test",
        "proposed_territory": "Individuo e identidad",
        "initial_evidence": ["evidence-1"],
        "sensitive_risks": [],
        "territory_classification": "ACTIVE",
        "identity_alignment": "ALIGNED",
        "promise_alignment": "ALIGNED",
        "risks": [],
        "recommended_conditions": [],
        "recommended_exclusions": [],
        "owner_escalation_recommended": False,
        "evidence": ["evidence-1"],
        "status": "CLOSED_FOR_REVIEW",
        "artifact_checksum": _VALID_CHECKSUM,
        "strategic_triggers": _TOPIC_TRIGGERS,
        "provenance": {
            "actor_id": "producer-http",
            "run_id": "run-http",
            "role_id": "CHANNEL_INTELLIGENCE_PRODUCER",
            "input_checksums": [_VALID_CHECKSUM],
            "output_checksum": _VALID_CHECKSUM,
        },
    }


class TestCanonicalRuntimePath:
    """D. REAL execute() -> profile/routing -> DeepSeekProvider -> HTTP -> Result

    Finding 02 correction: provider=None in the request, execution_mode="REAL".
    The runtime must resolve DeepSeek through its canonical profile route.
    """

    def test_runtime_valid_response_succeeds(
        self, httpserver: HTTPServer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        expected_content = _valid_topic_belonging_assessment()
        httpserver.expect_oneshot_request(
            "/chat/completions",
            method="POST",
        ).respond_with_json(_valid_deepseek_response(expected_content))

        monkeypatch.setenv("DEEPSEEK_API_KEY", FAKE_KEY)
        monkeypatch.setenv("DEEPSEEK_MODEL", FAKE_MODEL)
        monkeypatch.chdir(tmp_path)

        request = _governed_runtime_request(tmp_path, httpserver.url_for(""))
        # Verify the request starts provider-neutral and in the REAL product mode.
        assert request.provider is None
        assert request.execution_mode == "REAL"
        assert request.execution_profile == "deepseek_chat"
        assert request.execution_route == "api_model"
        result = execute(request)

        assert result.status is ExecutionStatus.SUCCEEDED
        assert result.output["assessment_id"] == "TBA-HTTP-001"
        assert result.output["topic"] == "Tema de test HTTP"
        # The canonical route resolver mutates the request with its verified
        # route. This proves provider selection was performed by runtime.
        assert request.resolved_route is not None
        assert request.resolved_route.execution_profile == "deepseek_chat"
        assert request.resolved_route.execution_route == "api_model"
        assert request.resolved_route.provider_adapter == "deepseek"
        assert request.provider == "deepseek"
        assert result.provider == "deepseek"
        assert result.model == FAKE_MODEL
        assert result.is_real_editorial_execution is True
        httpserver.check()

    def test_runtime_http_error_is_classified(
        self, httpserver: HTTPServer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        httpserver.expect_oneshot_request(
            "/chat/completions",
            method="POST",
        ).respond_with_data(
            b"Internal Server Error",
            status=500,
            content_type="text/plain",
        )

        monkeypatch.setenv("DEEPSEEK_API_KEY", FAKE_KEY)
        monkeypatch.setenv("DEEPSEEK_MODEL", FAKE_MODEL)
        monkeypatch.chdir(tmp_path)

        request = _governed_runtime_request(tmp_path, httpserver.url_for(""))
        result = execute(request)

        assert result.status is ExecutionStatus.BLOCKED_BY_RUNTIME_PROVIDER
        assert result.usage["availability_status"] == "PROVIDER_UNAVAILABLE"
        httpserver.check()

    def test_runtime_invalid_content_is_classified(
        self, httpserver: HTTPServer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        bad_response = {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1700000000,
            "model": FAKE_MODEL,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "not valid json at all"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        httpserver.expect_oneshot_request(
            "/chat/completions",
            method="POST",
        ).respond_with_json(bad_response)

        monkeypatch.setenv("DEEPSEEK_API_KEY", FAKE_KEY)
        monkeypatch.setenv("DEEPSEEK_MODEL", FAKE_MODEL)
        monkeypatch.chdir(tmp_path)

        request = _governed_runtime_request(tmp_path, httpserver.url_for(""))
        result = execute(request)

        assert result.status is ExecutionStatus.FAILED
        assert result.usage["availability_status"] == "INVALID_RESPONSE"
        httpserver.check()


class TestUnexpectedRequestDetection:
    """Verify httpserver detects requests that don't match expectations.

    Finding 01 correction: The previous test sent the EXPECTED request and
    passed httpserver.check() — that only proves correct requests are accepted.
    This test proves that an UNEXPECTED request (wrong path) is detected.
    """

    def test_unexpected_path_is_detected_by_httpserver(
        self, httpserver: HTTPServer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Arrange: expect a request to a WRONG path
        httpserver.expect_oneshot_request(
            "/wrong/path",
            method="POST",
        ).respond_with_json(
            _valid_deepseek_response({"ok": True})
        )

        monkeypatch.setenv("DEEPSEEK_API_KEY", FAKE_KEY)
        monkeypatch.setenv("DEEPSEEK_MODEL", FAKE_MODEL)

        provider = DeepSeekProvider()
        # The provider will send to /chat/completions, NOT /wrong/path
        request = _provider_request(httpserver.url_for(""))

        # Act: provider sends to /chat/completions but server expected /wrong/path
        # The server returns 500 (no handler matched), provider raises RuntimeError
        with pytest.raises(RuntimeError, match="PROVIDER_UNAVAILABLE"):
            provider.execute(request)

        # Assert: httpserver.check() detects the mismatch
        # It should fail because:
        #   1. The expected request to /wrong/path was never received
        #   2. An unexpected request to /chat/completions was received
        with pytest.raises(AssertionError):
            httpserver.check()


class TestMissingCredentials:
    """Verify provider blocks without API key."""

    def test_missing_api_key_raises_credentials_missing(
        self, httpserver: HTTPServer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.setenv("DEEPSEEK_MODEL", FAKE_MODEL)

        provider = DeepSeekProvider()
        request = _provider_request(httpserver.url_for(""))

        with pytest.raises(PermissionError, match="CREDENTIALS_MISSING"):
            provider.execute(request)

    def test_missing_model_raises_model_unavailable(
        self, httpserver: HTTPServer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEEPSEEK_API_KEY", FAKE_KEY)
        monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)

        provider = DeepSeekProvider()
        # model=None so provider must fall back to env var (which is deleted)
        request = _provider_request(httpserver.url_for(""), model=None)

        with pytest.raises(ValueError, match="MODEL_UNAVAILABLE"):
            provider.execute(request)
