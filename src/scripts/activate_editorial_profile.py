import argparse,json,sys
from datetime import datetime, timezone
from pathlib import Path
from src.core.editorial_profile_registry import EditorialProfileRegistry
def main():
 p=argparse.ArgumentParser();p.add_argument("--profile",required=True);p.add_argument("--approval",required=True);p.add_argument("--technical",required=True);p.add_argument("--output",required=True);p.add_argument("--actor",required=True);a=p.parse_args()
 try:
  profile=json.loads(Path(a.profile).read_text()).get("profile",json.loads(Path(a.profile).read_text())); approval=json.loads(Path(a.approval).read_text()); technical=json.loads(Path(a.technical).read_text()); c=EditorialProfileRegistry.verify_activation(profile,approval,technical); active={"ACTIVE_PROFILE_ID":profile["profile_id"],"ACTIVE_PROFILE_VERSION":profile["version"],"profile_checksum":c,"functional_approval":{"decision":"APPROVE","profile_checksum":c},"technical_validation":{"gate_id":"B3_TECHNICAL_PROFILE_VALIDATION","status":"PASS","profile_checksum":c},"activation":{"activated_by":a.actor,"activated_at":datetime.now(timezone.utc).isoformat()},"status":"ACTIVE"}; Path(a.output).write_text(json.dumps(active,indent=2));return 0
 except Exception as e:print(e,file=sys.stderr);return 1
if __name__=="__main__":sys.exit(main())
