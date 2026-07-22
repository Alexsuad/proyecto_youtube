import argparse, json, sys
from pathlib import Path
from src.core.editorial_profile_registry import EditorialProfileRegistry
def main():
 p=argparse.ArgumentParser(); p.add_argument("--payload", required=True); p.add_argument("--output", required=True); p.add_argument("--registry", required=True); a=p.parse_args()
 try:
  profile=json.loads(Path(a.payload).read_text()); checksum=EditorialProfileRegistry(Path(a.registry)).register(profile); out={"profile":profile,"checksum":checksum}; Path(a.output).write_text(json.dumps(out,sort_keys=True,indent=2)+"\n"); print(checksum); return 0
 except Exception as e: print(e, file=sys.stderr); return 1
if __name__ == "__main__": sys.exit(main())
