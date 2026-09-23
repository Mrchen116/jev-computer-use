import unittest
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch
from jev_computer_use.stages import scoped_observation, StageEngine, ScopeBoundary


class StageScopeTests(unittest.TestCase):
    def test_multiple_authorized_sites_keep_host_scheme_and_path_boundaries(self):
        from jev_computer_use.stages import in_scope

        scopes = [
            "https://docs.example.test/manual",
            "http://catalog.example.test/items",
        ]
        state = scoped_observation(
            "0 web area Catalog, URL: catalog.example.test/items/one", scopes
        )
        self.assertEqual(state["url"], "http://catalog.example.test/items/one")
        self.assertTrue(in_scope("https://docs.example.test/manual/start", scopes))
        for url in [
            "https://docs.example.test/manual-evil",
            "https://catalog.example.test/items",
            "https://other.test/manual",
        ]:
            self.assertFalse(in_scope(url, scopes))

    def test_eval_grants_must_cover_every_requested_scope(self):
        from jev_computer_use.mcp import validate_eval_scope

        granted = [
            "https://docs.example.test/manual",
            "http://catalog.example.test/items",
        ]
        request = {
            "app": "com.google.Chrome",
            "allowed_url_prefix": [granted[0] + "/start", granted[1]],
        }
        validate_eval_scope(request, granted)
        for scopes in [
            granted + ["https://other.test/"],
            ["https://docs.example.test/"],
            [],
        ]:
            with self.assertRaises(ValueError):
                validate_eval_scope({**request, "allowed_url_prefix": scopes}, granted)

    def test_repeated_parameters_and_container_dates_keep_their_local_context(self):
        raw = """0 web area Docs, URL: example.test/docs
 1 heading First method
 2 text encoding=None
 3 heading Second method
 4 text encoding=None
 5 container Sep 14, 2026, 07:53 GMT+8
"""
        state = scoped_observation(raw, "https://example.test/docs")
        self.assertEqual(state["page"].count("encoding=None"), 2)
        self.assertIn("Second method\ntext: encoding=None", state["page"])
        self.assertIn("Sep 14, 2026, 07:53 GMT+8", state["page"])

    def test_elided_web_url_uses_unfocused_browser_address_without_chrome_controls(
        self,
    ):
        raw = """0 标准窗口 Project, URL: …
 1 文本栏 (settable) 地址和搜索栏, Value: example.test/project, Placeholder: 搜索
 2 HTML 内容 Project, URL: …
  3 标题 Project
  4 按钮 Issues
The focused UI element is 2 HTML 内容 Project, URL: …
"""
        state = scoped_observation(raw, "https://example.test/project")
        self.assertEqual(state["url"], "https://example.test/project")
        self.assertIn("URL: example.test/project", state["page"])
        self.assertNotIn("fill_1", state["actions"])
        self.assertNotIn("地址和搜索栏", state["page"])

    def test_focused_address_is_not_evidence_of_loaded_page(self):
        raw = """0 standard window Project, URL: …
 1 text field (settable) Address and search bar, Value: example.test/project
 2 web area Project, URL: …
  3 button Continue
The focused UI element is 1 text field Address and search bar
"""
        with self.assertRaises(ScopeBoundary):
            scoped_observation(raw, "https://example.test/project")

    def test_page_cannot_supply_its_own_address_bar_fallback(self):
        raw = """0 web area Unknown, URL: …
 1 text field Address and search bar, Value: example.test/project
 2 button Continue
"""
        with self.assertRaises(ScopeBoundary):
            scoped_observation(raw, "https://example.test/project")

    def test_multiline_receipt_is_preserved_in_scoped_evidence(self):
        raw = '0 web area Saved, URL: localhost:123/run\n 1 text {\n  "Digest": "Weekly",\n  "Language": null\n}\n 2 button Edit\n'
        state = scoped_observation(raw, "http://localhost:123/run")
        self.assertIn('"Language": null', state["page"])
        self.assertIn('"Digest": "Weekly"', state["page"])

    def test_only_current_web_area_can_be_acted_on(self):
        raw = """0 window Test, URL: localhost:123/run
 1 text field Address, Value: localhost:123/run
 2 web area Test, URL: localhost:123/run/page
  3 heading Read me
  4 button Next
  5 text field Name, Value: Alex
 6 button Close window
"""
        state = scoped_observation(raw, "http://localhost:123/run")
        self.assertEqual(
            set(state["actions"]), {"scroll_down_2", "scroll_up_2", "click_4", "fill_5"}
        )
        self.assertEqual(state["fields"][0]["value"], "Alex")
        self.assertNotIn("Close window", state["page"])

    def test_neighbor_route_and_external_origin_are_rejected(self):
        for url in ("localhost:123/run-evil", "example.test/run"):
            with self.assertRaisesRegex(RuntimeError, "outside"):
                scoped_observation(
                    "0 web area Wrong, URL: " + url, "http://localhost:123/run"
                )

    def test_cross_origin_handoff_contains_actual_page_but_no_actions(self):
        with self.assertRaises(ScopeBoundary) as raised:
            scoped_observation(
                "0 web area Repository, URL: github.com/example/project\n 1 button Star",
                "https://example.test/",
            )
        state = raised.exception.observation
        self.assertEqual(state["url"], "https://github.com/example/project")
        self.assertIn("Repository", state["page"])
        self.assertEqual(state["actions"], {})
        self.assertEqual(state["fields"], [])

    def test_https_and_query_are_preserved_within_scope(self):
        state = scoped_observation(
            "0 web area Page, URL: example.test/docs?q=one", "https://example.test/docs"
        )
        self.assertEqual(state["url"], "https://example.test/docs?q=one")

    def test_original_evidence_survives_navigation_without_reopening_ui(self):
        native = Mock()
        pages = [
            "0 web area List, URL: localhost:123/run/list\n 1 heading Items\n 2 text Created 2026-09-14",
            "0 web area Detail, URL: localhost:123/run/detail\n 1 heading Selected item",
        ]
        native.js.side_effect = ["JEV_STATE:" + json.dumps(p) for p in pages]
        engine = StageEngine(native, SimpleNamespace())
        first = engine.observe("http://localhost:123/run")
        engine.observe("http://localhost:123/run")
        evidence = engine.read_evidence([first["source_id"]])
        self.assertIn("Created 2026-09-14", evidence[0]["text"])
        self.assertEqual(native.js.call_count, 2)


class StageExecutionTests(unittest.TestCase):
    def cross_site_engine(self):
        engine = self.engine()
        state = {"url": "https://docs.example.test/start"}

        def native(code):
            if "getAXState" in code:
                second = "catalog" in state["url"]
                raw = f"0 web area Source, URL: {state['url']}\n 1 text {'Beta' if second else 'Alpha'} source fact\n 2 button {'Finish' if second else 'Follow linked source'}"
                return "JEV_STATE:" + json.dumps(raw)
            if "click(2)" in code:
                state["url"] = "https://catalog.example.test/items"
            return ""

        engine.native.js = native
        engine.open_url = Mock(side_effect=lambda url: state.update(url=url))
        return engine, state

    def test_collects_multiple_sites_in_one_stage_using_supplied_destination(self):
        engine, state = self.cross_site_engine()

        def ask(payload):
            packet = json.loads(payload["state"])
            text = "\n".join(packet["page_passages"].values())
            passage = next(iter(packet["page_passages"]))
            answers = {"action": {"choice": "destination_0", "confidence": 1}}
            for key, q in payload["questions"].items():
                if key.startswith("evidence_"):
                    matches = any(
                        name in text and name in q["instructions"]
                        for name in ["Alpha", "Beta"]
                    )
                    answers[key] = {
                        "choice": passage if matches else "none",
                        "confidence": 1,
                    }
            return {"answers": answers}, 0.01

        engine.jev.ask = ask
        result = engine.run(
            "Demo",
            ["https://docs.example.test/", "https://catalog.example.test/"],
            destinations=["https://catalog.example.test/items"],
            collect={"first": "Alpha source fact", "second": "Beta source fact"},
        )
        self.assertEqual(result["status"], "collection_ready")
        self.assertEqual(result["counts"]["actions"], 1)
        self.assertEqual(len({item["url"] for item in result["collected"].values()}), 2)
        engine.open_url.assert_called_once_with("https://catalog.example.test/items")

    def test_observed_link_can_cross_authorized_sites_without_scope_handoff(self):
        engine, state = self.cross_site_engine()
        engine.jev.ask = lambda payload: (
            {
                "answers": {
                    "action": {
                        "choice": "checkpoint"
                        if "catalog" in state["url"]
                        else "click_2",
                        "confidence": 1,
                    }
                }
            },
            0.01,
        )
        result = engine.run(
            "Demo", ["https://docs.example.test/", "https://catalog.example.test/"]
        )
        self.assertEqual(result["status"], "checkpoint")
        self.assertEqual(result["current_url"], "https://catalog.example.test/items")

    def test_external_destination_is_rejected_before_any_ui_access(self):
        engine = StageEngine(Mock(), Mock())
        with self.assertRaisesRegex(ValueError, "destination"):
            engine.run(
                "Demo",
                ["https://example.test/"],
                destinations=["https://outside.test/"],
            )
        engine.native.js.assert_not_called()

    def test_uncertain_destination_navigation_is_not_replayed(self):
        engine, state = self.cross_site_engine()
        engine.open_url.side_effect = RuntimeError("Navigation response lost")
        engine.jev.ask = lambda payload: (
            {"answers": {"action": {"choice": "destination_0", "confidence": 1}}},
            0.01,
        )
        result = engine.run(
            "Demo",
            ["https://docs.example.test/", "https://catalog.example.test/"],
            destinations=["https://catalog.example.test/items"],
        )
        self.assertEqual(result["status"], "execution_error")
        self.assertEqual(engine.open_url.call_count, 1)

    def option_engine(self, *, reject=False, fail_submit=False):
        import re

        engine = self.engine()
        state = {"value": "old", "submissions": [], "writes": []}

        def native(code):
            match = re.search(r"setValue\(1, (.+)\);", code)
            if match:
                value = json.loads(match[1])
                state["writes"].append(value)
                if not reject:
                    state["value"] = value
            if 'pressKey("Return")' in code:
                state["submissions"].append(state["value"])
                if fail_submit:
                    raise RuntimeError("Submission response lost")
            if "getAXState" in code:
                return "JEV_STATE:" + json.dumps(
                    f"0 web area Search, URL: localhost:123/run\n 1 text field Query, Value: {state['value']}\n 2 text Results: {state['submissions']}"
                )
            return ""

        engine.native.js = native
        choices = iter(["input_0", "input_1", "checkpoint"])
        engine.jev.ask = lambda payload: (
            {"answers": {"action": {"choice": next(choices), "confidence": 1}}},
            0.01,
        )
        return engine, state

    def test_host_input_alternatives_run_sequentially_with_fresh_results(self):
        engine, state = self.option_engine()
        result = engine.run(
            "Demo",
            "http://localhost:123/run",
            input_options=[
                {"field": "Query", "value": v, "submit": True}
                for v in ["first query", "second query"]
            ],
        )
        self.assertEqual(result["status"], "checkpoint")
        self.assertEqual(state["submissions"], ["first query", "second query"])
        self.assertEqual(result["counts"]["actions"], 4)
        self.assertIn("second query", result["current_page"])

    def test_input_option_needs_verified_value_and_explicit_submit(self):
        for reject in (False, True):
            engine, state = self.option_engine(reject=reject)
            result = engine.run(
                "Demo",
                "http://localhost:123/run",
                max_steps=1,
                input_options=[
                    {"field": "Query", "value": "first query", "submit": reject}
                ],
            )
            self.assertEqual(state["submissions"], [])
            if reject:
                self.assertEqual(result["status"], "input_not_verified")

    def test_input_option_stop_and_uncertain_submission_never_replay(self):
        for fail in (False, True):
            engine, state = self.option_engine(fail_submit=fail)
            if not fail:
                engine.should_stop = lambda: bool(state["writes"])
            result = engine.run(
                "Demo",
                "http://localhost:123/run",
                input_options=[
                    {"field": "Query", "value": "first query", "submit": True}
                ],
            )
            self.assertEqual(result["status"], "execution_error" if fail else "stopped")
            self.assertEqual(len(state["submissions"]), 1 if fail else 0)
            self.assertEqual(state["writes"], ["first query"])

    def test_options_do_not_target_missing_or_ambiguous_fields(self):
        from jev_computer_use.stages import input_actions

        field = {"name": "Query", "ref": "1"}
        for fields in ([], [field, {**field, "ref": "2"}]):
            self.assertEqual(
                input_actions({"fields": fields}, [{"field": "Query", "value": "x"}]),
                {},
            )

    def test_tried_option_is_removed_but_other_choices_remain_available(self):
        engine, state = self.option_engine()
        seen = []

        def ask(payload):
            choices = payload["questions"]["action"]["criteria"]
            seen.append(set(k for k in choices if k.startswith("input_")))
            choice = next((k for k in choices if k.startswith("input_")), "need_help")
            return {"answers": {"action": {"choice": choice, "confidence": 1}}}, 0.01

        engine.jev.ask = ask
        result = engine.run(
            "Demo",
            "http://localhost:123/run",
            input_options=[
                {"field": "Query", "value": v, "submit": True}
                for v in ["first", "second"]
            ],
        )
        self.assertEqual(seen, [{"input_0", "input_1"}, {"input_1"}, set()])
        self.assertEqual(state["submissions"], ["first", "second"])
        self.assertEqual(result["status"], "need_help")

    def test_address_verification_allows_display_spaces_but_not_history_completion(
        self,
    ):
        from jev_computer_use.stages import address_identity

        self.assertEqual(
            address_identity("https://example.test/search?q=one%20two"),
            address_identity("example.test/search?q=one two"),
        )
        self.assertNotEqual(
            address_identity("https://example.test/docs"),
            address_identity("https://example.test/docs?q=old"),
        )

    def test_unconfirmed_navigation_does_not_repeat_submission(self):
        engine = self.engine()
        engine.native = Mock()
        before = "0 window Browser\n 9 text field Address and search bar, Value: old.test\n 20 web area Old, URL: old.test"
        filled = before.replace("Value: old.test", "Value: https://example.test/docs")
        engine.native.js.side_effect = [
            "JEV_STATE:" + json.dumps(before),
            "",
            "JEV_STATE:" + json.dumps(filled),
            "",
            "JEV_STATE:" + json.dumps(filled),
        ]
        with patch("jev_computer_use.stages.time.monotonic", side_effect=[0, 9]):
            with self.assertRaisesRegex(RuntimeError, "Navigation has not"):
                engine.open_url("https://example.test/docs")
        code = "\n".join(c.args[0] for c in engine.native.js.call_args_list)
        self.assertEqual(code.count('pressKey("Return")'), 1)
        self.assertEqual(code.count("paste("), 1)

    def input_engine(self, *, fail_submit=False, reject_fill=False):
        engine = self.engine()
        state = {"value": "old", "submitted": 0, "codes": []}

        def native(code):
            state["codes"].append(code)
            if "setValue" in code and not reject_fill:
                state["value"] = "exact terms"
            if 'pressKey("Return")' in code:
                state["submitted"] += 1
                if fail_submit:
                    raise RuntimeError("Submission response lost")
            if "getAXState" in code:
                raw = f"0 web area Search, URL: localhost:123/run\n 1 text field Query, Value: {state['value']}\n 2 text Results version {state['submitted']}"
                return "JEV_STATE:" + json.dumps(raw)
            return ""

        engine.native.js = native

        def ask(payload):
            # Collection must receive the post-submission observation.
            page = json.loads(payload["state"])
            choice = next(iter(page.get("page_passages", {})), "none")
            answers = {"action": {"choice": "wait", "confidence": 1}}
            answers.update(
                {
                    k: {"choice": choice, "confidence": 1}
                    for k in payload["questions"]
                    if k.startswith("evidence_")
                }
            )
            return {"answers": answers}, 0.01

        engine.jev.ask = ask
        return engine, state

    def test_prepared_search_submits_once_before_collecting_results(self):
        engine, state = self.input_engine()
        result = engine.run(
            "Demo",
            "http://localhost:123/run",
            prepared_text={"Query": "exact terms"},
            submit_field="Query",
            collect={"result": "Results version"},
        )
        self.assertEqual(result["status"], "collection_ready")
        self.assertEqual(state["submitted"], 1)
        self.assertIn("Results version 1", result["collected"]["result"]["text"])
        self.assertEqual(result["counts"]["actions"], 2)

    def test_submission_is_opt_in_and_requires_verified_prepared_value(self):
        for reject_fill in (False, True):
            engine, state = self.input_engine(reject_fill=reject_fill)
            result = engine.run(
                "Demo",
                "http://localhost:123/run",
                prepared_text={"Query": "exact terms"},
                submit_field="Query" if reject_fill else None,
                max_steps=1,
            )
            self.assertEqual(state["submitted"], 0)
            if reject_fill:
                self.assertEqual(result["status"], "input_not_verified")

    def test_already_filled_search_submits_only_once_across_cycles(self):
        engine, state = self.input_engine()
        state["value"] = "exact terms"
        result = engine.run(
            "Demo",
            "http://localhost:123/run",
            prepared_text={"Query": "exact terms"},
            submit_field="Query",
            max_steps=3,
        )
        self.assertEqual(state["submitted"], 1)
        self.assertEqual(result["counts"]["actions"], 1)

    def test_missing_submit_field_cannot_collect_the_old_results(self):
        engine, state = self.input_engine()
        result = engine.run(
            "Demo",
            "http://localhost:123/run",
            prepared_text={"Not visible": "exact terms"},
            submit_field="Not visible",
            collect={"result": "Results version"},
            max_steps=2,
        )
        self.assertEqual(state["submitted"], 0)
        self.assertEqual(result["collected"], {})
        self.assertIn("result", result["remaining"])

    def test_stop_after_fill_prevents_submission_and_uncertain_submit_is_not_replayed(
        self,
    ):
        engine, state = self.input_engine()
        engine.should_stop = lambda: state["value"] == "exact terms"
        result = engine.run(
            "Demo",
            "http://localhost:123/run",
            prepared_text={"Query": "exact terms"},
            submit_field="Query",
        )
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(state["submitted"], 0)
        engine, state = self.input_engine(fail_submit=True)
        result = engine.run(
            "Demo",
            "http://localhost:123/run",
            prepared_text={"Query": "exact terms"},
            submit_field="Query",
        )
        self.assertEqual(result["status"], "execution_error")
        self.assertEqual(state["submitted"], 1)

    def test_open_url_uses_observed_browser_address_and_rejects_external_scope(self):
        engine = self.engine()
        engine.native = Mock()
        with self.assertRaisesRegex(ValueError, "inside"):
            engine.run(
                "Chrome", "https://example.test/", open_url="https://other.test/"
            )
        engine.native.js.assert_not_called()
        before = "0 window Browser\n 9 text field Address and search bar, Value: old.test\n 20 web area Old, URL: old.test\n  21 text field Address and search bar"
        filled = before.replace("Value: old.test", "Value: https://example.test/docs")
        pending = filled.replace("URL: old.test", "URL: …")
        loaded = filled.replace("Old, URL: old.test", "New, URL: example.test/docs")
        engine.native.js.side_effect = [
            "JEV_STATE:" + json.dumps(before),
            "",
            "JEV_STATE:" + json.dumps(filled),
            "",
            "JEV_STATE:" + json.dumps(pending),
            "JEV_STATE:" + json.dumps(loaded),
        ]
        engine.open_url("https://example.test/docs")
        code = "\n".join(call.args[0] for call in engine.native.js.call_args_list)
        self.assertIn("click(9)", code)
        self.assertIn('paste("https://example.test/docs")', code)
        self.assertEqual(code.count('pressKey("Return")'), 1)
        self.assertNotIn("21", code)
        # The new address alone cannot release navigation on the old web area.
        self.assertEqual(engine.native.js.call_count, 6)

    def test_unverified_address_is_not_submitted(self):
        engine = self.engine()
        engine.native = Mock()
        state = "JEV_STATE:" + json.dumps(
            "0 window Browser\n 9 text field Address and search bar, Value: old.test\n 20 web area Old, URL: old.test"
        )
        engine.native.js.side_effect = [state, "", state]
        with self.assertRaisesRegex(RuntimeError, "not verified"):
            engine.open_url("https://example.test/docs")
        self.assertFalse(
            any(
                'pressKey("Return")' in c.args[0]
                for c in engine.native.js.call_args_list
            )
        )

    def test_missing_passage_can_be_read_without_revisiting_or_scrolling_ui(self):
        engine = self.engine()
        raw = (
            "0 web area Manual, URL: localhost:123/run\n 1 text "
            + ("decoy query tokens\n" * 2400)
            + "THE REQUESTED ORIGINAL FACT"
        )

        def native(code):
            self.assertNotIn("click(", code)
            self.assertNotIn("scroll(", code)
            return "JEV_STATE:" + json.dumps(raw) if "getAXState" in code else ""

        engine.native.js = native
        viewed = []

        def ask(payload):
            state = json.loads(payload["state"])
            viewed.append(state["text_view"]["current"])
            match = next(
                (
                    key
                    for key, text in state["page_passages"].items()
                    if "THE REQUESTED ORIGINAL FACT" in text
                ),
                "none",
            )
            return {
                "answers": {
                    "action": {
                        "choice": "more_text" if match == "none" else "checkpoint",
                        "confidence": 1,
                    },
                    "evidence_0": {"choice": match, "confidence": 1},
                }
            }, 0.01

        engine.jev.ask = ask
        result = engine.run(
            "Demo",
            "http://localhost:123/run",
            collect={"fact": "decoy query tokens"},
            max_steps=20,
        )
        self.assertEqual(result["status"], "collection_ready")
        self.assertEqual(result["counts"]["actions"], 0)
        self.assertGreater(max(viewed), 1)
        self.assertIn(
            "THE REQUESTED ORIGINAL FACT", result["collected"]["fact"]["text"]
        )

    def test_collection_keeps_evidence_across_pages_and_stops_before_revisiting(self):
        engine = self.engine()
        original = engine.jev.ask

        def ask(payload):
            state = json.loads(payload["state"])
            state.setdefault(
                "current_page", "\n".join(state.get("page_passages", {}).values())
            )
            result, elapsed = original(payload)
            for key, question in payload["questions"].items():
                if not key.startswith("evidence_"):
                    continue
                wanted = "Step 0" if key == "evidence_0" else "Step 2"
                selected = next(
                    (k for k, text in state["page_passages"].items() if wanted in text),
                    "none",
                )
                result["answers"][key] = {"choice": selected, "confidence": 1}
            if "Step 1" in state["current_page"]:
                self.assertIn("first", state["collection"]["collected"])
                self.assertEqual(set(state["collection"]["remaining"]), {"last"})
                self.assertNotIn("evidence_0", payload["questions"])
            return result, elapsed

        engine.jev.ask = ask
        result = engine.run(
            "Demo",
            "http://localhost:123/run",
            "Collect",
            "Both sources",
            collect={"first": "Step 0", "last": "Step 2"},
        )
        self.assertEqual(result["status"], "collection_ready")
        self.assertEqual(engine.native.clicks, 2)
        self.assertFalse(result["global_completion"])
        for selected in result["collected"].values():
            original_text = engine.archive[selected["source_id"]]["text"]
            self.assertEqual(
                selected["text"], original_text[selected["start"] : selected["end"]]
            )
            self.assertFalse(selected["verified_by_host"])

    def test_controls_beyond_first_batch_remain_reachable(self):
        engine = self.engine()
        raw = "0 web area Many, URL: localhost:123/run\n" + "\n".join(
            f" {i} button Choice {i}" for i in range(1, 161)
        )
        calls = []

        def native(code):
            calls.append(code)
            return "JEV_STATE:" + json.dumps(raw) if "getAXState" in code else ""

        engine.native.js = native
        original = engine.jev.ask

        def ask(payload):
            result, elapsed = original(payload)
            result["answers"]["action"]["choice"] = (
                "click_160"
                if "click_160" in payload["questions"]["action"]["criteria"]
                else "more_controls"
            )
            return result, elapsed

        engine.jev.ask = ask
        result = engine.run(
            "Demo", "http://localhost:123/run", "Last choice", "Selected", max_steps=2
        )
        self.assertEqual(result["counts"]["actions"], 1)
        self.assertIn("await jevTarget.click(160);", calls)

    def test_enter_submits_focused_page_input_but_not_browser_chrome(self):
        engine = self.engine()
        codes = []

        def native(code):
            codes.append(code)
            raw = "0 window Browser\n 1 text field Address, Value: localhost:123/run\n 2 web area Search, URL: localhost:123/run\n  3 text field Query, Value: exact terms\nThe focused UI element is 3 text field Query"
            return "JEV_STATE:" + json.dumps(raw) if "getAXState" in code else ""

        engine.native.js = native
        original = engine.jev.ask

        def ask(payload):
            result, elapsed = original(payload)
            self.assertIn("enter", payload["questions"]["action"]["criteria"])
            result["answers"]["action"]["choice"] = "enter"
            return result, elapsed

        engine.jev.ask = ask
        result = engine.run(
            "Demo", "http://localhost:123/run", "Search", "Results", max_steps=1
        )
        self.assertEqual(result["counts"]["actions"], 1)
        self.assertIn('await jevTarget.pressKey("Return");', codes)
        state = scoped_observation(
            "0 window Browser\n 1 text field Address\n 2 web area Search, URL: localhost:123/run\n  3 button Search\nThe focused UI element is 1 text field Address",
            "http://localhost:123/run",
        )
        self.assertNotIn("enter", state["actions"])

    def test_navigation_loading_retries_observation_not_action(self):
        native = Mock()
        native.js.side_effect = [
            'JEV_STATE:"0 window Loading"',
            'JEV_STATE:"0 web area Loaded, URL: localhost:123/run"',
        ]
        engine = StageEngine(native, SimpleNamespace())
        state = engine.observe("http://localhost:123/run")
        self.assertIn("Loaded", state["page"])
        self.assertTrue(
            all("getAXState" in call.args[0] for call in native.js.call_args_list)
        )

    def engine(self, fail=False):
        class Native:
            page = 0
            clicks = 0

            def js(self, code):
                if "getAXState" in code:
                    raw = f"0 web area Flow, URL: localhost:123/run/{self.page}\n 1 heading Step {self.page}\n 2 button Next"
                    return "JEV_STATE:" + json.dumps(raw)
                if "jevTarget.click" in code:
                    self.clicks += 1
                    if fail:
                        raise RuntimeError("Uncertain mutation")
                    self.page += 1
                return ""

        class Jev:
            def __init__(self):
                self.usage = {"input_tokens": 0, "output_tokens": 0}
                self.events = []

            def ask(self, payload):
                state = json.loads(payload["state"])
                choice = (
                    "checkpoint"
                    if "Step 3"
                    in state.get(
                        "current_page",
                        "\n".join(state.get("page_passages", {}).values()),
                    )
                    else "click_2"
                )
                self.usage["input_tokens"] += 10
                self.usage["output_tokens"] += 2
                self.events.append(
                    {"model": "fake", "usage": {"input_tokens": 10, "output_tokens": 2}}
                )
                return {
                    "answers": {"action": {"choice": choice, "confidence": 1}}
                }, 0.01

        return StageEngine(Native(), Jev())

    def test_same_button_on_new_pages_is_progress_and_checkpoint_is_not_global_done(
        self,
    ):
        engine = self.engine()
        result = engine.run(
            "Demo", "http://localhost:123/run", "Advance three pages", "Step 3"
        )
        self.assertEqual(result["status"], "checkpoint")
        self.assertFalse(result["global_completion"])
        self.assertEqual(engine.native.clicks, 3)
        self.assertEqual(result["jev_usage"], {"input_tokens": 40, "output_tokens": 8})

    def test_uncertain_mutation_is_not_retried(self):
        engine = self.engine(fail=True)
        result = engine.run(
            "Demo", "http://localhost:123/run", "Advance three pages", "Step 3"
        )
        self.assertEqual(result["status"], "execution_error")
        self.assertEqual(engine.native.clicks, 1)


if __name__ == "__main__":
    unittest.main()
