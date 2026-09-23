import tempfile
from pathlib import Path
import unittest

from miniwob_cases import MiniWoBWorld, instrumentation


class MiniWoBJudgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.world = MiniWoBWorld("click-checkboxes-large", 11, Path(self.temp.name), "http://localhost/test")
        self.world.record({"kind": "start", "query": "Select five boxes"})

    def terminal(self, reward):
        self.world.record({"kind": "terminal", "raw_reward": reward, "reward": reward * .5,
                           "elapsed_ms": 1000, "actions": [{"type": "click"}]})

    def test_positive_partial_reward_and_model_claim_are_not_success(self):
        self.assertFalse(self.world.judge("Success!", "")["success"])
        self.terminal(.8)
        self.assertFalse(self.world.judge("Success!", "")["success"])

    def test_raw_reward_is_independent_of_time_discount(self):
        self.terminal(1)
        result = self.world.judge("", "")
        self.assertTrue(result["success"])
        self.assertEqual(result["time_scaled_reward"], .5)
        self.assertEqual(result["observed_ui_events"]["click"], 1)

    def test_retry_cannot_replace_failed_first_episode(self):
        self.terminal(-1)
        self.world.record({"kind": "start", "query": "Another episode"})
        self.terminal(1)
        result = self.world.judge("Success!", "")
        self.assertFalse(result["success"])
        self.assertEqual(result["raw_reward"], -1)
        self.assertEqual(result["episodes_started"], 2)

    def test_seed_and_deadline_are_explicit_without_replacing_generator(self):
        script = instrumentation(11, 300000)
        self.assertIn('"seed": "11"', script)
        self.assertIn('"deadline_ms": 300000', script)
        self.assertIn("end.apply(this, args)", script)
        self.assertNotIn("genProblem =", script)

    def test_reset_clicks_native_start_and_verifies_split_visible_instruction(self):
        self.world.events = [{"kind": "start", "query": "Select five boxes"}]
        class Native:
            def execute(inner, action):
                self.assertEqual(action, {"verb": "click", "ref": "7"})
                return {"raw": "0 standard window Task\n 1 text Select\n 2 container\n  3 text five\n 4 text boxes"}
        self.world.prepare(Native(), {"raw": "0 standard window Task\n 7 text START"})
        self.assertIn("Instruction observed on the current page: Select five boxes", self.world.task)


if __name__ == "__main__":
    unittest.main()
