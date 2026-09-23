# Native computer-use cost experiment

For the additional official MiniWoB++ multi-step subset and its deliberately
relaxed time limit, see [MINIWOB.md](MINIWOB.md).

The primary suite has **four read-only public website tasks and one local real-time
game**. Earlier all-synthetic runs remain development evidence and cannot establish
real website performance. Actual Codex, Sol, Jev, Chrome and the installed native
Computer Use runtime execute measured attempts. Offline fake tests are separate.

## Comparison

- Baseline: fresh `codex exec`, `gpt-5.6-sol`, `medium`, standard service tier,
  native `cua_repl.js` and `js_reset` forwarded without changing their schemas,
  descriptions or outputs. Normal AX diffs, screenshots, grounded parsing and
  deterministic batching remain available.
- Hybrid: the same configuration and native tools, plus `delegate_task` and its
  host guidance (`delegate_stage` only for historical `--legacy-stages` runs). The same outer Sol session plans, provides prepared strings,
  handles checkpoints and writes the final answer. The delegate uses Jev plus
  native CUA directly. It does not start another text LLM.
- Both start on the same public entry page, or independently reset game instance, in a
  dedicated Chrome window. Runs are sequential because they share a desktop.
  Arm order alternates by case and repetition.
- The candidate has no shell or web search tool. Source code, server internals,
  hidden browser state, network APIs and the judge are forbidden. Parsing visible
  AX text and batching grounded UI actions are allowed in both arms.
- The harness opens a dedicated window and closes its task tab only if the observed
  URL is still in the task scope. No purchases, messages,
  real profiles, credentials, OS settings or personal-file operations are tasks.

## Five cases

| Case | Required work | Independent success checks |
| --- | --- | --- |
| Public portfolio | Find the macOS voice-input project on mrchen116.github.io | Observed portfolio, AudioInput name, exact GitHub link and relevant description |
| Latest GitHub issue | Find the multi-agent project, then its newest issue including closed issues | Actual issue detail observed; title, number, date and URL match a reference frozen by the evaluator |
| Official documentation | Compare Path.read_text/write_text in Python 3.13 docs | Actual pathlib source observed; parameters, returns and newline-introduction versions reported |
| Multi-source research | Find pip installation and single-file commands for pytest, Ruff and mypy | Each official site observed; all three rows have both correct commands and source links |
| Rescue Dispatch | 12 semantic requests, each expires after 4 real seconds | At least 10 timely correct rescues; misses, wrong tools and reaction time recorded |

Reference data stays outside the candidate workspace. The evaluator freezes the
latest issue from GitHub independently; neither arm can call that API. Other
expected facts are defined in `live_cases.py`. Observed window/web-area roots in
native journals establish page visits, not source URLs merely mentioned in answers.
Manual audit must also check claims and the read-only restriction; passing string
checks alone is not proof of every detail. If a live reference changes during a
pair, report that drift and do not silently judge against inconsistent versions.

For public websites, `--seeds` identifies repetitions; it does not randomize the
website or turn one task into many independent tasks. The game seed changes the
request/control order. Its server clock advances without observations and rejects
late clicks. The four-second deadline and 10/12 pass threshold are identical for
both arms. It tests accessible semantic decisions, not pixel-only arcade FPS.

The host chooses step or realtime per delegated task through the same Skill; the harness
does not select hybrid mode by case name. Baseline native parsing and deterministic
batching remain allowed. Do not slow the baseline to force a desired conclusion.
The already failed native realtime attempt is preserved, with incomplete billing;
at the user's request, it is not rerun in this development session. Report game
completion separately from the fully metered four-web-task paired cost aggregate.

The old unlimited-time game and synthetic form/catalog/lookup/research fixtures
remain available with `--suite synthetic` for diagnosis, not primary evidence.

## Metrics and accounting

Time starts immediately before launching Codex and ends at process exit. It
includes model startup, planning, every tool call, retries, delegation, and final
answer generation. Fixture/window setup and cleanup are outside this interval;
setup is recorded separately for both arms.

Cost is API-equivalent USD, **not an assertion about subscription billing**.
Use Codex's real cumulative `turn.completed.usage` and every Jev response's real
`usage`; never estimate tokens from characters or number of calls. Reasoning
tokens are already included in output tokens and are not charged twice.

Verified on 2026-09-21, prices per million tokens:

| Model | Ordinary input | Cached input | Cache write input | Output |
| --- | ---: | ---: | ---: | ---: |
| Sol, standard short context | $4 | $0.40 | $5 | $20 |
| Jev | $0.042 | — | — | $0 |

Sources: [OpenAI pricing](https://developers.openai.com/api/docs/pricing),
[TypeSafe announcement](https://typesafe.ai/blog/introducing-system-one-models-and-jev).
Record actual model and effort from the Codex session's turn context. Record
Jev's returned model version per API call. These runs must remain below the
long-context pricing threshold; do not apply short-context rates to larger runs.

`USD = ((Sol input - cached - cache writes)*4 + cached*0.40 + cache writes*5
+ Sol output*20 + Jev input*0.042) / 1,000,000`.

Missing token telemetry is **unknown**, not zero. A Jev transport failure with no
usage response makes total cost unknown; `known_usd` is only the metered subtotal. Report incomplete runs and
infrastructure failures; do not turn a failed delegation followed by native
fallback into a successful Jev saving. Preserve failures in development records.

## Iteration and frozen validation

Develop first, then freeze implementation, prompts, reference facts and case
definitions before final paired repetitions. Do not edit during final evaluation.
The intended engineering acceptance target is at least **50% lower aggregate
cost**, no lower observed total completion rate, and no case with a consistent
hybrid failure. For this small final suite the automated gate requires all hybrid
attempts to pass. Publish per-case results as well as aggregate cost so the game
cannot hide regressions elsewhere. Two or three repetitions are a smoke-sized
sample, not a statistically powered non-inferiority study.

Native MCP journals, session logs and prompts are private, outside the repository.
Published results contain sanitized metrics and public/synthetic evidence only; never
publish copied auth files, keys, app inventories or unrelated window contents.

## Reproduce

Requires the installed Codex desktop CUA runtime, Chrome with native accessibility
permission, a logged-in Codex CLI, and a private TypeSafe key file. No dependency
installation is needed for the suite beyond the project Python package.

```sh
python evals/computer_use/run.py --suite live \
  --cases portfolio latest_issue documentation research --seeds 19 43 \
  --key-file /private/typesafe-key \
  --output /private/new-empty-eval-directory
```

The fixture server binds to a random localhost port. The judge runs in its parent
process, outside the candidate workspace. Only this experiment's temporary
configuration preauthorizes `delegate_stage`, restricted to the authorized URL
prefixes for the current public task or exact localhost game scope. It does not alter the user's Codex configuration or permissions.
The Mac must be unlocked. A temporary process-scoped power assertion avoids idle
sleep while the suite runs; it never unlocks the Mac or prevents manual locking.

## Reuse of the frozen native baseline

For the general task protocol, the user requested reuse of the completed native
Sol/medium baseline. Do not rerun that arm for this comparison. Use the same four
web tasks, repetitions 211/257, 300-second timeout, native tools and frozen rates:

```sh
python evals/computer_use/run.py --suite live --protocol general \
  --cases latest_issue documentation research portfolio --arms hybrid --seeds 211 257 \
  --key-file /private/typesafe-key --output /private/new-hybrid-only-run --timeout 300
python evals/computer_use/compare_reused.py /private/new-hybrid-only-run \
  --baseline-report evals/computer_use/multisite-frozen.json \
  --baseline-reference /private/original-baseline/reference.json \
  --output evals/computer_use/general-comparison.json
```

The general arm exposes delegate_task/read_task_history rather than the legacy
stage protocol. Its outer agent remains Sol/medium. Count its complete LLM usage
plus every metered Jev call, including recovery. Reading the task's own retained
observations is allowed; accessing other files or hidden application state is not.
The delegate is constrained to the same dedicated Chrome/public-site grant.

The current handoff candidate registers this MCP namespace as direct model tools
and sets `delegate_task.output_token_limit=60000` in its temporary Codex config.
This prevents the separate Code Mode wrapper budget from cutting out the middle
of a full current interface. It leaves other tool namespaces and the user's Codex
config untouched. Record this integration difference against the historical
baseline, which is not rerun. Verify delivery against model-visible session
records rather than assuming the complete MCP server response reached the model.

Label the result as a comparison against a historical baseline, not simultaneous
paired testing. Verify task definitions, judge/reference facts, model/effort and
prices. Record live-site/environment drift explicitly. The baseline's eight runs
completed at $3.3710568 and 902.3655 seconds. The native realtime game is not rerun.

Interrupted development runs are retained in general-development.json. They have
no complete final billing and cannot establish a savings percentage. If another
user/task changes the active browser away from the authorized test window, stop
and resolve desktop ownership before another measured attempt.
