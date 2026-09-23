# Getting started

## Requirements

- macOS with Codex desktop open and Computer Use installed/enabled.
- Python 3.9 or later; the Skill itself needs no pip packages.
- A TypeSafe API key with access to Jev.
- An agent that can run local commands and read their output. Codex is the tested
  host; other agents can use the CLI protocol but still need the Codex runtime.

This is a community integration with an installed proprietary runtime, not a
standalone desktop-control SDK. Installing the Skill does not install that runtime,
create an API account or grant application permissions.

## Install

```sh
git clone https://github.com/Mrchen116/jev-computer-use-skill.git
cd jev-computer-use-skill
python3 scripts/install.py --configure-key
```

The hidden prompt saves your key to `~/.config/jev-computer-use/api-key` with mode
`0600`, and installs the Skill under `${CODEX_HOME:-~/.codex}/skills`. Existing
installations and keys are never overwritten. If you already have a key file, omit
`--configure-key` and tell your agent its path. Do not paste the key into a chat.

For another agent's skills directory:

```sh
python3 scripts/install.py --skills-dir /path/to/agent/skills
```

Alternatively, ask the agent to install the complete `skills/jev-computer-use`
directory from this repository. Start a new agent session after installing.

## Check and try

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/jev-computer-use/scripts/run.py" --doctor \
  --key-file "$HOME/.config/jev-computer-use/api-key"
```

Doctor reads installation metadata only. `runtime_found: true` confirms the
installed runtime files exist; it does not prove permissions, API connectivity or
successful UI control. `codex_cli: null` is fine for the basic Skill route.

Try this in a new Codex session:

> Use $jev-computer-use to go to https://mrchen116.github.io/, find the voice-input
> project, and return its GitHub link. My API key file is
> ~/.config/jev-computer-use/api-key. Use a dedicated browser window.

The agent prepares the task, chooses `step` mode and delegates multiple actions.
Jev asks it for missing text or reasoning, and the agent verifies the final answer.
Use a public read-only task first and leave the target window available while the
worker operates. A one-click task or reasoning-heavy comparison is usually better
handled directly by the agent.

## CLI or MCP?

**CLI works without registering an MCP server.** The Skill describes how to launch,
inspect and resume the worker. Handoffs include the current UI, but a different
process must bind the already-open app if it needs further interaction.

**MCP is recommended for frequent delegation.** It keeps the worker and agent in
one native session. Register the following stdio server in your agent, using
absolute paths (the server does not expand shell expressions):

```json
{
  "command": "/absolute/path/to/python3",
  "args": [
    "/absolute/path/to/skills/jev-computer-use/scripts/mcp_server.py",
    "--hybrid",
    "--key-file", "/absolute/path/to/api-key",
    "--journal", "/absolute/path/to/private/jev-native.jsonl"
  ]
}
```

The server exposes `delegate_task`, `read_task_history`, `js` and `js_reset`.
For Codex's direct-tool/output-budget configuration, see the Skill's
[setup reference](../skills/jev-computer-use/references/tasks.md). Keep existing
agent settings. Restart the session after registering the server.

## Common issues

| Symptom | What to do |
| --- | --- |
| Runtime not found | Enable/install Computer Use in Codex desktop; keep it open. An explicit installed manifest can be selected with `JEV_CUA_CONFIG`. |
| Application permission denied | Resolve the normal runtime permission request. Interactive CLI can present the native permission form; noninteractive runs cancel it and hand back. The runner does not auto-approve it. |
| Empty or stale interface | Unlock the Mac and make the intended test window available; do not run competing UI controllers. |
| Missing key | Pass `--key-file`, or set `TYPESAFE_API_KEY_FILE` / `TYPESAFE_API_KEY` in the worker's environment. Shell exports may not reach desktop-launched agents. |
| `needs_host` | This is a normal handoff, not completion. Read the supplied UI and reason; provide text/reasoning or verify the result. |
| Full interface exceeds capacity | The host receives it directly and handles the remaining work. Repeatedly resubmitting the same screen cannot shrink it. |
| Connection failure | Resume only after connectivity returns; uncertain requests are not automatically replayed. |

Logs include UI text and prepared inputs. Keep them outside Git and redact them
before sharing. Stop the worker and wait for exit before taking over the desktop.

## Update or uninstall

For an update, preserve your existing Skill directory under a different name
outside the active skills folder, pull the repository changes, and rerun the
installer. Keep your private key file and existing agent settings.
To uninstall, remove only the installed `jev-computer-use` Skill and any MCP entry
you registered. Credentials and private task logs are separate and remain yours.
