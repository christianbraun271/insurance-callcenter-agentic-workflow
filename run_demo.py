"""Runs each sample call transcript through the graph and prints what the
agents did and how the call was resolved.

Usage:
    python run_demo.py                              # runs every file in sample_calls/
    python run_demo.py call_1_simple_auto_claim.txt  # runs just this one
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

from src.graph import build_graph
from src.llm import get_llm

SAMPLE_DIR = Path(__file__).parent / "sample_calls"


def run_one(app, transcript_path: Path) -> None:
    transcript = transcript_path.read_text()

    print(f"\n{'=' * 72}")
    print(transcript_path.name)
    print("=" * 72)
    print(transcript.strip())

    result = app.invoke(
        {"call_transcript": transcript, "agent_log": [], "risk_flags": []}
    )

    print("\n--- agent trace ---")
    for line in result.get("agent_log", []):
        print(" ", line)

    print(f"\n--- decision: {result['decision']} ---")
    if result.get("resolution_message"):
        print(result["resolution_message"])
    if result.get("escalation_brief"):
        print(result["escalation_brief"])


def main() -> None:
    load_dotenv()
    llm = get_llm()
    app = build_graph(llm)

    if len(sys.argv) > 1:
        paths = [SAMPLE_DIR / name for name in sys.argv[1:]]
    else:
        paths = sorted(SAMPLE_DIR.glob("*.txt"))

    for path in paths:
        run_one(app, path)


if __name__ == "__main__":
    main()
