"""Deterministic, informational TH-07 quality baseline."""
from __future__ import annotations
import ast, hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
from src.core.evidence_freshness import sha256_path

ROOT=Path(__file__).resolve().parents[2]

def _sha(path: Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def _py(root: Path): return sorted((root/"src").rglob("*.py"))
def _branches(node: ast.AST)->int:return sum(isinstance(x,(ast.If,ast.For,ast.While,ast.Try,ast.BoolOp,ast.Match)) for x in ast.walk(node))

def build_quality_baseline(root: Path=ROOT)->dict:
    files=_py(root); complexities=[]; duplicates={}; unreachable=[]; syntax=[]
    for path in files:
        relative=path.relative_to(root).as_posix()
        try: tree=ast.parse(path.read_text(encoding="utf-8-sig"))
        except SyntaxError as exc: syntax.append({"path":relative,"error":str(exc)}); continue
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                score=1+_branches(node); complexities.append({"path":relative,"function":node.name,"cyclomatic_proxy":score})
                key=ast.dump(node,annotate_fields=False,include_attributes=False); duplicates.setdefault(hashlib.sha256(key.encode()).hexdigest(),[]).append(f"{relative}:{node.name}")
                for index, statement in enumerate(node.body[:-1]):
                    if isinstance(statement,(ast.Return,ast.Raise)):
                        unreachable.append({"path":relative,"function":node.name,"line":node.body[index+1].lineno})
    test_files=sorted(path.relative_to(root).as_posix() for path in (root/"tests").rglob("test_*.py"))
    try: revision=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    except subprocess.CalledProcessError: revision="UNRESOLVED"
    dimensions=[
      {"dimension":"test_coverage","status":"LIMITATION","reason":"coverage tool is not a declared portable dependency","evidence":[]},
      {"dimension":"complexity","status":"MEASURED","tool":"python_ast","version":"stdlib","scope":"src/**/*.py","value":{"functions":len(complexities),"hotspots":sorted(complexities,key=lambda x:x['cyclomatic_proxy'],reverse=True)[:10]}},
      {"dimension":"duplication","status":"MEASURED","tool":"python_ast","version":"stdlib","scope":"function AST identity","value":{"duplicate_groups":[v for v in duplicates.values() if len(v)>1]}},
      {"dimension":"dead_unreachable_code","status":"MEASURED","tool":"python_ast","version":"stdlib","scope":"statements after return or raise","value":{"findings":unreachable}},
      {"dimension":"static_analysis","status":"MEASURED","tool":"ast.parse","version":"stdlib","scope":"src/**/*.py","value":{"syntax_errors":syntax}},
      {"dimension":"critical_path_test_distribution","status":"MEASURED","tool":"filesystem_inventory","version":"stdlib","scope":"tests/test_*.py","value":{"test_files":len(test_files),"context_tests":[x for x in test_files if 'context' in x],"governance_tests":[x for x in test_files if 'governance' in x or 'repair' in x]}},
    ]
    source_inputs = [{"path": name, "sha256": sha256_path(root / name)} for name in ("src", "tests") if (root / name).exists()]
    return {"schema_version":"1.0.0","plan_id":"PLAN_004","mission_id":"TH-07","repository_revision":revision,"generated_at":datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),"source_inputs":source_inputs,"evidence_refs":[item["path"] for item in source_inputs],"limitations":["COVERAGE_TOOL_NOT_DECLARED_PORTABLE"],"result":"PASS","artifact_type":"QUALITY_BASELINE","dimensions":dimensions,"risk_hotspots":[x for x in sorted(complexities,key=lambda x:x['cyclomatic_proxy'],reverse=True)[:10]],"recommendation":"KEEP_INFORMATIONAL","thresholds":"NONE"}

def write_th07_artifact(root: Path=ROOT)->Path:
    path=root/"reports/implementation/plan_004/TH07_quality_baseline.json"; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(build_quality_baseline(root),indent=2)+"\n",encoding="utf-8"); return path
