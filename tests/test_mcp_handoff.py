"""Exercise the MCP handoff across the external native-runtime boundary."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from jev_computer_use import mcp
from jev_computer_use.computer import describe_window
from test_tasks import JevDouble


class NativeRuntimeDouble:
    """A persistent native app; reading/binding never navigates it elsewhere."""

    def __init__(self):
        self.tool_calls = 0
        self.request_meta = None
        self.closed = False
        self.bound = False
        self.body = 'The page Jev already opened'
        self.codes = []
        self.binds = 0
        self.doc_replays = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def raw(self):
        return ('Window: "Existing page", App: Test\n0 standard window Existing page\n'
                '  2 button Inspect\n  3 text ' + self.body)

    def request(self, method, params):
        if method == 'tools/list':
            return {'tools': [{'name': 'js'}, {'name': 'js_reset'}]}
        if params['name'] == 'js_reset':
            self.bound = False
            return {'content': [{'type': 'text', 'text': 'Reset'}]}
        code = params['arguments']['code']
        return {'content': [{'type': 'text', 'text': self.evaluate(code)}]}

    def js(self, code):
        self.tool_calls += 1
        return self.evaluate(code)

    def evaluate(self, code):
        if self.closed:
            raise AssertionError('The inherited session was closed')
        self.codes.append(code)
        if 'listApps' in code:
            apps = [{'id': 'test', 'displayName': 'Test'}]
            if 'getAXState' in code:
                if not self.bound:
                    raise AssertionError('No inherited application binding')
                return 'JEV_FULL:' + json.dumps([apps, self.raw()])
            return 'JEV_FULL:' + json.dumps(apps)
        if 'cua.getApp' in code:
            self.bound = True
            self.binds += 1
            return 'Native first-use documentation\n' + self.raw()
        if 'rewriteDocumentation' in code:
            self.doc_replays += 1
            return 'Native first-use documentation'
        if not self.bound:
            raise AssertionError('No inherited application binding')
        if '.click(2)' in code:
            self.body = 'Host continued on the same page'
        if 'JEV_FULL:' in code:
            return 'JEV_FULL:' + json.dumps(self.raw())
        if 'getAXState' in code:
            return 'Changed: ' + self.body
        raise AssertionError('Unexpected native code: ' + code)


class MCPHandoffTests(unittest.TestCase):
    def test_current_tree_is_sent_once_as_text_not_escaped_inside_json(self):
        raw = 'Window: "Mail"\n0 text ' + '邮件\n' * 5000
        observation = describe_window(raw, 'mail', [])
        value = {'steps': 2, 'reason': 'context_capacity', 'history': [],
                 'context': {'observation': observation}}
        result = mcp.handoff_result(value, 'jevComputer', 'Method documentation')
        self.assertEqual(result['content'][0]['text'], 'Method documentation')
        metadata = json.loads(result['content'][-1]['text'])
        self.assertEqual(metadata['takeover']['js_binding'], 'jevComputer')
        self.assertNotIn('ui_tree', metadata['current_observation'])
        self.assertEqual(result['content'][1]['text'].split('\n', 1)[1], raw)
        self.assertEqual(value['context']['observation']['ui_tree'], raw)

    def test_jev_host_and_resume_share_one_live_native_session(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            key = root / 'key'
            key.write_text('test-credential')
            state = root / 'task'
            calls = [
                {'name': 'delegate_task', 'arguments': {
                    'state_dir': str(state), 'task': 'Inspect the current app', 'mode': 'step'}},
                {'name': 'js', 'arguments': {
                    'code': 'await jevComputer.click(2); await jevComputer.getAXState();'}},
                {'name': 'delegate_task', 'arguments': {
                    'state_dir': str(state), 'mode': 'step', 'guidance': 'I inspected it; finish.'}},
                {'name': 'js_reset', 'arguments': {}},
                {'name': 'delegate_task', 'arguments': {
                    'state_dir': str(state), 'mode': 'step'}},
                {'name': 'js', 'arguments': {'code': 'await cua.rewriteDocumentation();'}},
                {'name': 'js', 'arguments': {'code': 'await jevComputer.click(2); await jevComputer.getAXState();'}},
            ]
            requests = '\n'.join(json.dumps({'jsonrpc': '2.0', 'id': i,
                                'method': 'tools/call', 'params': call})
                                for i, call in enumerate(calls, 1)) + '\n'
            native = NativeRuntimeDouble()
            jev = JevDouble(['app_test', 'help_reasoning', 'review_completion', 'review_completion'])
            jev.events = []
            jev.unmetered_calls = 0
            stdout = io.StringIO()
            argv = ['mcp', '--hybrid', '--journal', str(root / 'native.jsonl'), '--key-file', str(key)]
            with patch('sys.argv', argv), patch('sys.stdin', io.StringIO(requests)), \
                    contextlib.redirect_stdout(stdout), \
                    patch.object(mcp, 'NativeCUA', return_value=native) as factory, \
                    patch('jev_computer_use.models.JevClient', return_value=jev), \
                    patch.dict('os.environ', {'JEV_EVAL_SCOPES': '[]'}):
                mcp.main()
            replies = [json.loads(line) for line in stdout.getvalue().splitlines()]
            self.assertTrue(all('result' in reply for reply in replies), replies)
            first = replies[0]['result']['content']
            self.assertIn('documentation', first[0]['text'])
            self.assertIn('The page Jev already opened', first[-2]['text'])
            self.assertIn('Host continued on the same page', replies[1]['result']['content'][0]['text'])
            resumed = replies[2]['result']['content']
            self.assertIn('Host continued on the same page', resumed[-2]['text'])
            self.assertEqual(len(resumed), 2)  # No repeated method documentation.
            completed = replies[4]['result']['content']
            self.assertTrue(completed[0]['text'].startswith('CURRENT INTERFACE'))
            self.assertIn('rewriteDocumentation', json.loads(completed[-1]['text'])['takeover']['before_native_ui'])
            self.assertIn('documentation', replies[5]['result']['content'][0]['text'])
            self.assertEqual(native.doc_replays, 2)  # Reasoning handoff, then explicitly requested after completion.
            factory.assert_called_once_with()
            self.assertTrue(native.closed)  # Closed at MCP shutdown, not at handoff.
            self.assertEqual(native.binds, 3)  # Each delegation binds; host takeover does not.
            native_actions = [code for code in native.codes if '.click(' in code]
            self.assertEqual(native_actions, [calls[1]['arguments']['code'], calls[6]['arguments']['code']])


if __name__ == '__main__':
    unittest.main()
