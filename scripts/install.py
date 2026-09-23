#!/usr/bin/env python3
"""Install the self-contained Skill without changing agent or OS configuration."""
import argparse
import getpass
import os
from pathlib import Path
import shutil
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    default = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')) / 'skills'
    parser.add_argument('--skills-dir', type=Path, default=default,
                        help='Parent skills directory (default: CODEX_HOME/skills)')
    parser.add_argument('--configure-key', action='store_true',
                        help='Prompt privately and create a key file; never overwrite one')
    parser.add_argument('--key-file', type=Path,
                        default=Path.home() / '.config/jev-computer-use/api-key')
    args = parser.parse_args(argv)
    source = Path(__file__).resolve().parents[1] / 'skills/jev-computer-use'
    destination = args.skills_dir.expanduser().resolve() / source.name
    if destination.exists():
        parser.error('Skill already exists at ' + str(destination) +
                     '; preserve or move the existing copy before reinstalling')
    key_path = args.key_file.expanduser().resolve()
    if args.configure_key:
        if not sys.stdin.isatty():
            parser.error('--configure-key requires an interactive terminal')
        if key_path.exists():
            parser.error('Key file already exists; it will not be overwritten')
        key = getpass.getpass('TypeSafe API key (hidden): ').strip()
        if not key:
            parser.error('Key cannot be empty')
        key_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(str(key_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            stream.write(key + '\n')
    shutil.copytree(source, destination,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.egg-info', '.DS_Store'))
    print('Installed Skill: ' + str(destination))
    if args.configure_key:
        print('Private key file: ' + str(key_path))
    print('Start a new agent session and ask it to use $jev-computer-use.')
    print('Run doctor: python3 ' + repr(str(destination / 'scripts/run.py')) + ' --doctor')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
