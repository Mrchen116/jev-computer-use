"""Check files intended for publication; never print a matched secret."""
from pathlib import Path
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
try:
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
except subprocess.CalledProcessError:
    raise SystemExit('Run inside an initialized repository with staged files')
patterns = {
    'credential': re.compile(rb'\b(?:apikey_[a-f0-9]{20,}_[a-f0-9]{30,}|gh[opusr]_[A-Za-z0-9]{25,}|sk-[A-Za-z0-9_-]{24,})\b'),
    'private home path': re.compile(rb'/Users/[A-Za-z0-9_.-]+/|/home/[A-Za-z0-9_.-]+/'),
}
failures = []
for relative in filter(None, paths):
    path = root/relative
    if not path.is_file():
        continue
    if relative.startswith(('runs/', '.venv/', '.playwright-cli/')) or path.name.startswith('.env'):
        failures.append((relative, 'private runtime file'))
    data = path.read_bytes()
    for name, pattern in patterns.items():
        if pattern.search(data):
            failures.append((relative, name))
for path, reason in failures:
    print(f'{path}: {reason}')
print(f'Publication scan: {len(list(filter(None, paths)))} files, {len(failures)} findings')
sys.exit(bool(failures))
