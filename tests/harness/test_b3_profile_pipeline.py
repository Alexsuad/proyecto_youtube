import json, os, subprocess, sys
from pathlib import Path
from src.core.version_manifest import compute_checksum
from src.core.contract_validation import validate_against_schema

ROOT=Path(__file__).resolve().parents[2]
ENV={**os.environ,"PYTHONPATH":str(ROOT)}
def run(script,*args): return subprocess.run([sys.executable,str(ROOT/'src/scripts'/script),*map(str,args)],cwd=ROOT,env=ENV,text=True,capture_output=True)
def payload(): return json.loads((ROOT/'profiles/editorial/mas_alla_del_guion/1.0.0/profile_payload.json').read_text())
def approval(profile, checksum): return {'profile_id':profile['profile_id'],'profile_version':profile['version'],'profile_checksum':checksum,'decision':'APPROVE','functional_owner_role':'TEAM_01','approved_by':'team_01_owner','approved_at':'2026-07-22T20:00:00Z'}
def gate(profile, checksum): return {'gate_id':'B3_TECHNICAL_PROFILE_VALIDATION','artifact_id':profile['profile_id'],'artifact_version':profile['version'],'status':'PASS','summary':'synthetic','violations':[],'warnings':[],'evidence':{'profile_checksum':checksum},'checked_at':'2026-07-22T20:00:00Z','checker_version':'1.0.0','exit_code':0}
def test_cli_pipeline_and_rejections(tmp_path):
 source=tmp_path/'payload.json'; source.write_text(json.dumps(payload())); registry=tmp_path/'registry.json'; one=tmp_path/'one.json'; two=tmp_path/'two.json'
 assert run('compile_editorial_profile.py','--payload',source,'--output',one,'--registry',registry).returncode==0
 assert run('compile_editorial_profile.py','--payload',source,'--output',two,'--registry',registry).returncode==0
 assert json.loads(one.read_text())['checksum']==json.loads(two.read_text())['checksum']
 assert run('validate_editorial_profile.py','--profile',one).returncode==0
 bad=tmp_path/'bad.json'; bad.write_text('{}'); assert run('validate_editorial_profile.py','--profile',bad).returncode!=0
 profile=json.loads(one.read_text())['profile']; checksum=compute_checksum(profile); ap=tmp_path/'approval.json'; te=tmp_path/'gate.json'; ap.write_text(json.dumps(approval(profile,checksum)));te.write_text(json.dumps(gate(profile,checksum))); active=tmp_path/'active.json'
 assert run('activate_editorial_profile.py','--profile',one,'--approval',ap,'--technical',te,'--output',active,'--actor','synthetic').returncode==0
 assert validate_against_schema(json.loads(active.read_text()),'active_editorial_profile')==[]
 configured=json.loads((ROOT/'config/active_editorial_profile.json').read_text());assert configured['ACTIVE_PROFILE_ID']=='mas_alla_del_guion';assert configured['ACTIVE_PROFILE_VERSION']=='1.1.0';assert configured['profile_checksum']=='ff45c54267dd2c5f36896c802846322e57476820ed1fd9e81a5f9556b528c2cd'
 missing=tmp_path/'missing.json'; assert run('activate_editorial_profile.py','--profile',one,'--approval',missing,'--technical',te,'--output',tmp_path/'no.json','--actor','synthetic').returncode!=0
 wrong=gate(profile,'b'*64);te.write_text(json.dumps(wrong));assert run('activate_editorial_profile.py','--profile',one,'--approval',ap,'--technical',te,'--output',tmp_path/'wrong.json','--actor','synthetic').returncode!=0
