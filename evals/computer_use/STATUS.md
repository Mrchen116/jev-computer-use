# Latest update: 2026-09-23

R15: MiniWoB 9/9, $1.048699 / 374.28 s; historical native 9/9,
$2.216530 / 608.30 s. The numerical cost target is exceeded, but CLI-version drift
prevents strict matched acceptance. Four separate real-web tasks passed but were
12.3% slower with only 7.9% savings; one used host screenshots. Realtime 12/12,
1.21–1.52 s reactions. See [full results](MINIWOB-RUNTIME.md).
The dated milestones below are retained historical records.

# Development status — 2026-09-22

The current default is the general task protocol, not the older web-stage
executor. Its cost and completion target is **not met**. The suite has four
read-only public website cases plus a realtime local game. Historical results
below must not be presented as measurements of the current default.

## Current checkpoint

The subsequent frozen general batch passed **5/8**, taking **1828.22 s** with
known cost **at least $5.21881**, versus the reused native baseline's **8/8,
902.37 s, $3.37106**. The total price remains unknown because three runs timed
out. See [the current report](GENERAL-RESULTS.md) and
[full comparison data](general-comparison.json). No cost advantage is established.

The first complete general-protocol batch passed all 8 answer checks, but took
1428.22 s versus the reused native baseline's 902.37 s. Its known cost alone was
$4.97719 versus $3.37106; two Jev requests lacked billing data, so total cost is
unknown. One navigation also left its granted public-site prefixes: answer
correctness does not establish constraint compliance. See
[the development comparison](general-development-comparison.json).

Follow-up development records, including interrupted and timed-out attempts,
remain in [general-development.json](general-development.json). Only the Jev
arm is being rerun; the historical Sol/medium baseline and the failed native
realtime attempt are reused as requested. Project protocol tests establish
behavior, not task success or savings.

After the frozen batch, repeated focusing of an already focused field was removed,
and scope observation waits were bounded at 30 s without replaying navigation.
The targeted research reproduction passed at 286.51 s / $0.74978, still worse
than its native baseline. The same revised general runner passed two realtime
games at 12/12 each, with 2.25–3.82 s reactions. See the current report above;
none of these repairs establishes the full web target. Current checks: 92 project
and 10 evaluator tests passed.

## Historical web-stage checkpoint

The [multisite frozen comparison](multisite-frozen.json), seeds **211/257**,
passed **8/8 for both arms**. Native total: **$3.37106 / 902.37 s**; hybrid:
**$1.40768 / 858.25 s**. Savings are **58.2%**, with **4.9% less total time**.
The predetermined 50% cost target is met. Source hashes and telemetry match;
all 16 final answers and tool inventories were reviewed. The latest-issue
reference was rechecked and had not changed. No copied auth files remained.

The evaluated revision allows several authorized URL prefixes and exact
known destinations in one collection stage. This addresses a structural handoff
at every domain change while retaining host verification. It adds no site-specific
routes or completion predicates. **72 project tests and 9 evaluator tests pass**.
The [hybrid-only diagnostic](multisite-development.json) passed both selected cases:
three-source research **75.85 s / $0.10385** and portfolio lookup **38.37 s /
$0.08683**. Each used one delegated stage and three outer Sol requests. Source
hashes and token accounting matched; both final answers were reviewed against
the returned original passages. This diagnostic is not a paired savings claim.

The same frozen runtime also passed two [hybrid-only realtime game runs](realtime-final.json):
both **12/12**, no misses or wrong tools, reaction times **1.50–2.27 s** under
four-second deadlines. Complete task times were **57.43 / 57.24 s**, costs
**$0.07786 / $0.07745**. The host chose realtime mode, 150 / 100 ms minimum
periods and no extra target recheck. Native realtime gameplay was not rerun,
as requested; its historical failure and unknown final billing remain separate.

## Earlier iterations

The [text-recovery frozen comparison](text-recovery-frozen.json), seeds **101/137**,
passed **8/8 for both arms**. Native total: **$3.62603 / 947.35 s**; hybrid:
**$1.93365 / 1072.25 s**. It saved **46.7%** but was **13.2% slower**, missing the
50% target. Source hashes and telemetry matched before subsequent edits. All 16
answers and tool inventories were reviewed, and no copied auth files remained.

The subsequent [input-options frozen comparison](input-options-frozen.json), seeds
61 and 83, also **missed the target**: native **8/8**, hybrid **7/8**. One hybrid
issue attempt timed out after speculative screenshot/drag hover recovery. Total
hybrid billing is incomplete and aggregate savings are **unknown**, not computed
by excluding the failure. Native total: **$3.86481 / 965.55 s**; hybrid total time:
**1205.88 s**. The first repetition alone saved 47.3% but was 6.7% slower; it is not
substituted for the full result. All source hashes matched when the report was made.

The text-recovery revision changed generic host guidance only: keep textual recovery
text-based, avoid unavailable hover and speculative native methods, reuse observed
source URLs unless a deeper permalink was explicitly requested, and let the host
substitute user parameters into collected general syntax/examples. Runtime and
case criteria were unchanged. Its prospective paired run used seeds **101/137**;
the completed result is reported above.


The first frozen two-repetition comparison is complete. Both arms passed **8/8**
public-web attempts. Verified API-equivalent totals: native **$3.47927 / 824.19 s**,
hybrid **$2.82414 / 983.13 s**. Hybrid saved **18.8%** but took **19.3% longer**.
The 50% engineering target is **not met**. All source hashes and telemetry matched
when [collection-frozen.json](collection-frozen.json) was generated, before edits.

| Case | Native mean USD | Hybrid mean USD | Saving | Native mean time | Hybrid mean time |
| --- | ---: | ---: | ---: | ---: | ---: |
| Public portfolio | $0.19860 | $0.10604 | 46.6% | 42.54 s | 47.73 s |
| Latest GitHub issue | $0.67593 | $0.96114 | −42.2% | 164.42 s | 225.99 s |
| Official documentation | $0.35776 | $0.12777 | 64.3% | 98.79 s | 85.08 s |
| Three-source research | $0.50734 | $0.21711 | 57.2% | 106.34 s | 132.77 s |

The next revision addresses two reproduced generic failures:

- Native address assignment could accept Chrome history completion, then decisions
  could run against the previous web area. Address navigation now uses native
  paste, verifies the displayed URL, and waits for the requested web area without
  repeating the navigation action. A real zero-model probe switched between list
  and detail pages six times; all six final observations matched their targets.
- Lexical context selection excluded the needed sentence in a saved 25,460-character
  official document. Jev repeated navigation because it could not read the omitted
  text. All original spans are now reachable through bounded text views; Jev can
  choose `more_text` without a UI mutation. A real API probe selected none from
  the first view and the correct original passage from the second, in 2.154 s
  with 9,393 input tokens. This is not an end-to-end benchmark.

The [real-host follow-up](paging-navigation-followup.json) passed all three selected
cases: research **118.52 s / $0.19359**, issue lookup **246.95 s / $0.57940**,
and the realtime game **58.12 s / $0.07389**. The game achieved **12/12**, zero
misses/wrong tools, reactions **1.60–2.36 s**. Its failed native baseline was not
rerun. This is a hybrid-only diagnostic, not a paired savings claim.

Issue lookup now navigates correctly but still incurs repeated outer-agent calls
for date-filter input variants. The next generic addition lets the host provide
up to eight exact `input_options`; Jev chooses among them, verifies each value,
and submits only when that option explicitly authorizes Return. No website-specific
predicate or generated input is introduced. The first real-host issue follow-up
[timed out at 300 seconds](input-options-development.json), with incomplete total
billing. It is a failure, not a saving: the host's first date batch excluded the
matching date, and Jev repeatedly chose two used candidates. The follow-up revision
makes candidates explicitly single-use within a stage, with code-owned progress.
A saved-request probe showed that explicit remaining-input context prevented a
premature help choice. The [real native follow-up](../../docs/input-options-verification.json)
then tried all seven supplied values, each once, and collected the matching seventh
result: **22.315 s**, eight Jev decisions, **$0.00224 Jev-only**. No outer LLM was
metered in that isolated probe; it is not a whole-task savings claim.

That revision passed **66 project tests + 9 evaluator tests**, lint and diff checks.
Its frozen comparison used seeds **61 and 83**, the same four real-web cases,
alternating arms, 16 total runs. Its source archive and raw runs remain private;
the failure and incomplete billing are reported above.

Earlier follow-up diagnostics are in [collection-followup.json](collection-followup.json):
documentation **122.82 s / $0.20083**, newest issue **172.20 s / $0.72055**, both passed.
The locked-screen setup failure started no model task and remains recorded.

The unified Skill now uses the agreed **sequential cycle**. The host selects
`step` or `realtime`, sets `period_ms`, and chooses whether to recheck the selected
target. There is no separate observer or decision-age expiry. Changed page text
and slow decisions produce aggregated warnings instead of discarding valid
choices. Current and historical evidence is in
[control-verification.json](../../docs/control-verification.json).

Earlier sequential-cycle development verification:

- Real Sol/medium selected realtime with a 100 ms requested period and target
  rechecking disabled. It achieved **12/12 rescues, zero misses and zero wrong
  tools**: 79.31 s for the complete outer run, API-equivalent $0.11271; the stage
  took 31.2 s. Actual reactions were 1.75–2.43 s. All 14 decisions exceeded the
  requested period, so one warning group reports count 14; the game continued.
- Step mode found AudioInput on the actual public portfolio: 34.68 s, $0.10856,
  independently passed. This task was already answerable from the first page;
  it does not demonstrate savings from many delegated clicks.
- A real external CLI control smoke read concise progress and a slow-decision
  warning while Jev was deciding. It requested stop, verified the pending action
  did not execute (action count stayed at 1), then switched to step and recovered
  earlier evidence. This smoke did not meter an outer LLM.
- Public GitHub exposed native URL attributes elided as `…`. The parser now uses
  the unfocused browser address as observed metadata while excluding browser
  chrome and page-owned fields from the action scope. The original issue run
  completed via outer recovery at 256.76 s / $1.16519. An affected documentation
  run was interrupted for repair, with unknown total billing. Both are retained.
- After URL repair, the issue task passed at 237.27 s / $0.94569. Repeated host
  interventions to verify the exact creation date remain costly. Completion is
  not evidence that the price target has been met.
- At that earlier checkpoint: 43 project tests, 9 evaluator tests and Skill validation passed.
  The completed paired pilot is recorded below.

Earlier independent-observer pilots (including the 11/12 game and 64.61 s
portfolio result) remain in the evidence file with their own revision labels.
They do not validate the current sequential implementation. The earlier SSL
failure has an unmetered request; its total USD remains unknown.

## Resumed collection iteration

The user resumed implementation. The current candidate adds named original-passage
collection, persistent per-stage coverage, focused Return/Escape, control paging,
explicit input requests and native address-bar navigation for host-supplied URLs.
Long Jev context is retrieved into bounded shared passages; full observations stay
archived. The collection pilot revision passed fifty project tests and nine evaluator tests.

Development attempts (including HTTP 400 failures with unknown total billing) are
retained in [collection-development.json](collection-development.json). A saved
public-document API probe recovered six requested facts in 1.096 seconds with
6,431 input tokens; it is not an end-to-end benchmark. The paired collection pilot is complete: both arms passed 4/4 real-site tasks.
[Sanitized report](collection-pilot.json), with matching source hashes and verified
telemetry. It is one development repetition, not final validation.

| Case | Native time | Hybrid time | Native USD | Hybrid USD | Hybrid cost saving |
| --- | ---: | ---: | ---: | ---: | ---: |
| Official documentation | 103.15 s | 107.31 s | $0.51279 | $0.26871 | 47.6% |
| Three-source research | 95.36 s | 66.05 s | $0.71685 | $0.15943 | 77.8% |
| Public portfolio | 27.76 s | 45.21 s | $0.13230 | $0.14041 | −6.1% |
| Latest GitHub issue | 141.33 s | 164.48 s | $0.73615 | $0.78093 | −6.1% |
| **Total** | **367.61 s** | **383.05 s** | **$2.09809** | **$1.34949** | **35.7%** |

Hybrid was 4.2% slower overall; the 50% target remains unmet. Multi-source research
used five Sol requests versus fifteen natively. Documentation collected all six
facts in its first 12.2-second stage, but the host made redundant citation-anchor
visits. In the issue case, a filled query was collected as if it were submitted;
the host detected the stale results and recovered. The next generic revision
adds explicit host-authorized prepared-field submission before collection, and a
compact handoff reminder to verify passages and reuse their observed source URLs.

## Previous sequential pilot and pause checkpoint

The same source/prompt snapshot ran four public-web cases through fresh
Sol/medium sessions in each arm. Source hashes, model/effort and token-cost
telemetry verified. All eight attempts passed the independent judge; final
answers were inspected. This is one repetition, not a statistical success-rate
claim. [Sanitized report](sequential-pilot.json).

| Case | Native time | Hybrid time | Native USD | Hybrid USD | Hybrid cost saving |
| --- | ---: | ---: | ---: | ---: | ---: |
| Official documentation | 118.35 s | 136.10 s | $0.49194 | $0.30614 | 37.8% |
| Three-source research | 102.54 s | 169.46 s | $0.54339 | $0.40866 | 24.8% |
| Public portfolio | 45.24 s | 51.40 s | $0.20028 | $0.13365 | 33.3% |
| Latest GitHub issue | 106.73 s | 187.53 s | $0.69687 | $0.96967 | −39.1% |
| **Total** | **372.86 s** | **544.48 s** | **$1.93248** | **$1.81812** | **5.9%** |

Both arms completed 4/4. Hybrid was 46.0% slower overall. The 50% cost target is
**not met**. The issue task still triggers expensive host recovery and date
verification; its regression must not be hidden by the other three savings.
The historical native game failure was not rerun and is excluded from this
fully metered web-cost aggregate.

Current code preserves repeated text across sections and meaningful container
labels, returns bounded page previews, and exposes literal-query/range reads of
saved original evidence. This fixed a reproduced loss of method parameters and
removed tool-output truncation as a reason to reopen whole pages. The latest
checks pass 43 project tests, 9 evaluator tests and Skill validation. A copied
Skill also read evidence under Python with environment/site packages disabled,
without pip installation or credentials.

This earlier batch was paused at the user's request; work has since resumed as
described above.
All evaluation processes exited and temporary copied auth files were removed.
On resumption, inspect the latest-issue handoffs and remaining host-context cost,
make only generic changes, then continue controlled repetitions. Do not rerun
the failed native realtime game. No performance target is declared achieved.

## Real-time correction and latest outcome

The original game waited indefinitely for answers, so its success rates did not
measure real-time ability. The replacement **Rescue Dispatch** advances on the
server clock, with a four-second deadline per request and at least 10/12 timely
correct rescues required. Late clicks cannot score on expired requests.

- A live Jev stage invoked through the ordinary Skill script achieved **12/12,
  zero missed deadlines, zero wrong tools**, in 31.171 seconds including binding
  and checkpoint. Individual reactions were 1.97–2.68 seconds. This smoke did not
  measure an outer Sol session, so it is not a full hybrid USD result.
- Native **Sol medium + CUA failed this attempt**. It generated a rapid loop that
  misclassified a browser profile control as a game control, opened an account
  page, and failed to recover. The operator stopped it. Recorded actions contain
  no account submission or modification. The final game score and complete cost
  were not captured; neither is fabricated as zero. This supports an observed
  end-to-end failure, not a latency-only causal claim or a claim about all LLMs.
- Hybrid v2 completed four of the original five cases but omitted Language in
  the form, then falsely reported success. The independent judge caught it.
  The parser dropped multiline receipt text; that bug is fixed and regression
  tested. The stage guide now requires checking individual preferences before
  final submission. These changes still need full live validation.
- Recent actions now retain their source URL, so identical controls on different
  pages are not presented to Jev as if they were the same completed action.

[Game source research](../../docs/game-references.md) explains why paused emulator
and game-memory demonstrations cannot substitute for this UI timing test.

All figures below are from actual Sol/medium, Jev and native CUA executions.
USD is API-equivalent cost using real provider token telemetry, including prompt
cache and all outer-host calls. The raw sanitized measurements are in
[development-results.json](development-results.json).

| Same-seed comparable case | Native time | Hybrid v1 time | Native USD | Hybrid v1 USD | Cost change | Completion |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Semantic game | 93.83 s | 70.68 s | $0.35294 | $0.15175 | −57.0% | Both 12/12 correct |
| Multi-step form | 75.78 s | 58.25 s | $0.20602 | $0.13953 | −32.3% | Both passed |
| Project/newest issue | 43.39 s | 61.09 s | $0.11592 | $0.16601 | +43.2% | Both passed |

Game reaction time was about 4–8 seconds per round natively and about 2 seconds
with Jev. This is a text-accessible semantic game, not a pixel-action/FPS test.

Other development outcomes:

- Research hybrid v1 read all five sources, shortlisted exactly the three matching
  apps, and returned their correct prices, notes and URLs: 103.20 s, $0.15723.
  Its native baseline was interrupted by screen lock; its lower unfinished cost
  must not be compared as if it had completed the task.
- The first catalog variant used a simulated “Reserve” button. Sol requested
  confirmation and did not complete it. Both arms' final case was revised to a
  local comparison tray, retaining filtering and lowest-price selection without
  reservation semantics. The revised native case passed in 53.10 s, $0.16865.
- The unavailable in-app-browser attempt and a delegate-tool approval setup
  failure are retained as infrastructure diagnostics. The aborted setup attempt
  has incomplete billing telemetry, not zero cost.

Changes prepared for the next live iteration:

1. Let the host delegate directly when app and scope are already known, avoiding
   an unnecessary full native documentation/UI read before every delegation.
2. Keep comparison and global coverage decisions with the outer host. Return
   compact, fresh native evidence instead of every execution telemetry event.
3. Retain visited sources and expose `read_evidence`, so verification can recover
   an earlier issue list without navigating backward through the UI.
4. Give Jev the visited-source inventory as well as selected captures, preventing
   rejected sources from being forgotten during multi-page collection.
5. Support both the plain Skill script and persistent MCP through the same stage
   engine. No nested text LLM is started.

The current offline suite passes 43 project tests and nine evaluator
tests; Skill validation and Python lint checks pass. These checks do not replace
the outstanding real UI comparison. No frozen-result cost advantage or general
task-success claim is made yet.

Remaining work: finish development with seed 7, then
freeze source/prompt hashes and run paired seeds 19 and 43 with alternating arm
order. The [protocol](PROTOCOL.md) requires at least 50% aggregate savings and all
hybrid attempts passing before declaring the engineering target met.
