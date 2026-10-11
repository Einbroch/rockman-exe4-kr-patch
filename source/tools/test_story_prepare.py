"""Lock the rule that decides which Korean line a record gets.

The bug this exists for: four archives were covered by one batch and each held a
different line at script/18/literal/0. Resolving by path handed all four the
first archive's wording, and nothing downstream would have noticed — the text is
still valid Korean, still fits, still round-trips. Only the guard that an
authored line must reach at least one record caught it.
"""
import json
import unittest
from pathlib import Path

from prepare_story_batch import red_sun_wording, wording
from survey_dialogue_layout import ESCAPED_BREAK

p = Path(__file__).resolve().parents[1]
SHEET = p / 'translations/story_source.jsonl'


def record(ja):
    return {'ja': ja}


def differs(ja, ja_red_sun):
    return {'ja': ja, 'ja_red_sun': ja_red_sun}


class RedSunWording(unittest.TestCase):
    """Archive 504 names Aquaman in Blue Moon and Gutsman in Red Sun. A missing
    Red Sun wording fell back to the Blue Moon one, so Red Sun showed 아쿠아맨."""

    def test_red_sun_line_resolves_by_its_own_source(self):
        found = red_sun_wording(differs('アクアマン!!', 'ガッツマン!!'), 'script/0/literal/0', {},
                                {'アクアマン!!': '아쿠아맨!!', 'ガッツマン!!': '거츠맨!!'}, '아쿠아맨!!')
        self.assertEqual(found, ('거츠맨!!', 'source'))

    def test_red_sun_path_rule_wins_over_source(self):
        found = red_sun_wording(differs('あ', 'い'), 'script/0/literal/0', {'script/0/literal/0': '경로'},
                                {'い': '원문'}, '파랑')
        self.assertEqual(found, ('경로', 'path'))

    def test_a_line_that_differs_in_spacing_only_borrows_the_blue_moon_wording(self):
        found = red_sun_wording(differs('なにをやっているんだ!', 'なにを やっているんだ!'), 'script/4/literal/0',
                                {}, {}, '뭘 하고 있는 거야!')
        self.assertEqual(found, ('뭘 하고 있는 거야!', 'spacing'))

    def test_a_line_that_says_something_else_does_not_fall_back(self):
        found = red_sun_wording(differs('アクアマン!!', 'ガッツマン!!'), 'script/0/literal/0', {},
                                {'アクアマン!!': '아쿠아맨!!'}, '아쿠아맨!!')
        self.assertEqual(found, (None, None))


class Wording(unittest.TestCase):
    def test_path_rule_wins_over_source(self):
        ko, rule = wording(record('あ'), 'script/0/literal/0',
                           {'script/0/literal/0': '경로'}, {'あ': '원문'})
        self.assertEqual((ko, rule), ('경로', 'path'))

    def test_same_path_different_source_gets_its_own_line(self):
        scripts, by_source = {}, {'あ': '첫째', 'い': '둘째'}
        first = wording(record('あ'), 'script/18/literal/0', scripts, by_source)
        second = wording(record('い'), 'script/18/literal/0', scripts, by_source)
        self.assertEqual(first, ('첫째', 'source'))
        self.assertEqual(second, ('둘째', 'source'))

    def test_escaped_line_break_matches_a_written_newline(self):
        ko, rule = wording(record('あ' + ESCAPED_BREAK + 'い'), 'script/0/literal/0',
                           {}, {'あ\nい': '줄바꿈'})
        self.assertEqual((ko, rule), ('줄바꿈', 'source'))

    def test_unknown_record_resolves_to_nothing(self):
        self.assertEqual(wording(record('う'), 'script/0/literal/0', {}, {'あ': '가'}), (None, None))

    def test_real_sheet_has_a_shared_path_with_different_sources(self):
        """If this stops holding, the case above stops describing this ROM."""
        seen = {}
        for line in SHEET.read_text(encoding='utf-8').splitlines():
            r = json.loads(line)
            seen.setdefault(r['id'].split('/', 2)[2], set()).add(r['ja'])
        self.assertTrue(any(len(v) > 1 for v in seen.values()),
                        'no script/literal path is shared by differing source lines')


if __name__ == '__main__':
    unittest.main(verbosity=2)
