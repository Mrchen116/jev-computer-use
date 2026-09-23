#!/usr/bin/env python3
"""Self-contained skill entrypoint; Python standard library only."""
import sys

if len(sys.argv) > 1 and sys.argv[1] == 'task':
    from jev_computer_use.task_cli import main as task_main
    def main(): return task_main(sys.argv[2:])
elif len(sys.argv) > 1 and sys.argv[1] == 'stage':
    from jev_computer_use.stage_cli import main as stage_main
    def main(): return stage_main(sys.argv[2:])
elif len(sys.argv) > 1 and sys.argv[1] in ('status', 'respond', 'stop'):
    from jev_computer_use.host import main
else:
    from jev_computer_use.task_cli import main

if __name__ == '__main__':
    raise SystemExit(main())
