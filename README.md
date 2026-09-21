# jev-computer-use

[![tests](https://github.com/Mrchen116/jev-computer-use/actions/workflows/test.yml/badge.svg)](https://github.com/Mrchen116/jev-computer-use/actions/workflows/test.yml)
[![MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Give it a task. Jev chooses the actions; native Computer Use executes them; an LLM helps only when needed.**

[中文说明](docs/README.zh-CN.md) · [Design](docs/architecture.md) · [Related projects](docs/comparison.md) · [Verification](docs/testing.md)

An experimental macOS desktop agent built around TypeSafe Jev and the installed Codex Computer Use runtime. It starts at the application inventory, discovers accessibility controls, and works from a natural-language task. No starting URL, handcrafted button list, or per-website route is required.

```text
Task → application inventory → Jev chooses an app/action
                                      ↓
                     Need text/help? → LLM returns parameters/advice
                                      ↓
                    Local MCP → native Computer Use → observe again
                                      ↓
                        Jev proposes done → LLM checks evidence
```

The Python process calls the CUA runtime directly. **An LLM does not forward every UI action.** LLM calls still occur for text/shortcut generation, ambiguity or stalled progress, and final verification. This is not a zero-LLM agent, and we have not established cost or speed savings against a controlled baseline.

## Requirements

- macOS and Python 3.9+.
- Codex desktop running with the **Computer Use plugin installed** and normal OS/app permissions granted.
- Codex CLI installed and logged in for the text helper.
- A TypeSafe API key.

The project discovers the installed `unified-computer-use/.mcp.json` and launches its configured stdio runtime. It does **not** bundle OpenAI binaries, modify their signatures, grant OS permissions, or reuse a chat's credentials. This is a version-dependent local integration, not an official standalone OpenAI SDK. See [runtime details](docs/runtime.md).

## Install and run

```sh
git clone https://github.com/Mrchen116/jev-computer-use.git
cd jev-computer-use
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .

jev-computer-use --doctor
jev-computer-use 'Find the input-method project on https://mrchen116.github.io/ and return its GitHub URL'
```

If `TYPESAFE_API_KEY` is not set, the CLI asks for it with hidden input. Keep keys out of chat, command history and Git. `--clipboard-key` is available on macOS; it reads the current clipboard only when explicitly requested. There is no bundled key and no automatic `.env` loader.

Running `jev-computer-use` without a task opens an interactive task prompt. A task need not contain a URL: the text helper can supply a search query when Jev selects an address/search field. Missing personal facts must still come from you; the agent cannot infer whose website you meant.

```sh
# Known facts are sent to the models along with the task.
jev-computer-use 'Find the project described in my notes' --context facts.txt

# Local fixture: its address becomes a fact, not an automatic navigation action.
jev-computer-use 'Open the demo page, fill Test message with hello, click Apply locally, and report the result' --local-demo

# Bound decision and text-helper usage.
jev-computer-use 'Your task' --max-steps 20 --max-llm-calls 5
```

Additional options: `--runtime-config /path/to/.mcp.json` (or `JEV_CUA_CONFIG`), `--codex-command /path/to/codex`, `--output-dir /private/path`, `--trace-full`. See `--help`.

## What is implemented

- Application selection, accessibility-based clicks, single-line field replacement, scrolling and keyboard shortcuts.
- Separate tab inventory and paginated controls to reduce unrelated UI context without discarding actions.
- Last-six-step factual history, including actual input and observed effects; old LLM advice is not carried as standing instructions.
- Re-observation before mutations; stale targets cause a new decision.
- Native `setValue` plus observed-value checks for filling. Simulated keystrokes lost characters in local tests.
- Completion requires an LLM verdict with an exact quote from current evidence. An answer from Jev saying `done` alone cannot pass.
- Model response validation, budgets, and per-purpose LLM call accounting.

## Data and authority

This controls your **real applications and existing login sessions**, not an isolated browser. It is intended for supervised experiments.

The task, supplied facts, current UI text/labels/values and recent events are sent to TypeSafe; relevant state is also sent to the Codex text helper when invoked. Screenshots are not sent by this agent. **Do not run it on confidential or credential-bearing screens.** A small field-name check and model risk classification are not a comprehensive privacy or security boundary.

The runtime's native application permissions remain in force. A runtime permission form is relayed to the human; a noninteractive client cancels it. Potentially consequential actions flagged by Jev require terminal confirmation. This model-based gate can miss risky actions; it is not a substitute for supervision or an action allowlist.

Reports default to `~/.local/state/jev-computer-use/runs/`. Default reports contain statuses, operations, timings and call counts, not task text, field values, UI dumps or answers. Terminal output includes labels and results. `--trace-full` explicitly saves private debugging data locally; never attach it unreviewed to a public issue. Text-helper response files are temporary. Other applications/providers have their own logging policies.

## Verification and limits

Local predecessor runs completed a public project lookup and a synthetic Chinese form task, both starting from the application list. They used **3 and 6 LLM calls**, respectively, across 8 decision rounds each. These are small development samples, not a general success-rate or savings benchmark. The project publishes only sanitized summaries and synthetic fixtures; see [testing](docs/testing.md).

There is no image grounding, drag-and-drop, file-upload workflow or arbitrary multiline editor support. Accessibility coverage varies across apps and languages. Tests have primarily exercised Chrome through the **native desktop** backend; support for every native app is not claimed. An action/verification error stops the run for inspection instead of replaying an uncertain mutation. The program does not close the user's tabs when it exits.

## Development

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/check_release.py

# macOS only: controls Chrome, leaves a synthetic file tab open; no model calls.
python -m jev_computer_use.smoke
```

The Python package has no third-party runtime dependencies. Codex and the installed CUA runtime remain external requirements. CI runs offline contract/privacy tests on Linux; native UI and paid API checks are separate.

## Related work and license

We studied [jev-desktop](https://github.com/yikangy873-gif/jev-desktop), [hermes-jev-skills](https://github.com/kerpopule/hermes-jev-skills), [Jevbridge](https://github.com/tacticocc/Jevbridge), and [kangshifu1/jev-computer-use](https://github.com/kangshifu1/jev-computer-use). [The comparison](docs/comparison.md) records commit-pinned evidence, differences and ideas to evaluate. This repository does not vendor their implementations.

[MIT](LICENSE) for this repository's code. The externally installed runtime and services retain their own terms. Independent community project; not affiliated with OpenAI or TypeSafe. The repository with the same name under `kangshifu1` is a separate project.
