import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from jev_computer_use.models import CodexTextClient, validate_answers
from jev_computer_use.state import compact_report, make_state


class StateTests(unittest.TestCase):
    def test_history_contains_outcome_not_old_advice(self):
        state = make_state('task', '', {'page': 'page', 'actions': {}}, [{
            'operation': 'fill', 'input': 'query', 'execution': 'executed',
            'llm_guidance': {'reason': 'Type query now'},
        }])
        self.assertEqual(state['recent_events'][0]['input'], 'query')
        self.assertNotIn('Type query now', str(state))

    def test_default_report_has_no_private_text(self):
        report = dict(backend='native-cua', status='completed', elapsed_seconds=1,
                      llm_calls=1, llm_events=[{'purpose': 'input', 'step': 1}], jev_calls=2, cua_tool_calls=3,
                      task='PRIVATE_TASK', answer='PRIVATE_ANSWER', steps=[{
                          'step': 1, 'operation': 'fill', 'execution': 'executed', 'jev_seconds': .2,
                          'input': 'PRIVATE_INPUT', 'target': 'PRIVATE_TARGET', 'page': 'PRIVATE_PAGE',
                          'request': {'state': 'PRIVATE_STATE'}, 'error': 'PRIVATE_ERROR'}])
        result = compact_report(report)
        self.assertNotIn('PRIVATE_', json.dumps(result))
        self.assertEqual(result['steps'][0]['operation'], 'fill')
        self.assertEqual(result['llm_calls'], 1)


class ModelBoundaryTests(unittest.TestCase):
    def test_unknown_choice_and_nan_risk_are_rejected(self):
        payload = {'questions': {'action': {'type': 'choice', 'criteria': {'click_1': 'Click'}}}}
        with self.assertRaises(ValueError):
            validate_answers(payload, {'answers': {'action': {'choice': 'invented', 'confidence': .9}}})
        for invalid in (float('nan'), 2, True):
            with self.assertRaises(ValueError):
                validate_answers({'questions': {'risk': {'type': 'noul'}}}, {'answers': {'risk': {'noul': invalid}}})

    def test_llm_budget_blocks_before_process_launch(self):
        with patch('jev_computer_use.models.subprocess.run') as run:
            with self.assertRaisesRegex(RuntimeError, 'budget'):
                CodexTextClient(max_calls=0).ask('input', 1, '', {}, {'value': 'string'})
            run.assert_not_called()

    def test_text_response_is_temporary_and_key_not_forwarded(self):
        directories = []
        def fake_run(command, **kwargs):
            self.assertNotIn('TYPESAFE_API_KEY', kwargs['env'])
            self.assertIn('--ephemeral', command)
            self.assertEqual(command[command.index('-s')+1], 'read-only')
            directory = Path(command[command.index('-C')+1])
            directories.append(directory)
            Path(command[command.index('-o')+1]).write_text('{"value":"hello"}')
            return subprocess.CompletedProcess(command, 0, '', '')
        client = CodexTextClient()
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'synthetic-test-value'}), patch('jev_computer_use.models.subprocess.run', side_effect=fake_run):
            result = client.ask('input', 3, 'Return a value', {}, {'value': 'string'})
        self.assertEqual(result, {'value': 'hello'})
        self.assertFalse(directories[0].exists())
        self.assertEqual(client.events[0]['step'], 3)
        self.assertEqual(client.events[0]['purpose'], 'input')


if __name__ == '__main__':
    unittest.main()
