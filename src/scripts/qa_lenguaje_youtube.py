import argparse
import sys
import re
from pathlib import Path
from datetime import datetime

# File: src/scripts/qa_lenguaje_youtube.py
# ──────────────────────────────────────────────────────────────────────
# Propósito: Scaner determinista (Modo Ultra Seguro) para auditoría de lenguaje.
# Rol: Gate Pre-Guion y Post-Guion.
# ──────────────────────────────────────────────────────────────────────

def parse_simple_yaml(yaml_path):
    config = {
        'lista_roja': [],
        'lista_amarilla': [],
        'reemplazos': {},
        'zonas_criticas': []
    }
    
    current_key = None
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.endswith(':'):
                current_key = line[:-1].strip()
            elif current_key in ['lista_roja', 'lista_amarilla', 'zonas_criticas']:
                if line.startswith('-'):
                    item = line.replace('-', '', 1).strip().strip('"').strip("'")
                    config[current_key].append(item)
            elif current_key == 'reemplazos':
                if ':' in line:
                    parts = line.split(':', 1)
                    k = parts[0].strip().strip('"').strip("'")
                    v = parts[1].strip().strip('"').strip("'")
                    config['reemplazos'][k] = v
                    
    return config

def main():
    parser = argparse.ArgumentParser(description="QA de Lenguaje YouTube (Ultra Seguro)")
    parser.add_argument("--ep_path", required=True, help="Ruta absoluta al directorio del episodio")
    parser.add_argument("--fase", required=True, choices=["pre-guion", "post-guion"], help="Fase a ejecutar")
    args = parser.parse_args()

    ep_path = Path(args.ep_path)
    if not ep_path.exists():
        print(f"Error: No se encontró la ruta {ep_path}")
        sys.exit(1)

    repo_root = Path(__file__).parent.parent.parent
    config_path = repo_root / "config" / "qa_youtube_lenguaje.yml"
    
    if not config_path.exists():
        print(f"Error: No se encontró la config {config_path}")
        sys.exit(1)

    # 1. Cargar config
    config = parse_simple_yaml(config_path)

    # 2. Archivos a revisar
    if args.fase == "pre-guion":
        files_to_check = ["00_brief_episodio.md", "04_analisis_patrones.md", "05_sintesis_tesis.md"]
    else:
        files_to_check = ["06_guion_longform.md", "09_packaging.md", "10_seo.md"]

    findings = []
    
    # Identificadores de zonas criticas en markdown
    critical_markers = [marker.lower() for marker in config['zonas_criticas']]

    for fname in files_to_check:
        fpath = ep_path / fname
        if not fpath.exists():
            continue
            
        with open(fpath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        is_critical_block_active = False # Para trackear "primeros 30s" o similares si fuera un bloque
        
        for line_num, line in enumerate(lines, 1):
            lower_line = line.lower()
            
            # Chequeo dinámico si estamos en zona crítica
            is_critical = False
            for marker in critical_markers:
                if marker in lower_line: # ej: "título:", "hook"
                    is_critical = True
                    break
                    
            if fname == "00_brief_episodio.md" and line_num < 15:
                # El top del brief tiene todos los campos críticos
                is_critical = True
            elif fname in ["09_packaging.md", "10_seo.md"]:
                # Todo lo que es packaging y SEO suele ser crítico
                is_critical = True
            
            # Busqueda de términos rojos
            for word in config['lista_roja']:
                if re.search(r'\b' + re.escape(word.lower()) + r'\b', lower_line):
                    findings.append({
                        "file": fname,
                        "word": word,
                        "level": "🔴 FAIL (ROJO)",
                        "line_num": line_num,
                        "context": line.strip()[:60] + ("..." if len(line.strip()) > 60 else ""),
                        "replace": "ELIMINAR"
                    })
            
            # Busqueda de términos amarillos
            for word in config['lista_amarilla']:
                if re.search(r'\b' + re.escape(word.lower()) + r'\b', lower_line):
                    level = "🔴 FAIL (AMARILLO CRÍTICO)" if is_critical else "🟡 WARN (AMARILLO)"
                    reemplazo = config['reemplazos'].get(word, "Buscar sinónimo suave")
                    
                    findings.append({
                        "file": fname,
                        "word": word,
                        "level": level,
                        "line_num": line_num,
                        "context": line.strip()[:60] + ("..." if len(line.strip()) > 60 else ""),
                        "replace": reemplazo
                    })

    # 3. Generar reporte
    ep_folder_name = ep_path.name
    output_dir = repo_root / "output" / "qa_youtube_lenguaje"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"{ep_folder_name}__qa_youtube.md"

    fails = [f for f in findings if "FAIL" in f["level"]]
    estado_global = "FAIL" if fails else "PASS"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Reporte QA Lenguaje YouTube (Modo Ultra Seguro)\n")
        f.write(f"**Episodio:** {ep_folder_name}\n")
        f.write(f"**Fase:** {args.fase.upper()}\n")
        f.write(f"**Fecha:** {datetime.now().isoformat()}\n\n")
        f.write(f"## Resultado General: **{estado_global}**\n\n")
        
        if not findings:
            f.write("✅ No se detectaron palabras de riesgo algorítmico.\n")
        else:
            f.write("### Hallazgos del Escáner\n")
            f.write("| Palabra | Archivo | Ubicación (Contexto) | Severidad | Reemplazo Propuesto |\n")
            f.write("|---------|---------|----------------------|-----------|--------------------|\n")
            
            for find in findings:
                # Limpiar la barra vertical para que no rompa la tabla markdown
                ctx = find['context'].replace('|', ' ')
                rep = find['replace'].replace('|', ' ')
                f.write(f"| `{find['word']}` | {find['file']} (L{find['line_num']}) | *\"{ctx}\"* | {find['level']} | {rep} |\n")

    print(f"[qa_lenguaje_{args.fase}] ESTADO_GLOBAL: {estado_global} — output: {report_path}")

    if estado_global == "FAIL":
        sys.exit(1)

if __name__ == '__main__':
    main()
