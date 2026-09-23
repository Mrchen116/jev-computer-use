# MiniWoB++ multi-step subset

This is a native-accessibility, relaxed-deadline evaluation of the general Jev
Skill, with Sol/medium as its outer agent. It is **not** the standard MiniWoB++
leaderboard protocol. The initial phase ran only the hybrid arm. A subsequent
user-requested native Sol/medium comparison used the same tasks, seeds and timing.
The latest R15 batch completed 9/9 with full metering: 52.7% lower cost and 38.5%
less time than the historical native baseline. CLI-version drift prevents strict
matched acceptance. Real-web results are weaker and separately reported. See
[the runtime follow-up](MINIWOB-RUNTIME.md); earlier simplification failures remain
in [their original report](MINIWOB-SLIM-SKILL.md).

Use the [official Farama source](https://github.com/Farama-Foundation/miniwob-plusplus)
at commit `33c3b4ddef8c6eb67c57a29663d844b1eda7e614`. The benchmark adapter serves its
original HTML, CSS and JavaScript, with a generic instrumentation script appended.
Task generation, control labels, layout and official reward functions are unchanged.
The script sets `Math.seedrandom(String(seed))`, sets a 300-second episode deadline,
and records episode starts, native UI events and the original `core.endEpisode`
result through a private local evaluator endpoint. It supplies no answers or
task-specific shortcuts. The candidate cannot read source, DOM or that endpoint.

| Task | Minimum meaningful operations | Coverage | Original deadline |
| --- | ---: | --- | ---: |
| `click-checkboxes-large` | 6 | Select 5–12 named checkboxes, then submit | 20 s |
| `multi-layouts` | 4 | Fill three fields in a random layout, then submit | 20 s |
| `book-flight` | 5 | Fill origin, destination and date, search, choose a flight | 30 s |

These are lower bounds; focus, autocomplete and scrolling may add actions. Opening
the page, reading it and clicking START are not counted toward these lower bounds.
The selected tasks avoid requiring screenshot-based perception. No task-specific
behavior is added to the Jev runner. Seeds 11 and 22 are fixed before candidate runs.
Development follow-ups used additional seeds 33 and 44, selected before inspecting
their generated questions. Both runs retained a failure on a development seed.
The continuation-check follow-up completed six attempts on 11/22 before a setup
failure prevented seed 55 from running. The latest field-context/input-contract
candidate was frozen for all nine attempts on **11/22/66**; seed 66 was previously
uninspected at that R06 milestone. Native and routing-repair follow-ups reused all
three seeds; those follow-ups are not new held-out trials. Additional seeds are reported separately. All earlier reports remain
published; a later pass does not erase a failed attempt or make reused seeds independent.

As in upstream `SeleniumInstance.begin_task`, reset starts the episode before the
candidate runs. Our harness clicks START through native CUA and supplies the
public instruction verified in native AX; it does not give answers or UI routes.
The candidate follows that on-page instruction. A successful
attempt requires exactly one started and terminated episode whose **official raw
reward equals 1.0**. Partial positive reward, model claims, and successful retries
after a failed first episode do not count. The time-discounted reward is retained
separately. All trials, including failures, belong in the report.

The outer-agent wall limit is 300 seconds, including initialization, handoffs,
actions and final response. It starts before launching Codex; the separate episode
clock starts on the harness's START click. Setup time is excluded and recorded. This experiment
measures multi-step completion under a relaxed deadline, not original-deadline
real-time performance. Input, cached input and output token usage are recorded for
Sol and Jev and priced using the frozen rates in [PROTOCOL.md](PROTOCOL.md).

Before the scored run, an independent native-UI smoke check on seed 999 must
verify both an intentionally wrong submission and a correct submission against
the official reward. These checks are harness validation, not model results.

```sh
git clone https://github.com/Farama-Foundation/miniwob-plusplus /tmp/miniwob-plusplus
git -C /tmp/miniwob-plusplus checkout 33c3b4ddef8c6eb67c57a29663d844b1eda7e614
python3 evals/computer_use/run.py --suite miniwob --protocol general \
  --miniwob-root /tmp/miniwob-plusplus --miniwob-deadline 300 \
  --cases click-checkboxes-large multi-layouts book-flight --seeds 11 22 66 \
  --arms hybrid --key-file /private/jev-key --timeout 300 \
  --output /private/miniwob-run
```

For a fresh paired suite use `--arms baseline hybrid`. To compare a separately
run native baseline, export the hybrid run with `miniwob_report.py` and use
`compare_miniwob.py NATIVE_RUN --hybrid-report REPORT.json --output COMPARISON.json`.
Archive the source tree before each run; the comparer accepts
`--native-source-archive` and `--hybrid-source-archive` to verify frozen versions
after a treatment change. It requires matching generated instructions and shared
execution sources, while recording treatment-only changes. Native parsing and
deterministic UI batching are allowed, with no imposed per-click LLM requirement.

Run directories retain a source-hash manifest, actual model/effort and token usage,
complete private native/decision traces and official episode telemetry. The public
report contains sanitized measurements only. Chrome windows are dedicated to the
local benchmark; no personal account, mailbox, purchase or OS configuration is used.
