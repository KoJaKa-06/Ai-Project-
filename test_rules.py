import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from rules import Rule, next_cell_type, rules_from_json, rules_to_json, save_rules


class RuleTests(unittest.TestCase):
    def test_save_creates_directory_and_preserves_previous_rules(self):
        with TemporaryDirectory() as directory:
            folder = Path(directory) / 'saved_rules'
            first = save_rules([Rule('A', 'B')], folder)
            second = save_rules([Rule('B', 'A')], folder)
            self.assertNotEqual(first, second)
            self.assertEqual(rules_from_json(first.read_text(encoding='utf-8'), ['A', 'B']),
                             [Rule('A', 'B')])
            self.assertEqual(rules_from_json(second.read_text(encoding='utf-8'), ['A', 'B']),
                             [Rule('B', 'A')])

    def test_brians_brain_and_round_trip(self):
        rules = [Rule('OFF', 'FIRING', 'FIRING', '==', 2),
                 Rule('FIRING', 'DYING'), Rule('DYING', 'OFF')]
        restored = rules_from_json(rules_to_json(rules), ['OFF', 'FIRING', 'DYING'])
        self.assertEqual(restored, rules)
        self.assertEqual(next_cell_type('OFF', {'FIRING': 2}, rules), 'FIRING')
        self.assertEqual(next_cell_type('OFF', {'FIRING': 1}, rules), 'OFF')
        self.assertEqual(next_cell_type('FIRING', {}, rules), 'DYING')
        self.assertEqual(next_cell_type('DYING', {}, rules), 'OFF')

    def test_comparisons_and_missing_neighbor_type(self):
        for op, expected in [('==', True), ('!=', False), ('<', False),
                             ('<=', True), ('>', False), ('>=', True)]:
            with self.subTest(op=op):
                self.assertEqual(Rule('A', 'B', 'B', op, 2).matches('A', {'B': 2}), expected)
        self.assertTrue(Rule('A', 'B', 'B', '==', 0).matches('A', {}))
        self.assertFalse(Rule('A', 'B').matches('B', {}))

    def test_first_match_and_no_match(self):
        rules = [Rule('A', 'B'), Rule('A', 'C')]
        self.assertEqual(next_cell_type('A', {}, rules), 'B')
        self.assertEqual(next_cell_type('C', {}, rules), 'C')

    def test_invalid_rules(self):
        for text in ['{}', '[1]', '[{}]',
                     '[{"source":"A","target":"UNKNOWN"}]',
                     '[{"source":"A","target":"B","extra":1}]',
                     '[{"source":"A","target":"B","count":2}]']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                rules_from_json(text, ['A', 'B'])
        for op, count in [('=', 2), ('==', -1), ('==', True), ('==', 1.5)]:
            with self.subTest(op=op, count=count), self.assertRaises(ValueError):
                Rule('A', 'B', 'B', op, count)
        with self.assertRaises(ValueError):
            Rule('A', 'B', 'B', '==', 2).matches('A', {'B': -1})


if __name__ == '__main__':
    unittest.main()
