"""Compare new hybrid runs with an explicitly reused, fully metered baseline."""

import argparse
import hashlib
import json
from pathlib import Path

from report import collect, summarize


def compare(root, baseline_report, baseline_reference):
    """Require identical case/repetition keys and frozen pricing before comparison."""
    current = collect(root)
    baseline = json.loads(baseline_report.read_text())
    manifest = current["manifest"]
    if manifest["arms"] != ["hybrid"] or manifest.get("protocol") != "general":
        raise ValueError("Expected hybrid-only general-protocol results")
    if manifest["rates_per_million"] != baseline["manifest"]["rates_per_million"]:
        raise ValueError("Frozen token prices differ")
    keys = {(r["case"], r["seed"]) for r in current["runs"]}
    old = [r for r in baseline["runs"] if r["arm"] == "baseline" and (r["case"], r["seed"]) in keys]
    if {(r["case"], r["seed"]) for r in old} != keys or len(old) != len(keys):
        raise ValueError("Each new attempt needs exactly one matching historical baseline")
    before = json.loads(baseline_reference.read_text())
    after = json.loads((root / "reference.json").read_text())
    same_reference = before.get("latest_issue") == after.get("latest_issue")
    current["runs"] = old + current["runs"]
    current["baseline_reuse"] = {
        "report": baseline_report.name,
        "report_sha256": hashlib.sha256(baseline_report.read_bytes()).hexdigest(),
        "created_at": baseline["manifest"]["created_at"],
        "runs": len(old), "latest_issue_reference_unchanged": same_reference,
        "case_definitions_and_judges": "Unchanged; current observation parser additionally accepts general-task journals",
        "limitations": ["Historical, not contemporaneous paired baseline", "Public websites and runtime latency can change between runs", "Seeds label repetitions of the same public tasks, not independent websites"],
    }
    current["summary"] = summarize(current)
    if not same_reference:
        current["summary"]["engineering_target_met"] = False
    return current


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("--baseline-report", type=Path, required=True)
    p.add_argument("--baseline-reference", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = compare(args.root, args.baseline_report, args.baseline_reference)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
