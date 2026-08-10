from pathlib import Path
from src.core.mutation_baseline import build_mutation_report
ROOT=Path(__file__).resolve().parents[2]
def test_context_security_mutants_are_killed_in_isolation():
    report=build_mutation_report(ROOT)
    assert report["mutants_generated"]==2
    assert report["mutants_killed"]==2
    assert report["survivors"]==[]
    assert report["recommendation"]=="KEEP_SELECTIVELY"
