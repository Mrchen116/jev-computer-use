import unittest
from unittest.mock import patch
from fixtures import World, number_in_answer
from run import cost


class JudgeTests(unittest.TestCase):
    def test_game_claim_cannot_replace_real_actions(self):
        w = World("game", 11)
        self.assertFalse(w.judge("Score 12 / 12", "http://local")["success"])
        w.act({"action": "start"})
        for i, (_, choices) in enumerate(w.deck):
            w.act({"action": "pick", "value": choices[0], "round": i})
        self.assertTrue(w.judge("", "http://local")["success"])

    def test_game_clock_does_not_wait_for_observations_or_accept_late_clicks(self):
        with patch("fixtures.time.monotonic", return_value=100) as clock:
            w = World("game", 7)
            w.act({"action": "start"})
            clock.return_value = 108.1
            w.act({"action": "pick", "value": w.deck[0][1][0], "round": 0})
            self.assertEqual((w.round, w.missed, w.score), (2, 2, 0))
            clock.return_value = 148.1
            w.tick()
            self.assertEqual((w.stage, w.missed), ("finished", 12))
            self.assertFalse(w.judge("I won", "http://local")["success"])

    def test_research_requires_full_coverage_and_exact_shortlist(self):
        w = World("research", 11)
        good = [p for p in w.sources if p["offline"] and p["export"]]
        answer = "\n".join(
            f"{p['name']} {p['price']} {p['note']} http://local/notes/{p['name'].lower()}"
            for p in good
        )
        w.shortlist = {p["name"] for p in good}
        self.assertFalse(w.judge(answer, "http://local")["success"])
        w.visited = {p["name"] for p in w.sources}
        self.assertTrue(w.judge(answer, "http://local")["success"])
        w.shortlist.add("Maple")
        self.assertFalse(w.judge(answer, "http://local")["success"])

    def test_prices_preserve_cached_and_reasoning_semantics(self):
        usage = dict(
            input_tokens=1000,
            cached_input_tokens=400,
            cache_write_input_tokens=100,
            output_tokens=200,
            reasoning_output_tokens=150,
        )
        # Reasoning is already part of output_tokens; do not charge it twice.
        self.assertAlmostEqual(cost(usage, {"input_tokens": 10000}), 0.00708)
        self.assertFalse(
            number_in_answer("price omitted; http://local:35/notes/pine", 35)
        )
        self.assertTrue(number_in_answer("Pine | $35/month | source", 35))


if __name__ == "__main__":
    unittest.main()
