# Installed Codex runtime

The launcher reads the installed plugin manifest from:

```text
$CODEX_HOME/plugins/cache/openai-bundled/unified-computer-use/<version>/.mcp.json
```

`CODEX_HOME` defaults to `~/.codex`. `--runtime-config` or `JEV_CUA_CONFIG` can select an explicit installed manifest. The manifest supplies the command, arguments and runtime environment, so this project does not hardcode a developer's username or application executable path.

The discovered pipeline in the original development environment was `cua-repl → node_repl → native Computer Use service`. The MCP client initializes `elicitation.form` support. Permission forms go to the human; noninteractive use cancels them. Normal child processes receive basic environment variables plus the manifest's environment, not the Jev key or current chat's metadata.

Development observations on macOS with plugin `26.915.31945`:

- The older `SkyComputerUseClient mcp` entry point could initialize/list tools but rejected an app read with `Sender process is not authenticated`.
- Launching the current installed `cua-repl` entry point worked with Codex desktop open.
- Omitting form-elicitation capability produced a runtime error; declaring it allowed the normal permission mechanism to operate. No new Chrome permission was requested in the successful development run because it was already authorized.
- A standalone Python process performed native reads, clicks, field updates and verification with no model calls.

These observations do not promise support across all Codex releases, machines or closed-desktop operation. No binary, code-signing, authentication or OS-permission changes are made. OpenAI's runtime is not distributed under this repository's MIT license and is not included in releases.

Run `jev-computer-use --doctor` to check local files and CLI availability. It does not verify login or OS permissions and does not operate the desktop. Run the separately documented native smoke for actual transport/GUI validation.
