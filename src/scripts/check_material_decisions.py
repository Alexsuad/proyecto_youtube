"""Gate determinista del registro de decisiones materiales del PLAN 008, Misión 1.

Valida:
- schema del registro;
- autoridad dentro del vocabulario canónico de gobernanza;
- evidencia obligatoria y referencias locales resolubles;
- integridad de sucesión (sin ciclos, sin autoreferencias, sin sucesores inexistentes);
- unicidad de autoridad para decisiones vigentes;
- existencia física de los archivos legacy indexados, consumidores y sucesores;
- no ejecutabilidad de la documentación legacy;
- que la vista per-file comprometida esté derivada del registro canónico.

Uso:
    python src/scripts/check_material_decisions.py            # verifica y compara la vista
    python src/scripts/check_material_decisions.py --render   # regenera la vista derivada
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.material_decision_registry import (
    expected_view_path,
    load_registry,
    registry_path,
    render_view,
    validate_local_refs,
    validate_registry,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate del registro de decisiones materiales")
    parser.add_argument("--render", action="store_true", help="Regenerar la vista derivada en disco")
    args = parser.parse_args()

    violations = validate_registry(load_registry(registry_path()))
    violations.extend(validate_local_refs(load_registry(registry_path()), ROOT))

    if violations:
        for violation in violations:
            print(f"FAIL: {violation}")
        print(f"exit_code: 1")
        return 1

    rendered = render_view(load_registry(registry_path()))
    view_path = expected_view_path()
    if args.render:
        view_path.parent.mkdir(parents=True, exist_ok=True)
        view_path.write_text(rendered, encoding="utf-8")
        print(f"OK: vista derivada regenerada en {view_path}")
        print("exit_code: 0")
        return 0

    if not view_path.is_file():
        print(f"FAIL: vista derivada inexistente en {view_path}")
        print("exit_code: 1")
        return 1
    committed = view_path.read_text(encoding="utf-8")
    if committed != rendered:
        print("FAIL: la vista per-file no coincide con la derivación del registro canónico")
        print("exit_code: 1")
        return 1

    print("PASS: registro de decisiones materiales válido y vista derivada consistente")
    print("exit_code: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())