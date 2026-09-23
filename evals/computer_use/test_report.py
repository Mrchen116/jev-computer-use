import unittest

from report import summarize


class ReportTests(unittest.TestCase):
    def test_missing_billing_never_becomes_free_or_a_savings_claim(self):
        base = {
            "case": "portfolio",
            "seconds": 20,
            "judge": {"success": True, "reaction_seconds": []},
            "model_verified": True,
            "audit_violations": [],
            "max_request_input_tokens": 1000,
        }
        result = summarize(
            {
                "manifest": {"cases": ["portfolio"]},
                "source_hashes_match": True,
                "runs": [
                    {**base, "arm": "baseline", "usd": 0.1, "cost_verified": True},
                    {**base, "arm": "hybrid", "usd": None, "cost_verified": False},
                ],
            }
        )
        self.assertIsNone(result["totals"]["hybrid"]["usd"])
        self.assertIsNone(result["cost_saving"])
        self.assertFalse(result["engineering_target_met"])


if __name__ == "__main__":
    unittest.main()
