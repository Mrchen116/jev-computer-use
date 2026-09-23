# Setup and optional controls

`SKILL_ROOT` is this Skill's directory. Requires Python 3.9+, macOS, and running
Codex desktop with Computer Use installed and normal permissions; no pip packages.
Check with `python3 SKILL_ROOT/scripts/run.py --doctor`. Keep credentials and task
logs outside Git; use a private key file or `TYPESAFE_API_KEY[_FILE]` environment variable.

## Optional MCP

Start the server with:

```sh
python3 SKILL_ROOT/scripts/mcp_server.py --hybrid \
  --key-file /private/typesafe-key --journal /private/jev-native.jsonl
```

For a Codex server named `jev`, merge these settings, preserving other namespaces:

```toml
[features.code_mode]
direct_only_tool_namespaces = ["mcp__jev"]
[mcp_servers.jev.tools.delegate_task]
output_token_limit = 60000
```

Use your registered server name. This exposes `delegate_task`, `read_task_history`
and native `js`/`js_reset` sharing one session; handoff returns its existing app
binding and complete current UI. The output budget avoids premature truncation;
host context limits still apply.

## CLI and progress

Without MCP, save a request JSON and start it using a long-running shell tool:

```json
{"task":"Find 王明 and open the conversation for review.","mode":"step","input_texts":{"contact":{"text":"王明","purpose":"Contact name to search for"}}}
```

```sh
python3 SKILL_ROOT/scripts/run.py task --request-file /private/request.json \
  --state-dir /private/jev-task --key-file /private/typesafe-key
python3 SKILL_ROOT/scripts/run.py task --state-dir /private/jev-task --status
python3 SKILL_ROOT/scripts/run.py task --state-dir /private/jev-task --stop
python3 SKILL_ROOT/scripts/run.py task --state-dir /private/jev-task \
  --complete --answer-file /private/verified-answer.txt
```

Status includes all concise history, usage, warnings and `history_location`;
`--status --wait 20` waits for progress without model/UI calls. Stop is cooperative:
wait for exit before takeover. `--complete` records your verified verdict only.
Resume with the same directory and a JSON containing `mode` plus new guidance or
inputs. Unlike MCP, CLI cannot transfer JS bindings between processes: bind the
already-open app once only if further native actions are needed.

## Optional request fields

| Field | Default / meaning |
|---|---|
| `period_ms` | 1000; 100–30000, realtime minimum cycle spacing; overruns warn, do not queue. |
| `recheck_target` | true; changed window/target/focus or new choices at a focused input trigger a fresh decision. Other text changes only warn. |
| `max_steps`, `max_seconds` | 100, 300 per invocation; history and usage persist. |
| `min_continue_probability` | 0.9; low continuation score yields before acting. Not a calibrated guarantee. |
| `max_context_bytes` | 100000; larger requests hand back the full UI before calling Jev. Usually omit. |
| `pricing` | Optional verified USD/M Jev `input_tokens` and `output_tokens` rates. Missing cost is unknown. |

For older screens, `read_task_history(state_dir, observation_ids=[...])` reads saved
observations; optional `contains` filters literal lines for your read, not Jev's
context. Follow `next_offset` if truncated. `kind=decision` exposes diagnostics.
All current UI and concise history remain available to Jev; this reference does
not require the outer agent to generate rules, questions or action menus.
