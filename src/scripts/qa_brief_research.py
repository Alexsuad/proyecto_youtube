# File: src/scripts/qa_brief_research.py
# ──────────────────────────────────────────────────────────────────────
# Propósito: Script formal para la Skill skill_qa_brief_research.
# Rol: Validador determinista de Brief y Research pre-Gate Humano.
# ──────────────────────────────────────────────────────────────────────

import os
import re
from pathlib import Path
import argparse

REPO_ROOT = Path(__file__).parent.parent.parent

def check(label, ok, detail=""):
    icon = "✅" if ok else "❌"
    line = f"- {icon} {label}"
    if detail:
        line += f" — {detail}"
    return line, ok

def _write(lines, result, output_path):
    severity = "PASS" if result else "FAIL"
    lines.append(f"\n---\n**ESTADO_GLOBAL:** {severity}")
    if not result:
        lines.append("\n**CORRECCIONES REQUERIDAS:**")
        lines.append("- Revise los puntos marcados con ❌ y actualice los archivos correspondientes.")
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[qa_brief_research] ESTADO_GLOBAL: {severity} -> {output_path}")

def run(ep_path_str):
    ep_path = Path(ep_path_str)
    ep_name = ep_path.name
    brief_path = ep_path / "00_brief_episodio.md"
    research_path = ep_path / "01_research_bruto.md"
    
    # Extraer ID del episodio (ej. ep_0001) de la carpeta
    ep_match = re.search(r'(ep_\d+)', ep_name)
    ep_id = ep_match.group(1) if ep_match else ep_name
    
    output_path = REPO_ROOT / "output" / f"auditoria_brief_research_{ep_id}.md"
    
    lines = []
    all_ok = True
    
    lines.append(f"# Auditoría Brief y Research: {ep_name}")
    
    # ─── A) Brief ─────────────────────────────────────
    lines.append("\n## A) Brief (00_brief_episodio.md)")
    if not brief_path.exists():
        msg, ok = check("Archivo 00_brief_episodio.md", False, "NO ENCONTRADO")
        lines.append(msg); all_ok = False
    else:
        with open(brief_path, "r", encoding="utf-8") as f:
            b_text = f.read()
            
        # FECHA existe y formato YYYY-MM-DD
        m = re.search(r"- FECHA:\s*(\d{4}-\d{2}-\d{2})", b_text)
        if m:
            lines.append(check("FECHA formato YYYY-MM-DD", True, m.group(1))[0])
        else:
            lines.append(check("FECHA formato YYYY-MM-DD", False, "No válido o vacío")[0]); all_ok = False
            
        # TESIS_CENTRAL existe
        m = re.search(r"- TESIS_CENTRAL \(\d+ frase[s]?\):\s*(.+)", b_text)
        tesis = m.group(1).strip() if m else ""
        if tesis and "[PENDIENTE]" not in tesis:
            lines.append(check("TESIS_CENTRAL", True)[0])
        else:
            lines.append(check("TESIS_CENTRAL", False, "Vacía o pendiente")[0]); all_ok = False
            
        # OBRAS_PRINCIPALES: 1-5
        obras_section = re.search(r"- OBRAS_PRINCIPALES \(lista\):(.*?)- 5_IDEAS_FUERZA", b_text, re.DOTALL)
        if obras_section:
            bullets = len(re.findall(r"^\s*-\s+", obras_section.group(1), re.MULTILINE))
            if 1 <= bullets <= 5:
                lines.append(check(f"OBRAS_PRINCIPALES (1-5)", True, f"Hay {bullets}")[0])
            else:
                lines.append(check(f"OBRAS_PRINCIPALES (1-5)", False, f"Hay {bullets}")[0]); all_ok = False
        else:
            lines.append(check("OBRAS_PRINCIPALES", False, "Sección no detectada")[0]); all_ok = False

        # 5_IDEAS_FUERZA: exactamente 5 bullets
        ideas_section = re.search(r"- 5_IDEAS_FUERZA \(bullets\):(.*?)- AUDIENCIA", b_text, re.DOTALL)
        if ideas_section:
            bullets = len(re.findall(r"^\s*-\s+", ideas_section.group(1), re.MULTILINE))
            if bullets == 5:
                lines.append(check(f"5_IDEAS_FUERZA (5)", True, f"Hay {bullets}")[0])
            else:
                lines.append(check(f"5_IDEAS_FUERZA (5)", False, f"Hay {bullets}")[0]); all_ok = False
        else:
            lines.append(check("5_IDEAS_FUERZA", False)[0]); all_ok = False

        # PREGUNTAS_GUIA: 8-12
        pregs_section = re.search(r"- PREGUNTAS_GUIA \([^)]+\):(.*?)- DIFERENCIADOR", b_text, re.DOTALL)
        if pregs_section:
            bullets = len(re.findall(r"^\s*-\s+", pregs_section.group(1), re.MULTILINE))
            if 8 <= bullets <= 12:
                lines.append(check(f"PREGUNTAS_GUIA (8-12)", True, f"Hay {bullets}")[0])
            else:
                lines.append(check(f"PREGUNTAS_GUIA (8-12)", False, f"Hay {bullets}")[0]); all_ok = False
        else:
            lines.append(check("PREGUNTAS_GUIA", False)[0]); all_ok = False
            
        # NIVEL_SPOILER y SENSIBILIDADES
        spoil_sect = re.search(r"- SPOILERS/SENSIBILIDADES:\s*(.+)", b_text, re.IGNORECASE)
        val = spoil_sect.group(1).strip() if spoil_sect else ""
        if val and "[PENDIENTE]" not in val:
            lines.append(check("SPOILERS/SENSIBILIDADES", True)[0])
        else:
            lines.append(check("SPOILERS/SENSIBILIDADES", False, "Falta especificar o indicar nivel de spoiler")[0]); all_ok = False

    # ─── B) Research ──────────────────────────────────
    lines.append("\n## B) Research (01_research_bruto.md)")
    if not research_path.exists():
        msg, ok = check("Archivo 01_research_bruto.md", False, "NO ENCONTRADO")
        lines.append(msg); all_ok = False
    else:
        with open(research_path, "r", encoding="utf-8") as f:
            r_text = f.read()
            
        # Mínimo 8 URLs reales
        urls = re.findall(r"https?://[^\s\)]+", r_text)
        unique_urls = set(urls)
        if len(unique_urls) >= 8:
            lines.append(check(f">= 8 URLs reales", True, f"Hay {len(unique_urls)}")[0])
        else:
            lines.append(check(f">= 8 URLs reales", False, f"Solo {len(unique_urls)} detectadas")[0]); all_ok = False
            
        # Formato de fuente: Título, URL, "Por qué sirve"
        # Para ser flexibles verificamos si hay mención de "Por qué sirve" cerca de cada URL o conteo similar
        por_que = len(re.findall(r"[pP]or qu[eé] sirve", r_text, re.IGNORECASE))
        if por_que >= 8:
            lines.append(check("Formato de fuentes ('Por qué sirve' x8 mín.)", True, f"Detectado {por_que} veces")[0])
        else:
            lines.append(check("Formato de fuentes ('Por qué sirve' x8 mín.)", False, f"Solo {por_que} veces")[0]); all_ok = False
            
        # Riesgos/sensibilidades
        if re.search(r"(?:Riesgos|Sensibilidades)\s*(?:\n|:)", r_text, re.IGNORECASE):
            lines.append(check("Riesgos/Sensibilidades presentes", True)[0])
        else:
            lines.append(check("Riesgos/Sensibilidades presentes", False)[0]); all_ok = False
            
        # Marcar advertencias si usó fuentes débiles
        lower_r = r_text.lower()
        warns = []
        if "wiki" in lower_r: warns.append("wiki")
        if "fandom" in lower_r: warns.append("fandom")
        if warns:
            lines.append("\n> **⚠️ ADVERTENCIA:** Se detectó el uso de palabras ligadas a fuentes débiles: " + ", ".join(warns))

    _write(lines, all_ok, output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ep_path", required=True)
    args = parser.parse_args()
    run(args.ep_path)
