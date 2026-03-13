# File: src/scripts/qa_duracion_guion.py
# ──────────────────────────────────────────────────────────────────────
# Propósito: Evaluar la duración estimada del guion basándose en el conteo de palabras.
# Rol: Gate de calidad para asegurar que el contenido cumple con el target de retención.
# ──────────────────────────────────────────────────────────────────────

import argparse
import os
import re
from pathlib import Path

def count_words(text):
    # Limpiar formato básico de markdown para no inflar el conteo
    text = re.sub(r'#+\s+', '', text)
    text = re.sub(r'\*\*|\*', '', text)
    # Contar palabras
    words = re.findall(r'\b\w+\b', text)
    return len(words)

def main():
    parser = argparse.ArgumentParser(description="Auditoría de duración de guion.")
    parser.add_argument("--ep_path", required=True, help="Ruta de la carpeta del episodio.")
    parser.add_argument("--wpm", type=int, default=144, help="Palabras por minuto (velocidad de lectura)")
    parser.add_argument("--min_target", type=int, default=18, help="Duración mínima objetivo.")
    parser.add_argument("--max_target", type=int, default=22, help="Duración máxima objetivo.")
    args = parser.parse_args()

    ep_path = Path(args.ep_path)
    guion_path = ep_path / "06_guion_longform.md"

    if not guion_path.exists():
        print(f"🔴 Error: No se encuentra el guion en {guion_path}")
        exit(1)

    content = guion_path.read_text(encoding="utf-8")
    
    # Excluir la sección de INTRODUCCIÓN y CIERRE si se desea un conteo más fino, 
    # pero aquí contaremos todo el cuerpo del guion.
    total_words = count_words(content)
    duration_min = total_words / args.wpm
    
    status = "PASS" if args.min_target <= duration_min <= args.max_target else "FAIL"
    
    recommendation = "OK"
    diff_percent = 0
    if duration_min < args.min_target:
        diff_percent = ((args.min_target - duration_min) / args.min_target) * 100
        recommendation = f"EXPANDIR: Faltan aprox. {diff_percent:.1f}% de contenido para llegar al mínimo."
    elif duration_min > args.max_target:
        diff_percent = ((duration_min - args.max_target) / args.max_target) * 100
        recommendation = f"RECORTAR: Sobra aprox. {diff_percent:.1f}% de contenido para no exceder el máximo."

    # Crear carpeta de output si no existe
    output_dir = Path("output/qa_duracion")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    ep_name = ep_path.name
    report_path = output_dir / f"{ep_name}__qa_duracion.md"
    
    report_content = f"""# Reporte de Auditoría de Duración
**Episodio:** {ep_name}
**Estado:** {status}

## Métricas
- **Total de palabras:** {total_words}
- **WPM configurado:** {args.wpm}
- **Duración estimada:** {duration_min:.2f} minutos
- **Rango objetivo:** {args.min_target} - {args.max_target} min

## Recomendación
{recommendation}
"""

    report_path.write_text(report_content, encoding="utf-8")
    print(f"[qa_duracion] ESTADO_GLOBAL: {status} — Reporte en: {report_path}")
    
    if status == "FAIL":
        exit(1)

if __name__ == "__main__":
    main()
