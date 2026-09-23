"""Publish hybrid-only MiniWoB results, including who actually operated the UI."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re

from report import collect, complete_sum
from run import RATES, cost

UI_MUTATION = re.compile(r"\.(?:click|setValue|paste|typeText|pressKey|scroll|selectText|performSecondaryAction)\(")


def build_report(root):
    data = collect(root)
    for row in data["runs"]:
        directory = root / f"{row['case']}-{row['seed']}-{row['arm']}"
        path = directory / "task-state/progress.json"
        progress = json.loads(path.read_text()) if path.exists() else {"history": []}
        executed = [e for e in progress["history"] if e.get("actor") == "jev" and e["result"].get("status") == "executed"]
        row["jev_action_types"] = dict(Counter(e["action"]["type"] for e in executed))
        row["jev_executed_operations"] = len(executed)
        journal = [json.loads(line) for line in (directory / "native.jsonl").read_text().splitlines()]
        host_code = [e["arguments"]["code"] for e in journal if e.get("name") == "js"]
        row["outer_ui_action_calls"] = sum(bool(UI_MUTATION.search(code)) for code in host_code)
        row["vision_used"] = any(re.search(r"getScreenshot|getAXStateAndScreenshot|emitImage", code) for code in host_code)
        row["completion_without_outer_ui_actions"] = row["judge"]["success"] and row["outer_ui_action_calls"] == 0
        row["sol_usd"] = cost(row["llm_usage"], {}) if row["llm_usage"] else None
        row["jev_usd"] = row["jev_usage"]["input_tokens"] * RATES["jev_input"] / 1_000_000 if not row["unmetered_jev_calls"] else None
    groups = {case: [r for r in data["runs"] if r["case"] == case] for case in data["manifest"]["cases"]}

    def aggregate(rows):
        return {
            "runs": len(rows), "completed": sum(r["judge"]["success"] for r in rows),
            "seconds": sum(r["seconds"] for r in rows),
            "usd": complete_sum(r["usd"] for r in rows),
            "sol_usd": complete_sum(r["sol_usd"] for r in rows),
            "jev_usd": complete_sum(r["jev_usd"] for r in rows),
            "jev_executed_operations": sum(r["jev_executed_operations"] for r in rows),
            "outer_ui_action_calls": sum(r["outer_ui_action_calls"] for r in rows),
            "completion_without_outer_ui_actions": sum(r["completion_without_outer_ui_actions"] for r in rows),
        }

    data["summary"] = {
        "all": aggregate(data["runs"]),
        "by_case": {case: aggregate(rows) for case, rows in groups.items()},
        "development_seeds": aggregate([r for r in data["runs"] if r["seed"] in (11, 22)]),
        "additional_seeds": aggregate([r for r in data["runs"] if r["seed"] not in (11, 22)]),
        "telemetry_verified": all(r["model_verified"] and r["cost_verified"] and not r["audit_violations"]
                                  and not r["infrastructure_errors"] and not r["vision_used"]
                                  and r["max_request_input_tokens"] < 272000 for r in data["runs"]),
        "cost_saving": None,
    }
    data["interpretation"] = (
        "Hybrid-only, relaxed 300-second MiniWoB subset, official first raw reward must equal 1. "
        "No baseline comparison or standard leaderboard claim. Completion without outer UI actions "
        "still includes Sol planning, prepared inputs, guidance and final verification. Jev operations "
        "count runner actions; outer UI action calls may contain multiple actions, so their ratio is not an action-share percentage."
    )
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = build_report(args.root)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(data["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
