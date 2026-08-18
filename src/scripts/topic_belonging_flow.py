"""Handoff and gate validator; it never executes producer or reviewer models."""

from __future__ import annotations
import argparse, json
from pathlib import Path
from src.scripts.channel_intelligence import evaluate_topic_belonging_gate

def load(path: str) -> dict: return json.loads(Path(path).read_text(encoding="utf-8"))
def bind_episode_brief_to_topic_decision(brief: dict, decision: dict) -> dict:
    """Attach immutable topic-approval lineage before B5 consumes the brief."""
    bound = dict(brief)
    bound["topic_belonging_decision_ref"] = str(decision.get("decision_id") or "")
    bound["topic_belonging_decision_checksum"] = str(decision.get("provenance", {}).get("output_checksum") or "")
    return bound

def main() -> int:
    parser=argparse.ArgumentParser(description="Validates the isolated producer-to-reviewer Topic Belonging flow.")
    parser.add_argument("--input", required=True); parser.add_argument("--assessment", required=True); parser.add_argument("--decision", required=True); parser.add_argument("--owner-decision")
    parser.add_argument("--work-lifecycle"); parser.add_argument("--research-dossier")
    args=parser.parse_args()
    result=evaluate_topic_belonging_gate(
        load(args.decision), load(args.assessment), load(args.input),
        load(args.owner_decision) if args.owner_decision else None,
        load(args.work_lifecycle) if args.work_lifecycle else None,
        load(args.research_dossier) if args.research_dossier else None,
    )
    print(json.dumps(result, ensure_ascii=False)); return 0 if result["status"] == "PASS" else 2
if __name__ == "__main__": raise SystemExit(main())
