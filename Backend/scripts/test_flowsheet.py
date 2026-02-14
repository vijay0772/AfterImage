#!/usr/bin/env python3
"""Run flowsheet queries against an artifact. Usage: python scripts/test_flowsheet.py <doc_id>"""

import json
import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.storage import load_artifact
from app.flowsheet import (
    build_flowsheet_sections_from_lines,
    is_flowsheet_question,
    get_flowsheet_answer,
)

# Expected test queries (from user spec)
TEST_QUERIES = [
    # Page 6
    ("blood pressure at 20:15 on 04/03/24", "Blood 126/61"),
    ("pulse at 20:30 on 04/03/24", "Pulse: 84"),
    ("respiratory rate at 20:45 on 04/03/24", "Respiratory rate: 34"),
    ("MAP at 20:30", "Mean arterial pressure: 89"),
    ("level of consciousness at 21:00", "Awake/ Alert"),
    # Page 7
    ("blood pressure at 21:30", "127/65"),
    ("SpO2 at 22:00", "98"),
    ("MAP at 21:45", "91"),
    ("pulse at 21:00", "80"),
    ("blood pressure at 21:22", "132/66"),  # continued block
]


def main():
    if len(sys.argv) < 2:
        artifacts_dir = os.path.join(os.path.dirname(__file__), "..", "app", "data", "artifacts")
        files = [f for f in os.listdir(artifacts_dir) if f.endswith(".json")]
        doc_ids = [f.replace(".json", "") for f in files]
        print(f"Usage: python {sys.argv[0]} <doc_id>")
        print(f"Available doc_ids: {doc_ids[:5]}...")
        sys.exit(1)
    doc_id = sys.argv[1]
    art = load_artifact(doc_id)
    lines = art.get("lines", [])
    flowsheet_sections = art.get("flowsheet_sections")
    if not flowsheet_sections and lines:
        flowsheet_sections = build_flowsheet_sections_from_lines(lines)
        print(f"[build] flowsheet_sections: {len(flowsheet_sections)} sections")
    if not flowsheet_sections:
        print("No flowsheet sections found. Document may not have flowsheet pages.")
        sys.exit(0)
    # Log section keys
    keys = [(s.get("activity_date"), s.get("time"), len(s.get("lines", []))) for s in flowsheet_sections[:20]]
    print(f"[sections] sample keys: {keys}")
    print()
    passed = 0
    for q, expected_substr in TEST_QUERIES:
        if not is_flowsheet_question(q):
            print(f"SKIP (not flowsheet): {q}")
            continue
        answer, ev = get_flowsheet_answer(q, flowsheet_sections)
        anorm = (answer or "").lower().replace(" ", "").replace("i·ate", "rate").replace("1•", "r").replace("·", "")
        expnorm = expected_substr.lower().replace(" ", "")
        ok = answer and (expnorm in anorm or expected_substr.lower() in (answer or "").lower())
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        print(f"{status} | {q}")
        print(f"     -> answer: {answer!r}")
        if ev:
            print(f"     -> evidence: {ev[0].get('text', '')[:60]!r}...")
        if not ok and expected_substr:
            print(f"     -> expected to contain: {expected_substr!r}")
        print()
    print(f"Passed: {passed}/{len(TEST_QUERIES)}")


if __name__ == "__main__":
    main()
