# File: src/scripts/qa_momento_1.py
# ──────────────────────────────────────────────────────────────────────
# Propósito: Verificación automática de calidad para el Brief y Research (Gate Humano Momento 1).
# Rol: Asegurar que los campos clave y las fuentes estén completos y sean válidos.
# ──────────────────────────────────────────────────────────────────────

import os
import re
from pathlib import Path
import argparse

REPO_ROOT = Path(__file__).parent.parent.parent

def h2(title):
    return f"\n## {title}\n"

def check(label, ok, detail=""):
    icon = "✅" if ok else "❌"
    line = f"- {icon} {label}"
    if detail:
        line += f" — {detail}"
    return line

def _write(lines, severity, output_path):
    lines.append(f"\n---\nESTADO_GLOBAL: {severity}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[qa_momento_1] ESTADO_GLOBAL: {severity} — output: {output_path}")

def run(ep_path_str):
    ep_path = Path(ep_path_str)
    ep_name = ep_path.name
    brief_path = ep_path / "00_brief_episodio.md"
    research_path = ep_path / "01_research_bruto.md"
    
    # Nuevo destino del reporte
    output_path = REPO_ROOT / "output" / "qa_momento_1" / f"{ep_name}__qa_momento_1.md"
    
    lines = []
    severity = "OK"  # OK | FAIL
    
    lines.append("# QA Momento 1 (Brief y Research)")
    lines.append(f"**Episodio:** {ep_name}\n")
    
    # ─── Validación de Brief ─────────────────────────────────────
    lines.append(h2("1. Verificación de 00_brief_episodio.md"))
    if not brief_path.exists():
        lines.append(check("Archivo 00_brief_episodio.md", False, "NO ENCONTRADO"))
        severity = "FAIL"
    else:
        with open(brief_path, "r", encoding="utf-8") as f:
            brief_content = f.read()
            
        # FECHA no vacía y en formato YYYY-MM-DD
        fecha_match = re.search(r"- FECHA:\s*(\d{4}-\d{2}-\d{2})", brief_content)
        if fecha_match:
            lines.append(check("FECHA formato YYYY-MM-DD", True, fecha_match.group(1)))
        else:
            lines.append(check("FECHA formato YYYY-MM-DD", False, "Falta o formato inválido"))
            severity = "FAIL"
            
        # OBRAS_PRINCIPALES no vacía
        obras_section = re.search(r"- OBRAS_PRINCIPALES \(lista\):(.*?)- 5_IDEAS_FUERZA", brief_content, re.DOTALL)
        if obras_section and "[PENDIENTE]" not in obras_section.group(1):
            lines.append(check("OBRAS_PRINCIPALES no vacía", True))
        else:
            lines.append(check("OBRAS_PRINCIPALES no vacía", False, "Lista pendiente o no encontrada"))
            severity = "FAIL"
            
        # 5_IDEAS_FUERZA: exactamente 5 bullets
        ideas_section = re.search(r"- 5_IDEAS_FUERZA \(bullets\):(.*?)- AUDIENCIA", brief_content, re.DOTALL)
        if ideas_section:
            bullets = len(re.findall(r"^\s*-\s+", ideas_section.group(1), re.MULTILINE))
            if bullets == 5:
                lines.append(check(f"5_IDEAS_FUERZA (5 bullets)", True, f"Encontrados {bullets}"))
            else:
                lines.append(check(f"5_IDEAS_FUERZA (5 bullets)", False, f"Se encontraron {bullets}"))
                severity = "FAIL"
        else:
            lines.append(check(f"5_IDEAS_FUERZA (5 bullets)", False, "Sección no encontrada"))
            severity = "FAIL"

        # PREGUNTAS_GUIA: entre 8 y 12
        pregs_section = re.search(r"- PREGUNTAS_GUIA \([^)]+\):(.*?)- DIFERENCIADOR", brief_content, re.DOTALL)
        if pregs_section:
            bullets = len(re.findall(r"^\s*-\s+", pregs_section.group(1), re.MULTILINE))
            if 8 <= bullets <= 12:
                lines.append(check(f"PREGUNTAS_GUIA (8-12 bullets)", True, f"Encontrados {bullets}"))
            else:
                lines.append(check(f"PREGUNTAS_GUIA (8-12 bullets)", False, f"Se encontraron {bullets}"))
                severity = "FAIL"
        else:
            lines.append(check(f"PREGUNTAS_GUIA (8-12 bullets)", False, "Sección no encontrada"))
            severity = "FAIL"

        # NIVEL_SPOILER indicado
        spoiler_match = re.search(r"- SPOILERS/SENSIBILIDADES:\s*(.*)", brief_content)
        spoiler_val = spoiler_match.group(1).strip() if spoiler_match else ""
        if spoiler_val and "[PENDIENTE]" not in spoiler_val:
            lines.append(check("NIVEL_SPOILER indicado", True, spoiler_val[:50] + "..."))
        else:
            lines.append(check("NIVEL_SPOILER indicado", False, "No especificado"))
            severity = "FAIL"

    # ─── Validación de Research ──────────────────────────────────
    lines.append(h2("2. Verificación de 01_research_bruto.md"))
    if not research_path.exists():
        lines.append(check("Archivo 01_research_bruto.md", False, "NO ENCONTRADO"))
        severity = "FAIL"
    else:
        with open(research_path, "r", encoding="utf-8") as f:
            research_content = f.read()
            
        # Extraer bloques de fuentes (ej. números en listas o líneas con URLs)
        # Buscar "Por qué sirve" asociado a URLs
        # Para simplificar y hacerlo robusto, contamos cuántas URLs válidas tienen cerca "Por qué sirve" (o están en el mismo ítem de lista)
        # Método simple: contar cuántas ocurrencias de "Por qué sirve" existen
        # Método mejor: contar bloques que contienen una URL y la frase "Por qué sirve"
        
        # Obtenemos los bloques separados por números de lista
        blocks = re.split(r'\n\s*\d+\.\s+\*\*', research_content)
        valid_sources = 0
        for block in blocks:
            if re.search(r"https?://[^\s\)]+", block) and re.search(r"[pP]or qu[eé] sirve", block, re.IGNORECASE):
                valid_sources += 1
                
        if valid_sources >= 8:
            lines.append(check(f">= 8 URLs asociadas a 'Por qué sirve'", True, f"Encontradas {valid_sources} fuentes útiles"))
        else:
            lines.append(check(f">= 8 URLs asociadas a 'Por qué sirve'", False, f"Solo se encontraron {valid_sources} (se requieren 8)"))
            severity = "FAIL"

    _write(lines, severity, output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ejecutar QA de Momento 1")
    parser.add_argument("--ep_path", required=True, help="Ruta absoluta al directorio del episodio")
    args = parser.parse_args()
    
    run(args.ep_path)
