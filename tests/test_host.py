import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from jev_computer_use.cli import main as run
from jev_computer_use.host import HostHelper, main, validate_reply, write_json
from test_cli import ScriptedDesktop, ScriptedJev


class HostTests(unittest.TestCase):
    def test_live_worker_yields_inputs_and_evidence_without_spawning_codex(self):
        ScriptedDesktop.fail_fill = False
        ScriptedDesktop.mutations = []
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            exchange = root / 'exchange'
            results, purposes = [], []
            with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'synthetic-test-key'}), \
                 patch('jev_computer_use.cli.Desktop', ScriptedDesktop), \
                 patch('jev_computer_use.cli.JevClient', ScriptedJev), \
                 patch('jev_computer_use.cli.CodexTextClient', side_effect=AssertionError('Must not launch an LLM')), \
                 contextlib.redirect_stdout(io.StringIO()):
                worker = threading.Thread(target=lambda: results.append(run([
                    'Set Message to hello and report the result', '--exchange-dir', str(exchange),
                    '--output-dir', str(root / 'reports'), '--help-timeout', '3'])))
                worker.start()
                try:
                    handled = set()
                    deadline = time.monotonic() + 5
                    while worker.is_alive() and time.monotonic() < deadline:
                        path = exchange / 'event.json'
                        event = json.loads(path.read_text()) if path.exists() else {}
                        request_id = event.get('request_id')
                        if event.get('status') == 'needs_host' and request_id not in handled:
                            purposes.append(event['purpose'])
                            self.assertIn('current_page', event['state'])
                            if event['purpose'] == 'input':
                                self.assertEqual(ScriptedDesktop.mutations, [('app', None)])
                                answer = {'value': 'hello', 'needs_user': False, 'reason': 'User requested hello'}
                            else:
                                self.assertEqual(event['state']['current_page'], 'Result: hello')
                                answer = {'completed': True, 'answer': 'Result: hello', 'evidence': 'Result: hello'}
                            response_file = root / 'answer.json'
                            write_json(response_file, {'request_id': request_id, 'answer': answer})
                            main(['respond', str(exchange), '--response-file', str(response_file)])
                            handled.add(request_id)
                        time.sleep(.01)
                finally:
                    if worker.is_alive():
                        write_json(exchange / 'cancel', {})
                    worker.join(4)
                self.assertFalse(worker.is_alive())
            self.assertEqual(results, [0])
            self.assertEqual(purposes, ['input', 'completion'])
            final = json.loads((exchange / 'event.json').read_text())
            self.assertEqual(final['status'], 'completed')
            self.assertEqual(final['answer'], 'Result: hello')
            self.assertEqual(exchange.stat().st_mode & 0o777, 0o700)
            self.assertEqual((exchange / 'event.json').stat().st_mode & 0o777, 0o600)
            self.assertFalse((exchange / 'reply.json').exists())
            trace = json.loads(next((root / 'reports').glob('*/trace.json')).read_text())
            self.assertEqual(trace['helper'], 'external')
            self.assertNotIn('hello', json.dumps(trace))

    def test_wrong_request_and_wrong_types_cannot_resume_worker(self):
        request = {'request_id': 'current', 'fields': {'completed': 'boolean'}}
        for reply in ({'request_id': 'stale', 'answer': {'completed': True}},
                      {'request_id': 'current', 'answer': {'completed': 'true'}},
                      {'request_id': 'current', 'answer': {'completed': True, 'extra': ''}}):
            with self.assertRaises(ValueError):
                validate_reply(request, reply)

    def test_cancel_and_timeout_stop_a_wait_without_an_answer(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            host = HostHelper(Path(temporary) / 'timeout', timeout=.01)
            with self.assertRaisesRegex(RuntimeError, 'Timed out'):
                host.ask('input', 1, '', {}, {'value': 'string'})
            cancelled = HostHelper(Path(temporary) / 'cancelled')
            main(['stop', str(cancelled.directory)])
            with self.assertRaisesRegex(RuntimeError, 'cancelled'):
                cancelled.ask('input', 1, '', {}, {'value': 'string'})

    def test_existing_exchange_cannot_be_reused_and_budget_is_bounded(self):
        with tempfile.TemporaryDirectory() as temporary:
            host = HostHelper(temporary, max_calls=0)
            with self.assertRaisesRegex(ValueError, 'empty'):
                HostHelper(temporary)
            with self.assertRaisesRegex(RuntimeError, 'budget'):
                host.ask('input', 1, '', {}, {})
