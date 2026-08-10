from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.core.mutation_baseline import write_th08_artifact
if __name__=="__main__":print(write_th08_artifact())
