"""
Pruebas Unitarias de Integridad y Validación de los 24 JSON Schemas y sus Fixtures Válidos
"""

import os
import json
import unittest
import jsonschema
from jsonschema import Draft7Validator

from src.core.contract_validation import (
    SCHEMAS_DIR, 
    load_schema, 
    validate_against_schema,
    validate_editorial_script_approval,
    validate_human_production_approval,
    validate_human_publication_approval,
    validate_research_pack,
    validate_claims_ledger,
)

VALID_FIXTURES = {
    "agent_prompt_registry": {
        "registry_version": "1.0.0",
        "prompts": [
            {"role_id":"ORCHESTRATION","prompt_id":"prompt_orch","prompt_version":"1.0.0","status":"ACTIVE","objective":"test","authority":"test","required_inputs":[],"required_context":[],"allowed_actions":[],"forbidden_actions":[],"required_outputs":[],"blocking_conditions":[],"handoff":{"to":"next","condition":"pass"},"evidence_requirements":[]},
            {"role_id":"RESEARCH_AND_CURATION","prompt_id":"prompt_rc","prompt_version":"1.0.0","status":"ACTIVE","objective":"test","authority":"test","required_inputs":[],"required_context":[],"allowed_actions":[],"forbidden_actions":[],"required_outputs":[],"blocking_conditions":[],"handoff":{"to":"next","condition":"pass"},"evidence_requirements":[]},
            {"role_id":"NARRATIVE_ARCHITECTURE","prompt_id":"prompt_na","prompt_version":"1.0.0","status":"ACTIVE","objective":"test","authority":"test","required_inputs":[],"required_context":[],"allowed_actions":[],"forbidden_actions":[],"required_outputs":[],"blocking_conditions":[],"handoff":{"to":"next","condition":"pass"},"evidence_requirements":[]},
            {"role_id":"WRITING","prompt_id":"prompt_writing","prompt_version":"1.0.0","status":"ACTIVE","objective":"test","authority":"test","required_inputs":[],"required_context":[],"allowed_actions":[],"forbidden_actions":[],"required_outputs":[],"blocking_conditions":[],"handoff":{"to":"next","condition":"pass"},"evidence_requirements":[]},
            {"role_id":"EDITOR","prompt_id":"prompt_editor","prompt_version":"1.0.0","status":"ACTIVE","objective":"test","authority":"test","required_inputs":[],"required_context":[],"allowed_actions":[],"forbidden_actions":[],"required_outputs":[],"blocking_conditions":[],"handoff":{"to":"next","condition":"pass"},"evidence_requirements":[]},
            {"role_id":"FINAL_EDITORIAL_AUDITOR","prompt_id":"prompt_fea","prompt_version":"1.0.0","status":"ACTIVE","objective":"test","authority":"test","required_inputs":[],"required_context":[],"allowed_actions":[],"forbidden_actions":[],"required_outputs":[],"blocking_conditions":[],"handoff":{"to":"next","condition":"pass"},"evidence_requirements":[]}
        ]
    },
    "ai_runtime_config": {
        "registry_version": "1.0.0",
        "entries": [
            {"role_id":"ORCHESTRATION","provider":"mock","model":"default","adapter":"mock","tools":[],"permissions":{"read":[],"write":[]},"execution_mode":"DIRECT"}
        ]
    },
    "claims_ledger": {
        "ledger_id": "CL-001",
        "script_version": "1.0.0",
        "claims": [
            {
                "claim_id": "CLAIM-001",
                "script_location": "Bloque 1, Linea 10",
                "claim_text": "Dato historico verificado.",
                "claim_type": "FACT",
                "source_refs": [
                    "REF-001"
                ],
                "verification_status": "VERIFIED"
            }
        ]
    },
    "correction_routing_policy": {
        "defect_type": "FACTUAL_ERROR",
        "severity": "CRITICAL",
        "origin_artifact": "SCRIPT-001",
        "invalidated_artifacts": ["SHORTS-001"],
        "return_state": "DRAFT",
        "required_revalidation": "2026-07-21T22:00:00Z",
        "suggested_role": "EDITORIAL_LEAD"
    },
    "curation_decision": {
        "curation_id": "CUR-001",
        "research_version": "1.0.0",
        "preselected_materials": ["M1"],
        "selected_materials": ["M1"],
        "rejected_materials": [],
        "decision": "APPROVED"
    },
    "editorial_edit_report": {
        "input_version": "1.0.0",
        "output_version": "1.1.0",
        "edit_type": "RESTRUCTURE",
        "changes_by_category": {}
    },
    "editorial_learning_candidate": {
        "learning_id": "LEARN-001",
        "target_profile_id": "MADG-EDITORIAL-PROFILE",
        "target_profile_version": "1.0.0",
        "observed_change": "Ajuste de ritmo",
        "scope": "VOICE",
        "lineage": ["SAMPLE-001"],
        "evidence_items": [{"source_id": "SAMPLE-001", "locator": "fixtures/sample.md", "checksum": "a" * 64, "observation": "Patrón repetido"}],
        "confidence": 0.5,
        "examples": ["Ejemplo válido"],
        "counterexamples": ["Contraejemplo válido"],
        "exceptions": [],
        "functional_decision": {"status": "PENDING"},
        "status_history": [{"status": "CANDIDATE", "recorded_at": "2026-07-22T20:00:00Z"}]
    },
    "editorial_profile": {
        "profile_id": "MADG-EDITORIAL-PROFILE",
        "channel_id": "MasAllaDelGuion",
        "version": "1.0.0",
        "status": "DRAFT",
        "functional_owner_role": "TEAM_01",
        "source_lineage": [{"source_id": "B3-FUNCTIONAL-SPEC", "locator": "docs/specifications/B3_especificacion_funcional_equipo_01.md", "checksum": "a" * 64, "role": "FUNCTIONAL_SPECIFICATION"}],
        "identity_stable": {"identity": "Videoensayos narrativos", "purpose": ["Comprender historias"], "positioning": "Reflexión narrativa", "primary_promise": "Comprender cómo vivimos", "differentiator": ["Interpretación propia"], "editorial_pillars": ["Individuo e identidad"], "territories": [{"name": "Cultura", "classification": "ACTIVE"}], "permanent_limits": ["No inventar"], "authorial_persona": {"acts_as": "Observador con criterio", "does_not_act_as": ["Terapeuta"], "voice_traits": ["Claridad"]}, "first_person_rule": "FIRST_PERSON_ALLOWED_WHEN_TRUE_AND_EDITORIALLY_RELEVANT"},
        "audience_hypotheses": [{"classification": "AUDIENCE_HYPOTHESIS_INITIAL", "statement": "Personas aproximadamente entre 25 y 45 años", "status": "HYPOTHESIS"}],
        "voice_profile": {"corpus_status": "INCOMPLETE_MISSING_REQUIRED_SAMPLE", "approved_sample_ids": [], "initial_authorized_patterns": ["Observación concreta"], "anti_imitation_rules": ["No copiar referentes"], "approved_positive_examples": ["Ejemplo editorial compatible derivado de la especificación."], "approved_negative_examples": ["Ejemplo editorial incompatible derivado de la especificación."]},
        "supported_delivery_formats": ["VIDEO_ESSAY", "NARRATIVE_PODCAST", "AUDIO_CONTENT"],
        "external_policy_references": [],
        "pending_decisions": ["Incorporar muestra real principal autorizada"]
    },
    "editorial_profile_approval": {"profile_id": "MADG-EDITORIAL-PROFILE", "profile_version": "1.0.0", "profile_checksum": "a" * 64, "decision": "APPROVE", "functional_owner_role": "TEAM_01", "voice_evidence_level": "SPECIFICATION_BASED", "evidence_summary": "Aprobación final de fixture sintético.", "limitations": ["Fixture de validación."], "approved_by": "responsable_editorial_equipo_01", "approved_at": "2026-07-22T20:00:00Z"},
    "active_editorial_profile": {"ACTIVE_PROFILE_ID": "MADG-EDITORIAL-PROFILE", "ACTIVE_PROFILE_VERSION": "1.0.0", "profile_checksum": "a" * 64, "functional_approval": {"decision": "APPROVE", "profile_checksum": "a" * 64}, "technical_validation": {"gate_id": "B3_TECHNICAL_PROFILE_VALIDATION", "status": "PASS", "profile_checksum": "a" * 64}, "activation": {"activated_by": "technical_auditor_user", "activated_at": "2026-07-22T20:00:00Z"}, "status": "ACTIVE"},
    "voice_sample": {"sample_id": "SAMPLE-001", "locator": "fixtures/sample.md", "checksum": "a" * 64, "authorship": "OWNER", "text_type": "PERSONAL_TEXT", "classification": "AUTHENTIC", "usage_authorization": "AUTHORIZED", "representativeness": "HIGH", "recorded_at": "2026-07-22T20:00:00Z", "lineage": ["OWNER_PROVIDED"], "inclusion_reason": "Muestra autorizada"},
    "editorial_script_approval": {
        "artifact_id": "SCRIPT-001",
        "script_version": "1.0.0",
        "checksum": "a" * 64,
        "decision": "APPROVED",
        "approved_by": "editor_jefe_01",
        "approved_role": "EDITORIAL_LEAD",
        "approved_at": "2026-07-21T22:00:00Z"
    },
    "episode_brief": {
        "episode_id": "EP-001",
        "profile_id": "EP-001",
        "profile_version": "1.0.0",
        "tema": "El miedo al fracaso",
        "pregunta_central": "¿Por que tememos fracasar?",
        "tesis_provisional": "El fracaso es parte del aprendizaje.",
        "objetivo": "Inspirar al espectador",
        "audiencia_concreta": "Estudiantes y jovenes",
        "salida_esperada": "Ensayo de 15 minutos"
    },
    "fact_check_report": {
        "input_version": "1.0.0",
        "output_version": "1.0.0",
        "verified_claims": ["CLAIM-001"],
        "status": "PASS"
    },
    "final_delivery_manifest": {
        "final_script_clean": "06_guion_longform.md",
        "final_script_annotated": "06_guion_longform_anotado.md",
        "claims_ledger": "claims_ledger.json",
        "final_candidate_version": "1.0.0",
        "human_approved_version": "1.0.0",
        "checksums": {"06_guion_longform.md": "a" * 64},
        "approval_record": {}
    },
    "final_editorial_audit": {
        "profile_compliance": "PASS",
        "brief_compliance": "PASS",
        "packaging_promise_compliance": "PASS",
        "evidence_sufficiency": "PASS",
        "thesis_quality": "PASS",
        "decision": "PASS",
        "correction_route": "NONE"
    },
    "gate_result": {
        "gate_id": "GATE-001",
        "artifact_id": "ART-001",
        "artifact_version": "1.0.0",
        "status": "PASS",
        "summary": "Verificacion de gate exitosa",
        "violations": [],
        "warnings": [],
        "evidence": {},
        "checked_at": "2026-07-21T22:00:00Z",
        "checker_version": "1.0.0",
        "exit_code": 0
    },
    "human_production_approval": {
        "publication_package_id": "PUB-PKG-001",
        "publication_package_version": "1.0.0",
        "script_version": "1.0.0",
        "packaging_version": "1.0.0",
        "checksum": "a" * 64,
        "decision": "APPROVED_FOR_PRODUCTION",
        "approved_by": "lead_produccion_01",
        "approved_role": "PRODUCTION_LEAD",
        "approved_at": "2026-07-21T22:00:00Z"
    },
    "human_publication_approval": {
        "final_candidate_id": "FC-001",
        "audiovisual_version": "1.0.0",
        "thumbnail_version": "1.0.0",
        "title_version": "1.0.0",
        "checksum": "a" * 64,
        "decision": "APPROVED_FOR_PUBLICATION",
        "approved_by": "lead_publicacion_01",
        "approved_role": "PUBLICATION_LEAD",
        "approved_at": "2026-07-21T22:00:00Z",
        "has_final_audiovisual_assets": True
    },
    "narrative_plan": {
        "script_plan_id": "PLAN-001",
        "episode_id": "EP-001",
        "script_type": "LONGFORM",
        "thesis_provisional": "El exito requiere paciencia.",
        "blocks": [{}, {}],
        "word_budget_total": 2000
    },
    "packaging_hypothesis": {
        "episode_audience": "General",
        "promesa_de_clic": "La verdad detras del guion",
        "titulo_de_trabajo": "Detras del guion",
        "concepto_de_miniatura": "Imagen del director",
        "functional_owner_role": "EDITORIAL_LEAD",
        "authorized_approval_status": "APPROVED",
        "version": "1.0.0",
        "checksum": "a" * 64
    },
    "performance_snapshot": {
        "published_version": "1.0.0",
        "observation_window": "24H",
        "status": "PUBLISHED"
    },
    "publication_package": {
        "package_id": "PKG-001",
        "package_version": "1.0.0",
        "script_version": "1.0.0",
        "approved_title": "Detras del guion",
        "approved_thumbnail_or_brief": "miniatura_v1.png",
        "description": "Descripcion del episodio.",
        "status": "PUBLISHED"
    },
    "published_version_manifest": {
        "video_id": "YT-VIDEO-001",
        "publication_date": "2026-07-21T22:00:00Z",
        "script_version": "1.0.0",
        "audiovisual_version": "1.0.0",
        "publication_package_version": "1.0.0",
        "change_history": [],
        "status": "PUBLISHED"
    },
    "research_pack": {
        "research_id": "RP-001",
        "episode_id": "EP-001",
        "brief_version": "1.0.0",
        "facts": ["Hecho verificado."],
        "interpretations": ["Interpretacion libre."],
        "hypotheses": ["Hipotesis de trabajo."],
        "contradictions": [],
        "source_registry": [],
        "created_at": "2026-07-21T22:00:00Z"
    },
    "script_block_contract": {
        "block_id": "BLOCK-001",
        "plan_version": "1.0.0",
        "required_sources": ["SRC-01"],
        "word_budget_min": 100,
        "word_budget_max": 200,
        "narrative_function": "Introduccion y gancho",
        "output_path": "output/bloques/block_01.md"
    },
    "script_version_manifest": {
        "script_id": "SCRIPT-001",
        "version": "1.0.0",
        "checksum": "a" * 64,
        "narrative_plan_version": "1.0.0",
        "status": "DRAFT"
    },
    "source_access_and_evidence_report": {
        "material_principal_disponible": True,
        "tipo_de_acceso": "visionado directo",
        "fuentes_primarias": [],
        "fuentes_secundarias": [],
        "escenas_verificadas": [],
        "escenas_descritas_indirectamente": [],
        "claims_sostenibles": [],
        "claims_pendientes": [],
        "limitaciones": [],
        "nivel_de_confianza": "alto",
        "can_proceed": True,
        "required_disclosures": []
    },
    "thesis_artifact": {
        "thesis_id": "THESIS-001",
        "stage": "THESIS_PROVISIONAL",
        "statement": "La tesis del ensayo.",
        "supporting_reasoning": "Razonamiento logico.",
        "version": "1.0.0"
    },
    "viewer_journey": {
        "estado_inicial_del_espectador": "Curioso y expectante",
        "creencia_inicial_probable": "Cree que es simple",
        "pregunta_que_lo_mantiene": "¿Cual es el giro narrativo?",
        "estado_final_del_espectador": "Sorprendido e iluminado"
    }
}

# B4-I1: los registros canónicos sirven como fixtures válidos de sus schemas.
for _name in ("responsibility_registry", "skill_catalog"):
    with open(os.path.join(os.path.dirname(__file__), "..", "..", "config", f"{_name}.json"), encoding="utf-8") as _fixture:
        VALID_FIXTURES[_name] = json.load(_fixture)


class TestAllJSONSchemas(unittest.TestCase):

    def test_all_schemas_are_valid_draft7(self):
        """Valida el inventario de schemas y su sintaxis Draft 7."""
        schema_files = [f for f in os.listdir(SCHEMAS_DIR) if f.endswith(".json")]
        self.assertEqual(set(f.replace(".json", "") for f in schema_files), set(VALID_FIXTURES))

        for filename in schema_files:
            with self.subTest(schema=filename):
                schema_path = os.path.join(SCHEMAS_DIR, filename)
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema_data = json.load(f)
                
                try:
                    Draft7Validator.check_schema(schema_data)
                except jsonschema.exceptions.SchemaError as e:
                    self.fail(f"Esquema {filename} inválido contra el metaschema Draft 7: {e.message}")

    def test_schema_required_fields_in_properties(self):
        """Valida que todos los campos requeridos estén declarados en las propiedades del esquema."""
        schema_files = [f for f in os.listdir(SCHEMAS_DIR) if f.endswith(".json")]
        for filename in schema_files:
            with self.subTest(schema=filename):
                schema_data = load_schema(filename)
                required_fields = schema_data.get("required", [])
                properties = schema_data.get("properties", {})
                for field in required_fields:
                    self.assertIn(
                        field, 
                        properties, 
                        f"El campo requerido '{field}' no está definido en 'properties' en {filename}"
                    )

    def test_every_schema_has_valid_fixture(self):
        """Valida que cada schema tenga un fixture mínimo válido y pase la validación."""
        schema_files = [f for f in os.listdir(SCHEMAS_DIR) if f.endswith(".json")]
        for filename in schema_files:
            name = filename.replace(".json", "")
            with self.subTest(schema=name):
                self.assertIn(name, VALID_FIXTURES, f"No se encontró fixture válido para el esquema {filename}")
                fixture = VALID_FIXTURES[name]
                
                # 1. Validar contra el JSON Schema (con FormatChecker activo)
                violations = validate_against_schema(fixture, name)
                self.assertEqual(len(violations), 0, f"Fixture válido falló en la validación de schema para {filename}: {violations}")

                # 2. Validar con validadores de negocio específicos si existen
                if name == "claims_ledger":
                    business_violations = validate_claims_ledger(fixture)
                    self.assertEqual(len(business_violations), 0, f"Fixture de claims_ledger falló validaciones de negocio: {business_violations}")
                elif name == "editorial_script_approval":
                    business_violations = validate_editorial_script_approval(fixture)
                    self.assertEqual(len(business_violations), 0, f"Fixture de editorial_script_approval falló validaciones de negocio: {business_violations}")
                elif name == "human_production_approval":
                    business_violations = validate_human_production_approval(fixture)
                    self.assertEqual(len(business_violations), 0, f"Fixture de human_production_approval falló validaciones de negocio: {business_violations}")
                elif name == "human_publication_approval":
                    business_violations = validate_human_publication_approval(fixture)
                    self.assertEqual(len(business_violations), 0, f"Fixture de human_publication_approval falló validaciones de negocio: {business_violations}")
                elif name == "research_pack":
                    business_violations = validate_research_pack(fixture)
                    self.assertEqual(len(business_violations), 0, f"Fixture de research_pack falló validaciones de negocio: {business_violations}")

    def test_representative_invalid_fixtures(self):
        """Valida casos inválidos representativos para asegurar que las fallas sean detectadas."""
        # 1. Caso inválido para editorial_profile (falta campo obligatorio)
        profile_fixture = dict(VALID_FIXTURES["editorial_profile"])
        del profile_fixture["channel_id"]
        violations = validate_against_schema(profile_fixture, "editorial_profile")
        self.assertTrue(len(violations) > 0, "Se esperaba que fallara al faltar 'channel_id'")
        self.assertTrue(any("channel_id" in v for v in violations))

        # 2. Caso inválido para gate_result (enum incorrecto de status)
        gate_fixture = dict(VALID_FIXTURES["gate_result"])
        gate_fixture["status"] = "UNKNOWN_STATUS"
        violations = validate_against_schema(gate_fixture, "gate_result")
        self.assertTrue(len(violations) > 0, "Se esperaba que fallara con status inválido")
        self.assertTrue(any("status" in v for v in violations))

    def test_new_invalid_cases_for_hardness(self):
        """Prueba casos de fallo específicos añadidos para comprobar el endurecimiento de los schemas."""
        # A. Status con fecha
        profile_fixture = dict(VALID_FIXTURES["editorial_profile"])
        profile_fixture["status"] = "2026-07-21T22:00:00Z" # Fecha en vez de enum de status
        violations = validate_against_schema(profile_fixture, "editorial_profile")
        self.assertTrue(len(violations) > 0, "Se esperaba que fallara al ingresar fecha en 'status'")
        self.assertTrue(any("status" in v for v in violations))

        # B. Versión con fecha
        profile_fixture_v = dict(VALID_FIXTURES["editorial_profile"])
        profile_fixture_v["version"] = "2026-07-21T22:00:00Z" # Fecha en vez de SemVer
        violations = validate_against_schema(profile_fixture_v, "editorial_profile")
        self.assertTrue(len(violations) > 0, "Se esperaba que fallara al ingresar fecha en 'version'")
        self.assertTrue(any("version" in v for v in violations))

        # C. Date-time inválido
        profile_fixture_d = dict(VALID_FIXTURES["editorial_profile"])
        profile_fixture_d["created_at"] = "fecha-invalida" # String que no cumple date-time
        violations = validate_against_schema(profile_fixture_d, "editorial_profile")
        self.assertTrue(len(violations) > 0, "Se esperaba que fallara con date-time inválido en 'created_at'")
        self.assertTrue(any("created_at" in v for v in violations))

        # D. Checksum inválido
        profile_fixture_c = dict(VALID_FIXTURES["editorial_profile"])
        profile_fixture_c["checksum"] = "checksum-invalido-corto" # String que no tiene 64 chars hex
        violations = validate_against_schema(profile_fixture_c, "editorial_profile")
        self.assertTrue(len(violations) > 0, "Se esperaba que fallara con checksum inválido")
        self.assertTrue(any("checksum" in v for v in violations))


if __name__ == "__main__":
    unittest.main()
