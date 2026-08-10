from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.cross_registry_integrity import write_th05_artifacts

if __name__ == "__main__":
    print("\n".join(str(path) for path in write_th05_artifacts()))
