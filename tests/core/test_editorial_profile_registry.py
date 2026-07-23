import json
from pathlib import Path
import pytest
from src.core.editorial_profile_registry import EditorialProfileRegistry
ROOT=Path(__file__).resolve().parents[2]
def payload(): return json.loads((ROOT/'profiles/editorial/mas_alla_del_guion/1.0.0/profile_payload.json').read_text())
def test_registration_is_deterministic_and_rejects_overwrite(tmp_path):
 r=EditorialProfileRegistry(tmp_path/'registry.json'); p=payload(); c=r.register(p); assert c==r.register(p)
 p['identity_stable']['identity']='other'
 with pytest.raises(ValueError): r.register(p)
def test_activation_requires_matching_evidence():
 p=payload(); c=__import__('src.core.version_manifest',fromlist=['compute_checksum']).compute_checksum(p)
 a={'decision':'APPROVE','profile_id':p['profile_id'],'profile_version':p['version'],'profile_checksum':c,'functional_owner_role':'TEAM_01','voice_evidence_level':'SPECIFICATION_BASED','evidence_summary':'Aprobación final de fixture sintético.','limitations':['Fixture de validación.'],'approved_by':'equipo_01_responsable','approved_at':'2026-07-22T20:00:00Z'}
 t={'gate_id':'B3_TECHNICAL_PROFILE_VALIDATION','artifact_id':p['profile_id'],'artifact_version':p['version'],'status':'PASS','summary':'ok','violations':[],'warnings':[],'evidence':{'profile_checksum':c},'checked_at':'2026-07-22T20:00:00Z','checker_version':'1.0.0','exit_code':0}
 assert EditorialProfileRegistry.verify_activation(p,a,t)==c
 t['profile_checksum']='b'*64
 with pytest.raises(ValueError): EditorialProfileRegistry.verify_activation(p,a,t)
