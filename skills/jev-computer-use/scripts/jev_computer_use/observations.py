"""Compact model views and exact, read-only access to retained observations."""

import hashlib
import json
from pathlib import Path
import re

from .desktop import ROLE, ROLE_NAMES


UI_FORMAT = (
    "One leading space is one tree level. Plain lines are static text; 'group' "
    "marks a container. Static text/container IDs are omitted. All text, values, "
    "states, order and nesting remain. Other nodes retain native IDs and roles."
)


def compact_ui(raw):
    """Remove serialization overhead, never select content by task relevance."""
    lines = []
    for line in raw.split("\n"):
        match = re.match(r"^(\t*)(\d+) (.*)$", line)
        if not match:
            # Continuations, space-indented formats and unfamiliar lines remain
            # verbatim. In particular, do not strip indentation inside text.
            lines.append(line)
            continue
        indent, ref, rest = match.groups()
        role = ROLE.match(rest)
        kind = ROLE_NAMES[role[1].lower()] if role else None
        if kind == "container":
            rest = "group" + role[2]
        elif kind == "text":
            rest = role[2][1:] if role[2].startswith(" ") else role[2]
        else:
            rest = ref + " " + rest
        lines.append(" " * len(indent) + rest)
    return "\n".join(lines)


def observation_id(observation):
    """Identify an exact saved screen independently of rechecks and step numbers."""
    identity = json.dumps([observation["application"], observation["ui_tree"]], ensure_ascii=False)
    return hashlib.sha256(identity.encode()).hexdigest()[:16]


def observation_index(records):
    """List distinct screens in encounter order, including exact read handles."""
    index = {}
    for record in records:
        if record["kind"] != "observation":
            continue
        obs = record["observation"]
        ident = observation_id(obs)
        if ident not in index:
            index[ident] = {"observation_id": ident, "step": record["next_step"],
                            "application": obs["application"], "window": obs["window"],
                            "chars": len(obs["ui_tree"])}
    return list(index.values())


def read_task_history(state_dir, step=None, kind="observation", offset=0,
                      max_chars=6000, contains=None, context_lines=8,
                      observation_ids=None):
    """Read exact saved screens, optionally batching literal searches over them."""
    records = [json.loads(line) for line in (Path(state_dir) / "history.jsonl").read_text().splitlines()]
    if observation_ids is not None and (kind != "observation" or step is not None or
            not isinstance(observation_ids, list) or not observation_ids or
            not all(isinstance(ident, str) for ident in observation_ids)):
        raise ValueError("Use observation_ids for observation reads, without step")
    if step is None and not contains and not observation_ids:
        return {"observations": observation_index(records)}
    if contains is not None and (kind != "observation" or not isinstance(contains, list) or
            not contains or not all(isinstance(term, str) and term for term in contains)):
        raise ValueError("contains must be nonempty literal terms for observation search")
    selected = [r for r in records if (kind == "all" or r["kind"] == kind) and (step is None or
        r.get("step", r.get("event", {}).get("step")) == step or
        r["kind"] == "observation" and r.get("next_step") in (step, step + 1))]
    if kind != "observation":
        text = json.dumps(selected, ensure_ascii=False, indent=2)
        metadata = {}
    else:
        # A step always means one latest snapshot, with or without search. Exact
        # IDs allow several screens in one read without near-duplicate rechecks.
        if step is not None:
            selected = selected[-1:]
        unique = {observation_id(r["observation"]): r for r in selected}
        if observation_ids:
            missing = set(observation_ids) - unique.keys()
            if missing:
                raise ValueError("Unknown observation IDs: " + ", ".join(sorted(missing)))
            unique = {ident: unique[ident] for ident in dict.fromkeys(observation_ids)}
        parts, sources, found = [], [], set()
        radius = max(0, min(context_lines, 40))
        for ident, record in unique.items():
            obs = record["observation"]
            lines = obs["ui_tree"].splitlines()
            spans = []
            if contains:
                for i, line in enumerate(lines):
                    hits = [term for term in contains if term.casefold() in line.casefold()]
                    found.update(hits)
                    if hits:
                        start, end = max(0, i - radius), min(len(lines), i + radius + 1)
                        if spans and start <= spans[-1][1]:
                            spans[-1][1] = max(spans[-1][1], end)
                        else:
                            spans.append([start, end])
            else:
                spans = [[0, len(lines)]]
            sources.append({"observation_id": ident, "step": record["next_step"],
                            "application": obs["application"], "window": obs["window"],
                            "observed_at": obs.get("observed_at"), "matched_ranges": len(spans)})
            if spans:
                parts.append(f"OBSERVATION {ident} | {obs['window']}")
                for start, end in spans:
                    parts.append(f"LINES {start + 1}-{end}\n" + "\n".join(lines[start:end]))
        # Plain source text, not a pretty-printed JSON document inside JSON.
        # Continuations slice text only; response metadata always remains valid.
        text = "\n\n".join(parts)
        metadata = {"sources": sources, "missing_terms": [term for term in (contains or []) if term not in found]}
    size = max(500, min(max_chars, 20000))
    start = max(0, offset)
    end = start + size
    return {"step": step, "kind": kind, **metadata, "text": text[start:end],
            "total_chars": len(text), "next_offset": end if end < len(text) else None}
