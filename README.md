# jev-computer-use

[![tests](https://github.com/Mrchen116/jev-computer-use/actions/workflows/test.yml/badge.svg)](https://github.com/Mrchen116/jev-computer-use/actions/workflows/test.yml)
[![MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Ask your agent. The skill delegates desktop work to Jev; your agent helps only when needed.**

[中文说明](docs/README.zh-CN.md) · [Skill](skills/jev-computer-use/SKILL.md) · [Architecture](docs/architecture.md) · [Related projects](docs/comparison.md) · [Verification](docs/testing.md)

An experimental, self-contained **Skill + Python runner** for macOS. Give Codex or another shell-capable agent a natural-language computer-use task. Jev selects applications and controls, and the runner executes them through the installed native Computer Use runtime. No starting URL, handcrafted button list or per-website route is required.

```text
User → host agent → Skill → Python worker ↔ Jev
                               ↕
                         native Computer Use
                               |
                needs text / reasoning / verification
                               ↓
                   pause → host agent → resume
```

The host keeps the conversation context and supplies missing reasoning. **The default worker never starts another LLM and does not return every click to the host.** It pauses only at handoff points. This reduces unnecessary model orchestration; it is not evidence of a measured speed or cost advantage.

## Install the skill

Ask your agent to install `skills/jev-computer-use` from this repository, or copy that complete directory into its skill directory. For a new Codex installation:

```sh
git clone https://github.com/Mrchen116/jev-computer-use.git
mkdir -p ~/.codex/skills
cp -R jev-computer-use/skills/jev-computer-use ~/.codex/skills/
```

Keep an existing installation if present until you intentionally update it. Start a new agent session so it discovers the skill. Then ask:

> Use $jev-computer-use to find the input-method project on https://mrchen116.github.io/ and return its GitHub link.

> 用 $jev-computer-use 去我的个人网站找多 agent 项目，给我最新的一个 issue。

Supply your website or other personal facts when they are not already known to the host. Users do not need to write task JSON, model prompts, button lists or verification scripts. All runner code is inside the skill directory; copying it needs no pip installation and no third-party Python dependencies.

## Requirements and credentials

- macOS and Python 3.9+.
- Codex desktop running with **Computer Use installed** and normal OS/app permissions.
- A host agent that can run a long-lived shell command, read/write private files and service handoffs while the command runs.
- A TypeSafe API key in `TYPESAFE_API_KEY`, or a private key file selected by `TYPESAFE_API_KEY_FILE` / `--key-file`. Keep that file outside repositories and mode 0600. Do not put the key in chat or command arguments.

The host may be another agent, but the desktop backend **still depends on Codex's installed macOS runtime**. Actual integration has been tested with Codex as host; other agents use the same file protocol but are not individually certified. A Codex CLI login is needed only for the optional standalone helper below.

The runtime is discovered from the installed plugin manifest, not redistributed. No binary signatures, OS permissions or chat credentials are modified. This is a version-dependent community integration, not an official standalone OpenAI SDK. See [runtime details](docs/runtime.md).

## How the host delegates

The [skill](skills/jev-computer-use/SKILL.md) contains the complete host workflow. The small interface is:

```sh
python3 SKILL_ROOT/scripts/run.py --doctor
python3 SKILL_ROOT/scripts/run.py 'The user task' --exchange-dir /private/new-empty-run
# Keep the worker alive; use another shell call to read requests and reply.
python3 SKILL_ROOT/scripts/run.py status /private/new-empty-run --wait 30
python3 SKILL_ROOT/scripts/run.py respond /private/new-empty-run --response-file /private/answer.json
python3 SKILL_ROOT/scripts/run.py stop /private/new-empty-run
```

A handoff supplies `request_id`, purpose, instructions, current evidence and answer fields. The host returns the matching ID and a typed JSON answer. The same worker retains its CUA session and continues; it is not restarted for each reply. Stale/malformed replies cannot authorize an action. Waiting for the host has a timeout and consumes a bounded help-request budget.

The host handles text/shortcuts, ambiguous choices, missing user facts, authorization and final verification. Before a mutation or accepting completion, the worker observes again and rejects stale state. A failed or uncertain UI operation stops for inspection instead of replaying it.

## Optional standalone CLI

For manual terminal use without a calling agent, explicitly choose the legacy Codex subprocess helper:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
jev-computer-use 'Your task' --helper codex
```

This mode requires the logged-in Codex CLI and invokes it for text/help/verification. If no key is configured, it uses a hidden terminal prompt. `--clipboard-key` reads the clipboard only when explicitly requested.

Other options: `--context facts.txt`, `--local-demo`, `--max-steps 30`, `--max-llm-calls 20` (host-request budget in skill mode), `--help-timeout 600`, `--runtime-config /path/to/.mcp.json` (or `JEV_CUA_CONFIG`), `--output-dir`, `--trace-full`. See `--help`.

## Data and limits

This controls **real applications and existing login sessions**. Task text, supplied facts, current UI text/labels/values and recent events are sent to TypeSafe; handoffs also expose relevant evidence to the host agent. Screenshots are not sent. Field-name detection and model risk classification are not comprehensive privacy or authorization boundaries.

Native permissions remain enforced. Runtime forms are passed to the host for a user decision. Consequential actions flagged by Jev pause for authorization review; a model score alone does not grant permission.

Reports default to `~/.local/state/jev-computer-use/runs/`, containing metadata rather than task/UI/answer text. **The handoff exchange is a separate private channel**, mode 0700 with mode-0600 JSON files, and contains current task evidence and the final answer. Consumed replies are removed; the host removes its exchange and response files after completion. `--trace-full` explicitly retains private debugging data. Never publish unreviewed traces/exchanges. Other agents and providers have their own logging policies.

Supported: accessibility-based clicks, single-line replacement with observed-value checks, scrolling, keyboard shortcuts, app selection, tab/control paging and recent factual history. Unsupported: image grounding, drag-and-drop, upload workflows and arbitrary multiline editors. Native tests primarily cover Chrome, not every app. Completion quotes establish observed evidence, not the correctness of the host's interpretation. Jev `done` alone never proves success.

## Development and evidence

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/check_release.py
# macOS only, controls real Chrome with a synthetic fixture; no models:
python -m jev_computer_use.smoke
```

The source package lives inside the skill's `scripts/` directory and is also packaged by setuptools; there is no second vendored copy. CI tests the package and the directly runnable skill. [Testing](docs/testing.md) separates offline contracts, native transport checks and real Jev samples. Small development samples do not establish general success rate or cost savings.

We studied [jev-desktop](https://github.com/yikangy873-gif/jev-desktop), [hermes-jev-skills](https://github.com/kerpopule/hermes-jev-skills), [Jevbridge](https://github.com/tacticocc/Jevbridge), and [kangshifu1/jev-computer-use](https://github.com/kangshifu1/jev-computer-use). [Comparison](docs/comparison.md) records source-pinned evidence and trade-offs; their implementations are not vendored.

[MIT](LICENSE) for our code. External runtimes/services keep their own terms. Independent community project, not affiliated with OpenAI or TypeSafe. The same-named repository under `kangshifu1` is separate.
