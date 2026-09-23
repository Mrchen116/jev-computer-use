"""Private, compact progress and cooperative stop control for a delegated stage."""

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import time
import uuid


def write_private(path, data):
    temporary = path.with_suffix(".tmp")
    with temporary.open("w") as stream:
        os.chmod(temporary, 0o600)
        json.dump(data, stream, ensure_ascii=False)
    temporary.replace(path)


def read_status(directory, wait=0):
    path = Path(directory) / "progress.json"
    deadline = time.monotonic() + max(0, min(wait, 30))
    while True:
        value = (
            json.loads(path.read_text()) if path.exists() else {"status": "not_started"}
        )
        if value.get("status") == "running" and value.get("worker_pid"):
            try:
                os.kill(value["worker_pid"], 0)
            except ProcessLookupError:
                return {
                    **value,
                    "status": "interrupted",
                    "attention": "Worker exited without publishing a final result",
                }
        if value.get("status") == "running" and value.get("updated_at"):
            since_update = (
                datetime.now(timezone.utc) - datetime.fromisoformat(value["updated_at"])
            ).total_seconds()
            value["elapsed_seconds"] = round(
                value.get("elapsed_seconds", 0) + max(0, since_update), 1
            )
        if value["status"] != "running" or time.monotonic() >= deadline:
            return value
        time.sleep(min(0.2, max(0, deadline - time.monotonic())))


def request_stop(directory):
    value = read_status(directory)
    if value["status"] != "running":
        return {"stop_requested": False, "status": value["status"]}
    write_private(Path(directory) / "stop.json", {"run_id": value["run_id"]})
    return {"stop_requested": True, "run_id": value["run_id"], "status": "stopping"}


@contextmanager
def stage_state(engine, directory, request):
    """Attach telemetry to either CLI or MCP without sending raw traces to the host."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (directory / "stage.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(
                "A stage is already running in this state directory"
            ) from None
        run_id = uuid.uuid4().hex
        stop_path = directory / "stop.json"
        previous_progress, previous_stop = engine.progress, engine.should_stop
        latest = {}

        def persist(value):
            write_private(
                directory / "progress.json",
                {
                    **value,
                    "run_id": run_id,
                    "worker_pid": os.getpid(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "result_file": str(directory / "last-stage.json")
                    if value.get("status") in ("yielded", "stopped")
                    else None,
                },
            )

        def publish(value):
            latest.clear()
            latest.update(value)
            # Publish the final snapshot only after result/evidence files exist.
            if value.get("status") not in ("yielded", "stopped"):
                persist(value)
            previous_progress(value)

        def stopped():
            return previous_stop() or (
                stop_path.exists()
                and json.loads(stop_path.read_text()).get("run_id") == run_id
            )

        engine.progress, engine.should_stop = publish, stopped
        publish(
            {
                "status": "running",
                "mode": request.get("mode", "step"),
                "goal": request.get("goal", ""),
                "phase": "starting",
                "attention": None,
            }
        )
        try:
            yield run_id
        except BaseException as error:
            publish(
                {
                    **latest,
                    "status": "error",
                    "phase": "yielded",
                    "attention": str(error)[:500] or type(error).__name__,
                }
            )
            raise
        finally:
            write_private(directory / "evidence.json", engine.archive)
            persist(latest)
            engine.progress, engine.should_stop = previous_progress, previous_stop
