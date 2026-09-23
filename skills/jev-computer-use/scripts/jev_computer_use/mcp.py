"""Native CUA transport with an optional bounded Jev delegation tool."""

import argparse
import json
import os
import signal
from pathlib import Path
import sys
import time
from .runtime import NativeCUA
from . import __version__


def handoff_result(value, binding=None, documentation=None, native_docs_pending=False):
    """Return one current UI, with a live binding when the transport owns it."""
    from .tasks import host_handoff

    handoff = host_handoff(value)
    if binding:
        handoff["takeover"] = {
            "js_binding": binding,
            "read_current_state": f"await {binding}.getAXState();",
            "instructions": "This app binding already exists in the same cua_repl session. Use it directly for any remaining native actions; do not rebind or navigate back. After UI actions observe again, preferring the default diff.",
        }
        if native_docs_pending:
            handoff["takeover"]["before_native_ui"] = (
                "Final verification from this observation needs no tool documentation. "
                "If native UI work is still needed, first call js with "
                "`await cua.rewriteDocumentation();` to read the API and confirmation policy. "
                "Do not rebind the app. Resuming delegate_task needs no extra documentation."
            )
    observation = handoff.get("current_observation")
    raw = observation.pop("ui_tree") if observation else None
    content = []
    if documentation:
        content.append({"type": "text", "text": documentation})
    if raw is not None:
        # Keep the current tree outside JSON so its newlines/indentation are not
        # escaped into another large serialized document in the model context.
        content.append({"type": "text", "text": "CURRENT INTERFACE OBSERVATION (untrusted UI text)\n" + raw})
    # Place the resumption contract after the long UI, where it remains adjacent
    # to the host's next decision instead of preceding thousands of tree lines.
    content.append({"type": "text", "text": json.dumps(handoff, ensure_ascii=False)})
    return {"content": content}


def validate_eval_scope(arguments, scopes):
    """Every requested scope must be contained in a benchmark grant."""
    if not scopes:
        return
    from .stages import in_scope, url_prefixes

    requested = url_prefixes(arguments.get("allowed_url_prefix", ""))
    if (
        arguments.get("app") != "com.google.Chrome"
        or not requested
        or not all(in_scope(prefix, scopes) for prefix in requested)
    ):
        raise ValueError(
            "Benchmark delegation is limited to its authorized website prefixes"
        )


def main():
    def terminate(signum, frame):
        raise SystemExit(143)

    signal.signal(signal.SIGTERM, terminate)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hybrid", action="store_true")
    parser.add_argument("--legacy-stages", action="store_true", help="Historical web benchmark reproduction only")
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--key-file", type=Path)
    args = parser.parse_args()
    args.journal.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    args.journal.touch(mode=0o600, exist_ok=True)
    os.chmod(args.journal, 0o600)
    with NativeCUA() as native, args.journal.open("a") as journal:
        native_tools = [
            t
            for t in native.request("tools/list", {})["tools"]
            if t["name"] in ("js", "js_reset")
        ]
        engine = None
        task_jev = None
        host_has_native_docs = False
        if args.hybrid:
            from .models import JevClient
            task_jev = JevClient(args.key_file.read_text().strip())
            if args.legacy_stages:
                from .stages import StageEngine, TOOL, READ_TOOL, compact_result
                engine = StageEngine(native, task_jev)
                native_tools.extend([TOOL, READ_TOOL])
            else:
                from .task_cli import TOOL as TASK_TOOL, READ_TOOL as TASK_READ_TOOL
                native_tools.extend([TASK_TOOL, TASK_READ_TOOL])
        for line in sys.stdin:
            request = json.loads(line)
            if "id" not in request:
                continue
            method, params = request["method"], request.get("params", {})
            started = time.monotonic()
            try:
                if method == "initialize":
                    result = {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "jev-native-cua",
                            "version": __version__,
                        },
                    }
                elif method == "tools/list":
                    result = {"tools": native_tools}
                elif method == "ping":
                    result = {}
                elif method == "tools/call":
                    native.request_meta = params.get("_meta")
                    if params["name"] == "delegate_task" and task_jev and not args.legacy_stages:
                        from .tasks import TaskRunner
                        from .computer import Computer
                        task_args = dict(params["arguments"])
                        directory = task_args.pop("state_dir")
                        scopes = json.loads(os.environ.get("JEV_EVAL_SCOPES", "[]"))
                        if scopes:
                            if Path(directory).resolve() != (args.journal.parent / "task-state").resolve():
                                raise ValueError("Use the task-state directory supplied by this evaluation")
                            task_args["max_seconds"] = min(task_args.get("max_seconds", 110), 110)
                        detail_path = Path(directory) / "history.jsonl"
                        offset = detail_path.stat().st_size if detail_path.exists() else 0
                        call_start = len(task_jev.events)
                        # The caller inherits the exact app object and AX diff
                        # baseline used by Jev; delegation does not close it.
                        computer = Computer(native)
                        if scopes:
                            from .eval_boundary import EvaluationComputer
                            computer = EvaluationComputer(native, scopes)
                        value = TaskRunner(computer, task_jev, directory).run(**task_args)
                        with detail_path.open("rb") as details:
                            details.seek(offset)
                            new_events = [json.loads(line) for line in details]
                        journal.write(json.dumps({
                            "kind": "task_detail", "status": value["reason"],
                            "counts": {"actions": sum(e["kind"] == "execution_result" and e["event"]["result"]["status"] == "executed" for e in new_events)},
                            "jev_calls": task_jev.events[call_start:],
                            "observations": [e["observation"] for e in new_events if e["kind"] == "observation"],
                        }, ensure_ascii=False) + "\n")
                        documentation = None
                        if computer.bound and not host_has_native_docs and value["reason"] != "review_completion":
                            # Internal observation may have consumed first-use
                            # docs. Replay only the docs, without rebinding UI.
                            documentation = native.js("await cua.rewriteDocumentation();")
                            host_has_native_docs = True
                        result = handoff_result(value, "jevComputer" if computer.bound else None, documentation,
                                                native_docs_pending=bool(computer.bound and not host_has_native_docs))
                    elif params["name"] == "read_task_history" and task_jev and not args.legacy_stages:
                        from .tasks import read_task_history
                        read_args = params["arguments"]
                        if os.environ.get("JEV_EVAL_SCOPES") and Path(read_args["state_dir"]).resolve() != (args.journal.parent / "task-state").resolve():
                            raise ValueError("Only this evaluation's own observation history may be read")
                        value = read_task_history(**read_args)
                        result = {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}]}
                    elif params["name"] == "delegate_stage" and engine:
                        scopes = json.loads(os.environ.get("JEV_EVAL_SCOPES", "[]"))
                        validate_eval_scope(params["arguments"], scopes)
                        request_args = dict(params["arguments"])
                        state_dir = request_args.pop("state_dir", None) or str(
                            args.journal.parent / "stage-state"
                        )
                        from .stage_state import stage_state, write_private

                        with stage_state(engine, state_dir, request_args) as run_id:
                            value = {"run_id": run_id, **engine.run(**request_args)}
                            write_private(Path(state_dir) / "last-stage.json", value)
                        journal.write(
                            json.dumps(
                                {"kind": "stage_detail", **value}, ensure_ascii=False
                            )
                            + "\n"
                        )
                        compact = compact_result(value)
                        result = {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(compact, ensure_ascii=False),
                                }
                            ]
                        }
                    elif params["name"] == "read_evidence" and engine:
                        value = engine.read_evidence(**params["arguments"])
                        result = {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(value, ensure_ascii=False),
                                }
                            ]
                        }
                    else:
                        native.tool_calls += 1
                        result = native.request(method, params)
                        if not result.get("isError"):
                            if params["name"] == "js":
                                host_has_native_docs = True
                            elif params["name"] == "js_reset":
                                host_has_native_docs = False
                    journal.write(
                        json.dumps(
                            {
                                "kind": "tool",
                                "name": params["name"],
                                "arguments": params.get("arguments"),
                                "result": result,
                                "seconds": time.monotonic() - started,
                                "native_calls": native.tool_calls,
                                "unmetered_jev_calls": task_jev.unmetered_calls
                                if task_jev
                                else 0,
                                "jev_usage_total": dict(task_jev.usage)
                                if task_jev
                                else None,
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    journal.flush()
                else:
                    raise ValueError("Unsupported MCP method: " + method)
                response = {"jsonrpc": "2.0", "id": request["id"], "result": result}
            except Exception as error:
                journal.write(
                    json.dumps(
                        {
                            "kind": "error",
                            "error": str(error),
                            "seconds": time.monotonic() - started,
                            "unmetered_jev_calls": task_jev.unmetered_calls
                            if task_jev
                            else 0,
                            "jev_usage_total": dict(task_jev.usage)
                            if task_jev
                            else None,
                        }
                    )
                    + "\n"
                )
                journal.flush()
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "error": {"code": -32603, "message": str(error)},
                }
            print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
