"""Serve pinned upstream MiniWoB tasks; retain their first official reward privately."""

import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import subprocess
import threading
import time
from urllib.parse import unquote, urlparse

MINIWOB_REVISION = "33c3b4ddef8c6eb67c57a29663d844b1eda7e614"
MINIWOB_CASES = {
    "click-checkboxes-large": {"minimum_operations": 6, "original_deadline_ms": 20000},
    "multi-layouts": {"minimum_operations": 4, "original_deadline_ms": 20000},
    "book-flight": {"minimum_operations": 5, "original_deadline_ms": 30000},
}


def instrumentation(seed, deadline_ms):
    """Seed before generation and observe core's result without replacing its judge."""
    config = json.dumps({"seed": str(seed), "deadline_ms": deadline_ms})
    return """<script>
(() => {
  const config = CONFIG;
  Math.seedrandom(config.seed);
  core.EPISODE_MAX_TIME = config.deadline_ms;
  let started = false, finished = false, actions = [];
  const endpoint = new URL('../_episode', location.href);
  const post = value => fetch(endpoint, {method:'POST',
    headers:{'Content-Type':'application/json'}, body:JSON.stringify(value), keepalive:true});
  for (const type of ['click', 'input', 'keydown']) {
    document.addEventListener(type, event => {
      if (!started || finished || event.target.id === 'sync-task-cover') return;
      actions.push({type, tag:event.target.tagName, input_type:event.target.type || '',
        text:(event.target.innerText || event.target.getAttribute('aria-label') || '').slice(0,120),
        key:type === 'keydown' ? event.key : undefined,
        trusted:event.isTrusted, elapsed_ms:Date.now()-core.ept0});
    }, true);
  }
  const start = core.startEpisodeReal;
  core.startEpisodeReal = function(...args) {
    const result = start.apply(this, args);
    started = true; finished = false; actions = [];
    post({kind:'start', query:document.getElementById('query').innerText,
      seed:config.seed, deadline_ms:config.deadline_ms});
    return result;
  };
  const end = core.endEpisode;
  core.endEpisode = function(...args) {
    const wasDone = WOB_DONE_GLOBAL;
    const result = end.apply(this, args);
    if (!wasDone && WOB_DONE_GLOBAL && !finished) {
      finished = true;
      post({kind:'terminal', raw_reward:WOB_RAW_REWARD_GLOBAL,
        reward:WOB_REWARD_GLOBAL, reason:WOB_REWARD_REASON,
        elapsed_ms:Date.now()-core.ept0, actions});
    }
    return result;
  };
})();
</script>""".replace("CONFIG", config)


class MiniWoBWorld:
    def __init__(self, case, seed, directory, prefix):
        self.case, self.seed, self.directory = case, seed, directory
        self.allowed_prefixes = [prefix]
        self.events = []
        self.lock = threading.Lock()
        self.task = (
            "Complete ONE MiniWoB++ episode. The harness has already started it, "
            "as in the official environment reset. Follow the instruction displayed at the top of the page. "
            "When the reward appears, the episode has ended: report it and stop. "
            "The START overlay reappears automatically after termination; do not "
            "click it again, reload, or start a new episode. This is an upstream "
            "benchmark page, including any simulated booking controls; no real "
            "purchase is made. Use accessibility text only, without screenshots."
        )

    def prepare(self, desktop, observation):
        """Match upstream reset semantics using the native UI, before agent timing."""
        from jev_computer_use.desktop import nodes

        start = next(n for n in nodes(observation["raw"]) if n["detail"] == "START")
        current = desktop.execute({"verb": "click", "ref": start["ref"]})
        deadline = time.monotonic() + 2
        while not self.events and time.monotonic() < deadline:
            time.sleep(.05)
        if not self.events or self.events[0].get("kind") != "start":
            raise RuntimeError("MiniWoB reset did not produce an episode-start event")
        # The official environment also returns the public utterance on reset.
        # Verify its presence in native AX instead of exposing hidden task state.
        query = self.events[0]["query"]
        visible_text = "".join("".join(n["detail"].split()) for n in nodes(current["raw"]) if n["role"] == "text")
        if "".join(query.split()) not in visible_text:
            raise RuntimeError("MiniWoB instruction is not present in the native accessibility tree")
        self.task += "\nInstruction observed on the current page: " + query

    def record(self, event):
        with self.lock:
            self.events.append(event)
            with (self.directory / "miniwob-episodes.jsonl").open("a") as stream:
                stream.write(json.dumps(event, ensure_ascii=False) + "\n")

    def judge(self, answer, url):
        with self.lock:
            starts = [e for e in self.events if e.get("kind") == "start"]
            terminals = [e for e in self.events if e.get("kind") == "terminal"]
        first = terminals[0] if terminals else {}
        # Partial positive checkbox reward and successful retries are not passes.
        complete = first.get("raw_reward") == 1.0
        single = len(starts) == 1 and len(terminals) == 1
        return {
            "success": complete and single,
            "checks": {"official_raw_reward_one": complete, "single_episode": single},
            "raw_reward": first.get("raw_reward"),
            "time_scaled_reward": first.get("reward"),
            "reason": first.get("reason"),
            "episode_seconds": first.get("elapsed_ms", 0) / 1000 if terminals else None,
            "episodes_started": len(starts),
            "episodes_finished": len(terminals),
            "query": starts[0].get("query") if starts else None,
            "minimum_operations": MINIWOB_CASES[self.case]["minimum_operations"],
            "observed_ui_events": {
                kind: sum(a["type"] == kind for a in first.get("actions", []))
                for kind in ("click", "input", "keydown")
            },
            "reaction_seconds": [],
        }


class MiniWoBSuite:
    def __init__(self, upstream, output, deadline_seconds=300):
        self.upstream, self.output = Path(upstream), Path(output)
        self.html = (self.upstream / "miniwob/html").resolve()
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.upstream, text=True
        ).strip()
        if revision != MINIWOB_REVISION:
            raise ValueError("MiniWoB checkout must be pinned to " + MINIWOB_REVISION)
        if not self.html.is_dir():
            raise ValueError("Missing upstream miniwob/html directory")
        self.deadline_ms = deadline_seconds * 1000
        self.worlds = {}
        suite = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                parts = unquote(urlparse(self.path).path).strip("/").split("/", 1)
                if len(parts) != 2 or parts[0] not in suite.worlds:
                    self.send_error(404)
                    return
                world = suite.worlds[parts[0]]
                path = (suite.html / parts[1]).resolve()
                if suite.html not in path.parents or not path.is_file():
                    self.send_error(404)
                    return
                body = path.read_bytes()
                if parts[1] == f"miniwob/{world.case}.html":
                    body = body.replace(b"</body>", (instrumentation(world.seed, suite.deadline_ms) + "</body>").encode())
                self.send_response(200)
                self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                parts = urlparse(self.path).path.strip("/").split("/")
                if len(parts) != 2 or parts[0] not in suite.worlds or parts[1] != "_episode":
                    self.send_error(404)
                    return
                event = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                suite.worlds[parts[0]].record(event)
                self.send_response(204)
                self.end_headers()

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.origin = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def metadata(self):
        digest = hashlib.sha256()
        for path in sorted(self.html.rglob("*")):
            if path.is_file():
                digest.update(str(path.relative_to(self.html)).encode() + b"\0")
                digest.update(path.read_bytes())
        return {
            "upstream": "https://github.com/Farama-Foundation/miniwob-plusplus",
            "revision": MINIWOB_REVISION,
            "html_tree_sha256": digest.hexdigest(),
            "deadline_ms": self.deadline_ms,
            "score": "first official raw reward == 1.0, exactly one episode",
            "variant": "native accessibility, relaxed deadline; not standard leaderboard protocol",
            "reset": "harness clicks native START before agent launch; visible utterance supplied",
            "tasks": MINIWOB_CASES,
        }

    def add(self, case, seed, ident):
        if case not in MINIWOB_CASES:
            raise ValueError("Unsupported MiniWoB subset task: " + case)
        prefix = self.origin + "/" + ident
        world = MiniWoBWorld(case, seed, self.output / ident, prefix)
        self.worlds[ident] = world
        return world, prefix + f"/miniwob/{case}.html"

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
