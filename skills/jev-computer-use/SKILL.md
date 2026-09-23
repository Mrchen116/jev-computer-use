---
name: jev-computer-use
description: Delegate sustained, text-accessible computer interaction to fast System One Jev; keep reasoning, new text and final verification with the calling agent. For multi-step UI work or repeated reactive controls, not single actions or reasoning-heavy tasks. Requires macOS and running Codex desktop with Computer Use installed.
---

# Jev Computer Use

You are System Two; Jev handles stretches of recognizable UI choices. Delegate
navigation, known-value forms and repeated reactive controls. Handle single
operations, comparison, ranking, arithmetic and synthesis yourself. For mixed
work, delegate the interaction and resolve reasoning yourself, including on resume:
give Jev a specific conclusion, never an instruction to perform the comparison.
Resume when a useful interaction stretch remains. No predicted UI plan needed.

## Delegate

If `delegate_task` is not registered, read [setup](references/tasks.md) and use
the CLI route. Otherwise call it through its **registered tool interface**; do not
invent a `functions.exec` wrapper alias. Use a new private `state_dir` per task.
Supply only:

- `task`: the whole goal and **task-specific** constraints, briefly. Code already
  supplies generic interaction, input, authorization and stopping rules to Jev;
  do not restate them as a list of prohibitions or generate a UI script.
- `mode`: `step` for sequential work; `realtime` for an interface changing on its
  own clock. Its cycle is observe → Jev → execute; optional `period_ms` controls
  minimum spacing, not guaranteed latency. It is not a navigation speed boost.
- `input_texts`: **include every already-known field value on the first call**, as
  `{"id":{"text":"literal value","purpose":"what this value is for"}}`.
  Prepare known names, search criteria and destinations from the task without
  waiting to see the fields. Unknown widget types do not make known values unknown.
  Each entry is copied verbatim into one focused field; Jev cannot split, extract,
  rewrite or format it. A combined query is appropriate only when that whole phrase
  is intended for one field. The purpose describes meaning, not a predicted UI ID.
  For “fill name Lin and city Paris”, supply two entries: Lin/name and Paris/city,
  even before seeing their field labels. These are values to enter, **not labels
  of buttons or checkboxes to click**. Use `{}` for click-only work. Leave genuinely
  unknown text for a later handoff; missing text does not make a field optional.

Omit other options unless this task needs them. `guidance` carries your specific
conclusion or an unusual work boundary, not generic reasoning instructions.
The runner supplies the complete current accessibility tree, every concise step,
input texts and warnings to Jev. It uses no screenshots or nested LLM.

## Manage the handoff

Wait for the worker to yield before operating the UI. Read the **current interface
already in its response**; continue through `takeover.js_binding` in the same MCP
native session. Follow `takeover.before_native_ui` only if native actions remain.
Do not rebind, reopen, or read that screen from logs. After your
own UI action, obtain a fresh observation using the supplied native documentation.

- Missing text: supply `input_texts`. Reasoning needed: decide yourself, then act
  or supply the specific conclusion in `guidance`.
- Completion proposed: verify the whole result; a Jev proposal is not proof.
- Uncertainty, capacity, budget or error: inspect the supplied state and reason;
  resolve the cause before resuming. An uncertain operation needs a fresh
  observation before retry; an oversized unchanged screen needs host handling.

Resume the same `state_dir`, omit `task`, choose `mode`, and supply only changes.
Previous inputs/history persist; revised text needs a new ID. Finish a small
remainder directly. Use `read_task_history` only for earlier screens/diagnostics,
preferably batching `observation_ids`. No extra navigation to reconstruct answers.

For setup, CLI execution, progress/stop and optional settings, read
[the reference](references/tasks.md) **only when needed**. Progress includes all
concise steps; full observations stay in private logs. Never run two UI controllers
concurrently. Jev can misjudge stopping or obscured controls; delegation adds no
authorization, and model confidence is not a safety guarantee.
