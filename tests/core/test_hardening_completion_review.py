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
    mutation = statuses['MUTATION_DECISION_RECORDED']
    assert mutation == 'PASS'
    assert not any('TH05 tests' in value or 'TH06 tests' in value for value in next(item['evidence'] for item in review['dimensions'] if item['name'] == 'DETERMINISTIC_CONTROLS_OPERATIONAL'))
