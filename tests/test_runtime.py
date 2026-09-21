import json
from pathlib import Path
import sys
import tempfile
import unittest

from jev_computer_use.runtime import runtime_configuration


class RuntimeTests(unittest.TestCase):
    def test_explicit_manifest_uses_installed_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'.mcp.json'
            config = {'command': sys.executable, 'args': ['runtime.py'], 'env': {'EXAMPLE': 'value'}}
            path.write_text(json.dumps({'mcpServers': {'cua_repl': config}}))
            observed_path, observed = runtime_configuration(path)
            self.assertEqual(observed_path, path)
            self.assertEqual(observed, config)

    def test_stale_manifest_fails_with_actionable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'.mcp.json'
            path.write_text(json.dumps({'mcpServers': {'cua_repl': {'command': str(Path(directory)/'missing')}}}))
            with self.assertRaisesRegex(RuntimeError, 'missing'):
                runtime_configuration(path)


if __name__ == '__main__':
    unittest.main()
