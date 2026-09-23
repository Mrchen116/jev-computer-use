# Contributing

Keep the runner task-driven: avoid website URLs, project names or per-task button sequences in the agent policy. Fixed selectors belong in synthetic tests only.

Install in a virtual environment, run `python -m unittest discover -s tests -v`, and run `python scripts/check_release.py`. Explain user-visible changes and the evidence used to validate them. Native or API integration claims need an actual run and its conditions; offline tests do not substitute for those runs.

Never commit keys, local plugin manifests, screenshots of personal applications, full traces or private model responses. Share minimal synthetic reproductions. Update docs when changing data sent to a provider, logged fields, permissions, budgets, or completion semantics.

Raw native/model traces remain outside this repository. The evaluation directory retains sanitized results, failed attempts and reproducible harnesses; see [its index](evals/README.md).

Before submitting, run both suites and the publication scan:

```sh
python3 -m pip install -e .
python3 -m unittest discover -s tests -q
python3 -m unittest discover -s evals/computer_use -q
python3 scripts/check_release.py
```

Keep the Skill self-contained: its copied directory must work without the repository or a pip installation. Changes to onboarding should also be checked with `python3 scripts/install.py --skills-dir /tmp/jev-install-check` using a fresh directory.
