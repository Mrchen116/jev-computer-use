"""Restrict benchmark execution to its dedicated Chrome/public-site grant."""

from .computer import Computer
from .desktop import visible_page_url
from .stages import in_scope
from urllib.parse import urlsplit
import time


class EvaluationComputer(Computer):
    """The evaluation harness, not a task-specific Jev policy, supplies scope."""

    def __init__(self, native, prefixes):
        super().__init__(native, "com.google.Chrome")
        self.prefixes = prefixes

    def observe(self):
        if self.application != "com.google.Chrome":
            raise RuntimeError("Evaluation is restricted to its dedicated Chrome window")
        deadline = time.monotonic() + 30
        while True:
            observation = super().observe()
            url = visible_page_url(observation["ui_tree"])
            if url and "…" not in url:
                break
            # A navigation can temporarily remove URL metadata. Retry observation,
            # never the click whose effect is already in flight.
            if time.monotonic() >= deadline:
                break
            time.sleep(.2)
        if "://" not in url and url:
            host = urlsplit("//" + url).netloc
            scheme = next((urlsplit(p).scheme for p in self.prefixes if urlsplit(p).netloc == host), "https")
            url = scheme + "://" + url
        if not url or not in_scope(url, self.prefixes):
            raise RuntimeError("Cannot verify the evaluation's authorized URL scope; no delegated action is permitted. Observed URL: " + (url or "[not available]"))
        observation["applications"] = [a for a in observation["applications"] if a["id"] == self.application]
        # Authorization limits available operations, never the observed UI text.
        # Public off-site links (e.g. a package registry) are outside this grant.
        for ref, control in list(observation["controls"].items()):
            value = control["value"]
            if control["role"] != "link" or not value or "…" in value:
                continue
            if "://" in value:
                target = value
            else:
                host = urlsplit("//" + value).netloc
                scheme = next((urlsplit(p).scheme for p in self.prefixes if urlsplit(p).netloc == host), "https")
                target = scheme + "://" + value
            if "." in urlsplit(target).netloc and not in_scope(target, self.prefixes):
                del observation["controls"][ref]
        return observation

    def execute(self, action):
        if action["type"] == "switch_app":
            raise RuntimeError("Application switching is outside this benchmark's scope")
        return super().execute(action)
