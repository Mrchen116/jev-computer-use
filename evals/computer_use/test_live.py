import unittest

from live_cases import LiveWorld, canonical, observed_pages


class LiveJudgeTests(unittest.TestCase):
    def test_general_task_observations_use_the_same_visit_rules(self):
        raw = "0 standard window Project, URL: example.test/loaded\n 1 link Another, URL: example.test/mentioned"
        pages = observed_pages([{"kind": "task_detail", "observations": [{"ui_tree": raw}]}])
        self.assertEqual(pages, {("example.test", "/loaded")})

    def test_loaded_address_counts_when_native_root_elides_its_url(self):
        text = """0 标准窗口 Project, URL: …
 1 文本栏 (settable) 地址和搜索栏, Value: example.test/project, Placeholder: 搜索
 2 HTML 内容 Project, URL: …
  3 link Other, Value: example.test/other
The focused UI element is 2 HTML 内容 Project, URL: …
"""
        def pages(value):
            return observed_pages([{"kind": "tool", "name": "js", "result": {
                "content": [{"type": "text", "text": value}]
            }}])
        self.assertEqual(pages(text), {("example.test", "/project")})
        self.assertEqual(pages(text.replace('focused UI element is 2', 'focused UI element is 1')), set())
        self.assertEqual(pages(text[text.index(' 2 HTML'):]), set())

    def test_link_mentions_do_not_count_as_visited_pages(self):
        journal = [{"kind": "tool", "name": "js", "result": {"content": [{
            "type": "text", "text": "0 standard window Page, URL: example.test/one\n 1 web area Page, URL: example.test/one\n 2 link Other, URL: example.test/two"
        }]}}]
        self.assertEqual(observed_pages(journal), {("example.test", "/one")})

    def test_issue_answer_requires_actual_detail_observation(self):
        issue = {"number": 42, "title": "A new issue", "created_at": "2026-09-21T00:00:00Z", "html_url": "https://github.com/example/repo/issues/42"}
        world = LiveWorld("latest_issue", {"latest_issue": issue})
        answer = "A new issue #42 2026-09-21 https://github.com/example/repo/issues/42"
        self.assertFalse(world.judge(answer, world.url)["success"])
        world.pages.add(canonical(issue["html_url"]))
        self.assertTrue(world.judge(answer, world.url)["success"])

    def test_research_requires_three_observed_sources_and_facts(self):
        world = LiveWorld("research", {})
        answer = """| pytest | pip install -U pytest | pytest example.py | https://docs.pytest.org/en/stable/ |
| Ruff | pip install ruff | ruff check example.py | https://docs.astral.sh/ruff/ |
| mypy | python3 -m pip install mypy | mypy example.py | https://mypy.readthedocs.io/en/stable/ |"""
        world.pages = {canonical(p) for p in world.allowed_prefixes[:2]}
        self.assertFalse(world.judge(answer, world.url)["success"])
        world.pages.add(canonical(world.allowed_prefixes[2]))
        self.assertTrue(world.judge(answer, world.url)["success"])
        self.assertFalse(world.judge(answer.replace("ruff check example.py", "ruff example.py"), world.url)["success"])


if __name__ == "__main__":
    unittest.main()
