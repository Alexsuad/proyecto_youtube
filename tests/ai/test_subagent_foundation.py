import json
import unittest
from pathlib import Path

from src.ai.subagents import (
    assert_budget_within_limit,
    assert_cycle_within_limit,
    assert_handoff_integrity,
    assert_no_self_approval,
    assert_not_immutable_target,
    assert_read_allowed,
    assert_readiness_not_synthetic,
    assert_role_artifact_compatibility,
    assert_timeout_within_limit,
    assert_tool_allowed,
    assert_write_allowed,
    atomic_stage_write,
    build_handoff_checksum,
    build_run_context,
    get_agent_definition,
    load_registry,
)


LEGACY_AGENT_IDS = (
    "ROOT_ORCHESTRATOR",
    "EDITORIAL_DESIGN_PRODUCER",
    "INDEPENDENT_SEMANTIC_VERIFIER",
)
PRODUCER_FIXTURE = "YOUTUBE_ADAPTATION_PRODUCER"
VERIFIER_FIXTURE = "YOUTUBE_ADAPTATION_AUDITOR"


class TestSubagentFoundation(unittest.TestCase):
    def test_context_is_isolated_per_run(self):
        one = build_run_context(PRODUCER_FIXTURE, "RUN-1")
        two = build_run_context(PRODUCER_FIXTURE, "RUN-2")
        self.assertNotEqual(one.context_path, two.context_path)

    def test_permissions_are_enforced(self):
        assert_read_allowed(PRODUCER_FIXTURE, "profiles/editorial/mas_alla_del_guion/1.1.0/profile_payload.json")
        with self.assertRaises(PermissionError):
            assert_write_allowed(PRODUCER_FIXTURE, "config/subagent_registry.json")
        with self.assertRaises(PermissionError):
            assert_read_allowed(PRODUCER_FIXTURE, "profiles/editorial/../secrets.txt")
        with self.assertRaises(PermissionError):
            assert_write_allowed(PRODUCER_FIXTURE, "output-shadow/file.json")

    def test_tool_scope_is_enforced(self):
        assert_tool_allowed(VERIFIER_FIXTURE, "verify_semantics")
        with self.assertRaises(PermissionError):
            assert_tool_allowed(VERIFIER_FIXTURE, "produce_artifact")

    def test_producer_cannot_self_approve(self):
        with self.assertRaises(PermissionError):
            assert_no_self_approval(PRODUCER_FIXTURE, "approve")

    def test_verifier_cannot_modify_audited_artifact(self):
        with self.assertRaises(PermissionError):
            assert_not_immutable_target(VERIFIER_FIXTURE, "refined_thesis")

    def test_handoff_checksum_rejects_alteration(self):
        payload = {"artifact": "analysis", "artifact_id": "A-1", "checksum": "a" * 64}
        checksum = build_handoff_checksum(payload)
        assert_handoff_integrity(payload, checksum)
        altered = dict(payload)
        altered["artifact_id"] = "A-2"
        with self.assertRaises(ValueError):
            assert_handoff_integrity(altered, checksum)

    def test_unknown_or_incompatible_role_is_rejected(self):
        with self.assertRaises(ValueError):
            get_agent_definition("UNKNOWN_ROLE")
        with self.assertRaises(ValueError):
            assert_role_artifact_compatibility(VERIFIER_FIXTURE, "refined_thesis")

    def test_synthetic_cannot_authorize_readiness(self):
        with self.assertRaises(PermissionError):
            assert_readiness_not_synthetic(VERIFIER_FIXTURE, execution_mode="SYNTHETIC")

    def test_registry_defines_agent_handoff_compatible_agents(self):
        producer = get_agent_definition(PRODUCER_FIXTURE)
        verifier = get_agent_definition(VERIFIER_FIXTURE)
        self.assertEqual(producer["provider"], "agent_handoff")
        self.assertEqual(verifier["provider"], "agent_handoff")
        self.assertEqual(producer["model"], "handoff_only")
        self.assertEqual(verifier["model"], "handoff_only")

    def test_atomic_write_rolls_back_on_failure(self):
        root = Path("tmp_test_subagent_foundation")
        target = root / "artifact.json"
        root.mkdir(exist_ok=True)
        target.write_text(json.dumps({"previous": True}), encoding="utf-8")
        with self.assertRaises(OSError):
            atomic_stage_write(target, json.dumps({"new": True}), fail_after_stage=True)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"previous": True})
        self.assertFalse((root / "artifact.json.tmp").exists())

    def test_declared_limits_are_enforced(self):
        assert_budget_within_limit(PRODUCER_FIXTURE, consumed_tokens=1000, consumed_turns=2)
        with self.assertRaises(PermissionError):
            assert_budget_within_limit(PRODUCER_FIXTURE, consumed_tokens=20000, consumed_turns=2)
        with self.assertRaises(PermissionError):
            assert_timeout_within_limit(PRODUCER_FIXTURE, timeout_seconds=120)
        with self.assertRaises(PermissionError):
            assert_cycle_within_limit(PRODUCER_FIXTURE, cycle_number=3)

    def test_registry_does_not_claim_demonstrated_agents_without_evidence(self):
        producer = get_agent_definition(PRODUCER_FIXTURE)
        verifier = get_agent_definition(VERIFIER_FIXTURE)
        self.assertEqual(producer["maturity_status"], "AGENT_TESTED_IN_ISOLATION")
        self.assertEqual(verifier["maturity_status"], "AGENT_TESTED_IN_ISOLATION")

    def test_legacy_agents_are_absent_from_registry(self):
        for legacy_id in LEGACY_AGENT_IDS:
            with self.assertRaises(ValueError):
                get_agent_definition(legacy_id)

    def test_every_registered_agent_has_active_prompt_and_contract(self):
        registry = load_registry()
        prompt_registry = json.loads(Path("config/agent_prompt_registry.json").read_text(encoding="utf-8"))
        active_prompts = {
            p["role_id"]: p
            for p in prompt_registry["prompts"]
            if p.get("status") == "ACTIVE"
        }
        for agent in registry["agents"]:
            role_id = agent["agent_id"]
            self.assertIn(role_id, active_prompts, f"{role_id} registrado sin prompt ACTIVE")
            prompt_version = active_prompts[role_id]["prompt_version"]
            prompt_file = Path("prompts") / "roles" / role_id / f"{prompt_version}.md"
            self.assertTrue(prompt_file.exists(), f"Prompt file ausente: {prompt_file}")
            self.assertNotEqual(agent["provider"].lower(), "mock", f"{role_id} no debe ser mock")


if __name__ == "__main__":
    unittest.main()
