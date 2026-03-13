import argparse
import sys
import re
from pathlib import Path
from datetime import datetime

# File: src/scripts/qa_lenguaje_youtube_ultra.py
# ──────────────────────────────────────────────────────────────────────
# Propósito: Scaner determinista Modo A (Ultra Seguro) basado en MD configs.
# Rol: Gate Pre-Guion y Post-Guion.
# ──────────────────────────────────────────────────────────────────────

def cargar_politica_md(md_path):
    config = {
        'roja': [],
        'amarilla': [],
        'reemplazos': {},
        'zonas_criticas': ["título", "miniatura", "hook", "cta"]
    }
    
    current_section = None
    
    with open(md_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Detectar secciones
            if line.startswith("## Lista ROJA"):
                current_section = "roja"
                continue
            elif line.startswith("## Lista AMARILLA"):
                current_section = "amarilla"
                continue
            elif line.startswith("## Alternativas seguras"):
                current_section = "reemplazos"
                continue
            elif line.startswith("## ") and current_section:
                current_section = None # Finalizó lista
                
            # Parsear items
            if current_section in ["roja", "amarilla"] and line.startswith('- '):
                # Limpiar notas en parentesis o texto despues de item
                item = line[2:].split('(')[0].strip().lower()
                if item and not item.startswith("no listar"):
                    config[current_section].append(item)
                    
            elif current_section == "reemplazos" and line.startswith('- '):
                parts = line[2:].split('->')
                if len(parts) == 2:
                    keys = [k.strip().lower() for k in parts[0].split(',')]
                    val = parts[1].strip()
                    for k in keys:
                        # Limpiar sub items
                        k_clean = k.split('/')[0].strip()
                        config['reemplazos'][k_clean] = val

    return config

def main():
    parser = argparse.ArgumentParser(description="QA de Lenguaje YouTube (Modo Ultra Seguro)")
    parser.add_argument("--ep_path", required=True, help="Ruta absoluta al directorio del episodio")
    parser.add_argument("--fase", required=True, choices=["pre-guion", "post-guion"], help="Fase a ejecutar")
    args = parser.parse_args()

    ep_path = Path(args.ep_path)
    if not ep_path.exists():
        print(f"Error: No se encontró la ruta {ep_path}")
        sys.exit(1)

    repo_root = Path(__file__).parent.parent.parent
    config_path = repo_root / "config" / "qa_youtube_lenguaje_ultra_seguro.md"
    
    config = cargar_politica_md(config_path)

    if args.fase == "pre-guion":
        files_to_check = ["00_brief_episodio.md", "04_analisis_patrones.md", "05_sintesis_tesis.md"]
    else:
        files_to_check = ["06_guion_longform.md", "09_packaging.md", "10_seo.md"]

    findings = []
    critical_markers = config['zonas_criticas']

    for fname in files_to_check:
        fpath = ep_path / fname
        if not fpath.exists():
            continue
            
        with open(fpath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            lower_line = line.lower()
            
            # Determinación de criticidad general (por nombre de archivo / area del doc)
            is_critical = False
            for marker in critical_markers:
                if marker in lower_line:
                    is_critical = True
                    break
                    
            if fname == "00_brief_episodio.md" and line_num < 15:
                is_critical = True
            elif fname in ["09_packaging.md", "10_seo.md"]:
                is_critical = True
            
            # Chequeo Lista Roja
            for word in config['roja']:
                if re.search(r'\b' + re.escape(word) + r'\b', lower_line):
                    findings.append({
                        "file": fname,
                        "word": word,
                        "level": "🔴 FAIL (ROJO)",
                        "line_num": line_num,
                        "context": line.strip()[:60] + "...",
                        "replace": "ELIMINAR"
                    })
            
            # Chequeo Lista Amarilla
            for word in config['amarilla']:
                if re.search(r'\b' + re.escape(word) + r'\b', lower_line):
                    level = "🔴 FAIL (AMARILLO EN CRÍTICO)" if is_critical else "🟡 WARN (AMARILLO)"
                    reemplazo = config['reemplazos'].get(word, "Término suave clínico")
                    
                    findings.append({
                        "file": fname,
                        "word": word,
                        "level": level,
                        "line_num": line_num,
                        "context": line.strip()[:60] + "...",
                        "replace": reemplazo
                    })

    # Filtrar falsos duplicados si una palabra es substring de otra, aunque regex \b minimiza esto
    # Exportar Reporte
    ep_folder_name = ep_path.name
    output_dir = repo_root / "output" / "qa_youtube_lenguaje"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"{ep_folder_name}__qa_youtube_ultra.md"

    fails = [f for f in findings if "FAIL" in f["level"]]
    estado_global = "FAIL" if fails else "PASS"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Reporte QA Lenguaje YouTube (Modo A - Ultra Seguro)\n")
        f.write(f"**Episodio:** {ep_folder_name}\n")
        f.write(f"**Fase:** {args.fase.upper()}\n")
        f.write(f"**Fecha:** {datetime.now().isoformat()}\n\n")
        f.write(f"## Resultado General: **{estado_global}**\n\n")
        
        if not findings:
            f.write("✅ No se detectaron palabras de riesgo algorítmico.\n")
        else:
            f.write("### Hallazgos del Escáner\n")
            f.write("| Palabra | Archivo | Ubicación (Contexto) | Severidad | Reemplazo Sugerido |\n")
            f.write("|---------|---------|----------------------|-----------|--------------------|\n")
            
            for find in findings:
                ctx = find['context'].replace('|', ' ')
                rep = find['replace'].replace('|', ' ')
                f.write(f"| `{find['word']}` | {find['file']} (L{find['line_num']}) | *\"{ctx}\"* | {find['level']} | {rep} |\n")

    print(f"[qa_lenguaje_ultra_{args.fase}] ESTADO_GLOBAL: {estado_global} — output: {report_path}")

    if estado_global == "FAIL":
        sys.exit(1)

if __name__ == '__main__':
    main()
