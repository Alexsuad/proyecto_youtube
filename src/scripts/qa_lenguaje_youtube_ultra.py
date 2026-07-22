"""Variante Ultra del gate de lenguaje, con el mismo contrato canónico."""
import sys
from qa_lenguaje_youtube import main

if __name__ == "__main__":
    phase = sys.argv[sys.argv.index("--fase") + 1] if "--fase" in sys.argv else "pre-guion"
    gate_id = "qa_lenguaje_youtube_ultra_pre_guion" if phase == "pre-guion" else "qa_lenguaje_youtube_ultra_post_guion"
    sys.argv.extend(["--gate-id", gate_id])
    sys.exit(main())
