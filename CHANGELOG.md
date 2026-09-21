# Changelog

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
