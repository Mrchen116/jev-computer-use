> Historical web-stage protocol, retained for reproducing earlier benchmarks. The default Skill now uses [the general task protocol](tasks.md).

# Delegate a stage

The calling agent owns planning, text generation and final verification. The runner
uses Jev and native CUA directly; it starts no text LLM. Choose stages with several
related actions, and pass only the local goal and relevant known facts. Prefer
simple English for Jev instructions (its strongest language); preserve actual UI
labels and original source text in their original language.

## Execute

Call `delegate_stage` or write the same JSON for the Skill CLI:

```sh
python3 SKILL_ROOT/scripts/run.py stage --request-file /private/stage.json \
  --state-dir /private/task-evidence --key-file /private/typesafe-key
```

Required: `app`, `mode`, `goal`, `yield_when`. For web work supply
`allowed_url_prefix` (one prefix or a list of up to eight) to exclude browser
chrome and constrain navigation. If the
app and scope are known, delegate directly: the runner binds and observes it.
For a different site, pass `open_url` with a user-provided or previously observed
URL inside that scope. The runner uses the observed native address field; merely
mentioning a URL in `goal` does not navigate there. Omit `state_dir` for ordinary
MCP calls: the server already retains evidence in its private default directory.
Address navigation uses native paste to avoid inline history completion, verifies
the actual value, and waits for the target web area. Unverified navigation yields
an error for inspection; it is not silently replayed.

Batch related collection across authorized sites in one stage rather than returning
to the host at each domain change. Put all authorized prefixes in
`allowed_url_prefix`. For known but unlinked destinations, supply `destinations`
with up to eight exact user-provided or previously observed URLs. Jev can choose
these URLs through the same verified native navigation and retain collection
progress. Observed links can also cross the supplied scopes. Do not guess a deep
route or authorize an unrelated site. Returning outside every allowed prefix
yields a scope boundary for host inspection.

All controls, including later batches, remain accessible. It can click, scroll,
fill prepared text, press Return or Escape with observed focus inside the page,
and wait. Long text is also pageable: `more_text` reads additional original
passages without clicking or scrolling. Lexical ranking chooses the first view;
it does not make the rest of a document inaccessible. Image-only controls and
held keys are unsupported.

Use `mode: "step"` for navigation and forms; `"realtime"` for independently
changing state. Both run sequentially: observe → Jev → execute → observe result.
Realtime `period_ms` (100–30000, default 1000) sets minimum cycle-start spacing;
slow cycles do not queue catch-up ticks. The host chooses `recheck_target`
(default true) for one extra pre-action read. False saves a read where the host
accepts that tradeoff. Changed page text and slow decisions cause warnings, not
automatic expiry. An unavailable checked target is skipped; uncertain mutations
are not replayed. Briefly missing web areas during navigation are re-observed.

## Collect original evidence

For research, supply `collect`: up to eight named requirements describing the
specific original evidence this stage should bring back. Example:

```json
{
  "app": "com.google.Chrome",
  "mode": "step",
  "allowed_url_prefix": "https://example.org/manual/",
  "goal": "Find the official setup and single-file usage instructions.",
  "yield_when": "Return the requested source passages, or ask for missing input.",
  "collect": {
    "setup": "The command to install this tool using pip",
    "usage": "The syntax for running this tool on a single file"
  },
  "max_steps": 20
}
```

For a bounded comparison involving several sites, combine their requirements
(up to eight total) in the same `collect` request. Name the subject and required
source in each item, for example `"alpha_install": "Alpha's official pip install
command from docs.alpha.example"`. Supply the official entry URLs as destinations
when known. The host verifies every item and source after this batch; it need not
intervene merely because Jev moved to another authorized domain.

Jev selects verbatim passages from current observations. The runner records their
source IDs, URLs and offsets, and shows Jev which items remain across navigation.
`collection_ready` means candidate passages exist for all requested items and
control has returned to you. It is **not** verified coverage or task completion.
Read each `collected` item's `passage` reference in the shared `passages` map;
identical original text is returned once. Check it against each requirement. Correct missing
or unsupported items with a targeted follow-up; do not ask Jev to rediscover
already verified evidence. Ordinary stages can instead use `capture_when` to
retain matching pages without a fixed evidence checklist.

For parameterized tasks, collect the general syntax or an existing official
example. Apply the user's filenames, paths or other parameters in the host; do not
ask Jev to find a verbatim example containing a user-specific value.

Keep global comparisons, ranking and sufficiency decisions with the host. For
example, collect a filtered ordered list, verify the ordering and exclusions, then
delegate visiting the selected entries. State the literal evidence to extract,
not a compound conclusion to prove. Supply exact search/filter text through
`prepared_text` once the field is observed, then let Jev submit and continue.
For a search/filter that requires Return, also set `submit_field` to that exact
field label. The runner verifies the value and submits it once before Jev can
select evidence. This avoids mistaking a filled query for applied results.
Give a bounded batch of collection items;
do not ask Jev to decide whether an open-ended investigation is complete.

Returned passages are observed text, not generated summaries. They usually contain
what you need to answer. `current_page` is only a preview (2000 characters when
passages are returned, otherwise 6000). Missing text in a preview is not evidence
of absence. `current_source_id`, `visited_pages` and capture IDs reference the
saved full observations. `read_evidence` accepts `source_ids`, a literal `query`,
`offset`, and `max_chars` (500–12000, default 6000); it uses no UI or model calls.
The CLI equivalent is `stage --evidence s1 --query "phrase" --max-chars 3000`.
For ordinary citations, use the returned source-page URL in the final answer.
Do not navigate merely to obtain a deeper anchor unless the user explicitly asks
for a section-specific permalink. A source URL plus its original passage is
sufficient evidence; a more specific fragment is not an additional fact.

## Input and intervention

`needs_input` returns `input_request` with the exact observed field name. Supply
`prepared_text: {"exact field name": "exact value"}` on the next stage, retaining
the goal and evidence directory. Matching fields are filled together and verified.
Filling alone is not submission. `submit_field` explicitly authorizes one Return
on a verified prepared field; omit it when submission is not intended. Jev can
also choose a visible search button or Return. All text comes from the host;
never invent user data. Check the resulting list, since a submitted query alone
does not prove that new results finished loading.

When several related searches or filters have a known finite set of possible
inputs, supply up to eight `input_options` together instead of taking over for
each variation. Each option contains an observed `field`, exact host-written
`value`, and optional `submit: true` to authorize Return. Jev chooses among them,
verifies the filled value, submits only when authorized, and observes the result
before choosing again. Each candidate is used at most once per stage; code removes
tried candidates from the choices and retains them in context. A new stage can
explicitly supply an input again if it is needed. For example:

```json
"input_options": [
  {"field": "Search", "value": "offline export", "submit": true},
  {"field": "Search", "value": "local backup", "submit": true}
]
```

State the local evidence to seek and when to return; the host still checks the
matching result. Candidates contain no generated text, templates or custom
predicates. Do not also put the same field in `prepared_text`, which would reset
it on the next cycle. An unavailable or ambiguous field is not filled. If none
of the alternatives is suitable, Jev returns for help rather than inventing text.

For forms, use a checkpoint before final save/submit and check each requested
value and selected state. Submit only within the user's authorization, then verify
the resulting receipt. Neither visible options nor requested values prove selection.
Keep this text-accessibility workflow text-based during host recovery too. Do not
take screenshots or use drag to emulate hover for hidden textual facts. The native
app API has no hover method. When a fact is absent from AX text, first use retained
evidence or the observed search/filter interface with host-written input options.
Do not repeatedly probe unsupported actions. If the required evidence is still
unavailable, report the concrete limit rather than claiming success.

Use native CUA or the discovery worker for a supported text operation missing from
the stage vocabulary. On the first native takeover after a stage, read the native
API documentation with `cua.rewriteDocumentation()`; the runner may have consumed
the runtime's initial documentation. Do not guess methods such as `app.help` or
`app.back`. Bind the app once and reuse the binding. Repeated `getApp`
calls return large initial snapshots and invalidate assumptions about old indices.
After a delegated stage changed the UI, get a fresh observation before using a
native control; subsequent native reads can use normal diffs.
Do not reflexively take over after every checkpoint or re-read an entire page when
the returned evidence already answers the question.

## Monitor, stop and switch

Retain a `state_dir` across stages. The CLI works while an MCP stage is pending:

```sh
python3 SKILL_ROOT/scripts/run.py stage --state-dir /private/task-evidence --status
python3 SKILL_ROOT/scripts/run.py stage --state-dir /private/task-evidence --status --wait 20
python3 SKILL_ROOT/scripts/run.py stage --state-dir /private/task-evidence --stop
```

Progress contains mode, goal, phase, elapsed time, current URL, counts, collection
progress, recent actions and grouped warnings. No raw pages or model call is needed.
Inspect on demand; do not poll after every click. If the host cannot inspect files
while an MCP tool runs, use a background shell session for long stages.

Warnings include slow decisions, changed UI, missing targets, execution/input
errors and repeated no-change actions. They do not create extra calls or new stop
rules. Stop drains a pending Jev request for billing and suppresses its action;
it cannot undo a native action already in flight. Await `stopped` or a yielded
stage before any other controller operates the UI. Then change goal, mode or
period in the next request. Stop and await the discovery worker before switching
to a stage. `last-stage.json` and `evidence.json` preserve private detailed evidence.
