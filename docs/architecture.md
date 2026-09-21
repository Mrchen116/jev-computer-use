# Architecture

The primary product is a self-contained Skill. The host agent owns language reasoning and conversation context. A live Python worker owns the Jev/CUA execution loop. The small handoff protocol is independent of the host model and does not invoke a nested agent.

```mermaid
sequenceDiagram
    participant U as User
    participant A as Host agent
    participant S as Skill
    participant P as Python worker
    participant J as Jev
    participant C as Native CUA
    U->>A: Natural-language task
    A->>S: Read invocation and handoff contract
    S-->>A: Bundled runner and response protocol
    A->>P: Start task with relevant facts
    P->>C: List applications
    loop Until verified, stopped or bounded out
        P->>C: Observe current state
        P->>J: Task + current evidence + factual history + action menu
        J-->>P: Selected action and probabilities
        opt Text or reasoning is needed
            P-->>A: needs_host(id, purpose, state, fields)
            Note over P: Paused; CUA session remains alive
            A->>P: Matching id + typed answer
        end
        P->>J: Risk check for actual mutation and parameters
        opt Authorization review needed
            P-->>A: Concrete action to review
            opt Existing authorization is insufficient
                A->>U: Ask for the missing authorization
                U-->>A: Decision
            end
            A->>P: Approve or decline
        end
        P->>C: Re-observe; execute only if fresh
        C-->>P: Observed result
        opt Jev proposes done
            P-->>A: Current evidence and all task requirements
            A->>P: Verdict + answer + exact quote
            P->>C: Re-observe; reject stale evidence
        end
    end
    P-->>A: Completed answer or explicit incomplete/blocked status
    A-->>U: Final answer
```

The diagram shows conditional calls. App selection/view changes do not require risk inference. Ordinary actions execute without a host response. Native runtime permission forms are also handed to the host for a real user decision; they are not implied by model confidence.

## The host interface

The Skill is the human/agent entrypoint, not a second executing service. Its `scripts/run.py` starts the worker or handles `status`, `respond` and `stop`. All source code lives beside it in `scripts/jev_computer_use`; setuptools packages that same source.

`--exchange-dir` selects a new empty private directory. `event.json` is atomically replaced with `running`, `needs_host` or a terminal status. A pending event contains a unique request ID, purpose, instruction, relevant state and required scalar fields. `respond` validates and publishes `reply.json`. The worker consumes it once, validates again, removes it and resumes. Only one host may respond to a run. Wrong/stale IDs and field types cannot resume execution.

The process remains alive while waiting, preserving app/control context in memory. It never reloads a checkpoint and blindly replays the last mutation. Every wait has a timeout; help and decision budgets are bounded. `stop` is cooperative: a pending native call may finish, but cancellation is checked before the next mutation or while waiting for help. If the worker crashes, it is not resumable: inspect the UI before a new run. The retained shell session is the source of process-exit/error information.

Requests are private IPC, **not metadata-only logs**. The mode-0700 directory has mode-0600 messages. Consumed replies are removed, pending evidence is replaced by the next state, and the final answer remains for the host to consume. The host removes its exchange/response files once the worker exits. Reports remain metadata-only unless full tracing is requested.

## Responsibilities

| Module | Owns |
| --- | --- |
| `SKILL.md` | Invocation, host responsibilities, authorization and evidence interpretation |
| `cli.py` | Budgets, decision loop, help triggers, confirmation and completion |
| `host.py` | Live host handoffs, typed ID-bound replies, waits and cancellation; no model execution |
| `desktop.py` | App discovery, AX roles, current control menu, scopes/paging, mutations and fill verification |
| `runtime.py` | Installed manifest, stdio JSON-RPC, native permission callback and process lifecycle |
| `models.py` | Jev HTTP/validation; opt-in standalone Codex text helper |
| `state.py` | Last-six-step factual state and metadata report projection |
| `doctor.py` | Read-only prerequisites check; Codex CLI required only in standalone mode |

The worker uses `Desktop.observe()`, `execute(action, value)` and `close()` without knowing MCP framing. Host mode and optional `--helper codex` implement the same text-help boundary; only the latter starts `codex exec`. The host-request count is not a measured LLM invocation/token count, and its wait duration includes the host's tool scheduling and other work.

## Trade-offs and verification

One flat action-choice question couples operation and target. A separate risk question covers the actual mutation after text or action help. No untested speculative multihead policy was added.

Input text is produced on demand using the outer conversation, rather than requiring a prefilled slot list. This serves exploratory tasks, but introduces handoff latency and shares more state than a tightly scoped label-only runner. Exact completion quotes and a fresh read prove that evidence was observed; they do not prove that the host interpreted scope or ordering correctly.

Protocol tests replace Jev/CUA with scripted boundaries while retaining the live wait/reply mechanism. A guard makes constructing the internal Codex helper fail in the host-mode test. Native/paid samples separately test real runtime and model behavior. Other shell-capable agents can implement this protocol, but only the tested hosts are claimed as verified. The current desktop integration remains macOS/Codex-specific and text-first.
