import json
from pathlib import Path
import tempfile
import threading
import unittest

from jev_computer_use.control import Cycle
from jev_computer_use.stage_state import read_status, request_stop, stage_state
from jev_computer_use.stages import StageEngine


class Native:
    page = "A"
    clicks = 0
    reads = 0

    def js(self, code):
        if "getAXState" in code:
            self.reads += 1
            return "JEV_STATE:" + json.dumps(
                "0 web area Flow, URL: localhost:123/run\n 1 heading "
                + self.page
                + "\n 2 button Next"
            )
        if "jevTarget.click" in code:
            self.clicks += 1
            self.page = "Finished"
        return ""


class Jev:
    def __init__(self, choose=None):
        self.usage = {"input_tokens": 0, "output_tokens": 0}
        self.events = []
        self.choose = choose or (
            lambda payload: (
                "checkpoint"
                if "Finished" in json.loads(payload["state"])["current_page"]
                else "click_2"
            )
        )

    def ask(self, payload):
        choice = self.choose(payload)
        self.usage["input_tokens"] += 10
        self.usage["output_tokens"] += 1
        self.events.append({"model": "test"})
        return {"answers": {"action": {"choice": choice, "confidence": 1}}}, 0.01


class ControlTests(unittest.TestCase):
    def test_changed_page_warns_without_discarding_valid_target(self):
        native = Native()

        def choose(payload):
            native.page = "Clock changed"
            return "click_2"

        result = StageEngine(native, Jev(choose)).run(
            "Demo",
            "http://localhost:123/run",
            "Choose",
            "Finished",
            mode="realtime",
            max_steps=1,
        )
        self.assertEqual(native.clicks, 1)
        self.assertEqual(result["counts"]["skipped_actions"], 0)
        self.assertEqual([w["code"] for w in result["warnings"]], ["ui_changed"])

    def test_slow_decision_is_executed_and_only_warns(self):
        native, jev = Native(), Jev()
        ask = jev.ask

        def slow(payload):
            result, _ = ask(payload)
            return result, 2.4

        jev.ask = slow
        result = StageEngine(native, jev).run(
            "Demo",
            "http://localhost:123/run",
            "Choose",
            "Finished",
            mode="realtime",
            period_ms=1000,
            max_steps=1,
        )
        self.assertEqual(native.clicks, 1)
        self.assertEqual(result["warnings"][0]["code"], "decision_slow")
        self.assertEqual(result["warnings"][0]["latest"]["seconds"], 2.4)

    def test_agent_period_sets_start_spacing_without_catchup_queue(self):
        from unittest.mock import patch

        clock = [0.0]

        def sleep(seconds):
            clock[0] += seconds

        with (
            patch(
                "jev_computer_use.control.time.monotonic", side_effect=lambda: clock[0]
            ),
            patch("jev_computer_use.control.time.sleep", side_effect=sleep),
        ):
            cycle = Cycle(1000, lambda: False, lambda: None)
            self.assertFalse(cycle.wait())
            clock[0] = 0.4
            self.assertTrue(cycle.wait())
            self.assertAlmostEqual(clock[0], 1.0)
            clock[0] = 3.5
            self.assertFalse(cycle.wait())
            self.assertAlmostEqual(cycle.next_start, 4.5)

    def test_optional_target_check_adds_exactly_one_read(self):
        reads = []
        for check in (False, True):
            native = Native()
            result = StageEngine(native, Jev()).run(
                "Demo",
                "http://localhost:123/run",
                "Choose",
                "Finished",
                max_steps=1,
                recheck_target=check,
            )
            self.assertEqual(native.clicks, 1)
            self.assertEqual(result["warnings"], [])
            reads.append(native.reads)
        self.assertEqual(reads, [2, 3])

    def test_repeated_no_change_actions_warn_without_new_stop_policy(self):
        class Unchanging(Native):
            def js(self, code):
                if "jevTarget.click" in code:
                    self.clicks += 1
                    return ""
                return super().js(code)

        native = Unchanging()
        result = StageEngine(native, Jev()).run(
            "Demo",
            "http://localhost:123/run",
            "Choose",
            "Finished",
            max_steps=5,
        )
        self.assertEqual(native.clicks, 5)
        self.assertEqual(result["status"], "step_budget")
        self.assertEqual(len(result["warnings"]), 1)
        self.assertEqual(result["warnings"][0]["code"], "repeated_action")
        self.assertEqual(result["warnings"][0]["count"], 3)

    def test_host_can_change_mode_without_losing_evidence(self):
        engine = StageEngine(Native(), Jev())
        for mode in ("step", "realtime"):
            result = engine.run(
                "Demo", "http://localhost:123/run", "Advance", "Finished", mode=mode
            )
            self.assertEqual(result["status"], "checkpoint")
            self.assertEqual(result["mode"], mode)
            self.assertFalse(result["global_completion"])
        self.assertTrue(any("A" in p["text"] for p in engine.archive.values()))
        self.assertEqual(engine.native.clicks, 1)

    def test_live_progress_and_stop_work_while_model_is_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            entered, release = threading.Event(), threading.Event()
            native = Native()

            def choose(payload):
                entered.set()
                if not release.wait(3):
                    raise AssertionError("Test did not release inference")
                return "click_2"

            engine = StageEngine(native, Jev(choose))
            output, failures = [], []

            def run():
                try:
                    with stage_state(
                        engine, directory, {"mode": "realtime", "goal": "Choose"}
                    ):
                        output.append(
                            engine.run(
                                "Demo",
                                "http://localhost:123/run",
                                "Choose",
                                "Finished",
                                mode="realtime",
                                period_ms=100,
                            )
                        )
                except BaseException as error:
                    failures.append(error)

            thread = threading.Thread(target=run)
            thread.start()
            try:
                self.assertTrue(entered.wait(2))
                progress = read_status(directory)
                self.assertEqual(progress["status"], "running")
                self.assertEqual(progress["phase"], "deciding")
                self.assertEqual(progress["mode"], "realtime")
                self.assertEqual(progress["goal"], "Choose")
                self.assertEqual(
                    native.reads, 1, "No observation while Jev is deciding"
                )
                self.assertNotIn("current_page", progress)
                self.assertNotIn("raw", json.dumps(progress))
                self.assertTrue(request_stop(directory)["stop_requested"])
            finally:
                release.set()
                thread.join(3)
            self.assertFalse(thread.is_alive())
            self.assertFalse(failures, failures)
            self.assertEqual(native.clicks, 0)
            self.assertEqual(output[0]["status"], "stopped")
            self.assertEqual(read_status(directory)["status"], "stopped")
            self.assertEqual(
                (Path(directory) / "progress.json").stat().st_mode & 0o777, 0o600
            )

    def test_failed_provider_response_is_not_zero_cost(self):
        from unittest.mock import patch
        from urllib.error import URLError
        from jev_computer_use.models import JevClient

        client = JevClient("test-only-placeholder")
        with patch(
            "jev_computer_use.models.JevClient._post",
            side_effect=URLError("connection ended"),
        ):
            with self.assertRaises(URLError):
                client.ask({"questions": {}})
        self.assertEqual(client.unmetered_calls, 1)
        self.assertIsNone(client.events[0]["usage"])

    def test_wait_is_a_valid_realtime_action_without_clicking(self):
        engine = StageEngine(Native(), Jev(lambda p: "wait"))
        result = engine.run(
            "Demo",
            "http://localhost:123/run",
            "Observe",
            "Finished",
            mode="realtime",
            max_steps=1,
            period_ms=100,
        )
        self.assertEqual(result["status"], "step_budget")
        self.assertEqual(engine.native.clicks, 0)
        self.assertEqual(result["counts"]["actions"], 0)


if __name__ == "__main__":
    unittest.main()
