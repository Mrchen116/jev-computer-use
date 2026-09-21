#!/usr/bin/env python3
"""Self-contained skill entrypoint; Python standard library only."""
import sys

if len(sys.argv) > 1 and sys.argv[1] in ('status', 'respond', 'stop'):
    from jev_computer_use.host import main
else:
    from jev_computer_use.cli import main

if __name__ == '__main__':
    raise SystemExit(main())
