"""Exercise the distribution boundary, including preservation of existing files."""
import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('skill_install', ROOT / 'scripts/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def test_copied_skill_runs_outside_repository_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            with contextlib.redirect_stdout(io.StringIO()):
                installer.main(['--skills-dir', directory])
            root = Path(directory) / 'jev-computer-use'
            result = subprocess.run([sys.executable, str(root / 'scripts/run.py'), '--help'],
                                    cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('--request-file', result.stdout)
            marker = root / 'local-notes.txt'
            marker.write_text('preserve me')
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                installer.main(['--skills-dir', directory])
            self.assertEqual(marker.read_text(), 'preserve me')

    def test_key_is_private_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            key = Path(directory) / 'private/key'
            with patch.object(sys.stdin, 'isatty', return_value=True), \
                    patch.object(installer.getpass, 'getpass', return_value='synthetic-test-value'), \
                    contextlib.redirect_stdout(io.StringIO()):
                installer.main(['--skills-dir', directory + '/skills', '--configure-key', '--key-file', str(key)])
            self.assertEqual(key.stat().st_mode & 0o777, 0o600)
            with patch.object(sys.stdin, 'isatty', return_value=True), \
                    contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                installer.main(['--skills-dir', directory + '/second', '--configure-key', '--key-file', str(key)])
            self.assertEqual(key.read_text(), 'synthetic-test-value\n')
