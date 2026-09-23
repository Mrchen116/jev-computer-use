import unittest

from jev_computer_use.evidence import read_sources


class EvidenceTests(unittest.TestCase):
    def test_every_unicode_character_remains_reachable_with_bounded_text_views(self):
        from jev_computer_use.collection import passage_windows

        text = "甲乙🙂\n" * 6000 + "最后一段"
        views = passage_windows(text, [])
        covered = [False] * len(text)
        self.assertGreater(len(views), 1)
        for view in views:
            self.assertLessEqual(
                sum(len(text[a:b].encode("utf-8")) for a, b in view.values()), 14000
            )
            for a, b in view.values():
                covered[a:b] = [True] * (b - a)
        self.assertTrue(all(covered))

    def test_long_page_retrieval_preserves_distant_facts_under_context_budget(self):
        from jev_computer_use.collection import select_passages

        text = (
            "text: unrelated navigation and menu.\n" * 1500
            + "container: Path.read_text(encoding=None, newline=None)\ntext: Returns decoded text. Newline added in version 3.13.\n"
            + "text: unrelated discussion.\n" * 1500
            + "container: Path.write_text(data, encoding=None, newline=None)\ntext: Returns characters written. Newline added in version 3.10.\n"
        )
        spans = select_passages(
            text,
            [
                "Path.read_text signature newline version",
                "Path.write_text signature newline version",
            ],
        )
        selected = "".join(text[a:b] for a, b in spans.values())
        self.assertLessEqual(len(selected.encode()), 14000)
        self.assertIn("version 3.13", selected)
        self.assertIn("version 3.10", selected)

    def test_collection_questions_reference_one_shared_page_instead_of_repeating_it(
        self,
    ):
        import json
        from jev_computer_use.collection import Collection

        body = "text: Original long document.\n" * 2400
        collection = Collection({str(i): "Find the method signature" for i in range(8)})
        questions = collection.questions({"page": body})
        self.assertNotIn("Original long document", json.dumps(questions))
        self.assertLess(len(json.dumps(questions)), len(body))
        self.assertEqual(
            set(collection.passages),
            set(questions["evidence_0"]["criteria"]) - {"none"},
        )

    def source(self, text, source_id="s1"):
        return {
            "source_id": source_id,
            "url": "https://example.test/docs",
            "title": "Docs",
            "text": text,
        }

    def test_keyword_recovers_middle_of_long_original_without_mutating_archive(self):
        text = (
            "navigation " * 5000 + "Path.read_text returns a string.\n" + "body " * 3000
        )
        archive = {"s1": self.source(text)}
        result = read_sources(archive, ["s1"], query="path.read_text")[0]
        self.assertIn("Path.read_text returns a string.", result["text"])
        self.assertEqual(result["text"], text[result["start"] : result["end"]])
        self.assertTrue(result["truncated"])
        self.assertLessEqual(len(result["text"]), 6000)
        self.assertEqual(archive["s1"]["text"], text)

    def test_multiple_sources_share_a_bounded_payload_and_allow_next_segment(self):
        archive = {f"s{i}": self.source("x" * 20000, f"s{i}") for i in range(12)}
        result = read_sources(archive, list(archive))
        self.assertEqual(sum(len(s["text"]) for s in result), 12000)
        second = read_sources(archive, ["s0"], offset=result[0]["end"])[0]
        self.assertEqual(second["start"], 1000)

    def test_missing_query_is_explicit_and_does_not_substitute_other_text(self):
        result = read_sources(
            {"s1": self.source("Existing evidence")}, ["s1"], query="absent"
        )[0]
        self.assertFalse(result["query_found"])
        self.assertEqual(result["text"], "")
        self.assertEqual(result["match_count"], 0)

    def test_host_handoff_cannot_dump_a_long_page_or_duplicate_captured_text(self):
        from jev_computer_use.stages import compact_result

        text = "original " * 10000
        full = {
            "current_page": text,
            "current_source_id": "s1",
            "evidence": [self.source(text)],
            "actions": [],
            "jev_calls": [],
            "counts": {"actions": 0},
        }
        compact = compact_result(full)
        self.assertEqual(len(compact["current_page"]), 6000)
        self.assertTrue(compact["current_page_truncated"])
        self.assertEqual(compact["current_source_id"], "s1")
        self.assertNotIn("text", compact["evidence"][0])
        self.assertEqual(full["evidence"][0]["text"], text)

    def test_handoff_shares_original_passages_without_losing_item_requirements(self):
        from jev_computer_use.stages import compact_result

        item = {
            "source_id": "s1",
            "url": "https://example.test/docs",
            "start": 400,
            "end": 420,
            "text": "Exact original text.",
            "verified_by_host": False,
        }
        full = {
            "status": "collection_ready",
            "current_page": "current",
            "evidence": [],
            "actions": [],
            "jev_calls": [],
            "counts": {"actions": 0},
            "collected": {
                k: {**item, "requirement": k} for k in ("parameters", "returns")
            },
        }
        result = compact_result(full)
        self.assertEqual(len(result["passages"]), 1)
        for key, selected in result["collected"].items():
            self.assertEqual(selected["requirement"], key)
            self.assertFalse(selected["verified_by_host"])
            self.assertEqual(
                result["passages"][selected["passage"]]["text"], item["text"]
            )
        self.assertIn("text", full["collected"]["parameters"])


if __name__ == "__main__":
    unittest.main()
