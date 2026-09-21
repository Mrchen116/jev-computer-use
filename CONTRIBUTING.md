# Contributing

Keep the runner task-driven: avoid website URLs, project names or per-task button sequences in the agent policy. Fixed selectors belong in synthetic tests only.

Install in a virtual environment, run `python -m unittest discover -s tests -v`, and run `python scripts/check_release.py`. Explain user-visible changes and the evidence used to validate them. Native or API integration claims need an actual run and its conditions; offline tests do not substitute for those runs.

Never commit keys, local plugin manifests, screenshots of personal applications, full traces or private model responses. Share minimal synthetic reproductions. Update docs when changing data sent to a provider, logged fields, permissions, budgets, or completion semantics.

The original development experiments remain outside this repository. This release contains the maintained native agent and sanitized summaries, not personal run histories or the old browser prototype.
