"""Lock the menu-option width rule, and show it can fail.

The bug this exists for: the story gate measures the 180px dialogue budget, and
a menu option does not get 180px -- it shares a row with the option beside it.
`아니오` is 36px against `いいえ` at 33px because a Hangul syllable advances
12px and a kana 11px, so every option row got wider than the one it replaced
and nothing was measuring it.

The budget is the widest Japanese row the ROM itself draws at the same
placement and declared width. These cases check that the row parser really
finds multi-option rows in this ROM (or the rule would be vacuous), and that a
row pushed one syllable over its budget is rejected.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from check_option_widths import label, rows_of, row_pixels
from analyze_project import PROFILES, sha
from survey_dialogue_layout import ESCAPED_BREAK, ADVANCE_OFFSET, load_table, advances

p = Path(__file__).resolve().parents[1]
BATCH_DIR = p / 'translations/story_korean'


def run(batches, output):
    command = [sys.executable, str(p / 'tools/check_option_widths.py'), '--output', str(output)]
    for batch in batches:
        command += ['--batch', str(batch)]
    return subprocess.run(command, capture_output=True, text=True, encoding='utf-8')


class Rows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = list(rows_of('blue_moon'))
        cls.table = load_table()
        rom = next(f.read_bytes() for f in p.parent.parent.glob('*.gba')
                   if sha(f.read_bytes()) == PROFILES['blue_moon']['sha256'])
        cls.width = advances(rom, ADVANCE_OFFSET['blue_moon'])

    def test_rom_has_rows_with_two_options_side_by_side(self):
        """If every row held one option the shared-row rule would be vacuous."""
        self.assertTrue(any(len(members) > 1 for _a, _s, _p, members in self.rows))

    def test_rows_carry_a_declared_width(self):
        placed = [r for r in self.rows if r[2] is not None]
        self.assertGreater(len(placed), 100, 'almost no option row declares a position')

    def test_a_row_ends_at_the_literal_carrying_the_break(self):
        for _a, _s, _place, members in self.rows:
            broken = [i for i, (_id, text) in enumerate(members) if ESCAPED_BREAK in text]
            self.assertIn(broken, ([], [len(members) - 1]),
                          'a line break appeared before the end of a row')

    def test_label_stops_at_either_spelling_of_the_break(self):
        self.assertEqual(label('예' + ESCAPED_BREAK), '예')
        self.assertEqual(label('예\n'), '예')

    def test_hangul_is_wider_than_the_kana_it_replaces(self):
        """The reason this gate exists, stated as a measurement."""
        japanese, _ = row_pixels(['いいえ'], self.table, self.width)
        korean, _ = row_pixels(['아니오'], self.table, self.width)
        self.assertGreater(korean, japanese)


class Gate(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.output = Path(self.dir.name) / 'report.json'
        self.batch = Path(self.dir.name) / 'batch_probe.json'

    def tearDown(self):
        self.dir.cleanup()

    def widest_translated_row(self):
        """A real row of a real batch, with the batch it came from."""
        korean = {}
        for batch in sorted(BATCH_DIR.glob('*.json')):
            for entry in json.loads(batch.read_text(encoding='utf-8'))['entries']:
                korean[entry['id']] = (batch, entry)
        for _a, _s, place, members in rows_of('blue_moon'):
            if place is None:
                continue
            hit = [korean[i] for i, _t in members if i in korean]
            if hit:
                return hit[0]
        self.fail('no translated option row to perturb')

    def test_the_batches_as_written_pass(self):
        self.assertEqual(run(sorted(BATCH_DIR.glob('*.json')), self.output).returncode, 0)

    def test_one_syllable_too_many_is_rejected(self):
        batch, entry = self.widest_translated_row()
        original = json.loads(batch.read_text(encoding='utf-8'))
        for item in original['entries']:
            if item['id'] == entry['id']:
                item['ko'] = '가' * 20
                item.pop('ko_red_sun', None)
        self.batch.write_text(json.dumps(original, ensure_ascii=False), encoding='utf-8')
        result = run([self.batch], self.output)
        self.assertEqual(result.returncode, 1)
        self.assertIn('exceeds', result.stdout)

    def test_an_unencodable_option_is_rejected(self):
        batch, entry = self.widest_translated_row()
        original = json.loads(batch.read_text(encoding='utf-8'))
        for item in original['entries']:
            if item['id'] == entry['id']:
                item['ko'] = '☃'
                item.pop('ko_red_sun', None)
        self.batch.write_text(json.dumps(original, ensure_ascii=False), encoding='utf-8')
        result = run([self.batch], self.output)
        self.assertEqual(result.returncode, 1)
        self.assertIn('unencodable', result.stdout)

    def test_the_report_records_the_budget_it_used(self):
        run(sorted(BATCH_DIR.glob('*.json')), self.output)
        report = json.loads(self.output.read_text(encoding='utf-8'))
        self.assertEqual(report['status'], 'PASS')
        self.assertTrue(report['budgets'])
        self.assertIn('not_claimed', report)


if __name__ == '__main__':
    unittest.main(verbosity=2)
