"""Regresión B2: estados, inputs, parser, portabilidad y evidencia."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from src.core.gate_result import GateResult
from src.core.gate_runtime import emit
from src.core.legacy_gate_adapter import parse_legacy_gate_v
from src.core.status import GateStatus
from src.scripts.evidence_sufficiency_gate import evaluate as evidence_evaluate
from src.scripts import cerrar_episodio


ROOT = Path(__file__).resolve().parents[2]
SUBPROCESS_TIMEOUT_SECONDS = 20


def report(can_proceed=True, limitations=None, pending=None):
    return {
        "report_id": "ER-001",
        "episode_id": "ep",
        "research_id": "RP-001",
        "brief_version": "1.0.0",
        "material_principal_disponible": True,
        "tipo_de_acceso": "DIRECT",
        "fuentes_primarias": [{
            "source_id": "S1", "title": "Fuente sintética",
            "url": "https://example.com/source", "access_type": "DIRECT",
            "locator": "documento completo", "confidence": "HIGH"
        }],
        "fuentes_secundarias": [],
        "escenas_verificadas": [{
            "scene_id": "SC1", "description": "Escena sintética",
            "source_id": "S1", "locator": "00:10:00", "verification_mode": "DIRECT"
        }],
        "escenas_descritas_indirectamente": [],
        "claims_sostenibles": [],
        "claims_pendientes": pending or [],
        "limitaciones": limitations or [],
        "nivel_de_confianza": "HIGH",
        "can_proceed": can_proceed,
        "allowed_analyses": ["CONTEXTUAL_ANALYSIS"],
        "limited_analyses": [],
        "prohibited_analyses": [],
        "excluded_claims": [],
        "required_disclosures": [],
        "propagated_constraints": [],
        "critical_claim_assessments": [],
        "critical_claims_propagation": {"status": "NONE_JUSTIFIED", "claim_ids": [], "justification": "B2 no formula claims centrales.", "editorial_impact": "LIMITED", "scope_decision": "REDUCED_SCOPE"},
        "sufficiency_basis": {
            "central_question": "Pregunta sintética de B2.",
            "critical_claims": [],
            "analysis_type": "CONTEXTUAL_ANALYSIS",
            "material_roles": ["PRIMARY_NARRATIVE_MATERIAL"],
            "requested_depth": "ESTANDAR",
            "research_coverage": "Cobertura sintética de B2.",
        },
        "created_at": "2026-07-23T20:00:00Z",
    }


class TestB2Harness(unittest.TestCase):
    def make_valid_closure(self, temp_path: Path, ep_id: str = "ep_0001") -> tuple[Path, Path, Path]:
        vault, episode, output = temp_path / "vault", temp_path / ep_id, temp_path / "out"
        episode.mkdir()
        files = {"06_guion_longform.md": "guion", "06_guion_longform_limpio.md": "guion limpio", "06_guion_longform_anotado.md": "guion anotado", "08_shorts.md": "shorts", "09_packaging.md": "packaging", "10_seo.md": "seo"}
        for name, content in files.items(): (episode / name).write_text(content, encoding="utf-8")
        (episode / "07_verificacion_veracidad_notebooklm.md").write_text("ESTADO_GLOBAL: OK\n", encoding="utf-8")
        checksum = __import__("hashlib").sha256("guion".encode()).hexdigest()
        manifest = {"script_id": ep_id, "version": "1.0.0", "checksum": checksum, "narrative_plan_version": "1.0.0", "status": "EDITORIAL_SCRIPT_APPROVED"}
        approval = {"artifact_id": ep_id, "script_version": "1.0.0", "checksum": checksum, "decision": "APPROVED", "approved_by": "editor_jefe_01", "approved_role": "EDITORIAL_LEAD", "approved_at": "2026-07-21T20:00:00Z"}
        (episode / "script_version_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (episode / "editorial_script_approval.json").write_text(json.dumps(approval), encoding="utf-8")
        ledger = {"ledger_id": ep_id + "-claims", "script_version": "1.0.0", "claims": [{"claim_id": "claim-1", "script_location": "L1", "claim_text": "Texto", "claim_type": "FACT", "source_refs": ["source-1"], "verification_status": "VERIFIED"}]}
        (episode / "claims_ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
        checksums = {name: __import__("hashlib").sha256((episode / name).read_bytes()).hexdigest() for name in (*files, "claims_ledger.json")}
        final = {"final_script_clean": "06_guion_longform_limpio.md", "final_script_annotated": "06_guion_longform_anotado.md", "claims_ledger": "claims_ledger.json", "checksums": checksums, "approval_record": approval, "final_candidate_version": "1.0.0", "human_approved_version": "1.0.0"}
        (episode / "final_delivery_manifest.json").write_text(json.dumps(final), encoding="utf-8")
        gate_dir = output / "gates" / ep_id; gate_dir.mkdir(parents=True)
        for gate_id in ("qa_brief_research", "evidence_sufficiency", "qa_duracion_guion", "qa_lenguaje_youtube_ultra_post_guion"):
            result = GateResult(gate_id, ep_id, "1.0.0", GateStatus.PASS, "ok")
            (gate_dir / f"{gate_id}.json").write_text(json.dumps(result.to_dict()), encoding="utf-8")
        index_path = vault / "channel/index/episodes_index.json"; index_path.parent.mkdir(parents=True)
        index_path.write_text(json.dumps({"episodes": [{"ep_id": ep_id, "ep_path": str(episode), "estado": "en_progreso"}]}), encoding="utf-8")
        config = temp_path / "config.json"; config.write_text(json.dumps({"vault_root": str(vault), "channel_id": "channel"}), encoding="utf-8")
        return episode, output, config

    def close(self, config: Path, output: Path, ep_id="ep_0001") -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(ROOT / "src/scripts/cerrar_episodio.py"), "--ep-id", ep_id, "--config", str(config), "--output-root", str(output)], cwd=config.parent, env={**os.environ, "PYTHONPATH": str(ROOT)}, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_SECONDS)

    def test_canonical_exit_codes(self):
        with tempfile.TemporaryDirectory() as temp:
            for status, expected in ((GateStatus.PASS, 0), (GateStatus.WARN, 0), (GateStatus.FAIL, 1), (GateStatus.BLOCKED, 2)):
                result = GateResult("test", "ep", "1.0.0", status, "ok", ["x"] if status in {GateStatus.FAIL, GateStatus.BLOCKED} else [])
                self.assertEqual(emit(result, output_root=temp), expected)

    def test_legacy_parser_is_exact_and_unambiguous(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "gate.md"
            path.write_text("ESTADO_GLOBAL: FAIL\nESTADO_GLOBAL: OK\n", encoding="utf-8")
            status, error = parse_legacy_gate_v(path)
            self.assertIsNone(status); self.assertIn("exactamente una", error)
            path.write_text("ESTADO_GLOBAL: OK\n", encoding="utf-8")
            status, error = parse_legacy_gate_v(path)
            self.assertEqual(status, GateStatus.PASS); self.assertIsNone(error)

    def test_evidence_statuses(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "report.json"
            self.assertEqual(evidence_evaluate(path, "ep").status, GateStatus.BLOCKED)
            path.write_text("{}", encoding="utf-8")
            self.assertEqual(evidence_evaluate(path, "ep").status, GateStatus.FAIL)
            path.write_text(json.dumps(report(can_proceed=False, limitations=["sin acceso"])), encoding="utf-8")
            self.assertEqual(evidence_evaluate(path, "ep").status, GateStatus.BLOCKED)
            path.write_text(json.dumps(report(limitations=["acceso parcial"])), encoding="utf-8")
            self.assertEqual(evidence_evaluate(path, "ep").status, GateStatus.WARN)
            path.write_text(json.dumps(report()), encoding="utf-8")
            self.assertEqual(evidence_evaluate(path, "ep").status, GateStatus.PASS)
            unsupported = report(); unsupported["fuentes_primarias"] = []
            path.write_text(json.dumps(unsupported), encoding="utf-8")
            self.assertEqual(evidence_evaluate(path, "ep").status, GateStatus.FAIL)
            unavailable = report(); unavailable["material_principal_disponible"] = False; unavailable["fuentes_primarias"] = []; unavailable["tipo_de_acceso"] = "UNAVAILABLE"
            path.write_text(json.dumps(unavailable), encoding="utf-8")
            self.assertEqual(evidence_evaluate(path, "ep").status, GateStatus.BLOCKED)

    def test_post_script_inputs_block_and_output_is_portable(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp); episode = temp_path / "episode with spaces"; episode.mkdir(); output = temp_path / "out"
            command = [sys.executable, str(ROOT / "src/scripts/qa_lenguaje_youtube_ultra.py"), "--ep_path", str(episode), "--fase", "post-guion", "--output-root", str(output)]
            environment = {**os.environ, "PYTHONPATH": str(ROOT)}
            done = subprocess.run(command, cwd=temp_path, env=environment, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_SECONDS)
            self.assertEqual(done.returncode, 2, done.stderr)
            self.assertTrue((output / "gates" / episode.name / "qa_lenguaje_youtube_ultra_post_guion.json").is_file())
            self.assertFalse((temp_path / "output").exists())

    def test_pre_and_post_ultra_use_distinct_gate_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp); episode = temp_path / "ep_0001"; episode.mkdir(); output = temp_path / "out"
            command = [sys.executable, str(ROOT / "src/scripts/qa_lenguaje_youtube_ultra.py"), "--ep_path", str(episode), "--ep-id", "ep_0001", "--fase", "pre-guion", "--output-root", str(output)]
            done = subprocess.run(command, cwd=temp_path, env={**os.environ, "PYTHONPATH": str(ROOT)}, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_SECONDS)
            self.assertEqual(done.returncode, 2)
            self.assertTrue((output / "gates/ep_0001/qa_lenguaje_youtube_ultra_pre_guion.json").is_file())
            self.assertFalse((output / "gates/ep_0001/qa_lenguaje_youtube_ultra_post_guion.json").exists())

    def test_closure_with_empty_script_is_blocked_without_index_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp); vault = temp_path / "vault"; episode = temp_path / "episode"; episode.mkdir()
            for name in ("06_guion_longform.md", "08_shorts.md", "09_packaging.md", "10_seo.md"):
                (episode / name).write_text("" if name == "06_guion_longform.md" else "content", encoding="utf-8")
            index_path = vault / "channel/index/episodes_index.json"; index_path.parent.mkdir(parents=True)
            index = {"episodes": [{"ep_id": "ep_0001", "ep_path": str(episode), "estado": "en_progreso"}]}
            index_path.write_text(json.dumps(index), encoding="utf-8")
            config = temp_path / "config.json"; config.write_text(json.dumps({"vault_root": str(vault), "channel_id": "channel"}), encoding="utf-8")
            command = [sys.executable, str(ROOT / "src/scripts/cerrar_episodio.py"), "--ep-id", "ep_0001", "--config", str(config), "--output-root", str(temp_path / "out")]
            done = subprocess.run(command, cwd=temp_path, env={**os.environ, "PYTHONPATH": str(ROOT)}, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_SECONDS)
            self.assertEqual(done.returncode, 2, done.stderr)
            self.assertEqual(json.loads(index_path.read_text(encoding="utf-8"))["episodes"][0]["estado"], "en_progreso")

    def test_closure_blocked_inputs_and_invalid_index_are_non_mutating(self):
        for filename in ("06_guion_longform.md", "09_packaging.md", "10_seo.md"):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp); episode, output, config = self.make_valid_closure(temp_path)
                (episode / filename).write_text("", encoding="utf-8")
                done = self.close(config, output)
                self.assertEqual(done.returncode, 2)
                index = json.loads((temp_path / "vault/channel/index/episodes_index.json").read_text())
                self.assertEqual(index["episodes"][0]["estado"], "en_progreso")

    def test_closure_with_all_deliverables_empty_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp); episode, output, config = self.make_valid_closure(temp_path)
            for name in ("06_guion_longform.md", "08_shorts.md", "09_packaging.md", "10_seo.md"):
                (episode / name).write_text("", encoding="utf-8")
            self.assertEqual(self.close(config, output).returncode, 2)
            index = json.loads((temp_path / "vault/channel/index/episodes_index.json").read_text())
            self.assertEqual(index["episodes"][0]["estado"], "en_progreso")

    def test_closure_rejects_gate_v_and_contract_mismatches(self):
        cases = {
            "ambiguous_gate_v": ("07_verificacion_veracidad_notebooklm.md", "ESTADO_GLOBAL: FAIL\nESTADO_GLOBAL: OK\n", 1),
            "failed_gate_v": ("07_verificacion_veracidad_notebooklm.md", "ESTADO_GLOBAL: FAIL\n", 1),
            "approval_other_version": ("editorial_script_approval.json", "version", 1),
            "approval_checksum": ("editorial_script_approval.json", "checksum", 1),
            "modified_script": ("06_guion_longform.md", "modified", 1),
            "missing_final": ("final_delivery_manifest.json", None, 2),
            "missing_manifest_target": ("final_delivery_manifest.json", "missing_target", 2),
            "failed_final_gate": ("qa_lenguaje_youtube_ultra_post_guion.json", "failed_gate", 1),
            "foreign_gate": ("qa_lenguaje_youtube_ultra_post_guion.json", "foreign_gate", 1),
            "contradictory_gate": ("qa_lenguaje_youtube_ultra_post_guion.json", "contradictory_gate", 1),
        }
        for label, (target, mutation, expected) in cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp); episode, output, config = self.make_valid_closure(temp_path)
                path = episode / target if target.endswith(".md") or target in {"editorial_script_approval.json", "final_delivery_manifest.json"} else output / "gates/ep_0001" / target
                if mutation == "version":
                    data = json.loads(path.read_text()); data["script_version"] = "2.0.0"; path.write_text(json.dumps(data))
                elif mutation == "checksum":
                    data = json.loads(path.read_text()); data["checksum"] = "b" * 64; path.write_text(json.dumps(data))
                elif mutation == "missing_target":
                    data = json.loads(path.read_text()); data["final_script_clean"] = "absent.md"; data["checksums"]["absent.md"] = "a" * 64; path.write_text(json.dumps(data))
                elif mutation == "failed_gate":
                    data = json.loads(path.read_text()); data["status"] = "FAIL"; data["exit_code"] = 1; data["violations"] = ["failed"]; path.write_text(json.dumps(data))
                elif mutation == "foreign_gate":
                    data = json.loads(path.read_text()); data["artifact_id"] = "ep_9999"; path.write_text(json.dumps(data))
                elif mutation == "contradictory_gate":
                    data = json.loads(path.read_text()); data["exit_code"] = 1; path.write_text(json.dumps(data))
                elif mutation is None:
                    path.unlink()
                else: path.write_text(mutation, encoding="utf-8")
                self.assertEqual(self.close(config, output).returncode, expected)

    def test_valid_closure_is_single_atomic_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp); _, output, config = self.make_valid_closure(temp_path)
            self.assertEqual(self.close(config, output).returncode, 0)
            index_path = temp_path / "vault/channel/index/episodes_index.json"; first = index_path.read_text()
            self.assertEqual(json.loads(first)["episodes"][0]["estado"], "completado")
            self.assertEqual(self.close(config, output).returncode, 2)
            self.assertEqual(index_path.read_text(), first)

    def test_closure_requires_approval_and_final_manifest_integrity(self):
        mutations = ("missing_approval", "missing_checksum", "empty_approval_record", "same_scripts", "invalid_ledger", "foreign_manifest", "foreign_approval")
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp); episode, output, config = self.make_valid_closure(temp_path)
                if mutation == "missing_approval":
                    (episode / "editorial_script_approval.json").unlink()
                    expected = 2
                elif mutation in {"foreign_manifest", "foreign_approval"}:
                    target = episode / ("script_version_manifest.json" if mutation == "foreign_manifest" else "editorial_script_approval.json")
                    data = json.loads(target.read_text()); data["script_id" if mutation == "foreign_manifest" else "artifact_id"] = "ep_0001_extra"; target.write_text(json.dumps(data)); expected = 1
                else:
                    final_path = episode / "final_delivery_manifest.json"; final = json.loads(final_path.read_text())
                    if mutation == "missing_checksum": final["checksums"].pop("06_guion_longform_limpio.md")
                    elif mutation == "empty_approval_record": final["approval_record"] = {}
                    elif mutation == "same_scripts": final["final_script_annotated"] = final["final_script_clean"]
                    else: (episode / "claims_ledger.json").write_text("{}", encoding="utf-8")
                    final_path.write_text(json.dumps(final)); expected = 1
                self.assertEqual(self.close(config, output).returncode, expected)

    def test_index_write_error_returns_technical_error_without_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp); _, output, config = self.make_valid_closure(temp_path)
            with patch.object(sys, "argv", ["cerrar_episodio.py", "--ep-id", "ep_0001", "--config", str(config), "--output-root", str(output)]):
                with patch.object(cerrar_episodio, "save_index_atomically", side_effect=OSError("disk full")):
                    self.assertEqual(cerrar_episodio.main(), 3)
            index = json.loads((temp_path / "vault/channel/index/episodes_index.json").read_text())
            self.assertEqual(index["episodes"][0]["estado"], "en_progreso")

    def test_persisted_gate_result_rejects_missing_and_contradictory_fields(self):
        valid = GateResult("gate", "ep", "1.0.0", GateStatus.PASS, "ok").to_dict()
        broken = dict(valid); broken["exit_code"] = 1
        with self.assertRaises(ValueError): GateResult.from_dict(broken)
        broken = dict(valid); del broken["summary"]
        with self.assertRaises(ValueError): GateResult.from_dict(broken)

    def test_legacy_cli_regressions_and_workflow_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp); env = {**os.environ, "PYTHONPATH": str(ROOT)}
            for script in ("qa_brief_research.py", "qa_momento_1.py"):
                done = subprocess.run([sys.executable, str(ROOT / "src/scripts" / script), "--ep_path", str(temp_path / "missing"), "--output-root", str(temp_path / "out")], cwd=temp_path, env=env, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_SECONDS)
                self.assertEqual(done.returncode, 2)
            done = subprocess.run([sys.executable, str(ROOT / "src/scripts/gate0_auditoria.py"), "--output-root", str(temp_path / "out")], cwd=temp_path, env=env, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_SECONDS)
            self.assertIn(done.returncode, (0, 1, 2))
        workflow = (ROOT / ".agent/workflows/01_pipeline_episodio.md").read_text(encoding="utf-8")
        self.assertNotIn("output/auditoria_brief_research_", workflow)
        self.assertNotIn("qa_youtube_ultra.md` + ESTADO_GLOBAL", workflow)
        self.assertIn("READY_FOR_TEAM_02_FUNCTIONAL_REAUDIT", workflow)
        self.assertNotIn("09_packaging.md", workflow)
        self.assertNotIn("EditorialScriptApproval", workflow)

    def test_evidence_substantive_regression_cases(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "report.json"
            
            # fuentes_primarias=[{}] -> FAIL
            rep = report(can_proceed=True)
            rep["fuentes_primarias"] = [{}]
            path.write_text(json.dumps(rep), encoding="utf-8")
            self.assertEqual(evidence_evaluate(path, "ep").status, GateStatus.FAIL)

            # fuente con todos sus valores vacíos -> FAIL
            rep["fuentes_primarias"] = [{"name": "   ", "url": ""}]
            path.write_text(json.dumps(rep), encoding="utf-8")
            self.assertEqual(evidence_evaluate(path, "ep").status, GateStatus.FAIL)

    def test_final_delivery_manifest_security_and_roles_regression(self):
        # Shorts como final_script_clean -> FAIL
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp); episode, output, config = self.make_valid_closure(temp_path)
            final = json.loads((episode / "final_delivery_manifest.json").read_text())
            final["final_script_clean"] = "08_shorts.md"
            final["checksums"]["08_shorts.md"] = __import__("hashlib").sha256((episode / "08_shorts.md").read_bytes()).hexdigest()
            (episode / "final_delivery_manifest.json").write_text(json.dumps(final))
            self.assertEqual(self.close(config, output).returncode, 1)

        # Packaging como final_script_annotated -> FAIL
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp); episode, output, config = self.make_valid_closure(temp_path)
            final = json.loads((episode / "final_delivery_manifest.json").read_text())
            final["final_script_annotated"] = "09_packaging.md"
            final["checksums"]["09_packaging.md"] = __import__("hashlib").sha256((episode / "09_packaging.md").read_bytes()).hexdigest()
            (episode / "final_delivery_manifest.json").write_text(json.dumps(final))
            self.assertEqual(self.close(config, output).returncode, 1)

        # ruta ../outside.md -> FAIL
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp); episode, output, config = self.make_valid_closure(temp_path)
            final = json.loads((episode / "final_delivery_manifest.json").read_text())
            final["final_script_clean"] = "../outside.md"
            final["checksums"]["../outside.md"] = "a" * 64
            (episode / "final_delivery_manifest.json").write_text(json.dumps(final))
            self.assertEqual(self.close(config, output).returncode, 1)

        # ruta absoluta externa -> FAIL
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp); episode, output, config = self.make_valid_closure(temp_path)
            final = json.loads((episode / "final_delivery_manifest.json").read_text())
            abs_path = str((temp_path / "outside.md").resolve())
            (temp_path / "outside.md").write_text("outside content", encoding="utf-8")
            final["final_script_clean"] = abs_path
            final["checksums"][abs_path] = "a" * 64
            (episode / "final_delivery_manifest.json").write_text(json.dumps(final))
            self.assertEqual(self.close(config, output).returncode, 1)

        # FinalDeliveryManifest sin versiones -> FAIL
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp); episode, output, config = self.make_valid_closure(temp_path)
            final = json.loads((episode / "final_delivery_manifest.json").read_text())
            del final["final_candidate_version"]
            (episode / "final_delivery_manifest.json").write_text(json.dumps(final))
            self.assertEqual(self.close(config, output).returncode, 1)

        # final_script_clean = research -> FAIL (nombre no canónico)
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp); episode, output, config = self.make_valid_closure(temp_path)
            (episode / "01_research_bruto.md").write_text("dummy", encoding="utf-8")
            final = json.loads((episode / "final_delivery_manifest.json").read_text())
            final["final_script_clean"] = "01_research_bruto.md"
            final["checksums"]["01_research_bruto.md"] = __import__("hashlib").sha256(b"dummy").hexdigest()
            (episode / "final_delivery_manifest.json").write_text(json.dumps(final))
            self.assertEqual(self.close(config, output).returncode, 1)

        # final_script_annotated = brief -> FAIL (nombre no canónico)
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp); episode, output, config = self.make_valid_closure(temp_path)
            (episode / "00_brief_episodio.md").write_text("dummy", encoding="utf-8")
            final = json.loads((episode / "final_delivery_manifest.json").read_text())
            final["final_script_annotated"] = "00_brief_episodio.md"
            final["checksums"]["00_brief_episodio.md"] = __import__("hashlib").sha256(b"dummy").hexdigest()
            (episode / "final_delivery_manifest.json").write_text(json.dumps(final))
            self.assertEqual(self.close(config, output).returncode, 1)

    def test_workflow_b2_requirements(self):
        workflow = (ROOT / ".agent/workflows/01_pipeline_episodio.md").read_text(encoding="utf-8")
        # workflow crea SourceAccessAndEvidenceReport antes de ejecutar el gate
        self.assertIn("<EP_PATH>/source_access_and_evidence_report.json", workflow)
        self.assertIn("schemas/source_access_and_evidence_report.json", workflow)
        # B5-I1 se detiene antes de los controles pre-guion heredados.
        self.assertIn("READY_FOR_TEAM_02_FUNCTIONAL_REAUDIT", workflow)
        self.assertNotIn("qa_lenguaje_youtube_ultra_pre_guion.json", workflow)
