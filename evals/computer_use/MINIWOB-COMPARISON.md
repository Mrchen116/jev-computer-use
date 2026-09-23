# Native Codex versus the Jev Skill — MiniWoB++

This page retains the R07 comparison. The later [Skill simplification follow-up](MINIWOB-SLIM-SKILL.md)
also completed 9/9, with shorter prompts but incomplete provider billing and longer aggregate time.

The routing-repaired general Skill completed **9/9**, matching native **Sol/medium 9/9** on the same three tasks and seeds 11/22/66. Total API-equivalent cost was **25.2% lower**, and total end-to-end time was **9.8% lower**. The 50% cost-reduction target is **not met**.

This is a small accessibility-only evaluation on original Farama pages with a **300-second deadline**, relaxed from the original 20–30 seconds. It is not standard leaderboard timing or evidence of universal desktop reliability. [Protocol and reproduction](MINIWOB.md).

## R07 matched comparison

| Metric | Native Sol/medium | Sol/medium + Jev, R07 |
| --- | ---: | ---: |
| Completed | 9/9 | 9/9 |
| Total end-to-end time | 608.30 s | 548.90 s |
| Total API-equivalent cost | $2.216530 | $1.658808 |
| Outer LLM requests | 76 | 41 |
| LLM input tokens, including cached | 2,212,591 | 1,212,403 |
| LLM cached input tokens | 1,890,176 | 922,752 |
| LLM output tokens | 8,540 | 5,721 |
| Jev requests | 0 | 82 |
| Jev input / output tokens | 0 / 0 | 397,210 / 52,085 |

The hybrid cost contains **$1.642125 Sol + $0.016683 Jev**. Cost includes task preparation, all handoffs and final verification. Input, cached input and output use the frozen [API-equivalent rates](PROTOCOL.md#metrics-and-accounting), not subscription billing. Reasoning output is already included in output and is not charged twice.

| Task, three seeds each | Native mean time | Jev mean time | Native mean cost | Jev mean cost | Jev cost reduction |
| --- | ---: | ---: | ---: | ---: | ---: |
| `click-checkboxes-large` | 54.98 s | 45.79 s | $0.15052 | $0.11305 | 24.9% |
| `multi-layouts` | 38.33 s | 45.56 s | $0.16630 | $0.12250 | 26.3% |
| `book-flight` | 109.45 s | 91.62 s | $0.42202 | $0.31739 | 24.8% |

All six checkbox/form attempts used exactly two outer LLM requests: delegation with known inputs/guidance, then final review. They needed no intermediate LLM call or outer UI action. For that subset, native cost/time was **$0.950461 / 279.95 s**, versus hybrid **$0.706651 / 274.05 s**: **25.7% cheaper but only 2.1% less time**. Flight tasks used outer takeover; their 29 LLM requests and 19 native UI action calls are included in the totals. A native call can batch several actions, so native call counts and Jev operations are not comparable action counts.

[Complete comparison, source manifests and audit](miniwob-native-comparison.json) · [R07 hybrid measurements](miniwob-routing-followup.json).

## Why no intermediate intervention does not guarantee a faster or cheaper task

The task still pays for its initial outer LLM decision and final review. Jev is about 1% of the latest aggregate cost. Fewer outer requests reduce repeated context, but cached context is priced at one tenth of ordinary input in this experiment. Total LLM input fell 45.2%; ordinary uncached input fell only 10.2%. Request count alone is not a cost measure.

Native Sol can batch visible deterministic actions. On form seed 11, it generated one native call to fill three fields, submit and observe. The hybrid worker instead focused and filled each field, then submitted and reviewed, making eight serial Jev decisions. In R07 these Jev calls took **9.73 s**, and the complete worker took **14.87 s**. End-to-end time was **41.24 s**, versus native **32.73 s**. The remaining time includes outer/provider/startup/transport work; it is not a measurement of pure LLM inference.

On that same form, R07 cost **$0.110743**, including only **$0.001568 Jev**, versus native **$0.156248**. Thus the latest form is cheaper, while the repeated small decisions still cost time. The intended advantage is replacing many sequential LLM decisions; a count of clickable controls alone does not show how many LLM decisions native execution needs.

### Time allocation for the six uninterrupted delegations

Reanalysis of the existing native tool journals gives this per-task mean; no model or UI trial was rerun:

| Cumulative time category | Native | Hybrid |
| --- | ---: | ---: |
| Outside recorded tools: outer agent/provider, startup/exit and dispatch | 44.56 s | 28.60 s |
| Jev API round trips, including network | 0.00 s | 10.48 s |
| Recorded tools excluding Jev: CUA, checks, executor and in-tool transport | 2.10 s | 6.60 s |
| Total | 46.66 s | 45.67 s |

Outside-tool time fell by 15.96 s, while Jev requests added 10.48 s and other tool time increased by 4.50 s, leaving only 0.98 s saved. The 57 Jev API requests averaged **1.10 s**, ranging from **0.79 to 1.58 s**; each task made 8–12 serial requests. These are client round trips, not server-only inference. The outside-tool category is a residual and must not be labeled pure LLM inference. The logs do not separately time each native observation, action or recheck. [All twelve attempts, category definitions and raw-file hashes](miniwob-time-breakdown.json).

A [closer look at Sol first-response latency](MINIWOB-SOL-LATENCY.md) separates startup from model-turn windows. All six R07 initial responses reported zero reasoning tokens; longer delegation output and cold-start/session overhead remain. Existing stderr also contains model-transport and remote-initialization retries that the original result-level infrastructure audit did not classify. They remain included in elapsed time; the comparison is not a network-controlled latency experiment.

## Routing repair and retained previous results

The original R06 comparison completed 9/9 in both arms: native **608.30 s / $2.216530**, hybrid **607.30 s / $1.552588**. R06 was **30.0% cheaper**, with effectively unchanged total time. [Before-repair comparison](miniwob-native-comparison-before-routing.json).

Two R06 form attempts guessed an unavailable wrapper alias for the directly exposed delegation tool. Each failed and then called the correct direct tool. The failed provider requests cost **$0.169028** total, already included in R06 costs. The seed-11 hybrid form cost $0.213692, exceeding its native counterpart despite having no intermediate LLM intervention during the worker's execution.

The Skill entrypoint, tool description and transport reference now direct the host to its registered call interface without inventing an alias. The Jev questions and execution loop were unchanged. In the fresh frozen R07 suite, inspection of actual Codex session records found **10 direct delegations, zero wrapper attempts and zero routing TypeErrors**. The original baseline was reused. [Request-level routing evidence and R07 cost breakdown](miniwob-routing-diagnostics.json).

The complete R07 batch cost more than R06 despite fixing the routing error: flight cost rose from $0.666148 to $0.952157. In flight seed 66, the host performed calendar and airport-autocomplete recovery after handoff, using 16 LLM requests. We retain that cost and elapsed time. Cache hits, host choices and provider latency varied between runs; the aggregate difference cannot be causally assigned entirely to this narrow repair.

## Evidence limits

- Original task queries, seeds, native execution sources, model/effort and rates match. Frozen source archives verify both arms; treatment-only changes are recorded. All attempts have complete usage, official raw reward 1.0, one episode, and no detected forbidden API or screenshot use.
- Baseline and hybrid ran in separate batches. R07 reused development seeds, including seed 66 first evaluated in R06. Nine passes across three task types are not an independent large-sample reliability estimate.
- The earlier [real stopping counterexample](MINIWOB-RESULTS.md#stopping-remains-imperfect) remains unresolved: native AX can expose controls obscured by an overlay, and Jev can confidently continue incorrectly. This repair does not address that failure.
- Earlier real-web cost targets and the failed native realtime game remain separate evidence. The native game was not rerun. These MiniWoB measurements establish neither visual/realtime competence nor general savings across arbitrary applications.

The 20 evaluation tests, Skill validation and publication/whitespace checks passed; the previously completed 106 project tests cover the unchanged execution implementation. Offline checks are separate from the real model/UI trials above.
