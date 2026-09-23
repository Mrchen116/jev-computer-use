# MiniWoB++ general Skill results — 2026-09-22

This records the R06 hybrid milestone. A native baseline was added afterward: see [the matched comparison](MINIWOB-COMPARISON.md).

The R06 frozen candidate completed **9/9** attempts across three task types with real Jev, native Chrome Computer Use, and an outer **Sol/medium** agent. Six attempts (all checkbox and form tasks) required no outer-agent UI actions. This milestone alone is evidence for these interaction patterns, not universal desktop reliability or a cost advantage over native Codex.

**Protocol:** original pinned Farama pages and reward functions; accessibility text only; the deadline is relaxed to **300 seconds**. These results do not measure the original 20–30-second MiniWoB deadlines or establish a standard leaderboard score. See [protocol and reproduction](MINIWOB.md). A native baseline had not yet been run at this milestone.

## R06 frozen run

Seeds 11 and 22 were development seeds. Seed 66 was selected before its generated questions were inspected; the implementation remained frozen for all nine attempts. Success requires the first official raw reward to equal 1.0 and exactly one started/finished episode.

| Task | Completed | Mean end-to-end time | Mean total API-equivalent cost | Attempts without outer UI actions |
| --- | ---: | ---: | ---: | ---: |
| `click-checkboxes-large` | 3/3 | 59.65 s | $0.13175 | 3/3 |
| `multi-layouts` | 3/3 | 57.39 s | $0.16373 | 3/3 |
| `book-flight` | 3/3 | 85.39 s | $0.22205 | 0/3 |

Total: **607.30 seconds / $1.552588**, including **$1.536190 Sol** and **$0.016397 Jev**. Jev executed 72 runner operations; the outer agent made 14 native UI action calls. A host call may batch several actions, so these two counts must not be turned into an action-share percentage.

“Without outer UI actions” still includes Sol planning, prepared inputs, guidance and final verification. Flight tasks used outer UI takeover for date-picker interaction and/or selection after comparing results. Model handoffs are part of the intended hybrid system.

Time covers Codex startup through the final answer; harness setup/cleanup is excluded. Cost uses actual recorded input, cached input and output tokens at the frozen [published rates](PROTOCOL.md#metrics-and-accounting): Sol $4/$0.40/$20 per million ordinary input/cached input/output tokens (cache-write rate $5 when reported); Jev $0.042 input and $0 output. It is API-equivalent cost, not subscription billing. All latest attempts have complete model/usage telemetry, verified source hashes, and no detected forbidden API or screenshot usage.

[Full token-level results and audit](miniwob-field-context-followup.json).

## Generic changes exercised

- Native text nodes can be clicked, covering custom buttons and autocomplete options. Readonly text fields remain clickable but do not offer value assignment.
- Placeholder identity and displayed values of unnamed inputs are retained/verified correctly. Input action options quote the immediately preceding native AX sibling text; they do not infer a label, select by task name, or remove the full interface.
- The host supplies independent exact text values. Missing text does not make a field optional, and Jev must not distribute a combined string among fields.
- The outer agent owns numeric comparison, ranking and synthesis. It supplies a recognizable handoff boundary without predicting a UI route.
- Continuation and action selection are batched in one Jev request. A continuation score below 0.9 yields before execution. This is a heuristic, with a retained real counterexample below.

## Retained failures and development runs

| Run | Completed | Time | Total cost | Main finding |
| --- | ---: | ---: | ---: | --- |
| [R01](miniwob-development.json) | 6/6 | 695.30 s | $1.565947 | START incorrectly included in candidate work; heavy host takeover. Different reset protocol. |
| [R02](miniwob-first-reset.json) | 6/6 | 476.35 s | $1.211755 | Official reset semantics; 2/6 completed without outer UI actions. |
| [R03](miniwob-input-followup.json) | 8/9 | 679.53 s | $1.522406 | Wrong duration comparison, then unintended restart on flight seed 22. |
| [R04](miniwob-boundary-followup.json) | 8/9 | 672.38 s | $1.620722 | Combined prepared string filled into multiple fields, then unintended restarts on form seed 22. |
| [R05](miniwob-continuation-development.json) | 5/6 | 421.19 s | $1.112603 | One value omitted and two fields misfilled on form seed 11; safe handoff after failure. Seed 55 suite setup interrupted before model launch. |
| [R06](miniwob-field-context-followup.json) | 9/9 | 607.30 s | $1.552588 | Field-context/input-contract candidate; 6/9 without outer UI actions. |
| [R07](miniwob-routing-followup.json) | 9/9 | 548.90 s | $1.658808 | Registered-tool routing repair; 6/9 without intermediate LLM/UI actions. [Native comparison](MINIWOB-COMPARISON.md). |

R05 contains six scored attempts and explicitly records three unrun seed-55 cases. Its setup failed while a Chrome password-warning dialog was in the foreground; the onset/cause was not established. The observed Close button was used, without changing settings. No unrun case is counted as a success. Development runs reuse tasks and seeds; they are not independent samples and must not be pooled into a general success-rate claim.

### Stopping remains imperfect

A fresh native failure probe intentionally submitted an incomplete checkbox episode before invoking the worker. The worker assigned **0.98 continuation probability**, clicked an AX control obscured by the START overlay, and began another episode. The probe **failed**. Earlier saved-state replays had suggested a useful threshold separation; the fresh UI test disproved any guarantee. The native AX tree can expose obscured controls, and identity/focus rechecking does not detect that occlusion. See [20 real API replays and the failed native probe](miniwob-continuation-diagnostics.json).

The field-context repair was also checked against retained native states using six real Jev calls: the missing-value decision changed from inserting another field’s text to requesting help, while a supplied-value control kept the correct choice. These are diagnostics, not completion trials: [field-context replay](miniwob-field-context-diagnostics.json). Earlier [reasoning-boundary diagnostics](miniwob-boundary-diagnostics.json) are retained too.

### Missing-input handoff verified on the real page

A separate native probe intentionally supplied only the director/year for the
same seed-11 form, leaving the required genre unavailable. Jev focused the Genre
field and returned `help_input` before any submission. The outer Codex agent read
the supplied current UI and provided the literal `drama`. The same worker state
then resumed, completed all fields, submitted once, and stopped with official raw
reward **1.0**. No host UI action was needed after delegation.

This is an integration probe, separate from the nine Sol/medium trials; its wall
time includes human-paced host review, and only Jev usage was metered. It must not
be added to the benchmark completion, latency or total-cost figures. See
[the native handoff/resume record](miniwob-input-handoff.json).

## Scope of the conclusion

The R06 run supports a generic executor for these bounded, text-accessible interaction patterns. It does **not** establish robust termination, arbitrary unknown applications, visual interfaces or realtime game performance. This hybrid-only milestone did not establish savings; the later [matched comparison](MINIWOB-COMPARISON.md) measures the cost and time difference. The previous real-web cost target remains unmet.

Offline validation: **106 project tests**, **15 evaluation tests**, Skill validation and whitespace checks passed. These are separate from the real model/UI results above.
