import copy
import unittest

from compare_miniwob import comparison, SHARED_SOURCES, native_mcp_fingerprint


def sample(arm):
    return {
        "manifest": {
            "arms": [arm], "suite": "miniwob", "protocol": "general",
            "codex_version": "test", "miniwob": {"deadline_ms": 300000},
            "rates_per_million": {"input": 4}, "source_sha256": dict.fromkeys(SHARED_SOURCES, "abc"),
            "cases": ["form"], "seeds": [11, 22],
        },
        "source_hashes_match": True,
        "runs": [{
            "case": "form", "seed": seed, "arm": arm,
            "seconds": seconds, "usd": .2 if arm == "baseline" else .08,
            "judge": {"success": True, "query": f"Fill {seed}", "reaction_seconds": []},
            "model_verified": True, "cost_verified": True, "audit_violations": [],
            "max_request_input_tokens": 1000, "llm_requests": 2,
            "native_calls": 8, "jev_calls": 0 if arm == "baseline" else 4,
        } for seed, seconds in zip([11, 22], [10, 30] if arm == "baseline" else [12, 18])],
    }


class MiniWoBComparisonTests(unittest.TestCase):
    def test_comparison_uses_total_time_and_cost_and_retains_failed_attempts(self):
        native, hybrid = sample("baseline"), sample("hybrid")
        hybrid["runs"][0]["judge"]["success"] = False
        result = comparison(native, hybrid)["summary"]
        self.assertAlmostEqual(result["cost_saving"], .6)
        self.assertAlmostEqual(result["time_saving"], .25)
        self.assertEqual(result["totals"]["hybrid"]["runs"], 2)
        self.assertEqual(result["totals"]["hybrid"]["completed"], 1)
        self.assertFalse(result["engineering_target_met"])

    def test_incomparable_tasks_or_metadata_are_rejected(self):
        for change in ("query", "missing", "duplicate", "rates", "source"):
            with self.subTest(change=change):
                native, hybrid = sample("baseline"), sample("hybrid")
                if change == "query": hybrid["runs"][0]["judge"]["query"] = "Different task"
                if change == "missing": hybrid["runs"].pop()
                if change == "duplicate": hybrid["runs"].append(copy.deepcopy(hybrid["runs"][0]))
                if change == "rates": hybrid["manifest"]["rates_per_million"]["input"] = 1
                if change == "source": hybrid["manifest"]["source_sha256"][SHARED_SOURCES[0]] = "different"
                with self.assertRaises(ValueError): comparison(native, hybrid)

    def test_treatment_only_change_is_recorded_without_requiring_a_new_native_run(self):
        native, hybrid = sample("baseline"), sample("hybrid")
        hybrid["manifest"]["source_sha256"]["skills/jev-computer-use/SKILL.md"] = "new"
        result = comparison(native, hybrid)
        self.assertEqual(result["source_changes"]["skills/jev-computer-use/SKILL.md"],
                         {"baseline": None, "hybrid": "new"})

    def test_version_drift_is_explicit_and_cannot_pass_acceptance(self):
        native, hybrid = sample("baseline"), sample("hybrid")
        hybrid["manifest"]["codex_version"] = "new-version"
        with self.assertRaisesRegex(ValueError, "codex_version"):
            comparison(native, hybrid)
        result = comparison(native, hybrid, allow_version_drift=True)
        self.assertFalse(result["runtime_version_matched"])
        self.assertFalse(result["summary"]["engineering_target_met"])
        self.assertAlmostEqual(result["summary"]["cost_saving"], .6)
        self.assertIn("descriptive", result["limitations"][-1])

    def test_native_fingerprint_ignores_only_unreachable_hybrid_code(self):
        source = """
def handoff_result():
    return 'old docs'
def main():
    if params["name"] == "delegate_task" and task_jev and not args.legacy_stages:
        result = 'old handoff'
    else:
        result = native.request(method, params)
"""
        base = native_mcp_fingerprint(source)
        self.assertEqual(base, native_mcp_fingerprint(source.replace('old docs', 'new docs').replace('old handoff', 'new handoff')))
        self.assertNotEqual(base, native_mcp_fingerprint(source.replace('native.request(method, params)', 'native.request(method, changed_params)')))
        native, hybrid = sample("baseline"), sample("hybrid")
        hybrid["manifest"]["source_sha256"]["skills/jev-computer-use/scripts/jev_computer_use/mcp.py"] = "changed"
        with self.assertRaises(ValueError): comparison(native, hybrid)
        native["native_mcp_fingerprint"] = hybrid["native_mcp_fingerprint"] = base
        self.assertTrue(comparison(native, hybrid)["source_hashes_match"])

    def test_missing_billing_remains_unknown(self):
        native, hybrid = sample("baseline"), sample("hybrid")
        hybrid["runs"][0].update(usd=None, cost_verified=False)
        result = comparison(native, hybrid)["summary"]
        self.assertIsNone(result["cost_saving"])
        self.assertIsNone(result["totals"]["hybrid"]["usd"])
        self.assertFalse(result["telemetry_verified"])

    def test_vision_use_blocks_the_accessibility_only_acceptance(self):
        native, hybrid = sample("baseline"), sample("hybrid")
        native["runs"][0]["vision_used"] = True
        result = comparison(native, hybrid)["summary"]
        self.assertFalse(result["telemetry_verified"])
        self.assertFalse(result["engineering_target_met"])


if __name__ == "__main__":
    unittest.main()
