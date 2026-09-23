"""Compare a new native run with a frozen MiniWoB hybrid report."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import tarfile

from report import collect, summarize
from run import REPO

SHARED_SOURCES = (
    "evals/computer_use/run.py",
    "evals/computer_use/miniwob_cases.py",
    "skills/jev-computer-use/scripts/jev_computer_use/desktop.py",
    "skills/jev-computer-use/scripts/jev_computer_use/runtime.py",
    "skills/jev-computer-use/scripts/jev_computer_use/mcp.py",
)


def native_mcp_fingerprint(source):
    """Ignore only the helper and branch that cannot run without hybrid mode."""
    delegated_test = ast.dump(ast.parse('params["name"] == "delegate_task" and task_jev and not args.legacy_stages', mode="eval").body)
    class NativePath(ast.NodeTransformer):
        removed = 0

        def visit_FunctionDef(self, node):
            return None if node.name == "handoff_result" else self.generic_visit(node)

        def visit_If(self, node):
            if ast.dump(node.test) == delegated_test:
                node.body = [ast.Pass()]
                self.removed += 1
            return self.generic_visit(node)
    transform = NativePath()
    tree = transform.visit(ast.parse(source))
    if transform.removed != 1:
        raise ValueError("Cannot isolate the hybrid-only MCP delegation branch")
    return hashlib.sha256(ast.dump(tree).encode()).hexdigest()


def fingerprint_from_archive(archive):
    path = "skills/jev-computer-use/scripts/jev_computer_use/mcp.py"
    if archive:
        with tarfile.open(archive) as bundle:
            return native_mcp_fingerprint(bundle.extractfile(path).read())
    return native_mcp_fingerprint((REPO / path).read_bytes())


def verified_sources(manifest, archive=None):
    """Verify a frozen archive after treatment changes, or the live source tree."""
    if archive:
        with tarfile.open(archive) as bundle:
            return all(hashlib.sha256(bundle.extractfile(path).read()).hexdigest() == digest
                       for path, digest in manifest["source_sha256"].items())
    return all(hashlib.sha256((REPO / path).read_bytes()).hexdigest() == digest
               for path, digest in manifest["source_sha256"].items())


def comparison(native, hybrid, allow_version_drift=False):
    """Require the same tasks, generated instructions, environment and rates."""
    before, after = native["manifest"], hybrid["manifest"]
    if before["arms"] != ["baseline"] or after["arms"] != ["hybrid"]:
        raise ValueError("Expected native-only and hybrid-only inputs")
    version_drift = before["codex_version"] != after["codex_version"]
    if version_drift and not allow_version_drift:
        raise ValueError("Comparison metadata differs: codex_version")
    for field in ("suite", "protocol", "miniwob", "rates_per_million"):
        if before[field] != after[field]:
            raise ValueError("Comparison metadata differs: " + field)
    if before["suite"] != "miniwob" or before["protocol"] != "general":
        raise ValueError("Expected the general MiniWoB protocol")
    for path in SHARED_SOURCES:
        if before["source_sha256"][path] == after["source_sha256"][path]:
            continue
        same_native_path = (path.endswith("/mcp.py") and native.get("native_mcp_fingerprint")
                            and native["native_mcp_fingerprint"] == hybrid.get("native_mcp_fingerprint"))
        if not same_native_path:
            raise ValueError("The shared benchmark/native execution sources differ: " + path)

    def keyed(rows):
        result = {(r["case"], r["seed"]): r for r in rows}
        if len(result) != len(rows):
            raise ValueError("Duplicate case/seed pair")
        return result

    native_rows, hybrid_rows = keyed(native["runs"]), keyed(hybrid["runs"])
    expected = {(case, seed) for case in before["cases"] for seed in before["seeds"]}
    if native_rows.keys() != expected or hybrid_rows.keys() != expected:
        raise ValueError("Missing or extra case/seed pairs")
    for key in expected:
        if native_rows[key]["judge"]["query"] != hybrid_rows[key]["judge"]["query"]:
            raise ValueError("Generated task instruction differs: " + str(key))

    result = {
        "manifest": {**before, "arms": ["baseline", "hybrid"]},
        "arm_manifests": {"baseline": before, "hybrid": after},
        "source_changes": {path: {"baseline": before["source_sha256"].get(path),
                                  "hybrid": after["source_sha256"].get(path)}
                           for path in sorted(before["source_sha256"].keys() | after["source_sha256"].keys())
                           if before["source_sha256"].get(path) != after["source_sha256"].get(path)},
        "source_hashes_match": native["source_hashes_match"] and hybrid["source_hashes_match"],
        "runtime_version_matched": not version_drift,
        "native_mcp_fingerprints": {"baseline": native.get("native_mcp_fingerprint"), "hybrid": hybrid.get("native_mcp_fingerprint")},
        "runs": native["runs"] + hybrid["runs"],
        "limitations": [
            "Arms ran in separate batches, not interleaved; each arm manifest records its start timestamp.",
            "Three task types and three seeds are a small sample; reused development seeds are not independent held-out trials.",
            "Both arms use a relaxed 300-second deadline, not standard MiniWoB leaderboard timing.",
            "Normal native parsing and deterministic UI batching remain available; no per-click LLM requirement.",
            "Elapsed time includes Codex startup and final response; runtime and provider latency may vary.",
        ],
    }
    result["summary"] = summary = summarize(result)
    if version_drift:
        result["limitations"].append("Codex CLI changed from " + before["codex_version"] + " to " + after["codex_version"] + "; historical totals are descriptive, not a controlled estimate of this code change.")
    for entry in summary["cases"]:
        entry["time_saving"] = 1 - entry["hybrid"]["mean_seconds"] / entry["baseline"]["mean_seconds"]
    summary["time_saving"] = 1 - summary["totals"]["hybrid"]["seconds"] / summary["totals"]["baseline"]["seconds"]
    for arm, total in summary["totals"].items():
        rows = [r for r in result["runs"] if r["arm"] == arm]
        total["llm_requests"] = sum(r["llm_requests"] for r in rows)
        total["native_calls"] = sum(r["native_calls"] for r in rows)
        total["jev_calls"] = sum(r["jev_calls"] for r in rows)
        for field in ("llm_usage", "jev_usage"):
            values = [r.get(field) for r in rows]
            total[field] = ({key: sum(v.get(key, 0) for v in values)
                             for key in set().union(*values)}
                            if all(v is not None for v in values) else None)
    no_vision = not any(r.get("vision_used") for r in result["runs"])
    summary["telemetry_verified"] = summary["telemetry_verified"] and no_vision
    summary["engineering_target_met"] = summary["engineering_target_met"] and no_vision and not version_drift
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("native_root", type=Path)
    parser.add_argument("--hybrid-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--native-source-archive", type=Path)
    parser.add_argument("--hybrid-source-archive", type=Path)
    parser.add_argument("--allow-version-drift", action="store_true", help="Report historical differences with an explicit runtime mismatch; never mark the engineering target met")
    args = parser.parse_args()
    native = collect(args.native_root)
    native["native_mcp_fingerprint"] = fingerprint_from_archive(args.native_source_archive)
    native["source_hashes_match"] = verified_sources(native["manifest"], args.native_source_archive)
    for row in native["runs"]:
        path = args.native_root / f"{row['case']}-{row['seed']}-baseline/native.jsonl"
        entries = [json.loads(line) for line in path.read_text().splitlines()]
        row["vision_used"] = any(
            re.search(r"getScreenshot|getAXStateAndScreenshot|emitImage", e["arguments"]["code"])
            for e in entries if e.get("name") == "js"
        )
    hybrid = json.loads(args.hybrid_report.read_text())
    hybrid["source_hashes_match"] = verified_sources(hybrid["manifest"], args.hybrid_source_archive)
    hybrid["native_mcp_fingerprint"] = fingerprint_from_archive(args.hybrid_source_archive)
    result = comparison(native, hybrid, args.allow_version_drift)
    result["source_verification"] = {
        "baseline": "frozen archive" if args.native_source_archive else "working tree",
        "hybrid": "frozen archive" if args.hybrid_source_archive else "working tree",
    }
    result["hybrid_report"] = {
        "name": args.hybrid_report.name,
        "sha256": hashlib.sha256(args.hybrid_report.read_bytes()).hexdigest(),
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
