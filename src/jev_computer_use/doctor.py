"""Read-only installation diagnostics, with no desktop or model requests."""
import json
import os
import shutil
import sys
from .runtime import runtime_configuration


def doctor(config=None, codex_command='codex'):
    checks = {'macos': sys.platform == 'darwin', 'python': sys.version.split()[0],
              'codex_cli': shutil.which(codex_command),
              'jev_key_in_environment': bool(os.environ.get('TYPESAFE_API_KEY'))}
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
    return 0 if checks['macos'] and checks['codex_cli'] and checks['runtime_found'] else 1
