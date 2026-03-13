# File: src/scripts/cerrar_episodio.py
# ──────────────────────────────────────────────────────────────────────
# Propósito: Validar entregables del episodio activo y marcarlo como completado.
# Rol: Último paso del pipeline. Garantiza que no se cierre un episodio incompleto.
# ──────────────────────────────────────────────────────────────────────
#
# Uso:
#   python src/scripts/cerrar_episodio.py
#   python src/scripts/cerrar_episodio.py --ep-id ep_0001  (cerrar uno específico)
#   python src/scripts/cerrar_episodio.py --forzar          (cierra aunque falten archivos opcionales)
#
# Validación:
#   - Verifica los 5 entregables OBLIGATORIOS del episodio.
#   - Verifica que el Gate V (veracidad) tenga ESTADO_GLOBAL: OK.
#   - Si alguno falta o Gate V no es OK → 🔴 STOP, lista detallada de faltantes.
#   - Si todos presentes y Gate V OK → Actualiza índice con estado "completado".
# ──────────────────────────────────────────────────────────────────────

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# ─── Constantes ────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "local_settings.json"
INDEX_FILENAME = "episodes_index.json"

# Entregables obligatorios para considerar un episodio completo
ENTREGABLES_OBLIGATORIOS = [
    "06_guion_longform.md",
    "07_verificacion_veracidad_notebooklm.md",  # Gate V obligatorio
    "08_shorts.md",
    "09_packaging.md",
    "10_seo.md",
]

# Marcador de Gate V que debe aparecer en el reporte de veracidad
GATE_V_ARCHIVO = "07_verificacion_veracidad_notebooklm.md"
GATE_V_MARCADOR_OK = "ESTADO_GLOBAL: OK"

# Entregables deseables (no bloquean el cierre pero generan WARN)
# Nota: 99_notebooklm_pack.md puede moverse a OBLIGATORIOS activando
# "notebooklm_pack_required": true en config/local_settings.json
ENTREGABLES_DESEABLES = [
    "00_brief_episodio.md",
    "01_research_bruto.md",
    "02_curation_obras.md",
    "03_mapa_eventos.md",
    "04_analisis_patrones.md",
    "05_sintesis_tesis.md",
    "07_qa_revisiones.md",
    "99_notebooklm_pack.md",
]


# ─── Helpers ────────────────────────────────────────────────────────────────────
def load_config() -> dict:
    if not CONFIG_PATH.exists():
        _abort(f"No se encontró config en: {CONFIG_PATH}")
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    for key in ("vault_root", "channel_id"):
        if not cfg.get(key):
            _abort(f"Clave '{key}' faltante en local_settings.json")
    return cfg


def load_index(index_path: Path) -> dict:
    if not index_path.exists():
        _abort(f"Índice no encontrado: {index_path}\nEjecuta iniciar_episodio.py primero.")
    with open(index_path, encoding="utf-8") as f:
        return json.load(f)


def save_index(index_path: Path, index: dict) -> None:
    index["last_updated"] = datetime.now().isoformat()
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def _abort(msg: str) -> None:
    print(f"\n🔴 ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _warn(msg: str) -> None:
    print(f"⚠️  WARN: {msg}")


def _ok(msg: str) -> None:
    print(f"✅ {msg}")


# ─── Verificación de entregables ────────────────────────────────────────────────
def verificar_entregables(ep_path: Path) -> tuple[list, list]:
    """
    Verifica entregables del episodio.
    Retorna: (faltantes_obligatorios, faltantes_deseables)
    """
    faltantes_oblig = []
    faltantes_desea = []

    for archivo in ENTREGABLES_OBLIGATORIOS:
        if not (ep_path / archivo).exists():
            faltantes_oblig.append(archivo)

    for archivo in ENTREGABLES_DESEABLES:
        if not (ep_path / archivo).exists():
            faltantes_desea.append(archivo)

    return faltantes_oblig, faltantes_desea


# ─── Validación Gate V ────────────────────────────────────────────────────────────
def verificar_gate_v(ep_path: Path) -> str:
    """
    Lee el reporte de veracidad y verifica que contenga ESTADO_GLOBAL: OK.
    Retorna: 'OK', 'WARN', 'FAIL', o 'AUSENTE'.
    """
    gate_v_path = ep_path / GATE_V_ARCHIVO
    if not gate_v_path.exists():
        return "AUSENTE"
    contenido = gate_v_path.read_text(encoding="utf-8")
    if "ESTADO_GLOBAL: OK" in contenido:
        return "OK"
    elif "ESTADO_GLOBAL: WARN" in contenido:
        return "WARN"
    elif "ESTADO_GLOBAL: FAIL" in contenido:
        return "FAIL"
    return "AUSENTE"


def imprimir_resumen(ep_path: Path, faltantes_oblig: list, faltantes_desea: list) -> None:
    """Imprime el resumen de validación de entregables."""
    print("\n📋 Resumen de entregables:")

    total_oblig = len(ENTREGABLES_OBLIGATORIOS)
    presentes_oblig = total_oblig - len(faltantes_oblig)
    print(f"   Obligatorios: {presentes_oblig}/{total_oblig}")

    if faltantes_oblig:
        print("\n   🔴 Faltantes OBLIGATORIOS:")
        for f in faltantes_oblig:
            print(f"      ❌ {f}")

    if faltantes_desea:
        print(f"\n   ⚠️  Faltantes deseables ({len(faltantes_desea)}):")
        for f in faltantes_desea:
            print(f"      - {f}")

    presentes_des = len(ENTREGABLES_DESEABLES) - len(faltantes_desea)
    print(f"   Deseables: {presentes_des}/{len(ENTREGABLES_DESEABLES)}")


# ─── Lógica principal ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Cerrar el episodio activo y marcarlo como completado."
    )
    parser.add_argument(
        "--ep-id", type=str, default=None,
        help="ID del episodio a cerrar (ej: ep_0001). Si no se da, usa el único 'en_progreso'."
    )
    parser.add_argument(
        "--forzar", action="store_true",
        help="Cierra el episodio aunque falten entregables deseables (no los obligatorios)."
    )
    args = parser.parse_args()

    # ── Cargar config ──
    cfg = load_config()
    vault_root = Path(cfg["vault_root"])
    channel_id = cfg["channel_id"]
    index_path = vault_root / channel_id / "index" / INDEX_FILENAME

    # ── Flag NotebookLM Pack ──
    # Si notebooklm_pack_required=true en local_settings.json,
    # el 99_notebooklm_pack.md se vuelve obligatorio para el cierre.
    notebooklm_pack_required = cfg.get("notebooklm_pack_required", False)
    if notebooklm_pack_required and "99_notebooklm_pack.md" in ENTREGABLES_DESEABLES:
        ENTREGABLES_DESEABLES.remove("99_notebooklm_pack.md")
        ENTREGABLES_OBLIGATORIOS.append("99_notebooklm_pack.md")
        print("ℹ️  Modo NotebookLM activo: 99_notebooklm_pack.md es OBLIGATORIO")

    # ── Cargar índice ──
    index = load_index(index_path)
    episodes = index.get("episodes", [])

    # ── Encontrar episodio a cerrar ──
    if args.ep_id:
        candidatos = [e for e in episodes if e.get("ep_id") == args.ep_id]
        if not candidatos:
            _abort(f"No se encontró el episodio '{args.ep_id}' en el índice.")
        ep_entry = candidatos[0]
    else:
        in_progress = [e for e in episodes if e.get("estado") == "en_progreso"]
        if not in_progress:
            _abort("No hay episodios con estado 'en_progreso'.\n"
                   "Usa --ep-id para especificar uno manualmente si crees que hay error.")
        if len(in_progress) > 1:
            ids = ", ".join(e.get("ep_id", "?") for e in in_progress)
            _abort(f"Hay múltiples episodios en_progreso: {ids}\n"
                   "Usa --ep-id para indicar cuál cerrar.")
        ep_entry = in_progress[0]

    ep_path = Path(ep_entry["ep_path"])
    ep_id = ep_entry["ep_id"]
    print(f"\n🔒 Cerrando episodio: {ep_id}")
    print(f"   Ruta: {ep_path}\n")

    # ── Verificar que la carpeta existe ──
    if not ep_path.exists():
        _abort(f"La carpeta del episodio no existe: {ep_path}")

    # ── Verificar entregables ──
    faltantes_oblig, faltantes_desea = verificar_entregables(ep_path)
    imprimir_resumen(ep_path, faltantes_oblig, faltantes_desea)

    # ── Verificar Gate V (veracidad) ──
    gate_v_estado = verificar_gate_v(ep_path)
    if gate_v_estado == "AUSENTE":
        print(f"\n🔴 GATE V: '{GATE_V_ARCHIVO}' no existe.")
        print("   El reporte de veracidad es obligatorio antes del cierre.")
        print("   Ejecuta: skill_verificacion_veracidad_notebooklm.md")
        sys.exit(1)
    elif gate_v_estado in ("WARN", "FAIL"):
        print(f"\n🔴 GATE V: '{GATE_V_ARCHIVO}' tiene ESTADO_GLOBAL: {gate_v_estado}.")
        print("   No se puede cerrar el episodio con warnings o fallos de veracidad.")
        print("   Corrige el guion, repite QA y Gate V antes de cerrar.")
        sys.exit(1)
    else:
        _ok(f"Gate V (veracidad): {gate_v_estado}")

    # ── Gate: bloquear si faltan obligatorios ──
    if faltantes_oblig:
        print(f"\n🔴 STOP: El episodio '{ep_id}' no puede cerrarse.")
        print("   Completa los entregables obligatorios antes de cerrar.")
        sys.exit(1)

    # ── Aviso si faltan deseables ──
    if faltantes_desea and not args.forzar:
        print(f"\n⚠️  Hay {len(faltantes_desea)} entregable(s) deseable(s) faltantes.")
        print("   El episodio PUEDE cerrarse (no son bloqueantes).")
        print("   Usa --forzar para omitir esta advertencia en el futuro.")

    # ── Actualizar índice ──
    ep_entry["estado"] = "completado"
    ep_entry["cerrado"] = datetime.now().isoformat()
    ep_entry["entregables_faltantes_al_cierre"] = faltantes_desea if faltantes_desea else []
    save_index(index_path, index)
    _ok(f"Índice actualizado: {index_path}")

    # ── Resultado final ──
    print(f"\n🟢 Episodio '{ep_id}' cerrado correctamente.")
    print(f"   Estado: completado")
    print(f"   Cerrado: {ep_entry['cerrado']}")
    if faltantes_desea:
        _warn(f"{len(faltantes_desea)} entregable(s) deseable(s) quedaron pendientes (registrados en índice).")
    print()


if __name__ == "__main__":
    main()
