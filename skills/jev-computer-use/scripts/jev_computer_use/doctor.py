"""Read-only installation diagnostics, with no desktop or model requests."""
import json
import os
from pathlib import Path
import shutil
import sys
from .runtime import runtime_configuration


def doctor(config=None, codex_command='codex', helper='external', key_file=None):
    checks = {'macos': sys.platform == 'darwin', 'python': sys.version.split()[0],
              'codex_cli': shutil.which(codex_command),
              'helper': helper, 'jev_key_in_environment': bool(os.environ.get('TYPESAFE_API_KEY'))}
    key_file = key_file or os.environ.get('TYPESAFE_API_KEY_FILE')
    checks['jev_key_file_exists'] = bool(key_file and Path(key_file).expanduser().is_file())
    try:
        path, _ = runtime_configuration(config)
        checks['runtime_config'] = str(path)
        checks['runtime_found'] = True
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        checks['runtime_found'] = False
        checks['runtime_error'] = str(error)
    checks['note'] = ('Keep Codex desktop running. OS/app permissions and login are checked by actual use. '
                      'A missing environment key can be entered at the hidden prompt.')
    print(json.dumps(checks, indent=2))
    return 0 if checks['macos'] and (helper == 'external' or checks['codex_cli']) and checks['runtime_found'] else 1
