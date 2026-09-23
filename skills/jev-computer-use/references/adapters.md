# Custom observations and actions

Use this route when default accessible UI or primitive actions cannot express a
useful interaction stretch. Ordinary UI tasks stay on the default runner.
This is an agent-authored worker workflow, not an implemented adapter option on
`delegate_task`. Native UI handoff bindings and CLI task status are not automatically
available to a separate worker. State this distinction when reporting results.

## Prepare once, then delegate

Inspect the actual application and choose an authorized observation/execution
interface. Prepare only the task-specific code needed:

- Observation: extend the default UI with extra state, or replace it entirely.
  Use meaningful names, consistent units and task-relevant grouping. Read current state without changing
  application resources, rules or clock. A game engine reader may require specific
  integration; it is not universal Canvas perception.
- Actions: extend or replace default controls with a finite map of action IDs to
  descriptions and executable handlers. Rebuild available choices from current
  state when needed. Handlers may perform a short compound action such as selecting
  a plant and clicking a cell. They must not silently decide the ongoing strategy.
- Questions: explain the immediate choice and task-specific priorities briefly.
  State success quality and priorities, not only "finish". Keep option labels
  consistent with them; a generic wait/skip option must not encourage omitting
  required work.
  Prefer complete actions. Batch independent questions only; if location depends
  on a chosen action, include both in one choice or ask sequentially with the first
  answer supplied. Each choice question supports at most 255 alternatives.

Use the bundled `jev_computer_use.models.JevClient` through Python with
`SKILL_ROOT/scripts` on the import path. `ask(payload)` returns `(result, seconds)`;
`close()` releases its connection. Inspect that module if needed. Minimal payload:

```json
{
  "model": "jev-latest",
  "state": {
    "task": "<whole goal>",
    "guidance": "<host priorities>",
    "observation": {},
    "history": [],
    "warnings": []
  },
  "questions": {
    "next_action": {
      "type": "choice",
      "instructions": ["<immediate decision>"],
      "criteria": {"action_id": "<meaning>", "help": "Yield to the host"}
    }
  }
}
```

## Run and manage

Implement observe → Jev → execute with the same mode semantics: `step` proceeds
when the prior action completes; `realtime` has a host-chosen minimum cycle period.
Keep one cycle in flight, warn on overruns and do not pause the application while
waiting for inference. Reuse the execution connection or installed tool; avoid
installer/package-resolution startup inside every cycle. Check the next observation for the action's actual outcome;
record attempted, succeeded, failed or uncertain rather than assuming success.

Retain host cancellation, step/time budgets and explicit help/completion handoffs.
Write compact live progress with current phase, concise step history and outcomes,
warnings, timings, token usage and `history_location`. Store full observations and
responses in private history. On yielding, return the current observation directly
and the live application's identity/connection details so the host can continue
without reopening it. Do not claim a transferable native binding unless one exists.
The host verifies completion and handles reasoning or new text, then resumes only
if a useful interaction stretch remains. Never run both controllers concurrently.

Before sustained use, verify the actual task phase, the reader and one authorized
action against the real application; initialized objects alone do not prove readiness.
Selection shortcuts can toggle off an already selected item; focus,
overlays and resource changes can also turn a valid choice into a failed action.
Make handlers honor actual control state and report their observed outcome. For
compound actions, wait for transitions and check the result before another decision;
yield after repeated non-progress instead of looping on an ineffective action.
For text widgets, verify the value after leaving the field; some require real
keyboard events, not just setting a DOM value.

Optimize from recorded failures: separate observation, decision, execution and
verification time; distinguish poor choices from failed execution. Test dependent
choices as complete actions before adding more strategy prose. Short macros can
combine mechanical preparation with an explicit chosen action, without moving
strategic decisions into code. Repeat bounded real runs after changes, retain
unsuccessful attempts, and record video at normal speed from start through verdict.
Report adapter-specific success separately from default Skill support; rerun a
representative default task when changing shared Skill routing.
