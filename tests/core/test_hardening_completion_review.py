import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def test_completion_review_does_not_convert_pending_external_review_to_pass():
    review=json.loads((ROOT/'reports/implementation/plan_004/HARDENING_COMPLETION_REVIEW.json').read_text())
    statuses={item['name']:item['status'] for item in review['dimensions']}
    assert review['result']=='HARDENING_COMPLETED_PENDING_OWNER_REVIEW'
    assert statuses['INDEPENDENT_REVIEW_VERIFIABLE']=='LIMITATION'
    assert review['owner_decision_required'] is True
    assert review['r1_m4_opened'] is False
