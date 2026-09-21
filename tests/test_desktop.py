import unittest
from jev_computer_use.desktop import observation, descriptions, PAGE_SIZE
from jev_computer_use.cli import effect


class NativeObservationTests(unittest.TestCase):
    def test_native_text_link_url_and_disabled_controls(self):
        raw = '''Window: "Example", App: Browser.
0 standard window Example, URL: https://example.test/
    1 HTML 内容 Example, URL: https://example.test/
        2 文本栏 (settable) Search, Value: cameras
        3 按钮 (disabled) Unavailable
        4 link Project, URL: https://github.com/example/project
        5 text A result with evidence
'''
        obs = observation(raw, 'example.app')
        self.assertEqual(obs['actions']['fill_2']['value'], 'cameras')
        self.assertIn('LLM supplies text', descriptions(obs['actions'])['fill_2'])
        self.assertNotIn('click_3', obs['actions'])
        self.assertIn('https://github.com/example/project', obs['page'])
        self.assertIn('A result with evidence', obs['page'])

    def test_tabs_are_separate_reachable_scope(self):
        raw = '''0 标准窗口 Task
    1 文本 Current task evidence
    2 标签 (settable, boolean) Unrelated old tab, Value: off
    3 标签 (settable, boolean) Task, Value: on
    4 按钮 Open new tab
'''
        window = observation(raw, 'app')
        self.assertNotIn('Unrelated old tab', window['page'])
        self.assertIn('show_tabs', window['actions'])
        tabs = observation(raw, 'app', 'tabs')
        self.assertIn('click_2', tabs['actions'])
        self.assertIn('show_window', tabs['actions'])
        self.assertTrue(effect(window, tabs)['view_changed'])

    def test_control_paging_never_silently_discards_actions(self):
        raw = '\n'.join(f'{n} button Action {n}' for n in range(PAGE_SIZE+5))
        first = observation(raw, 'app')
        last = observation(raw, 'app', offset=PAGE_SIZE)
        refs = {a['ref'] for o in (first, last) for a in o['actions'].values() if 'ref' in a}
        self.assertEqual(refs, {str(n) for n in range(PAGE_SIZE+5)})
        self.assertIn('more_controls', first['actions'])
        self.assertIn('previous_controls', last['actions'])
        self.assertTrue(effect(first, last)['view_changed'])
        many = raw + f'\n{PAGE_SIZE+10} text field (settable) Last field, Value: precise'
        self.assertEqual(observation(many, 'app')['fields'][0]['value'], 'precise')


if __name__ == '__main__':
    unittest.main()
