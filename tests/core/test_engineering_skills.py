import json
import re
from pathlib import Path


ROOT = Path(__file__).parents[2]
SKILLS_ROOT = ROOT / ".agents" / "skills"
PRODUCT_SKILLS_ROOT = ROOT / ".agent" / "skills"
EXPECTED = {
    "preparar-paquete-ejecucion-tecnica",
    "auditar-trazabilidad-input-output",
    "evidencia-proporcional-git",
    "verificar-no-mezcla-de-capas",
    "harness-determinista",
}
GENERAL_CAPABILITIES_MATERIALIZED_HERE = {
    "auditar-trazabilidad-input-output",
    "evidencia-proporcional-git",
    "verificar-no-mezcla-de-capas",
}
FORBIDDEN_PROVIDER_MARKERS = re.compile(
    r"codex|opencode|chatgpt|antigravity|notebooklm|laboratorios", re.IGNORECASE
)


def _skill_text(name: str) -> str:
    return (SKILLS_ROOT / name / "SKILL.md").read_text(encoding="utf-8")


def test_engineering_skills_are_discoverable_outside_product_catalog():
    discovered = {path.parent.name for path in SKILLS_ROOT.glob("*/SKILL.md")}
    assert discovered == EXPECTED
    assert not any(
        FORBIDDEN_PROVIDER_MARKERS.search(_skill_text(name)) for name in EXPECTED
    )
    catalog = json.loads(
        (ROOT / "config" / "skill_catalog.json").read_text(encoding="utf-8")
    )
    assert not any(
        entry["path"].startswith(".agents/skills/") for entry in catalog["skills"]
    )


def test_general_capabilities_have_an_explicit_non_product_seat():
    product_ids = {path.stem for path in PRODUCT_SKILLS_ROOT.glob("*.md")}
    engineering_ids = {
        path.parent.name for path in SKILLS_ROOT.glob("*/SKILL.md")
    }
    assert PRODUCT_SKILLS_ROOT != SKILLS_ROOT
    assert not product_ids & GENERAL_CAPABILITIES_MATERIALIZED_HERE
    assert GENERAL_CAPABILITIES_MATERIALIZED_HERE <= engineering_ids


def test_engineering_skill_references_are_local_and_existing():
    for name in EXPECTED:
        text = _skill_text(name)
        assert re.search(
            r"^name:\s*" + re.escape(name) + r"\s*$", text, re.MULTILINE
        )
        assert re.search(r"^description:\s*\S", text, re.MULTILINE)
    for relative_path in (
        "AGENTS.md",
        "plans/001_CONTROL_OPERATIVO.md",
        "src/core/mission_authorization.py",
        "src/core/mission_completion_gate.py",
        "src/core/repair_integrity.py",
        "src/core/execution_preflight.py",
        "src/scripts/gate0_auditoria.py",
        "src/scripts/gate0_integridad.py",
    ):
        assert (ROOT / relative_path).is_file(), relative_path


def test_minimal_use_preparation_and_traceability_on_project_context():
    context = {
        "authority": "plans/001_CONTROL_OPERATIVO.md",
        "authorized_paths": [".agents/skills/"],
        "forbidden_paths": ["plans/001_CONTROL_OPERATIVO.md"],
        "actions": ["read", "write", "pytest", "git diff --check"],
        "reported_result": "skills prepared for independent review",
    }
    package_skill = _skill_text("preparar-paquete-ejecucion-tecnica")
    trace_skill = _skill_text("auditar-trazabilidad-input-output")
    assert all(
        field in package_skill
        for field in ("Entradas mínimas", "Salida mínima", "Criterio de cierre")
    )
    assert all(field in trace_skill for field in ("Entradas", "Procedimiento", "Salida"))
    serialized_context = json.dumps(context, ensure_ascii=False)
    assert "plans/001_CONTROL_OPERATIVO.md" in serialized_context
    assert ".agents/skills/" in serialized_context
    assert "Laboratorios" not in serialized_context
    assert set(context["authorized_paths"]).isdisjoint(context["forbidden_paths"])
    assert "git diff --check" in context["actions"]
