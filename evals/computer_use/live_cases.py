"""Public website tasks. Reference answers stay in the evaluator, never the agent."""

import json
import re
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlsplit

from fixtures import FixtureServer

LIVE_CASES = ("portfolio", "latest_issue", "documentation", "research", "game")


def canonical(url):
    if "://" not in url:
        url = "https://" + url
    p = urlsplit(url)
    return (p.netloc.lower(), p.path.rstrip("/"))


def observed_pages(journal):
    """Only actual window/webarea observations count, not links in an answer."""
    found = set()
    for event in journal:
        if event.get("kind") == "task_detail":
            found.update(observed_pages([{"kind": "tool", "name": "js", "result": {
                "content": [{"type": "text", "text": obs["ui_tree"]}]
            }} for obs in event["observations"]]))
        if event.get("kind") == "stage_detail":
            found.add(canonical(event["current_url"]))
            found.update(canonical(p["url"]) for p in event["visited_pages"])
        if event.get("kind") == "tool" and event.get("name") == "js":
            for block in event.get("result", {}).get("content", []):
                if block.get("type") != "text":
                    continue
                # nodeRepl.write may render a JSON object with escaped newlines.
                text = block["text"].replace("\\n", "\n").replace("\\t", "\t")
                for line in text.splitlines():
                    if re.search(r"\b(?:web area|standard window)\b|HTML 内容|标准窗口", line, re.I):
                        match = re.search(r"URL: ([^\s,\\\"]+)", line)
                        if match and '…' not in match[1]:
                            found.add(canonical(match[1]))
                # Independently recognize native URL elision. Only browser chrome
                # before the web root can supply a loaded address, never page text.
                root = re.search(r'^.*\b(?:web area|HTML 内容)\b.*URL: …', text, re.M)
                if root:
                    chrome = text[:root.start()]
                    address = re.search(
                        r'^\s*[~+]?\s*(\d+) (?:text field|文本栏) (?:\([^)]*\) )?(?:Address and search bar|地址和搜索栏), Value: ([^\s,]+)',
                        chrome, re.M | re.I,
                    )
                    focused = re.search(r'The focused UI element is (\d+)\b', text)
                    if address and '…' not in address[2] and not (focused and focused[1] == address[1]):
                        found.add(canonical(address[2]))
    return found


class LiveWorld:
    live = True

    def __init__(self, case, truth):
        self.case, self.truth = case, truth
        self.pages = set()
        common = ["https://mrchen116.github.io/", "https://github.com/Mrchen116/"]
        definitions = {
            "portfolio": (
                "https://mrchen116.github.io/", common,
                "去这个人的网站，找到关于 macOS 语音输入/听写的开源项目，给我项目名、它的 GitHub 仓库链接，并用一句话说明为什么是它。只读，不下载、不安装。",
            ),
            "latest_issue": (
                "https://mrchen116.github.io/", common,
                "去这个人的网站找到多 agent 项目，然后在对应 GitHub 仓库里找按创建时间最新的一个 issue（包括已关闭，排除 pull request）。返回 issue 标题、编号、创建日期和详情页链接。需要打开详情核实；只读，不提交任何内容。",
            ),
            "documentation": (
                "https://docs.python.org/3.13/", ["https://docs.python.org/3.13/"],
                "在 Python 3.13 官方文档中找到 pathlib 的 Path.read_text 和 Path.write_text。比较它们的参数和返回值，特别说明 newline 参数分别在哪个 Python 版本加入，并提供对应文档链接。只查文档，不操作本机文件。",
            ),
            "research": (
                "https://docs.pytest.org/en/stable/",
                ["https://docs.pytest.org/en/stable/", "https://docs.astral.sh/ruff/", "https://mypy.readthedocs.io/en/stable/"],
                "我要为 Python 项目准备测试、lint 和类型检查。分别查 pytest、Ruff、mypy 的官方文档，汇总 pip 安装命令和检查单个文件 example.py 的最小命令，用三行表格给出每项的两个命令和实际官方来源链接。三个项目都要查到。官方入口：https://docs.pytest.org/en/stable/ 、https://docs.astral.sh/ruff/ 、https://mypy.readthedocs.io/en/stable/ 。只收集信息，不安装或运行这些命令。",
            ),
        }
        self.url, self.allowed_prefixes, self.task = definitions[case]

    def judge(self, answer, base):
        text = answer.lower()
        if self.case == "portfolio":
            checks = {
                "visited_portfolio": canonical(self.url) in self.pages,
                "project": "audioinput" in text,
                "url": "https://github.com/mrchen116/audioinput" in text,
                "description": bool(re.search(r"听写|转写|语音|dictat|transcri", text)),
            }
        elif self.case == "latest_issue":
            p = self.truth["latest_issue"]
            checks = {
                "opened_issue": canonical(p["html_url"]) in self.pages,
                "title": p["title"].lower() in text,
                "number": bool(re.search(r"(?<!\d)" + str(p["number"]) + r"(?!\d)", text)),
                "date": p["created_at"][:10] in text,
                "url": p["html_url"].lower() in text,
            }
        elif self.case == "documentation":
            checks = {
                "observed_source": ("docs.python.org", "/3.13/library/pathlib.html") in self.pages,
                "source_link": "https://docs.python.org/3.13/library/pathlib.html" in text,
                "read_version": bool(re.search(r"read_text[\s\S]{0,650}3\.13", text)),
                "write_version": bool(re.search(r"write_text[\s\S]{0,650}3\.10", text)),
                "arguments": all(s in text for s in ("encoding", "errors", "newline", "data")),
                "returns": bool(re.search(r"str|字符串|文本内容", text)) and bool(re.search(r"字符数|字符数量|characters|integer|\bint\b", text)),
            }
        else:
            checks = {}
            for name, domain, command in (
                ("pytest", "docs.pytest.org", r"pytest\s+example\.py"),
                ("ruff", "docs.astral.sh", r"ruff\s+check\s+example\.py"),
                ("mypy", "mypy.readthedocs.io", r"mypy\s+example\.py"),
            ):
                checks[name + "_visited"] = any(host == domain for host, _ in self.pages)
                checks[name + "_facts"] = any(
                    name in line and domain in line
                    and re.search(r"pip\s+install(?:\s+-\S+)*\s+" + name, line)
                    and re.search(command, line)
                    for line in text.splitlines()
                )
        return {"success": all(checks.values()), "checks": checks, "reaction_seconds": []}


class LiveSuite:
    def __init__(self, root, cases):
        self.fixture = FixtureServer()
        self.origin = self.fixture.origin
        self.worlds = {}
        self.truth = {"frozen_at": datetime.now(timezone.utc).isoformat()}
        if "latest_issue" in cases:
            items = json.loads(subprocess.check_output([
                "gh", "api", "repos/Mrchen116/nano-multiagent/issues?state=all&sort=created&direction=desc&per_page=100"
            ], text=True))
            issues = [p for p in items if "pull_request" not in p]
            if not issues:
                raise RuntimeError("No issue reference found in the first 100 current GitHub records")
            p = max(issues, key=lambda p: p["created_at"])
            self.truth["latest_issue"] = {k: p[k] for k in ("number", "title", "created_at", "html_url")}
        (root / "reference.json").write_text(json.dumps(self.truth, ensure_ascii=False, indent=2))

    def add(self, case, seed, ident):
        if case == "game":
            world, url = self.fixture.add(case, seed, ident)
        else:
            world = LiveWorld(case, self.truth)
            url = world.url
        self.worlds[ident] = world
        return world, url

    def close(self):
        self.fixture.close()
