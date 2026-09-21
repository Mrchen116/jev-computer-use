import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from jev_computer_use.cli import main


class ScriptedDesktop:
    fail_fill = False
    mutations = []
    def __init__(self, config=None):
        self.stage = 0
        self.client = SimpleNamespace(tool_calls=0)

    def observe(self):
        self.client.tool_calls += 1
        actions = (
            {'app_0': {'verb': 'app', 'app': 'example.app', 'label': 'Example'}},
            {'fill_1': {'verb': 'fill', 'ref': '1', 'role': 'textbox', 'name': 'Message', 'label': 'Message'}},
            {'done': {'verb': 'done', 'label': 'Verify completion'}},
        )[self.stage]
        page = ('Desktop inventory', 'Message: empty', 'Result: hello')[self.stage]
        return dict(page=page, raw=page, app=None if self.stage == 0 else 'example.app',
                    scope='apps' if self.stage == 0 else 'window', url='', actions=actions)

    def execute(self, action, value=None):
        type(self).mutations.append((action['verb'], value))
        if action['verb'] == 'fill' and self.fail_fill:
            raise RuntimeError('Synthetic uncertain mutation')
        self.stage += 1
        return self.observe()

    def close(self):
        pass


class ScriptedJev:
    def __init__(self, key):
        self.calls = 0
        self.decisions = iter(('app_0', 'fill_1', 'done'))

    def ask(self, payload):
        self.calls += 1
        if 'confirmation' in payload['questions']:
            return {'answers': {'confirmation': {'noul': 0}}}, .01
        selected = next(self.decisions)
        assert selected in payload['questions']['action']['criteria']
        if selected == 'app_0':
            state = json.loads(payload['state'])
            assert state['view'] == 'apps' and state['current_app'] is None
        return {'answers': {'action': {'choice': selected, 'confidence': 1, 'probabilities': {selected: 1}}}}, .01


class ScriptedText:
    def __init__(self, max_calls, command):
        self.events = []

    def ask(self, purpose, step, instruction, state, fields):
        self.events.append({'purpose': purpose, 'step': step})
        if purpose == 'input':
            return {'value': 'hello', 'needs_user': False, 'reason': 'Requested text'}
        assert purpose == 'completion'
        return {'completed': True, 'answer': 'Result: hello', 'evidence': 'Result: hello'}


class LoopTests(unittest.TestCase):
    def run_loop(self, fail=False):
        ScriptedDesktop.fail_fill = fail
        ScriptedDesktop.mutations = []
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'synthetic-test-key'}), \
                 patch('jev_computer_use.cli.Desktop', ScriptedDesktop), \
                 patch('jev_computer_use.cli.JevClient', ScriptedJev), \
                 patch('jev_computer_use.cli.CodexTextClient', ScriptedText), \
                 contextlib.redirect_stdout(io.StringIO()):
                code = main(['Set Message to hello and report the result', '--output-dir', directory])
            trace = json.loads(next(Path(directory).glob('*/trace.json')).read_text())
        return code, trace

    def test_task_starts_at_apps_and_text_help_is_not_an_action_relay(self):
        code, trace = self.run_loop()
        self.assertEqual(code, 0)
        self.assertEqual(trace['status'], 'completed')
        self.assertEqual(ScriptedDesktop.mutations, [('app', None), ('fill', 'hello')])
        self.assertEqual([e['purpose'] for e in trace['llm_events']], ['input', 'completion'])
        self.assertNotIn('hello', json.dumps(trace))

    def test_uncertain_mutation_is_not_replayed_or_marked_complete(self):
        code, trace = self.run_loop(fail=True)
        self.assertEqual(code, 1)
        self.assertEqual(trace['status'], 'blocked')
        self.assertEqual([s['execution'] for s in trace['steps']], ['executed', 'needs_inspection'])
        self.assertEqual(ScriptedDesktop.mutations.count(('fill', 'hello')), 1)
        self.assertEqual(trace['llm_calls'], 1)


if __name__ == '__main__':
    unittest.main()
