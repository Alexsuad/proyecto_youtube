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
        for relative_path in PREEXISTING_UNTRACKED:
            target = ROOT / relative_path
            if not target.exists() or f"?? {relative_path}" not in status:
                raise AssertionError(f"pre-existing untracked target unavailable: {relative_path}")
        cls.preexisting_digests = {
            relative_path: content_digest(ROOT / relative_path)
            for relative_path in PREEXISTING_UNTRACKED
        }

    @classmethod
    def tearDownClass(cls) -> None:
        for relative_path, expected_digest in cls.preexisting_digests.items():
            assert content_digest(ROOT / relative_path) == expected_digest, relative_path

    def setUp(self) -> None:
        self.config = json.loads((ROOT / "opencode.json").read_text(encoding="utf-8"))

    def test_config_and_agents_define_restricted_permissions(self) -> None:
        self.assertEqual(self.config["$schema"], "https://opencode.ai/config.json")
        self.assertEqual(self.config["permission"]["edit"], "deny")
        self.assertEqual(self.config["permission"]["bash"]["*"], "deny")
        self.assertEqual(self.config["permission"]["bash"]["git push*"], "deny")

        implementer, _ = read_frontmatter(ROOT / ".opencode/agents/technical-implementer.md")
        reviewer, _ = read_frontmatter(ROOT / ".opencode/agents/technical-reviewer.md")
        self.assertEqual(implementer["mode"], "primary")
        self.assertEqual(reviewer["mode"], "subagent")

        reviewer_text = (ROOT / ".opencode/agents/technical-reviewer.md").read_text(encoding="utf-8")
        implementer_text = (ROOT / ".opencode/agents/technical-implementer.md").read_text(encoding="utf-8")
        self.assertIn('"*": deny', implementer_text)
        self.assertIn("edit: ask", implementer_text)
        self.assertIn("edit: deny", reviewer_text)
        self.assertIn("task: deny", reviewer_text)
        self.assertIn('"*": deny', reviewer_text)
        self.assertIn('"git push*": deny', reviewer_text)

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
        command, body = read_frontmatter(ROOT / ".opencode/commands/mission-preflight.md")
        self.assertEqual(command["agent"], "technical-reviewer")
        self.assertEqual(command["subtask"], "true")
        self.assertIn("plans/001_CONTROL_OPERATIVO.md", body)
        self.assertIn("OWNER authorization", body)
        self.assertIn("contradicts the live control", body)
        self.assertIn("request human confirmation", body)
        self.assertIn("Do not edit files", body)
        self.assertIn("PROCEED", body)
        self.assertIn("STOP", body)


if __name__ == "__main__":
    unittest.main()
