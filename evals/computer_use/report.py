"""Audit a frozen paired run and publish sanitized measurements."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics

from run import cost, REPO


def collect(root):
    manifest = json.loads((root / "manifest.json").read_text())
    rows = []
    for seed in manifest["seeds"]:
        for case in manifest["cases"]:
            for arm in manifest["arms"]:
                directory = root / f"{case}-{seed}-{arm}"
                result = json.loads((directory / "result.json").read_text())
                journal = [
                    json.loads(l)
                    for l in (directory / "native.jsonl").read_text().splitlines()
                ]
                violations = []
                jev_calls = []
                for event in journal:
                    if event.get("kind") in ("stage_detail", "task_detail"):
                        jev_calls.extend(event.get("jev_calls", []))
                    if event.get("name") == "js":
                        code = event["arguments"].get("code", "")
                        # Audit model-written code; the candidate is instructed to use UI APIs only.
                        if re.search(
                            r"\b(?:require|import|fetch|eval|evaluate|readFile|execSync|spawn)\b",
                            code,
                        ):
                            violations.append(code)
                        if (
                            re.search(
                                r"cua\.(?:getApp|createBrowserTab|listApps|getState)",
                                code,
                            )
                            and "com.google.Chrome" not in code
                        ):
                            violations.append(code)
                clean = {
                    k: v
                    for k, v in result.items()
                    if k not in ("answer", "model_contexts")
                }
                clean["jev_calls"] = len(jev_calls)
                clean["jev_models"] = sorted(
                    {e["model"] for e in jev_calls if e.get("model")}
                )
                clean["audit_violations"] = violations
                clean["cost_verified"] = (
                    result["llm_usage"] is not None
                    and result["usd"] is not None
                    and not result.get("unmetered_jev_calls", 0)
                    and abs(
                        cost(result["llm_usage"], result["jev_usage"]) - result["usd"]
                    )
                    < 1e-12
                )
                rows.append(clean)
    hashes_match = all(
        hashlib.sha256((REPO / path).read_bytes()).hexdigest() == digest
        for path, digest in manifest["source_sha256"].items()
    )
    return {"manifest": manifest, "source_hashes_match": hashes_match, "runs": rows}


def complete_sum(values):
    values = list(values)
    return sum(values) if all(v is not None for v in values) else None


def summarize(data):
    groups = {}
    for row in data["runs"]:
        groups.setdefault((row["case"], row["arm"]), []).append(row)
    summaries = []
    for case in data["manifest"]["cases"]:
        entry = {"case": case}
        for arm in ("baseline", "hybrid"):
            rows = groups[case, arm]
            entry[arm] = {
                "completed": sum(r["judge"]["success"] for r in rows),
                "runs": len(rows),
                "mean_seconds": statistics.mean(r["seconds"] for r in rows),
                "mean_usd": total / len(rows)
                if (total := complete_sum(r["usd"] for r in rows)) is not None
                else None,
            }
        baseline, hybrid = entry["baseline"]["mean_usd"], entry["hybrid"]["mean_usd"]
        entry["cost_saving"] = (
            1 - hybrid / baseline if baseline and hybrid is not None else None
        )
        summaries.append(entry)
    totals = {}
    for arm in ("baseline", "hybrid"):
        rows = [r for r in data["runs"] if r["arm"] == arm]
        reactions = [v for r in rows for v in r["judge"]["reaction_seconds"]]
        totals[arm] = {
            "completed": sum(r["judge"]["success"] for r in rows),
            "runs": len(rows),
            "seconds": sum(r["seconds"] for r in rows),
            "usd": complete_sum(r["usd"] for r in rows),
            "game_median_reaction_seconds": statistics.median(reactions)
            if reactions
            else None,
        }
    baseline, hybrid = totals["baseline"]["usd"], totals["hybrid"]["usd"]
    saving = 1 - hybrid / baseline if baseline and hybrid is not None else None
    verified = all(
        r["model_verified"]
        and r["cost_verified"]
        and not r.get("infrastructure_errors")
        and not r["audit_violations"]
        and r["max_request_input_tokens"] < 272000
        for r in data["runs"]
    )
    accepted = (
        data["source_hashes_match"]
        and len(data["manifest"].get("seeds", [])) >= 2
        and verified
        and saving is not None
        and saving >= 0.5
        and all(r["judge"]["success"] for r in data["runs"] if r["arm"] == "hybrid")
        and all(
            c["hybrid"]["completed"] >= c["baseline"]["completed"] for c in summaries
        )
    )
    return {
        "cases": summaries,
        "totals": totals,
        "cost_saving": saving,
        "telemetry_verified": verified,
        "engineering_target_met": accepted,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    data = collect(args.root)
    data["summary"] = summarize(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(data["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
