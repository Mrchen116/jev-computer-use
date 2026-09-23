"""Simple sequential cycle timing and aggregated, non-blocking warnings."""

import time


class Cycle:
    def __init__(self, period_ms, should_stop, on_wait):
        self.period = period_ms / 1000
        self.should_stop, self.on_wait = should_stop, on_wait
        self.next_start = 0

    def wait(self):
        """Return whether we waited; None means stop. Missed ticks never queue."""
        waited = False
        while time.monotonic() < self.next_start:
            if self.should_stop():
                return None
            if not waited:
                self.on_wait()
                waited = True
            time.sleep(min(0.1, max(0, self.next_start - time.monotonic())))
        if self.should_stop():
            return None
        self.next_start = time.monotonic() + self.period
        return waited


class Warnings:
    def __init__(self, history):
        self.history = history
        self.groups = {}

    def add(self, code, message, **details):
        event = {"code": code, "message": message, **details}
        self.history.append({"warning": event})
        previous = self.groups.get(code, {})
        self.groups[code] = {
            "code": code,
            "count": previous.get("count", 0) + 1,
            "latest": event,
        }

    def summary(self):
        return list(self.groups.values())
