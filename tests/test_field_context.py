import unittest

from jev_computer_use.computer import action_menu, describe_window


class FieldContextTests(unittest.TestCase):
    def test_unnamed_input_options_quote_the_visible_sibling_without_renaming(self):
        raw = ('0 standard window Form\n'
               ' 1 text Destination\n 2 text field (settable)\n'
               ' 3 text Reference\n 4 text field (settable)\n'
               'The focused UI element is 4 text field')
        observation = describe_window(raw, 'test', [])
        menu = action_menu(observation, {'code': {'text': 'X7', 'purpose': 'reference code'}})
        self.assertEqual(observation['ui_tree'], raw)
        self.assertEqual(observation['controls']['2']['name'], '')
        self.assertEqual(observation['controls']['4']['preceding_text'], 'Reference')
        self.assertIn("AX sibling text: 'Destination'", menu['click_2']['label'])
        self.assertIn("AX sibling text: 'Reference'", menu['replace_code']['label'])
        self.assertIn("AX sibling text: 'Reference'", menu['help_input']['label'])
        self.assertNotIn('Destination', menu['replace_code']['label'])

    def test_text_from_another_level_is_not_presented_as_a_field_sibling(self):
        observation = describe_window(
            '0 standard window Form\n 1 container\n  2 text Unrelated\n 3 text field (settable)',
            'test', [])
        self.assertNotIn('preceding_text', observation['controls']['3'])
        self.assertNotIn('Unrelated', action_menu(observation, {})['click_3']['label'])


if __name__ == '__main__':
    unittest.main()
