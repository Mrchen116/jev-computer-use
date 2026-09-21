# Verification scope

## Offline checks

```sh
python -m pip install .
python -m unittest discover -s tests -v
python scripts/check_release.py
```

These cover native AX parsing, source evidence retention, tab/control paging, factual history, metadata-only reports, model response validation, text-helper budgets and key exclusion, temporary response cleanup, runtime manifest discovery, and a synthetic end-to-end policy loop. The uncertain-action case verifies that a failed mutation is not replayed or declared complete.

Offline tests use fake model responses/desktop state. They do not establish compatibility with a live Codex installation or Jev service. The release scan checks tracked files for common credential formats, developer home paths and private runtime artifacts; it is not a comprehensive secret detector.

## Native smoke, zero model calls

```sh
python -m jev_computer_use.smoke
```

This operates real Chrome through native CUA, opens a new tab with the packaged synthetic fixture, fills a field with mixed English/Chinese text, clicks a local button, and independently checks the output. It leaves the tab open. No Jev or text-LLM call is made. The printed JSON contains counts and a synthetic outcome, not the user's application inventory.

Use this on macOS with Codex desktop open and normal permissions available. `--doctor` does not replace this check.

## Paid task run

```sh
jev-computer-use 'Open the demo page, fill Test message with native test, click Apply locally, and report the result' --local-demo --max-steps 18 --max-llm-calls 8
```

The fixture's URL is a supplied fact; the agent still begins from the app inventory and chooses its own actions. The command requires valid credentials and may invoke the text helper. Only the local fixture is synthetic: the surrounding browser is the real user's application.

## Development evidence

[development-samples.json](development-samples.json) contains sanitized counts from the pre-packaging prototype. Original private traces stay outside the repository.

| Sample | Outcome | Decision rounds | Jev calls, including risk | LLM calls | Wall time |
| --- | --- | ---: | ---: | ---: | ---: |
| Public input-method project lookup | Completed | 8 | 14 | 3 | 71.54 s |
| Synthetic Chinese field + local button | Completed | 8 | 14 | 6 | 105.61 s |

Environment: macOS, installed `unified-computer-use` plugin `26.915.31945`, Jev API, configured Codex CLI helper. The main helper model was not pinned. These cases were run during development, not randomized repetitions on the packaged release. The first run encountered stale/frameless actions before additional execution checks were added; the second passed after native field replacement was adopted.

An isolated input probe found dropped characters with `typeText`; three direct `setValue` attempts, including Chinese, matched the requested value. The backend now checks the observed field value after every fill. This does not imply every app implements AX value assignment identically.

See [release-verification.json](release-verification.json) for checks performed on the packaged version. No comparison here establishes general task success rate, all-app support, or cost/speed superiority over another agent.
