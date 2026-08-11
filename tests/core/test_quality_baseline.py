from pathlib import Path
from src.core.quality_baseline import build_quality_baseline
ROOT=Path(__file__).resolve().parents[2]
def test_baseline_is_informational_and_has_all_required_dimensions():
    report=build_quality_baseline(ROOT)
    assert report["recommendation"] in {"KEEP_INFORMATIONAL","ADD_SELECTIVE_THRESHOLDS","ADD_RISK_BASED_GATES"}
    assert report["thresholds"] == "NONE"
    assert {item["dimension"] for item in report["dimensions"]} == {"test_coverage","complexity","duplication","dead_unreachable_code","static_analysis","critical_path_test_distribution"}
    assert {item["status"] for item in report["dimensions"]} <= {"MEASURED","NOT_APPLICABLE","LIMITATION"}


def test_utf8_bom_python_is_not_reported_as_syntax_error(tmp_path):
    source = tmp_path / "src" / "bom.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(bytes([0xEF, 0xBB, 0xBF, 118, 97, 108, 117, 101, 32, 61, 32, 49, 10]))
    report = build_quality_baseline(tmp_path)
    syntax = next(item for item in report["dimensions"] if item["dimension"] == "static_analysis")
    assert syntax["value"]["syntax_errors"] == []
