# Security and data scope

The executor controls real applications. Model confidence and continuation checks
are not security boundaries. Use supervised tasks within the user's authorization;
normal OS and native application permissions remain in force.

## What leaves the computer

Jev receives the task, complete current accessibility text, prepared inputs and
concise action history through TypeSafe's API. Handoffs expose the current UI and
history to the outer agent and its model provider. Do not delegate sensitive
screens unless that transmission is authorized.

## What is stored locally

The default task engine retains full observations, decisions, prepared inputs and
history in the private state directory. It creates private directories/files with
`0700`/`0600` permissions. MCP journals also contain UI/tool data. These are **not
metadata-only logs**: keep them outside repositories, protect backups and redact
before sharing. The installation script stores an optional key outside Git with
`0600` permissions and refuses to overwrite an existing key.

Published evaluation summaries are sanitized separately. Raw traces, credentials,
local runtime manifests and personal screenshots must never be committed.

## Execution boundaries

The project does not modify OS security settings or automatically approve native
permission forms. Noninteractive permission requests are cancelled and returned to
the host. Uncertain mutations and failed inference POSTs are not automatically
replayed. Only the outer agent can record verified completion.

The general Skill uses no nested LLM. The explicitly invoked historical helper
and stage engines exist for reproducing earlier experiments; they are not the
default workflow. The installed Codex runtime has its own permissions and license
and is not redistributed here.

## Reporting vulnerabilities

Use GitHub private vulnerability reporting if enabled. Do not publish keys,
account details or raw traces in issues. If private reporting is unavailable,
open a minimal issue requesting a private contact channel without sensitive details.
