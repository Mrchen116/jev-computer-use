# Full UI context and outer-agent rereads

Investigation date: 2026-09-22. The default task runner stays generic: the whole
user task, all concise history and the complete accessibility content are
available. It does not add website routes, keyword-selected model context or an
inner reasoning LLM.

## What other projects actually send

These are source observations, not comparable benchmark claims:

| Project / inspected revision | Input boundary |
| --- | --- |
| [Browser Use Jev Ultrafast](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/snapshot.js) | Visible DOM text, 6,000-character text limit, 250-action limit; its model code retains ten history entries. |
| [Jev Desktop](https://github.com/yikangy873-gif/jev-desktop/blob/9b02783ed96a81f2529827492de708ca1956c265/plugins/jev-desktop/scripts/runner.mjs) | Host-allowed controls and observations; at most 240 candidates and eight recent actions. |
| [Hermes Jev skills](https://github.com/kerpopule/hermes-jev-skills/blob/655cee2604d5f1896b7ffc4b31254d19a7ac3438/jevkit/choose.py) | Bounded candidates/regions/history; its GUI agent filters visible controls and ranks them using task tokens. |
| [Jev browser Skill](https://github.com/wy-coliney/jev-browser-use/tree/f14b60e0ae1ee90cd73eb6650e30a666a84c021a/skills/jev-browser-use) | Browser-only chunks; persistent session object and compact handoffs to Codex. |
| [Typesafe computer use](https://github.com/awlevin/typesafe-computer-use/blob/cc7b5066ae1a07b5e3182e8f87a9b5b6dfdcffc1/typesafe_computer_use/decide.py) | On-screen items, separate offscreen candidates and eight recent actions. |

These implementations largely avoid an unrestricted full AX document. Their
input strategy does not demonstrate that a full document fits or remains easy
for Jev. We adopt compact state and persistent host sessions, without copying
content/history truncation or browser-only scope.

The [official model limits](https://docs.typesafe.ai/models) are 32k tokens for
state plus the longest question, and 64k for the entire request. The
[official limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13) warn
that irrelevant large state reduces accuracy. Capacity and decision quality are
separate issues; fitting the request does not prove task success.

## Observed waste and changes

The previous pathlib observation had 2,505 indexed nodes and 359 anonymous
containers. It repeated indentation, static node IDs and role prefixes; the
question then repeated actionable labels. The model view now removes static
text/container IDs and compresses indentation, retaining all text, groups,
values, states, order and actionable/unknown controls. The raw observation stays
verbatim in the private log. There is no keyword ranking or hidden page of
controls. The byte guard is now 100,000 for the compact request; it is not a
provider tokenizer.

Capacity probes against saved public observations, using actual Jev 1.13:

- Indentation compression alone still exceeded the token limit.
- A compact complete pathlib state with a minimal recognition question used
  30,884 input tokens. Adding its complete action menu still exceeded the limit.
  Raising a byte budget cannot fix that boundary.
- A compact complete mypy state with the exhaustive grouped action question was
  accepted: 31,192 input tokens, 1.566 seconds, 92,883 UTF-8 request bytes.
  This probe tests capacity; it is not a completed computer-use task.

Seven exploratory API requests produced two metered responses and five
capacity rejections without usage telemetry. Their aggregate cost is unknown;
they are development probes, outside the separately metered task benchmark.

The previous documentation run then performed six log searches, rebound Chrome,
and fetched the same full page again. A research run repeatedly called getApp,
which emits the initial full UI even when subsequent reads suppress output.

Current handoff:

- The latest complete UI is returned directly with concise history. A capacity
  handoff bypasses Jev and delivers the observation already obtained; the host
  does not need another tool call to read that same screen.
- MCP delegation and the host's native `js` share one CUA runtime. The existing
  `takeover.js_binding` lets the host continue on the already-open application.
  Native method documentation is replayed at first handoff when needed. Later
  observations use the native diff behavior; no rebinding or return navigation
  is needed for takeover. CLI returns UI inline but does not transfer JS bindings.
- MCP emits the raw current tree once as a plain-text block alongside metadata.
  It does not JSON-escape or duplicate the tree in its metadata block.
- Codex integration exposes this MCP namespace directly and sets a 60,000-token
  handoff-output budget. Real runs showed that the intervening `functions.exec`
  wrapper truncated a 38,280-token result at its default budget. Prompt-only
  instructions to raise the wrapper budget were not reliably followed. See
  [the tested configuration](../skills/jev-computer-use/references/tasks.md#optional-mcp).

- Every exact saved screen has a stable content ID. Concise status includes its
  app/window, size and ID; action results link to the observed resulting screen.
- A caller can batch exact IDs and search terms in one read. A step selects one
  latest snapshot consistently, including search reads. Identical rechecks do not
  duplicate the result.
- Reads return plain source text, metadata, missing terms and explicit text
  continuation. They do not embed a pretty JSON document inside another JSON
  document or chop JSON syntax at an arbitrary character boundary.
- The Skill says to use the supplied current screen and existing native app binding,
  reading logs only for earlier screens or diagnostics. It also says
  to verify the user's actual requirements without adding extra precision or
  stronger output requirements. Fresh UI reads remain appropriate for missing,
  stale or unconfirmed information.

A previous attempt replaced repeated native UI output with a log pointer only
when text matched exactly. It failed to suppress a repeat when a Chrome memory
label changed. That workaround was removed: current UI delivery and a shared
native session address the extra read/rebind in the handoff itself.

A still-oversized screen returns to System Two with its complete current content
and a saved-screen ID for later reference. This is a capacity boundary, not a
claim that arbitrary full documents now fit Jev. Progress remains compact.

## Verification

Focused tests cover complete text/structure, direct capacity handoff without
another observation/model call, shared MCP-session takeover/resumption, exact
snapshot selection, batched reads, missing terms, persistent history and existing
execution safety checks. The shared-session test doubles the external runtime;
it is a protocol regression check, not a new live-browser benchmark.
Four subsequent real Chrome iterations exposed and fixed the output-delivery
failure. In the final two-task iteration all five handoff trees reached Sol
verbatim, with zero current-screen history reads and zero app rebindings.
One earlier-screen history read was appropriate for the research task. Both
answers passed. The final variant still cost 13.2% more and took 22.4% longer than
the reused native baseline; complete UI delivery alone does not establish a cost
advantage. Results and failed iterations are linked from
[the verification report](testing.md#real-handoff-follow-up-2026-09-22).
