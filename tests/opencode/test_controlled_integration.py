"""Regression checks for the repository-local OpenCode integration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
PREEXISTING_UNTRACKED = (
    "output/r6_b/",
    "reference/Ejemplo_01.md",
    "reference/estilo_usuario/Ejemplo_02.md",
)


def read_frontmatter(path: Path) -> tuple[dict[str, object], str]:
    raw = path.read_text(encoding="utf-8")
    _, frontmatter, body = raw.split("---", 2)
    # The checked frontmatter uses only scalars and one-level mappings.
    lines = [line for line in frontmatter.strip().splitlines() if line]
    return {line.split(":", 1)[0].strip(): line.split(":", 1)[1].strip() for line in lines if ":" in line}, body


def content_digest(target: Path) -> str:
    digest = hashlib.sha256()
    if target.is_file():
        digest.update(target.name.encode("utf-8"))
        digest.update(target.read_bytes())
        return digest.hexdigest()

    for child in sorted(path for path in target.rglob("*") if path.is_file()):
        digest.update(child.relative_to(target).as_posix().encode("utf-8"))
        digest.update(child.read_bytes())
    return digest.hexdigest()


class ControlledOpenCodeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        cls.missing_preexisting = [
            relative_path
            for relative_path in PREEXISTING_UNTRACKED
            if not (ROOT / relative_path).exists() or f"?? {relative_path}" not in status
        ]
        cls.preexisting_digests = {
            relative_path: content_digest(ROOT / relative_path)
            for relative_path in PREEXISTING_UNTRACKED
            if relative_path not in cls.missing_preexisting
        }

    @classmethod
    def tearDownClass(cls) -> None:
        for relative_path, expected_digest in cls.preexisting_digests.items():
            assert content_digest(ROOT / relative_path) == expected_digest, relative_path

    def setUp(self) -> None:
        self.config = json.loads((ROOT / "opencode.json").read_text(encoding="utf-8"))

    def test_repository_keeps_controlled_opencode_permissions(self) -> None:
        self.assertEqual(self.config["$schema"], "https://opencode.ai/config.json")
        self.assertNotIn("agent", self.config)
        self.assertEqual(self.config["permission"]["bash"]["rm -rf *"], "deny")

        implementer, _ = read_frontmatter(ROOT / ".opencode/agents/technical-implementer.md")
        reviewer, _ = read_frontmatter(ROOT / ".opencode/agents/technical-reviewer.md")
        self.assertEqual(implementer["mode"], "primary")
        self.assertEqual(reviewer["mode"], "subagent")

        reviewer_text = (ROOT / ".opencode/agents/technical-reviewer.md").read_text(encoding="utf-8")
        implementer_text = (ROOT / ".opencode/agents/technical-implementer.md").read_text(encoding="utf-8")
        self.assertNotIn("\npermission:", implementer_text)
        self.assertNotIn("\npermission:", reviewer_text)
        self.assertNotIn("allowlisted inspection commands", reviewer_text)
        self.assertNotIn("Once the mission preflight has confirmed authorization", implementer_text)
        self.assertIn("Independently verify the live authority, authorization, and file scope", implementer_text)
        self.assertIn("must not be blocked only because it is absent", implementer_text)
        self.assertIn("independent, read-only technical reviewer", reviewer_text)
        self.assertIn("Never edit, correct, commit", reviewer_text)
        self.assertIn("inspection commands and targeted tests necessary", reviewer_text)
        self.assertIn("do not run it by default after every change", reviewer_text)
        self.assertIn("Never push", implementer_text)

    def test_opencode_discovers_the_configured_agents(self) -> None:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                "opencode agent list",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("technical-implementer", result.stdout)
        self.assertIn("technical-reviewer", result.stdout)

    def test_preexisting_untracked_targets_are_not_changed_by_the_test(self) -> None:
        if self.missing_preexisting:
            self.skipTest(
                "Historical OpenCode fixture(s) absent; no workspace artifacts are fabricated: "
                + ", ".join(self.missing_preexisting)
            )
        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        for relative_path in PREEXISTING_UNTRACKED:
            self.assertIn(f"?? {relative_path}", status)
            self.assertEqual(content_digest(ROOT / relative_path), self.preexisting_digests[relative_path])

    def test_preflight_is_read_only_and_requires_authorization_details(self) -> None:
        preflight_path = ROOT / ".opencode/commands/mission-preflight.md"
        before = preflight_path.read_bytes()
        command, body = read_frontmatter(preflight_path)
        after = preflight_path.read_bytes()
        self.assertNotIn("agent", command)
        self.assertNotIn("subtask", command)
        self.assertEqual(before, after)
        self.assertIn("Use this formal preflight selectively", body)
        self.assertIn("It is not required for", body)
        self.assertIn("small, clear, authorized, low-risk correction", body)
        self.assertIn("a substitute for an independent post-change review", body)
        self.assertIn("plans/001_CONTROL_OPERATIVO.md", body)
        self.assertIn("OWNER authorization", body)
        self.assertIn("contradicts the live control", body)
        self.assertIn("request human confirmation", body)
        self.assertIn("Do not edit files", body)
        self.assertIn("SEARCH BEFORE CREATE", body)
        self.assertIn("reutilización antes de crear", body)
        self.assertIn("software determinista antes que IA", body)
        self.assertIn("ENCONTRADA` from `APLICABLE", body)
        self.assertIn("SDD: NO NECESARIO", body)
        self.assertIn("possible duplication", body)
        self.assertIn("PROCEED", body)
        self.assertIn("STOP", body)

    def test_reviewer_preserves_read_only_controls_and_new_review_dimensions(self) -> None:
        reviewer_text = (ROOT / ".opencode/agents/technical-reviewer.md").read_text(encoding="utf-8")
        for phrase in (
            "independent, read-only technical reviewer",
            "regressions",
            "files outside scope",
            "excessive permissions",
            "false validation",
            "accidental state changes",
            "pre-existing files",
            "general capability duplication",
            "temporary files",
            "final repository remains coherent",
            "architecture more complex than necessary",
            "INTRODUCIDO POR ESTA MISIÓN",
            "PREEXISTENTE",
            "INDETERMINADO",
            "Resumen",
            "Archivo | Qué cambió | Para qué",
            "Never edit, correct, commit, push",
            "Use this reviewer when independent review adds value",
            "do not run it by default after every change",
            "A small, clear, low-risk change with direct validation may omit this review",
        ):
            self.assertIn(phrase, reviewer_text)

    def test_basic_rules_do_not_require_the_specialized_flow(self) -> None:
        agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        implementer_text = (ROOT / ".opencode/agents/technical-implementer.md").read_text(encoding="utf-8")
        preflight_text = (ROOT / ".opencode/commands/mission-preflight.md").read_text(encoding="utf-8")
        reviewer_text = (ROOT / ".opencode/agents/technical-reviewer.md").read_text(encoding="utf-8")

        self.assertIn("Principios básicos siempre aplicables", agents_text)
        self.assertIn("se seleccionan y usan solo cuando sean pertinentes", agents_text)
        self.assertIn("need not run formal preflight", implementer_text)
        self.assertIn("not required for", preflight_text)
        self.assertIn("may omit this review", reviewer_text)


if __name__ == "__main__":
    unittest.main()
