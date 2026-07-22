import argparse,json,sys
from pathlib import Path
from src.core.contract_validation import validate_against_schema
def main():
 p=argparse.ArgumentParser();p.add_argument("--profile",required=True);a=p.parse_args()
 try: profile=json.loads(Path(a.profile).read_text()).get("profile", json.loads(Path(a.profile).read_text())); errors=validate_against_schema(profile,"editorial_profile"); print("PASS" if not errors else "FAIL"); return 0 if not errors else 1
 except Exception as e: print(e,file=sys.stderr);return 1
if __name__=="__main__":sys.exit(main())
