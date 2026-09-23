"""Track a bounded collection using model-selected, verbatim source passages."""

import math
import re


def clip_bytes(text, limit):
    return text.encode("utf-8")[:limit].decode("utf-8", errors="ignore")


def passages(text, size=1800, overlap=300):
    """Keep source offsets so a selection cannot manufacture evidence."""
    result = {}
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = text.rfind("\n", start + size // 2, end)
            if boundary >= 0:
                end = boundary + 1
        result["p" + str(len(result))] = (start, end)
        if end == len(text):
            break
        start = end - overlap
    return result


def passage_windows(text, queries, limit=14000):
    """Rank original spans into bounded views, keeping every character reachable."""
    size = min(1800, limit // 4)
    spans = passages(text, size=size, overlap=min(300, size // 6))

    def words(value):
        return set(re.findall(r"[\w]+", value.lower()))

    tokens = {k: words(text[a:b]) for k, (a, b) in spans.items()}
    query_words = [words(query) for query in queries]
    weights = {
        word: math.log(
            1 + len(spans) / (1 + sum(word in row for row in tokens.values()))
        )
        for query in query_words
        for word in query
    }
    ranked = [
        sorted(
            spans,
            key=lambda k: sum(weights[w] for w in query & tokens[k]),
            reverse=True,
        )
        for query in query_words
    ]
    # Interleave requirements so one long document section cannot consume the
    # entire budget. Always retain the page identity before relevant passages.
    order = [next(iter(spans))] if spans else []
    order.extend(key for group in zip(*ranked) for key in group)
    order.extend(spans)
    windows, used = [{}], 0
    for key in dict.fromkeys(order):
        a, b = spans[key]
        byte_count = len(text[a:b].encode("utf-8"))
        if windows[-1] and used + byte_count > limit:
            windows.append({})
            used = 0
        windows[-1][key] = (a, b)
        used += byte_count
    return windows


def select_passages(text, queries, limit=14000):
    """Return the first view; callers needing coverage can page through all views."""
    return passage_windows(text, queries, limit)[0]


class Collection:
    def __init__(self, requirements=None):
        self.requirements = requirements or {}
        if len(self.requirements) > 8:
            raise ValueError("Collect at most eight evidence items per stage")
        self.found = {}
        self.pending = {}
        self.passages = {}

    def questions(self, obs, selected=None):
        self.passages = (
            selected
            if selected is not None
            else select_passages(
                obs["page"],
                [v for k, v in self.requirements.items() if k not in self.found],
            )
        )
        self.pending = {
            "evidence_" + str(i): key
            for i, key in enumerate(self.requirements)
            if key not in self.found
        }
        return {
            question: {
                "type": "choice",
                "instructions": (
                    "Select an original passage from `page_passages` that directly supplies this requested evidence: "
                    + self.requirements[key]
                    + ". Choose none when the requested fact is absent. A navigation link, "
                    "section title or keyword mention alone is not evidence of its contents. "
                    "Do not infer missing facts. If several passages qualify, choose the most complete."
                ),
                "criteria": {
                    "none": "No passage in this text view supplies the requested evidence",
                    **{
                        k: "The original text at `page_passages." + k + "`"
                        for k in self.passages
                    },
                },
            }
            for question, key in self.pending.items()
        }

    def update(self, answers, obs):
        for question, key in self.pending.items():
            choice = answers[question]["choice"]
            if choice == "none":
                continue
            start, end = self.passages[choice]
            self.found[key] = {
                "requirement": self.requirements[key],
                "source_id": obs["source_id"],
                "url": obs["url"],
                "start": start,
                "end": end,
                "text": obs["page"][start:end],
                "verified_by_host": False,
            }

    @property
    def ready(self):
        return bool(self.requirements) and len(self.found) == len(self.requirements)

    def progress(self):
        return {
            "collected": {
                k: {f: v[f] for f in ("source_id", "url")}
                for k, v in self.found.items()
            },
            "remaining": {
                k: v for k, v in self.requirements.items() if k not in self.found
            },
        }
