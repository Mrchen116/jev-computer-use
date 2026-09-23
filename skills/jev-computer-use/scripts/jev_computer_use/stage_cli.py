"""Use bounded stages from any host agent with a shell, without MCP registration."""

import argparse
import json
import os
from pathlib import Path

from .models import JevClient
from .runtime import NativeCUA
from .stages import StageEngine, compact_result
from .evidence import read_sources
from .stage_state import write_private, stage_state, read_status, request_stop


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--request-file", type=Path)
    parser.add_argument(
        "--key-file", type=Path, default=os.environ.get("TYPESAFE_API_KEY_FILE")
    )
    parser.add_argument("--evidence", nargs="+")
    parser.add_argument(
        "--query",
        default="",
        help="With --evidence, find a literal phrase in saved original text",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="With --evidence, start reading/searching at this character offset",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=6000,
        help="With --evidence, bound each excerpt (500–12000 characters)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Read concise live progress without UI or model calls",
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=0,
        help="With --status, wait up to 30 seconds for a handoff, then return the latest progress",
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Cooperatively stop; check status until the worker yields",
    )
    args = parser.parse_args(argv)
    if args.status or args.stop:
        print(
            json.dumps(
                request_stop(args.state_dir)
                if args.stop
                else read_status(args.state_dir, args.wait),
                ensure_ascii=False,
            )
        )
        return
    args.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    archive_path = args.state_dir / "evidence.json"
    archive = json.loads(archive_path.read_text()) if archive_path.exists() else {}
    if args.evidence:
        print(
            json.dumps(
                read_sources(
                    archive, args.evidence, args.query, args.offset, args.max_chars
                ),
                ensure_ascii=False,
            )
        )
        return
    if not args.request_file:
        parser.error("--request-file is required for a stage")
    key = (
        args.key_file.read_text().strip()
        if args.key_file
        else os.environ.get("TYPESAFE_API_KEY")
    )
    if not key:
        parser.error("Configure TYPESAFE_API_KEY or --key-file")
    request = json.loads(args.request_file.read_text())
    with NativeCUA() as native:
        engine = StageEngine(native, JevClient(key))
        engine.archive = archive
        engine.by_content = {(e["url"], e["text"]): k for k, e in archive.items()}
        with stage_state(engine, args.state_dir, request) as run_id:
            result = {"run_id": run_id, **engine.run(**request)}
            write_private(args.state_dir / "last-stage.json", result)
            print(json.dumps(compact_result(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
