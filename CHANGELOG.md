# Changelog

## 0.3.0

- Add a non-overwriting Skill installer with optional private key setup, a complete onboarding guide, documentation/evaluation indexes and a CLI fallback when MCP is not registered.

- Reuse Jev HTTPS connections, combine native observation reads, and reuse post-action state in step mode while keeping realtime observations fresh. Never automatically replay a failed inference POST.
- Reconsider clicks when delayed input choices appear during a decision; honor the existing target-recheck switch. Correct HTTP scheme elision in the benchmark-only URL guard.
- Defer native API documentation on final-review handoffs until the outer agent actually needs native actions; keep the complete current UI and existing binding.
- Record R15 MiniWoB 9/9, 52.7% lower cost and 38.5% less time against the historical native baseline, with CLI-version drift explicitly preventing strict acceptance. Retain the real-web regression: 4/4 answers, 7.9% lower cost but 12.3% more time, including one host-vision fallback.

- Shorten the Skill and setup reference; supply generic interaction rules in code. Make known input preparation explicit and gate unresolved reasoning before executing an action, without requiring caller-written generic policies.
- Make the general task protocol the default Skill, CLI and MCP path: whole task, full AX observation, all concise step history, and batched continuation/next-action questions.
- Quote observed sibling text in native input action options, preserve placeholder identity, verify unnamed input values, and avoid value assignment to readonly controls.
- Keep prepared values independent and exact; missing inputs and unresolved numeric comparisons belong to the outer agent. Add native MiniWoB multi-step trials and retain failed development and stopping probes.
- Correct delegation routing guidance to use the registered host tool without inventing a wrapper alias. Retain the R07 matched native Sol/medium comparison: both 9/9, Skill cost 25.2% lower and total time 9.8% lower; the 50% target remained unmet at that milestone.
- Let Jev select exact host-prepared inputs after focus; keep replace, insert and submission separate, with host reasoning/input handoffs and persistent resumption.
- Include every concise step in live status and link full private logs by history_location. Clarify System One task suitability in the Skill.
- Deliver the complete current interface directly on handoff and share the MCP native session/app binding with the host; reserve log reads for earlier screens and diagnostics.
- Retain older web-stage experiments explicitly as historical; their measured savings do not apply to this redesign.

- Batch related evidence across multiple authorized URL scopes and exact known destinations within one delegated stage.
- Preserve the historical web-stage frozen two-repetition real-web comparison: both arms 8/8, 58.2% lower API-equivalent cost and 4.9% less total time; preserve earlier failures and separate realtime game evidence.
- Keep all original page text reachable through bounded text views without UI scrolling.
- Verify native pasted addresses and destination web areas before delegated decisions.
- Let the host provide finite exact input alternatives that Jev can test without per-input LLM handoffs.
- Add named evidence collection with original passage selection, bounded shared context and explicit per-item progress; leave final verification with the host.
- Deduplicate original passages in host handoffs and allow explicit host-authorized prepared-field submission before collection.
- Support host-provided URL navigation through the native address field, focused Return/Escape, later control batches and explicit input requests.
- Measure outer LLM request counts and delegated stage actions as well as end-to-end time, cost and completion.

- Let the host select step or realtime execution per stage, a simple sequential cycle period and an optional target recheck; add aggregated non-blocking warnings, live compact progress, cooperative stop and retained evidence.
- Add bounded stage delegation through either the self-contained Skill script or a persistent MCP server.
- Keep global planning, comparisons, text and completion with the original host agent; batch prepared input values and retain source evidence across checkpoints.
- Recognize elided native page URLs using the observed, unfocused browser address while keeping browser controls outside delegated web scope.
- Bound host page previews and retrieve original evidence by literal query or character range without model calls or UI revisits.
- Preserve repeated text in different sections and meaningful native container labels, including method signatures and timestamps.
- Add four read-only public website cases and a real-time local game for Sol/medium comparison, plus synthetic development fixtures, independent judges and real token accounting.
- Preserve the first frozen comparison, including its failed cost target; further validation is tracked in the evaluation status.

## 0.2.0

- Make a self-contained Skill the primary entrypoint; one canonical source copy is both bundled in the skill and packaged by setuptools.
- Default to host-agent handoffs for text, reasoning, permission review and completion; no nested text model is launched.
- Keep one live worker/CUA session across typed, request-ID-bound replies, with cancellation and bounded waits.
- Reject completion when evidence changes during host verification; retain standalone `--helper codex` as explicit opt-in.
- Document private exchange data separately from metadata-only reports.

## 0.1.0

- Package the native desktop prototype as an installable Python CLI.
- Start from an application inventory without a required initial URL.
- Direct CUA MCP execution, with Jev action selection and on-demand Codex text help.
- Native field-value verification, stale-state checks and explicit stop on uncertain execution.
- Metadata-only reports by default, opt-in full traces, LLM budgets and installation diagnostics.
- Synthetic fixtures, offline CI tests, reproducible native smoke and source-pinned related-work comparison.
