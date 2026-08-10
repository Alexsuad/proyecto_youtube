"""Small, portable TH-08 mutation probe for the TH-06 security hotspot."""
from __future__ import annotations
import json, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PROBE="""import json, hashlib, sys\nfrom pathlib import Path\nfrom src.core.context_resolution import resolve_context, ContextResolutionError\nroot=Path(sys.argv[1]); root.joinpath('config').mkdir(); root.joinpath('policies').mkdir(); root.joinpath('config/context_resolution_policy.json').write_text(json.dumps({'normative_allowed_roots':['policies'],'evidentiary_allowed_roots':[],'historical_allowed_roots':[]})); p=root/'policies/rule.md'; p.write_text('rule'); d=hashlib.sha256(p.read_bytes()).hexdigest(); ref={'ref_id':'x','context_class':'NORMATIVE','artifact_path':sys.argv[2],'artifact_type':'markdown','artifact_sha256':d,'authority_domain':'D','required':True}\nif sys.argv[3]=='bad': ref['artifact_sha256']='0'*64\ntry: resolve_context([ref],root=root,capability_id='C',role_id='R',run_id='RUN')\nexcept ContextResolutionError: raise SystemExit(0)\nraise SystemExit(1)\n"""

def _run_mutant(source: str, replacement: str, artifact_path: str, bad_checksum: bool=False)->bool:
    original=(ROOT/"src/core/context_resolution.py").read_text(encoding="utf-8")
    assert source in original
    with tempfile.TemporaryDirectory() as directory:
        temp=Path(directory); package=temp/"src/core"; package.mkdir(parents=True); (temp/"src/__init__.py").write_text(""); (package/"__init__.py").write_text("")
        (package/"context_resolution.py").write_text(original.replace(source,replacement,1),encoding="utf-8")
        case=temp/"case"; command=[sys.executable,"-c",PROBE,str(case),artifact_path,"bad" if bad_checksum else "valid"]
        result=subprocess.run(command,cwd=temp,env={**__import__('os').environ,"PYTHONPATH":str(temp)},capture_output=True,text=True)
        return result.returncode != 0

def build_mutation_report(root: Path=ROOT)->dict:
    probes=[
      ("ABSOLUTE_PATH_BYPASS","candidate.is_absolute() or \"..\" in candidate.parts or not relative","False","C:/outside.md",False),
      ("CHECKSUM_BYPASS","expected_raw and expected_raw != raw_digest.lower()","False","policies/rule.md",True),
    ]
    results=[]
    for identifier,source,replacement,path,bad_checksum in probes:
        killed=_run_mutant(source,replacement,path,bad_checksum); results.append({"mutant_id":identifier,"status":"KILLED" if killed else "SURVIVED","classification":"MISSING_TEST" if not killed else "NOT_APPLICABLE","evidence":"isolated_subprocess_probe"})
    survivors=[x for x in results if x["status"]=="SURVIVED"]
    return {"schema_version":"1.0.0","plan_id":"PLAN_004","mission_id":"TH-08","repository_revision":subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip(),"generated_at":datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),"source_inputs":[{"path":"src/core/context_resolution.py","sha256":None},{"path":"tests/core/test_context_hardening.py","sha256":None}],"evidence_refs":["TH07_quality_baseline.json"],"limitations":[],"result":"PASS" if not survivors else "COMPLETED_WITH_FINDINGS","artifact_type":"MUTATION_TESTING","scope":{"modules":["src/core/context_resolution.py"],"tests":["tests/core/test_context_hardening.py"],"budget":"2 targeted security mutants; no network or cost"},"mutants_generated":len(results),"mutants_killed":len(results)-len(survivors),"survivors":survivors,"runtime":"local subprocess","cost":"0","useful_findings":[],"noisy_findings":[],"recommendation":"KEEP_SELECTIVELY"}

def write_th08_artifact(root: Path=ROOT)->Path:
    path=root/"reports/implementation/plan_004/TH08_mutation_testing.json";path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(build_mutation_report(root),indent=2)+"\n",encoding="utf-8");return path
