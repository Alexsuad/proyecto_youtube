from pathlib import Path
from src.core.quality_baseline import build_quality_baseline
ROOT=Path(__file__).resolve().parents[2]
def test_baseline_is_informational_and_has_all_required_dimensions():
    report=build_quality_baseline(ROOT)
    assert report["recommendation"] in {"KEEP_INFORMATIONAL","ADD_SELECTIVE_THRESHOLDS","ADD_RISK_BASED_GATES"}
    assert report["thresholds"] == "NONE"
    assert {item["dimension"] for item in report["dimensions"]} == {"test_coverage","complexity","duplication","dead_unreachable_code","static_analysis","critical_path_test_distribution"}
    assert {item["status"] for item in report["dimensions"]} <= {"MEASURED","NOT_APPLICABLE","LIMITATION"}
