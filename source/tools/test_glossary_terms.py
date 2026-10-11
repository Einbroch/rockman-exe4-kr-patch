"""Lock the glossary-term rule, and show it can fail.

The bug this exists for: the story gate keeps one Korean per Japanese source
line, so a name repeated across different lines can drift without any line
failing. The story-data puzzle called the sun spirit 해님 in one chapter and
오텐코 님 in the next, and the PET menu's 데이터 도감 was 데이터 라이브러리 in
the dialogue that tells the player to open it. A later sweep found five more
names split the same way: the park's axe princess was 마사카리히메 in six lines
and 도끼공주 in sixteen, Netto's town 아키하라초 in six and 아키하라 마을 in
the rest.

These cases prove the rule refuses a drifted name, checks the Red Sun variant
as well, does not mistake a longer word for the term, and actually exercises
the terms this rule was written for (or it would pass by checking nothing).
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from check_glossary_terms import check, chip_terms, glossary, names

p = Path(__file__).resolve().parents[1]
BATCH_DIR = p / 'translations/story_korean'


def run(batches, output):
    command = [sys.executable, str(p / 'tools/check_glossary_terms.py'), '--output', str(output)]
    for batch in batches:
        command += ['--batch', str(batch)]
    return subprocess.run(command, capture_output=True, text=True, encoding='utf-8')


def first_entry_naming(term):
    for batch in sorted(BATCH_DIR.glob('*.json')):
        data = json.loads(batch.read_text(encoding='utf-8'))
        for entry in data['entries']:
            if names(entry['ja'], term):
                return data, entry
    raise AssertionError('no gated line names ' + term)


class Rule(unittest.TestCase):
    def test_a_longer_word_is_not_the_term(self):
        self.assertFalse(names('アメロッパンに チャレンジ', 'アメロッパ'))
        self.assertTrue(names('アメロッパエリアの ひろば', 'アメロッパ'))
        self.assertFalse(names('ナビカスタマイザーを きどうする', 'ナビカス'))
        self.assertTrue(names('ナビカスタマイザーと、ナビカス用プログラム', 'ナビカス'))

    def test_the_terms_this_rule_was_written_for_are_exercised(self):
        _problems, usage = check(sorted(BATCH_DIR.glob('*.json')), glossary())
        for term in ('おてんこさま', 'ドラッキー', 'データライブラリ', 'バトルチップ', '太陽の光',
                     'マサカリひめ', 'ウィザーモンキー', '秋原町', 'ヌポポぞう', 'ナビカス'):
            self.assertGreater(usage[term], 0, term + ' is never checked')
        self.assertGreater(sum(usage.values()), 1000, 'the rule checks almost nothing')


class Gate(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.output = Path(self.dir.name) / 'report.json'
        self.batch = Path(self.dir.name) / 'batch_probe.json'

    def tearDown(self):
        self.dir.cleanup()

    def test_the_batches_as_written_pass(self):
        self.assertEqual(run(sorted(BATCH_DIR.glob('*.json')), self.output).returncode, 0)

    def test_the_drift_that_happened_is_rejected(self):
        data, entry = first_entry_naming('おてんこさま')
        for item in data['entries']:
            if item['id'] == entry['id']:
                item['ko'] = item['ko'].replace('오텐코 님', '해님')
        self.batch.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        result = run([self.batch], self.output)
        self.assertEqual(result.returncode, 1)
        self.assertIn('おてんこさま should read 오텐코 님', result.stdout)

    def test_a_chip_is_called_what_the_folder_calls_it(self):
        # The dialogue said 메트가드 where the chip folder says 메톨가드, and a trade
        # asked for a chip the player could not find under that name.
        terms = chip_terms()
        self.assertIn(('メットガード', '메톨가드'), {(t['source'], t['korean']) for t in terms})
        data, entry = first_entry_naming('メットガード')
        for item in data['entries']:
            if item['id'] == entry['id']:
                item['ko'] = item['ko'].replace('메톨가드', '메트가드')
        self.batch.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        result = run([self.batch], self.output)
        self.assertEqual(result.returncode, 1)
        self.assertIn('メットガード should read 메톨가드', result.stdout)

    def test_the_red_sun_korean_follows_the_red_sun_source(self):
        # Archive 504 names Aquaman in Blue Moon and Gutsman in Red Sun; a term
        # only the Red Sun line names binds only the Red Sun Korean.
        entry = {'id': 'archive/504/script/0/literal/0', 'ja': 'アクアマン!!', 'ja_red_sun': 'ドラッキー!!',
                 'ko': '아쿠아맨!!', 'ko_red_sun': '아쿠아맨!!'}
        self.batch.write_text(json.dumps({'entries': [entry]}, ensure_ascii=False), encoding='utf-8')
        problems, _usage = check([self.batch], glossary())
        self.assertEqual([(x['revision'], x['term']) for x in problems], [('red_sun', 'ドラッキー')])
        entry['ko_red_sun'] = '드락키!!'
        self.batch.write_text(json.dumps({'entries': [entry]}, ensure_ascii=False), encoding='utf-8')
        self.assertEqual(check([self.batch], glossary())[0], [])

    def test_the_red_sun_variant_is_checked_too(self):
        data, entry = first_entry_naming('ドラッキー')
        for item in data['entries']:
            if item['id'] == entry['id']:
                item['ko_red_sun'] = item['ko'].replace('드락키', '드래키')
        self.batch.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        result = run([self.batch], self.output)
        self.assertEqual(result.returncode, 1)
        self.assertIn('red_sun', result.stdout)


if __name__ == '__main__':
    unittest.main()
