"""Prove the story gate rejects each thing it claims to reject.

A gate that has never failed is not known to work. Each case below takes a real
record from the extraction sheet, breaks exactly one property, and asserts the
gate names that property. The last case is the same record left intact, so a
failure everywhere would be caught too.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

p = Path(__file__).resolve().parents[1]
SHEET = p / 'translations/story_source.jsonl'
GATE = p / 'tools/check_story_translation.py'


def sheet_records():
    return [json.loads(line) for line in SHEET.read_text(encoding='utf-8').splitlines()]


def run(entries, tmp):
    batch = Path(tmp) / 'batch_test.json'
    out = Path(tmp) / 'gate.json'
    batch.write_text(json.dumps({'schema': 1, 'state': 'test', 'entries': entries}, ensure_ascii=False),
                     encoding='utf-8')
    # The gate prints Korean; the console codepage here is not UTF-8, so pin the
    # child's IO encoding or capturing its output raises instead of the test
    # reporting what the gate decided.
    import os
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    subprocess.run([sys.executable, str(GATE), '--batch', str(batch), '--output', str(out)],
                   capture_output=True, text=True, encoding='utf-8', env=env)
    return json.loads(out.read_text(encoding='utf-8'))


class StoryGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        records = sheet_records()
        # Pin a record on the ordinary dialogue budget: a record whose own source
        # line is wider carries a wider budget, and the width cases below would
        # then be measuring against the wrong number.
        cls.story = next(r for r in records if r['text_class'] == 'story' and r['revision'] == 'both'
                         and len(r['ja_lines']) == 1 and r['line_budget_pixels'] == 180)
        cls.short = next(r for r in records if r['text_class'] == 'short')
        cls.differs = next(r for r in records if r['revision'] == 'differs')

    def entry(self, record, ko, **extra):
        return {'id': record['id'], 'ko': ko, 'source_bindings': record['source_bindings'], **extra}

    def gate(self, entries):
        with tempfile.TemporaryDirectory() as tmp:
            return run(entries, tmp)

    def test_clean_entry_passes(self):
        report = self.gate([self.entry(self.story, '한 줄짜리 번역')])
        self.assertEqual(report['status'], 'PASS', report['problems'])
        self.assertEqual(report['story_ids_translated'], 1)

    def test_unknown_id_is_refused(self):
        report = self.gate([{'id': 'archive/999/script/0/literal/0', 'ko': '없는 칸',
                             'source_bindings': self.story['source_bindings']}])
        self.assertEqual(report['status'], 'FAIL')
        self.assertTrue(any('not in the extraction sheet' in x['problem'] for x in report['problems']))

    def test_source_binding_drift_is_refused(self):
        bad = {k: {'payload_sha256': '0' * 64, 'tpl_sha256': '0' * 64} for k in self.story['source_bindings']}
        report = self.gate([{'id': self.story['id'], 'ko': '바뀐 원본', 'source_bindings': bad}])
        self.assertTrue(any('source binding drift' in x['problem'] for x in report['problems']))

    def test_missing_binding_is_refused(self):
        report = self.gate([{'id': self.story['id'], 'ko': '묶이지 않은 번역'}])
        self.assertTrue(any('no source binding' in x['problem'] for x in report['problems']))

    def test_short_class_is_refused(self):
        report = self.gate([self.entry(self.short, '메뉴 라벨')])
        self.assertTrue(any('not story class' in x['problem'] for x in report['problems']))

    def test_fourth_line_is_refused(self):
        report = self.gate([self.entry(self.story, '한\n두\n세\n네')])
        self.assertTrue(any('exceeds the page budget' in x['problem'] for x in report['problems']))

    def test_over_wide_line_is_refused(self):
        # Sixteen syllables at the fixed 12-pixel advance is 192px, past the budget.
        report = self.gate([self.entry(self.story, '가' * 16)])
        self.assertTrue(any('over the' in x['problem'] for x in report['problems']))

    def test_widest_allowed_line_passes(self):
        report = self.gate([self.entry(self.story, '가' * 15)])
        self.assertEqual(report['status'], 'PASS', report['problems'])

    def test_unencodable_character_is_refused(self):
        report = self.gate([self.entry(self.story, '한글과 ㄱㄴ 자모')])
        self.assertTrue(any('cannot encode' in x['problem'] for x in report['problems']))

    def test_untranslated_japanese_is_refused(self):
        report = self.gate([self.entry(self.story, self.story['ja'])])
        self.assertTrue(any('kana or CJK' in x['problem'] for x in report['problems']))

    def test_duplicate_id_is_refused(self):
        report = self.gate([self.entry(self.story, '첫 번역'), self.entry(self.story, '두 번째')])
        self.assertTrue(any('already translated' in x['problem'] for x in report['problems']))

    def test_line_count_change_is_refused_by_default(self):
        # This is the check that catches a translation written against the wrong
        # record: a misaligned line usually has a different shape.
        two_lines = next(r for r in sheet_records() if r['text_class'] == 'story' and len(r['ja_lines']) == 2
                         and r['line_budget_pixels'] == 180)
        report = self.gate([self.entry(two_lines, '한 줄뿐인 번역')])
        self.assertTrue(any('source lines' in x['problem'] for x in report['problems']))

    def test_line_count_change_can_be_meant(self):
        two_lines = next(r for r in sheet_records() if r['text_class'] == 'story' and len(r['ja_lines']) == 2
                         and r['line_budget_pixels'] == 180)
        report = self.gate([self.entry(two_lines, '한 줄뿐인 번역', line_count_change_ok=True)])
        self.assertEqual(report['status'], 'PASS', report['problems'])

    def test_ascii_comma_is_refused(self):
        report = self.gate([self.entry(self.story, '쉼표, 있음')])
        self.assertTrue(any('ASCII comma' in x['problem'] for x in report['problems']))

    def test_japanese_comma_is_allowed(self):
        report = self.gate([self.entry(self.story, '쉼표、 있음')])
        self.assertEqual(report['status'], 'PASS', report['problems'])

    def test_empty_literal_is_refused(self):
        # TextPet stops the whole compile on "", so the gate has to see it first.
        report = self.gate([self.entry(self.story, '')])
        self.assertTrue(any('empty literal' in x['problem'] for x in report['problems']))

    def test_emptied_source_line_is_refused(self):
        # Batch 018 emptied `・・・ですよ`: the page still drew, the words were gone.
        two = next(r for r in sheet_records() if r['text_class'] == 'story' and r['revision'] == 'both'
                   and len(r['ja_lines']) == 2 and all(len(x.strip()) > 1 for x in r['ja_lines']))
        report = self.gate([self.entry(two, '첫 줄만 옮김\n')])
        self.assertTrue(any('is empty under source line' in x['problem'] for x in report['problems']))

    def test_lone_particle_line_may_be_emptied(self):
        # Archive 214 folds a lone ` を` into the name before it; that is the one
        # emptied line the rule allows, and the rest of the entry is clean.
        particle = next(r for r in sheet_records() if r['id'] == 'archive/214/script/4/literal/1')
        report = self.gate([self.entry(particle, '\n 바쳐라...」\n라고、쓰여 있다')])
        self.assertEqual(report['problems'], [])

    def test_revision_split_needs_both_wordings(self):
        report = self.gate([self.entry(self.differs, '한쪽만 쓴 번역')])
        self.assertTrue(any('only one Korean line given' in x['problem'] for x in report['problems']))

    def aquaman(self):
        # Archive 504 names Aquaman in Blue Moon and Gutsman in Red Sun.
        return next(r for r in sheet_records() if r['id'] == 'archive/504/script/0/literal/0')

    def test_red_sun_line_that_says_something_else_needs_its_own_wording(self):
        # The Red Sun wording used to fall back to the Blue Moon one, and Red Sun
        # showed 아쿠아맨 over the Gutsman scene.
        record = self.aquaman()
        report = self.gate([self.entry(record, '아쿠아맨!!', ko_red_sun='아쿠아맨!!',
                                       ja_red_sun=record['ja_red_sun'])])
        self.assertTrue(any('repeats the Blue Moon line' in x['problem'] for x in report['problems']))

    def test_red_sun_line_with_its_own_wording_passes(self):
        record = self.aquaman()
        report = self.gate([self.entry(record, '아쿠아맨!!', ko_red_sun='거츠맨!!',
                                       ja_red_sun=record['ja_red_sun'])])
        self.assertEqual(report['problems'], [])

    def test_spacing_only_difference_may_share_a_wording(self):
        from check_story_translation import spacing_only
        record = next(r for r in sheet_records() if r['revision'] == 'differs'
                      and spacing_only(r['ja'], r['ja_red_sun']))
        ko = '\n'.join('번역' for _ in record['ja_lines'])
        report = self.gate([self.entry(record, ko, ko_red_sun=ko, ja_red_sun=record['ja_red_sun'])])
        self.assertEqual(report['problems'], [])

    def test_red_sun_wording_is_measured_too(self):
        record = self.aquaman()
        report = self.gate([self.entry(record, '아쿠아맨!!', ko_red_sun='가' * 16,
                                       ja_red_sun=record['ja_red_sun'])])
        self.assertTrue(any(x['problem'].startswith('ko_red_sun: line 0') and 'over the' in x['problem']
                            for x in report['problems']))

    def test_stale_red_sun_source_is_refused(self):
        record = self.aquaman()
        report = self.gate([self.entry(record, '아쿠아맨!!', ko_red_sun='거츠맨!!', ja_red_sun='ガッツマン!')])
        self.assertTrue(any('does not show the Red Sun source' in x['problem'] for x in report['problems']))

    def kidnapper(self):
        # The kidnapper's mail reads down the columns from the right:
        # ひろばにいる おじいさんに ききな.
        return next(r for r in sheet_records() if r['id'] == 'archive/007/script/1/literal/8')

    def test_riddle_that_still_reads_passes(self):
        report = self.gate([self.entry(self.kidnapper(), '보께아있광\n아물버는장\n라어지할에')])
        self.assertEqual(report['problems'], [])

    def test_riddle_that_no_longer_reads_is_refused(self):
        # Two letters swapped: still Korean, still three lines of five, so every
        # other rule passes it, but the columns no longer say where to go.
        report = self.gate([self.entry(self.kidnapper(), '께보아있광\n아물버는장\n라어지할에')])
        self.assertTrue(any('riddle no longer reads' in x['problem'] for x in report['problems']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
