"""Cierre fuerte: no modifica el índice hasta que todos los contratos pasan."""
import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from src.core.contract_validation import validate_against_schema, validate_claims_ledger, validate_editorial_script_approval
from src.core.gate_result import GateResult
from src.core.gate_runtime import run_gate
from src.core.invalidation import InvalidationEngine
from src.core.legacy_gate_adapter import parse_legacy_gate_v
from src.core.path_resolution import REPO_ROOT, expand_path, output_root
from src.core.status import GateStatus
from src.core.version_manifest import compute_checksum


DELIVERABLES = ["06_guion_longform.md", "08_shorts.md", "09_packaging.md", "10_seo.md"]


def load_json(path: Path, label: str, blocked: list[str], failures: list[str]) -> dict | None:
    if not path.exists():
        blocked.append(f"{label} ausente")
        return None
    if not path.is_file() or not path.read_text(encoding="utf-8").strip():
        blocked.append(f"{label} vacío o no regular")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"{label}: JSON inválido ({exc.msg})")
        return None


def validate_gate(path: Path, gate_id: str, allowed: set[GateStatus], blocked: list[str], failures: list[str]) -> None:
    data = load_json(path, f"Gate requerido {gate_id}", blocked, failures)
    if data is None: return
    try: result = GateResult.from_dict(data)
    except (KeyError, TypeError, ValueError) as exc:
        failures.append(f"Gate {gate_id} inválido: {exc}")
        return
    if result.gate_id != gate_id: failures.append(f"Gate esperado {gate_id}, recibido {result.gate_id}")
    elif result.artifact_id != path.parent.name:
        failures.append(f"Gate {gate_id} pertenece a otro episodio: {result.artifact_id}")
    elif result.status not in allowed: failures.append(f"Gate {gate_id} en estado no permitido: {result.status.value}")


def evaluate(ep_id: str, ep_path: Path, gates_root: Path) -> GateResult:
    blocked: list[str] = []; failures: list[str] = []
    evidence: dict = {"episode_path": str(ep_path), "inputs_reviewed": []}
    if not ep_path.is_dir():
        return GateResult("cerrar_episodio", ep_id, "1.0.0", GateStatus.BLOCKED, "Carpeta de episodio ausente", [str(ep_path)], evidence=evidence)
    for name in DELIVERABLES:
        path = ep_path / name; evidence["inputs_reviewed"].append(str(path))
        if not path.exists() or not path.is_file() or not path.read_text(encoding="utf-8").strip(): blocked.append(f"Entregable obligatorio ausente o vacío: {name}")

    gate_v, error = parse_legacy_gate_v(ep_path / "07_verificacion_veracidad_notebooklm.md")
    if error:
        (blocked if "ausente" in error or "vacío" in error else failures).append(error)
    elif gate_v != GateStatus.PASS:
        failures.append(f"Gate V debe ser PASS; recibido {gate_v.value}")

    gate_dir = gates_root / "gates" / ep_id
    validate_gate(gate_dir / "qa_brief_research.json", "qa_brief_research", {GateStatus.PASS}, blocked, failures)
    validate_gate(gate_dir / "evidence_sufficiency.json", "evidence_sufficiency", {GateStatus.PASS, GateStatus.WARN}, blocked, failures)
    validate_gate(gate_dir / "qa_duracion_guion.json", "qa_duracion_guion", {GateStatus.PASS, GateStatus.WARN}, blocked, failures)
    validate_gate(gate_dir / "qa_lenguaje_youtube_ultra_post_guion.json", "qa_lenguaje_youtube_ultra_post_guion", {GateStatus.PASS, GateStatus.WARN}, blocked, failures)

    manifest = load_json(ep_path / "script_version_manifest.json", "ScriptVersionManifest", blocked, failures)
    approval = load_json(ep_path / "editorial_script_approval.json", "EditorialScriptApproval", blocked, failures)
    final = load_json(ep_path / "final_delivery_manifest.json", "FinalDeliveryManifest", blocked, failures)
    script = ep_path / "06_guion_longform.md"
    current_checksum = compute_checksum(script.read_text(encoding="utf-8")) if script.is_file() and script.read_text(encoding="utf-8").strip() else None

    if manifest:
        failures.extend(f"ScriptVersionManifest: {v}" for v in validate_against_schema(manifest, "script_version_manifest"))
        if manifest.get("script_id") != ep_id: failures.append("ScriptVersionManifest pertenece a otro episodio")
        if current_checksum and manifest.get("checksum") != current_checksum: failures.append("Checksum del manifest no coincide con el guion actual")
    if approval:
        failures.extend(f"EditorialScriptApproval: {v}" for v in validate_editorial_script_approval(approval))
        if approval.get("artifact_id") != ep_id: failures.append("Aprobación pertenece a otro episodio")
        if current_checksum and approval.get("checksum") != current_checksum: failures.append("Checksum aprobado no coincide con el guion actual")
        if manifest and approval.get("script_version") != manifest.get("version"): failures.append("La aprobación referencia una versión distinta")
        if manifest and approval.get("artifact_id") and approval.get("artifact_id") != manifest.get("script_id"): failures.append("Aprobación y manifest refieren artefactos distintos")
        if approval.get("invalidated_at"): failures.append("La aprobación está invalidada")
        if current_checksum and not InvalidationEngine().check_approval_validity(approval.get("checksum", ""), current_checksum): failures.append("Cambio posterior invalidó la aprobación")
    if final:
        failures.extend(f"FinalDeliveryManifest: {v}" for v in validate_against_schema(final, "final_delivery_manifest"))
        if manifest and final.get("human_approved_version") != manifest.get("version"):
            failures.append("FinalDeliveryManifest no referencia la versión aprobada")
        if manifest and final.get("final_candidate_version") != manifest.get("version"):
            failures.append("FinalDeliveryManifest no referencia la versión candidata exacta")
        if not final.get("approval_record"):
            failures.append("FinalDeliveryManifest no contiene approval_record")
        elif approval and final["approval_record"] != approval:
            failures.append("approval_record no coincide con la aprobación cargada")
        clean_rel = final.get("final_script_clean", "")
        annotated_rel = final.get("final_script_annotated", "")
        ledger_rel = final.get("claims_ledger", "")

        if clean_rel == annotated_rel:
            failures.append("Guion limpio y anotado deben ser artefactos distintos")

        def check_path_and_role(rel_path: str, role_label: str, allowed_ext: str, forbidden_keywords: list[str], allowed_basenames: list[str] | None = None) -> Path | None:
            if not rel_path or not isinstance(rel_path, str) or not rel_path.strip():
                failures.append(f"FinalDeliveryManifest {role_label}: ruta vacía o inválida")
                return None

            p = Path(rel_path)
            parts = rel_path.replace("\\", "/").split("/")
            if p.is_absolute() or rel_path.startswith("/") or rel_path.startswith("\\") or (len(rel_path) > 1 and rel_path[1] == ":") or ".." in parts:
                failures.append(f"FinalDeliveryManifest {role_label}: la ruta debe ser relativa y no escapar del episodio ({rel_path})")
                return None

            resolved_ep = ep_path.resolve()
            target = (ep_path / rel_path).resolve()
            try:
                target.relative_to(resolved_ep)
            except ValueError:
                failures.append(f"FinalDeliveryManifest {role_label}: la ruta se escapa de la carpeta del episodio ({rel_path})")
                return None

            if target == resolved_ep:
                failures.append(f"FinalDeliveryManifest {role_label}: referencia la carpeta raíz del episodio")
                return None

            lower_path = rel_path.lower()
            if allowed_ext and not lower_path.endswith(allowed_ext):
                failures.append(f"FinalDeliveryManifest {role_label} debe ser de tipo {allowed_ext}: {rel_path}")
                return None

            if allowed_basenames is not None:
                basename = parts[-1]
                if basename not in allowed_basenames:
                    failures.append(f"FinalDeliveryManifest {role_label}: nombre de archivo no permitido: {basename}. Debe ser uno de: {', '.join(allowed_basenames)}")
                    return None

            for kw in forbidden_keywords:
                if kw in lower_path:
                    failures.append(f"FinalDeliveryManifest {role_label} no puede ser un artefacto de {kw}: {rel_path}")
                    return None

            if not target.exists() or not target.is_file():
                blocked.append(f"FinalDeliveryManifest {role_label} referencia archivo ausente o no regular: {rel_path}")
                return None

            if not target.read_text(encoding="utf-8").strip():
                blocked.append(f"FinalDeliveryManifest {role_label} referencia archivo vacío: {rel_path}")
                return None

            return target

        target_clean = check_path_and_role(clean_rel, "final_script_clean", ".md", [], ["06_guion_longform.md", "06_guion_longform_limpio.md"])
        target_annotated = check_path_and_role(annotated_rel, "final_script_annotated", ".md", [], ["06_guion_longform_anotado.md"])
        target_ledger = check_path_and_role(ledger_rel, "claims_ledger", ".json", [])

        if target_ledger:
            ledger = load_json(target_ledger, "ClaimsLedger", blocked, failures)
            if ledger:
                failures.extend(f"ClaimsLedger: {item}" for item in validate_claims_ledger(ledger))
                if manifest and ledger.get("script_version") != manifest.get("version"):
                    failures.append("ClaimsLedger no referencia la versión exacta del guion")

        checksums = final.get("checksums", {})
        if not checksums or not isinstance(checksums, dict):
            failures.append("FinalDeliveryManifest: checksums no puede estar vacío")
        else:
            for key in (clean_rel, annotated_rel, ledger_rel):
                if key and key not in checksums:
                    failures.append(f"Checksum requerido ausente en FinalDeliveryManifest: {key}")

            for relative, expected_checksum in checksums.items():
                target = check_path_and_role(relative, f"checksums[{relative}]", "", [])
                if target:
                    actual_checksum = compute_checksum(target.read_text(encoding="utf-8"))
                    if actual_checksum != expected_checksum:
                        failures.append(f"Checksum incorrecto en FinalDeliveryManifest: {relative}")
    evidence["gate_directory"] = str(gate_dir)
    if blocked: return GateResult("cerrar_episodio", ep_id, "1.0.0", GateStatus.BLOCKED, "Cierre bloqueado por requisitos ausentes", blocked, evidence=evidence)
    if failures: return GateResult("cerrar_episodio", ep_id, "1.0.0", GateStatus.FAIL, "Cierre rechazado por contratos inválidos", failures, evidence=evidence)
    return GateResult("cerrar_episodio", ep_id, "1.0.0", GateStatus.PASS, "Cierre validado", evidence=evidence)


def save_index_atomically(index_path: Path, index: dict) -> None:
    """Escribe el índice completo y reemplaza el archivo solo tras un write correcto."""
    descriptor, temporary_path = tempfile.mkstemp(prefix=".episodes_index.", suffix=".tmp", dir=index_path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(index, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, index_path)
    except Exception:
        try:
            os.unlink(temporary_path)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--ep-id"); parser.add_argument("--config", default=str(REPO_ROOT / "config/local_settings.json")); parser.add_argument("--output-root")
    args = parser.parse_args(); config_path = Path(args.config)
    try: config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return run_gate(lambda: (_ for _ in ()).throw(RuntimeError(f"No se pudo cargar config: {exc}")), output_root=args.output_root)
    vault = expand_path(config.get("vault_root", "")); channel = config.get("channel_id")
    index_path = vault / str(channel) / "index/episodes_index.json"
    try: index = json.loads(index_path.read_text(encoding="utf-8")); episodes = index.get("episodes", [])
    except Exception as exc:
        return run_gate(lambda: (_ for _ in ()).throw(RuntimeError(f"No se pudo cargar índice: {exc}")), output_root=args.output_root)
    choices = [item for item in episodes if item.get("ep_id") == args.ep_id] if args.ep_id else [item for item in episodes if item.get("estado") == "en_progreso"]
    if len(choices) != 1:
        return run_gate(lambda: GateResult("cerrar_episodio", args.ep_id or "unknown", "1.0.0", GateStatus.BLOCKED, "No hay un episodio único para cerrar", ["Especifique un ep-id existente y único"]), output_root=args.output_root)
    entry = choices[0]; gates = output_root(args.output_root)
    if entry.get("estado") != "en_progreso":
        return run_gate(lambda: GateResult("cerrar_episodio", entry["ep_id"], "1.0.0", GateStatus.BLOCKED, "El episodio no está en progreso", [f"Estado actual: {entry.get('estado')}"]), output_root=args.output_root)
    result = evaluate(entry["ep_id"], expand_path(entry["ep_path"]), gates)
    if result.status == GateStatus.PASS:
        entry["estado"] = "completado"; entry["cerrado"] = datetime.now(timezone.utc).isoformat(); index["last_updated"] = entry["cerrado"]
        try:
            save_index_atomically(index_path, index)
        except Exception as exc:
            return run_gate(lambda: (_ for _ in ()).throw(RuntimeError(f"No se pudo actualizar el índice: {exc}")), output_root=args.output_root)
    return run_gate(lambda: result, output_root=args.output_root)

if __name__ == "__main__":
    import sys
    sys.exit(main())
