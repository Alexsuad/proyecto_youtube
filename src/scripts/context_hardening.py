from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from src.core.context_hardening import write_th06_artifacts
if __name__ == "__main__": print("\n".join(map(str,write_th06_artifacts())))
