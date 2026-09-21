# Security and data scope

This is an experimental agent with access to real applications. Its model-based risk checks are not a security boundary. Use it supervised on non-sensitive tasks; keep OS and native application permissions in force.

UI text and values, task context and recent events can leave the computer for TypeSafe and the host agent (or optional standalone Codex text helper). Metadata-only reporting concerns saved reports, not provider requests or other software's logs. The mode-0700 exchange directory is a separate private IPC channel: current requests and final answers are stored in mode-0600 files. Consumed replies are deleted, and the host cleans up the exchange plus its own response files on completion. Full tracing is explicitly opt-in and may contain private information.

The project does not bundle credentials, modify system security settings, or automatically approve native permission forms. It stops rather than replaying a mutation whose outcome is uncertain. Skill mode returns typed requests to the host and launches no text model. Only explicit `--helper codex` launches a read-only Codex CLI subprocess; its instruction to return structured data without tools is not a general network/tool isolation guarantee.

For a security report, use GitHub private vulnerability reporting if enabled. Do not place secrets, account information or raw traces in public issues. If private reporting is unavailable, open only a minimal issue asking for a private contact channel.
