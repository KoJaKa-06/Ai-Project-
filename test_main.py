import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from main import main, read_rules
from rules import Rule, rules_from_json


class ConsoleTests(unittest.TestCase):
    def run_main(self, answers, directory):
        output = StringIO()
        with patch('builtins.input', side_effect=answers), \
                patch('main.RULES_DIRECTORY', Path(directory)), redirect_stdout(output):
            status = main()
        return status, output.getvalue()

    def test_enter_save_and_simulate_rules(self):
        types = ['OFF', 'FIRING', 'DYING']
        expected = [Rule('OFF', 'FIRING', 'FIRING', '==', 2),
                    Rule('FIRING', 'DYING'), Rule('DYING', 'OFF')]
        for iterations in (0, 2):
            with self.subTest(iterations=iterations), TemporaryDirectory() as directory:
                answers = ['1', '1', ','.join(types), 'OFF',
                           'OFF', 'FIRING', 'FIRING', 'exactly', '2',
                           'FIRING', 'DYING', '', 'DYING', 'OFF', '', '',
                           str(iterations), '0 0 FIRING', '']
                status, text = self.run_main(answers, directory)
                self.assertEqual(status, 0)
                self.assertEqual(text.count('Generation '), iterations + 1)
                self.assertIn('Generation 0:\nFIRING\n', text)
                if iterations == 2:
                    self.assertIn('Generation 1:\nDYING\nGeneration 2:\nOFF\n', text)
                paths = list(Path(directory).glob('*.json'))
                self.assertEqual(len(paths), 1)
                saved = rules_from_json(paths[0].read_text(encoding='utf-8'), types)
                self.assertEqual(saved, expected)
                self.assertIn(str(paths[0]), text)

    def test_invalid_rule_fields_can_be_corrected(self):
        answers = ['BAD', 'OFF', 'BAD', 'FIRING', 'BAD', 'FIRING',
                   'approximately', 'at least', 'two', '-1', '2', '']
        output = StringIO()
        with patch('builtins.input', side_effect=answers), redirect_stdout(output):
            rules = read_rules(('OFF', 'FIRING'))
        self.assertEqual(rules, [Rule('OFF', 'FIRING', 'FIRING', '>=', 2)])
        self.assertIn('Choose one of:', output.getvalue())
        self.assertIn('Choose a comparison', output.getvalue())
        self.assertIn('Enter a whole number.', output.getvalue())

    def test_comparison_words_symbols_and_default(self):
        cases = [('exactly', '=='), ('at least', '>='), ('at most', '<='),
                 ('more than', '>'), ('fewer than', '<'), ('not exactly', '!='),
                 ('', '=='), ('AT LEAST', '>='), ('==', '=='), ('>=', '>='),
                 ('<=', '<='), ('>', '>'), ('<', '<'), ('!=', '!=')]
        for entered, expected in cases:
            with self.subTest(entered=entered):
                answers = ['A', 'B', 'B', entered, '0', '']
                with patch('builtins.input', side_effect=answers), redirect_stdout(StringIO()):
                    rules = read_rules(('A', 'B'))
                self.assertEqual(rules, [Rule('A', 'B', 'B', expected, 0)])

    def test_setup_retries_and_empty_rules(self):
        answers = ['abc', '0', '2', '-1', '3', '', 'A,A', 'A,B', 'X', 'A',
                   '', 'bad', '-1', '0', '0', 'x 0 B', '2 0 B', '0 0 X', '0 0 B', '']
        with TemporaryDirectory() as directory:
            status, text = self.run_main(answers, directory)
            self.assertEqual(status, 0)
            self.assertIn('Generation 0:\nB A A\nA A A\n', text)
            self.assertIn('Invalid cell:', text)
            path = next(Path(directory).glob('*.json'))
            self.assertEqual(rules_from_json(path.read_text(encoding='utf-8'), ['A', 'B']), [])

    def test_interrupted_input_exits_cleanly(self):
        for interruption in (EOFError(), KeyboardInterrupt()):
            with self.subTest(interruption=type(interruption).__name__), TemporaryDirectory() as directory:
                status, text = self.run_main([interruption], directory)
                self.assertEqual(status, 1)
                self.assertIn('Setup cancelled.', text)
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_save_failure_stops_before_simulation(self):
        with TemporaryDirectory() as directory, \
                patch('main.save_rules', side_effect=PermissionError('access denied')):
            status, text = self.run_main(['1', '1', 'A', 'A', ''], directory)
        self.assertEqual(status, 1)
        self.assertIn('Unable to save rules: access denied', text)
        self.assertNotIn('Rules saved to:', text)
        self.assertNotIn('Generation 0:', text)


if __name__ == '__main__':
    unittest.main()
