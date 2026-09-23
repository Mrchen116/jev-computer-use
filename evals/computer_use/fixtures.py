"""Resettable localhost websites. The judge reads server state, never model claims."""

import html
import json
import random
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

CASES = ("game", "form", "catalog", "lookup", "research")
GAME_WINDOW_SECONDS = 4.0


def number_in_answer(text, number):
    """A port or source URL is not evidence that the answer reported a numeric fact."""
    visible = re.sub(r"https?://\S+", "", text)
    return bool(re.search(r"(?<!\d)" + str(number) + r"(?:\.0+)?(?!\d)", visible))


GAME = [
    (
        "Choose something that measures elapsed time",
        ["Stopwatch", "Compass", "Lantern", "Thermometer"],
    ),
    (
        "Select the item useful when rain starts",
        ["Umbrella", "Sunscreen", "Notebook", "Scarf"],
    ),
    (
        "Choose a device for preserving frozen food",
        ["Freezer", "Oven", "Toaster", "Kettle"],
    ),
    ("Choose an instrument for finding north", ["Compass", "Ruler", "Scale", "Clock"]),
    (
        "Select the tool that tightens a screw",
        ["Screwdriver", "Paintbrush", "Pliers", "Saw"],
    ),
    (
        "Choose a material commonly recycled with bottles",
        ["Glass", "Bread", "Cotton", "Sand"],
    ),
    (
        "Select something used to check a fever",
        ["Thermometer", "Telescope", "Timer", "Microscope"],
    ),
    ("Choose transport that runs on rails", ["Tram", "Ferry", "Bicycle", "Bus"]),
    (
        "Choose what helps a plant get water slowly",
        ["Drip irrigation", "Wind turbine", "Solar panel", "Air filter"],
    ),
    (
        "Select an item that protects hands from heat",
        ["Oven mitt", "Apron", "Goggles", "Earplugs"],
    ),
    (
        "Choose a device that turns sunlight into electricity",
        ["Solar panel", "Battery", "Generator", "Radiator"],
    ),
    (
        "Select something that helps see distant stars",
        ["Telescope", "Binocular case", "Magnifying glass", "Camera bag"],
    ),
]


def button(label, action, value="", **fields):
    payload = html.escape(
        json.dumps(dict(action=action, value=value, **fields)), quote=True
    )
    return f'<button onclick="act({payload})">{html.escape(str(label))}</button>'


class World:
    def __init__(self, case, seed):
        self.case, self.seed = case, seed
        self.rng = random.Random(seed)
        self.stage = "home"
        self.events, self.visited = [], set()
        self.saved, self.filters, self.selected = {}, {}, None
        self.project = None
        self.round, self.score, self.reactions = 0, 0, []
        self.round_started = None
        self.missed = 0
        self.wrong = 0
        self.lock = threading.RLock()
        self.deck = self.rng.sample(GAME, len(GAME))
        self.choices = []
        for _, choices in self.deck:
            shuffled = list(choices)
            self.rng.shuffle(shuffled)
            self.choices.append(shuffled)
        self.person = {
            "Name": f"Alex Chen {seed}",
            "Email": f"alex{seed}@example.test",
            "City": ["Osaka", "Lisbon", "Helsinki"][seed % 3],
            "Note": f"Local demo {seed}; no real booking.",
        }
        self.products = [
            dict(
                name=f"Trail {i + 1}",
                price=40 + (seed * 7 + i * 13) % 100,
                waterproof=i % 3 != 0,
                stock=i % 4 != 0,
            )
            for i in range(9)
        ]
        self.rng.shuffle(self.products)
        self.best = min(
            (p for p in self.products if p["waterproof"] and p["stock"]),
            key=lambda p: p["price"],
        )
        self.issues = [
            dict(number=31 + i + seed, title=t, date=f"2026-09-{11 + i:02}")
            for i, t in enumerate(
                [
                    "Add shared memory",
                    "Fix worker timeout",
                    "Improve trace viewer",
                    "Document team setup",
                ]
            )
        ]
        self.rng.shuffle(self.issues)
        self.sources = [
            dict(
                name=n,
                price=12 + seed + i * 4,
                offline=i != 1,
                export=i != 3,
                note=[
                    "Local-first notes",
                    "Cloud sync only",
                    "Team workspaces",
                    "No bulk export",
                    "Encrypted archive",
                ][i],
            )
            for i, n in enumerate(["Cedar", "Maple", "Birch", "Willow", "Pine"])
        ]
        self.rng.shuffle(self.sources)
        self.shortlist = set()

    @property
    def task(self):
        return {
            "game": "Play Rescue Dispatch: 12 incoming requests, each with a strict 4-second deadline. Click the tool best matching the current request before it expires. The world keeps advancing while you think; expired requests are lost and cannot be replayed. Finish with at least 10 rescues out of 12. Start when ready and report the final score and missed requests.",
            "form": "Create and save a local profile with these exact values: "
            + json.dumps(self.person)
            + ". Set Digest to Weekly, Language to English, and enable Offline mode. These are synthetic details; save only inside this demo.",
            "catalog": "In the catalog, filter to waterproof and in-stock products, then add the cheapest matching product to the local comparison tray. Report its name and price.",
            "lookup": "Find the project about multi-agent collaboration, open its issues, and return the newest issue by creation date: title, issue number and its page URL. Check ordering; the initial list is not sorted.",
            "research": "Compare all five note apps. Read every detail page; shortlist every app that supports BOTH offline work and Markdown export. Return a Markdown table with one row per qualifying app: name, monthly price, distinguishing note and its actual source page URL. Do not stop at the first matching page.",
        }[self.case]

    def act(self, data):
        self.tick()
        self.events.append({"at": time.monotonic(), **data})
        action, value = data["action"], data.get("value")
        if self.case == "game":
            if action == "start" and self.stage == "home":
                self.stage = "playing"
                self.round_started = time.monotonic()
            elif (
                action == "pick"
                and self.stage == "playing"
                and data.get("round") == self.round
            ):
                if self.round_started is not None:
                    self.reactions.append(time.monotonic() - self.round_started)
                self.score += value == self.deck[self.round][1][0]
                self.wrong += value != self.deck[self.round][1][0]
                self.round += 1
                self.round_started = time.monotonic()
                if self.round == len(self.deck):
                    self.stage = "finished"
        elif self.case == "form":
            if action == "details":
                self.stage = "details"
            elif action == "next":
                self.saved.update(data.get("fields", {}))
                self.stage = "preferences"
            elif action in ("Digest", "Language", "Offline mode"):
                self.saved[action] = value
            elif action == "save":
                self.stage = "saved"
        elif self.case == "catalog":
            if action == "catalog":
                self.stage = "catalog"
            elif action in ("waterproof", "stock"):
                self.filters[action] = not self.filters.get(action, False)
            elif action == "compare":
                self.selected = value
                self.stage = "compared"
        elif self.case == "lookup":
            if action == "project":
                self.stage = value
                self.project = value
            elif action == "issues":
                self.stage = "issues"
            elif action == "sort":
                self.issues.sort(key=lambda p: p["date"], reverse=True)
            elif action == "issue":
                self.stage = "issue"
                self.selected = value
            elif action == "back":
                self.stage = "home"
        elif self.case == "research":
            if action == "source":
                self.selected = value
                self.visited.add(value)
                self.stage = "source"
            elif action == "shortlist":
                self.shortlist.add(self.selected)
            elif action == "back":
                self.stage = "home"

    def tick(self):
        """Deadlines follow the server clock, independent of UI reads or model calls."""
        if self.case != "game" or self.stage != "playing":
            return
        now = time.monotonic()
        while (
            self.round < len(self.deck)
            and now >= self.round_started + GAME_WINDOW_SECONDS
        ):
            self.missed += 1
            self.round += 1
            self.round_started += GAME_WINDOW_SECONDS
        if self.round == len(self.deck):
            self.stage = "finished"

    def content(self):
        self.tick()
        b = button
        if self.case == "game":
            if self.stage == "home":
                return (
                    "<h1>Rescue Dispatch</h1><p>12 incoming requests. Each request expires after 4 seconds of real time, even while you think. Dispatch the best tool. Rescue at least 10 to win. No replay.</p>"
                    + b("Start game", "start")
                )
            if self.stage == "finished":
                return f"<h1>Game complete — {'victory' if self.score >= 10 else 'defeat'}</h1><p>Rescued: {self.score} / 12. Missed deadlines: {self.missed}. Wrong tools: {self.wrong}.</p>"
            return (
                f"<h1>Request {self.round + 1} of 12</h1><p>Rescued: {self.score}; missed: {self.missed}. Deadline: 4 seconds.</p><div class='track' aria-hidden='true'><div id='courier'>🚨</div></div><h2>{self.deck[self.round][0]}</h2>"
                + "".join(
                    b(c, "pick", c, round=self.round) for c in self.choices[self.round]
                )
            )
        if self.case == "form":
            if self.stage == "home":
                return "<h1>Local profile</h1>" + b("Create profile", "details")
            if self.stage == "details":
                return (
                    "<h1>Profile details</h1>"
                    + "".join(
                        f'<label>{k}<input id="{k}" aria-label="{k}"></label>'
                        for k in self.person
                    )
                    + "<button onclick=\"act({action:'next',fields:Object.fromEntries([...document.querySelectorAll('input')].map(x=>[x.id,x.value]))})\">Continue to preferences</button>"
                )
            if self.stage == "preferences":
                return (
                    "<h1>Preferences</h1>"
                    + "".join(
                        "<section><h2>"
                        + k
                        + "</h2>"
                        + "".join(
                            b(
                                v + (" — selected" if self.saved.get(k) == v else ""),
                                k,
                                v,
                            )
                            for v in vals
                        )
                        + "</section>"
                        for k, vals in [
                            ("Digest", ["Daily", "Weekly", "Never"]),
                            ("Language", ["English", "Japanese"]),
                            ("Offline mode", ["Enabled", "Disabled"]),
                        ]
                    )
                    + b("Save profile", "save")
                )
            return (
                "<h1>Profile saved</h1><pre>"
                + html.escape(json.dumps(self.saved, indent=2))
                + "</pre>"
            )
        if self.case == "catalog":
            if self.stage == "home":
                return "<h1>Outdoor gear</h1>" + b("Browse catalog", "catalog")
            if self.stage == "compared":
                return (
                    "<h1>Comparison tray saved</h1><p>"
                    + html.escape(self.selected)
                    + "</p>"
                )
            controls = b(
                "Waterproof only"
                + (" — active" if self.filters.get("waterproof") else ""),
                "waterproof",
            ) + b(
                "In stock only" + (" — active" if self.filters.get("stock") else ""),
                "stock",
            )
            products = [
                p
                for p in self.products
                if all(not enabled or p[k] for k, enabled in self.filters.items())
            ]
            return (
                "<h1>Catalog</h1>"
                + controls
                + "".join(
                    f"<article><h2>{p['name']}</h2><p>${p['price']}; Waterproof: {p['waterproof']}; In stock: {p['stock']}</p>"
                    + b("Compare " + p["name"], "compare", p["name"])
                    + "</article>"
                    for p in products
                )
            )
        if self.case == "lookup":
            if self.stage == "home":
                return "<h1>Project portfolio</h1>" + "".join(
                    "<article><h2>"
                    + n
                    + "</h2><p>"
                    + d
                    + "</p>"
                    + b("Open " + n, "project", n)
                    + "</article>"
                    for n, d in [
                        ("KeyGarden", "Input method experiments"),
                        (
                            "SwarmDesk",
                            "Multi-agent collaboration and shared task execution",
                        ),
                        ("FrameKit", "Screenshot styling"),
                    ]
                )
            if self.stage in ("KeyGarden", "SwarmDesk", "FrameKit"):
                return (
                    "<h1>"
                    + self.stage
                    + "</h1>"
                    + b("Issues", "issues")
                    + b("Back to projects", "back")
                )
            if self.stage == "issues":
                if self.project != "SwarmDesk":
                    return "<h1>No open issues</h1>" + b("Back to projects", "back")
                return (
                    "<h1>SwarmDesk issues</h1>"
                    + b("Sort: newest created first", "sort")
                    + "".join(
                        "<article><p>#"
                        + str(p["number"])
                        + " "
                        + p["title"]
                        + "; Created "
                        + p["date"]
                        + "</p>"
                        + b("Open issue #" + str(p["number"]), "issue", p["number"])
                        + "</article>"
                        for p in self.issues
                    )
                )
            p = next(p for p in self.issues if p["number"] == self.selected)
            return f"<h1>Issue #{p['number']}: {p['title']}</h1><p>Created {p['date']}. SwarmDesk.</p><p>Source: /issue/{p['number']}</p>"
        if self.stage == "home":
            return (
                "<h1>Note apps directory</h1><p>Read the details to verify features. Five independent products.</p><p>Shortlist: "
                + ", ".join(sorted(self.shortlist))
                + "</p>"
                + "".join(
                    b("Read " + p["name"], "source", p["name"]) for p in self.sources
                )
            )
        p = next(p for p in self.sources if p["name"] == self.selected)
        return (
            f"<h1>{p['name']}</h1><p>Monthly price: ${p['price']}</p><p>Offline work: {'Yes' if p['offline'] else 'No'}. Markdown export: {'Yes' if p['export'] else 'No'}.</p><p>Notes: {p['note']}</p><p>Source: /notes/{p['name'].lower()}</p>"
            + b(
                "Add to shortlist"
                + (" — added" if self.selected in self.shortlist else ""),
                "shortlist",
            )
            + b("Back to directory", "back")
        )

    def judge(self, answer, base):
        self.tick()
        checks = {}
        if self.case == "game":
            checks = {"finished": self.round == 12, "rescues": self.score >= 10}
        elif self.case == "form":
            checks = {
                "saved": self.stage == "saved",
                **{
                    k: self.saved.get(k) == v
                    for k, v in dict(
                        self.person,
                        Digest="Weekly",
                        Language="English",
                        **{"Offline mode": "Enabled"},
                    ).items()
                },
            }
        elif self.case == "catalog":
            checks = {
                "both_filters": all(
                    self.filters.get(k) for k in ("waterproof", "stock")
                ),
                "cheapest": self.selected == self.best["name"],
                "name_in_answer": self.best["name"].lower() in answer.lower(),
                "price_in_answer": number_in_answer(answer, self.best["price"]),
            }
        elif self.case == "lookup":
            p = max(self.issues, key=lambda p: p["date"])
            checks = {
                "correct_project": self.project == "SwarmDesk",
                "opened_latest": self.selected == p["number"],
                "title": p["title"].lower() in answer.lower(),
                "number": number_in_answer(answer, p["number"]),
                "url": base + "/issue/" + str(p["number"]) in answer,
            }
        else:
            eligible = [p for p in self.sources if p["offline"] and p["export"]]
            checks = {
                "visited_all": len(self.visited) == 5,
                "shortlist_exact": self.shortlist == {p["name"] for p in eligible},
            }
            for p in eligible:
                checks[p["name"]] = any(
                    all(
                        str(v).lower() in line.lower()
                        for v in (
                            p["name"],
                            p["note"],
                            base + "/notes/" + p["name"].lower(),
                        )
                    )
                    and number_in_answer(line, p["price"])
                    for line in answer.splitlines()
                )
        return dict(
            success=all(checks.values()),
            checks=checks,
            game_score=self.score if self.case == "game" else None,
            game_missed=self.missed if self.case == "game" else None,
            game_wrong=self.wrong if self.case == "game" else None,
            reaction_seconds=self.reactions,
        )


class FixtureServer:
    def __init__(self):
        self.worlds = {}
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                parts = urlparse(self.path).path.strip("/").split("/")
                world = outer.worlds.get(parts[0])
                if world is None:
                    self.send_error(404)
                    return
                with world.lock:
                    content = world.content()
                    remaining = max(
                        0,
                        (world.round_started or 0)
                        + GAME_WINDOW_SECONDS
                        - time.monotonic(),
                    )
                if urlparse(self.path).query == "view=live":
                    self.send_body(
                        json.dumps({"html": content, "remaining": remaining}).encode(),
                        "application/json",
                    )
                    return
                script = """<script>async function act(data){const r=await fetch(location.pathname,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const result=await r.json();location.href=result.url;}</script>"""
                if world.case == "game":
                    script = """<script>
let busy=false,last=document.querySelector('main').innerHTML;
async function refresh(){if(busy)return;busy=true;try{const r=await fetch(location.pathname+'?view=live');const s=await r.json();if(s.html!==last){document.querySelector('main').innerHTML=s.html;last=s.html;}const c=document.getElementById('courier');if(c)c.style.left=((1-Math.min(4,s.remaining)/4)*92)+'%';}finally{busy=false;}}
async function act(data){await fetch(location.pathname,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});await refresh();}
setInterval(refresh,100);
</script>"""
                body = (
                    """<!doctype html><html lang="en"><meta charset="utf-8"><title>Jev Safe Benchmark</title><style>body{font:18px system-ui;max-width:920px;margin:30px auto;padding:16px}button,input{font:inherit;padding:10px;margin:7px}label{display:block}article,section{display:inline-block;vertical-align:top;border:1px solid #bbb;padding:12px;margin:8px}pre{white-space:pre-wrap}.track{height:66px;background:linear-gradient(90deg,#dcfce7,#fef3c7,#fee2e2);border-radius:12px;position:relative}#courier{position:absolute;top:12px;font-size:32px;transition:left .1s linear}button{cursor:pointer;border:1px solid #94a3b8;border-radius:8px;background:#f8fafc}</style><body><main>"""
                    + content
                    + "</main>"
                    + script
                    + "</body></html>"
                ).encode()
                self.send_body(body, "text/html; charset=utf-8")

            def send_body(self, body, content_type):
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                ident = urlparse(self.path).path.strip("/").split("/")[0]
                w = outer.worlds[ident]
                with w.lock:
                    w.act(
                        json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                    )
                suffix = (
                    "/issue/" + str(w.selected)
                    if w.case == "lookup" and w.stage == "issue"
                    else "/notes/" + w.selected.lower()
                    if w.case == "research" and w.stage == "source"
                    else "/" + w.stage
                )
                body = json.dumps({"url": "/" + ident + suffix}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.origin = f"http://127.0.0.1:{self.server.server_port}"
        self.stopping = threading.Event()

        def clock_loop():
            while not self.stopping.wait(0.05):
                for world in list(self.worlds.values()):
                    with world.lock:
                        world.tick()

        self.clock_thread = threading.Thread(target=clock_loop, daemon=True)
        self.clock_thread.start()

    def add(self, case, seed, ident):
        self.worlds[ident] = World(case, seed)
        return self.worlds[ident], self.origin + "/" + ident

    def close(self):
        self.stopping.set()
        self.clock_thread.join()
        self.server.shutdown()
        self.server.server_close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Play or inspect one synthetic case without calling models."
    )
    parser.add_argument("--case", choices=CASES, default="game")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    server = FixtureServer()
    world, url = server.add(args.case, args.seed, "manual")
    print(url, flush=True)
    print(world.task, flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
