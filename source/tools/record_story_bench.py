"""Bind the story gate's negative tests to a log, so "the gate passed" is only
ever reported next to proof that the gate can fail."""
import json, os, subprocess, sys
from pathlib import Path
from analyze_project import sha

p = Path(__file__).resolve().parents[1]
suites = ['tools/test_story_gate.py', 'tools/test_story_prepare.py',
          'tools/test_option_widths.py', 'tools/test_glossary_terms.py']
log = p / 'analysis/story_gate_bench.log'
out = b''
commands = []
for suite in suites:
    c = [sys.executable, str(p / suite)]
    commands.append(c)
    r = subprocess.run(c, capture_output=True, env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
    out += ('=== ' + suite + '\n').encode() + r.stdout + r.stderr
    log.write_bytes(out)
    if r.returncode:
        raise SystemExit(suite + ' failed; see ' + str(log))
report = {
    'schema': 1,
    'status': 'PASS',
    'scope': ('one real sheet record per case: unknown id, binding drift, missing binding, short class, fourth line, '
              'over-wide line, widest allowed line, unencodable character, untranslated Japanese, duplicate id, '
              'revision split, line-count change, ASCII comma, empty literal, emptied source line (a lone particle line excepted), '
              'a Red Sun line that says something else given the Blue Moon Korean again, a Red Sun wording '
              'measured against its own source, a stale Red Sun source, a scrambled riddle whose Korean no longer '
              'reads back its message; plus clean entries including the Japanese '
              'comma, a Red Sun line with its own wording, one that differs in spacing only and a riddle that still reads. '
              'Separately: the wording-resolution rule, including that two archives sharing a script path keep '
              'their own lines and that a Red Sun line resolves by its own source and never falls back to the '
              'Blue Moon wording unless the sources differ in spacing alone; and the menu-option row rule, including that this ROM really does put '
              'two options on one row and that a row pushed past its budget is refused; and the glossary-term '
              'rule, including that the 해님/오텐코 님 drift it was written for is refused again if reintroduced '
              'and that a Red Sun Korean is held to the Red Sun source, and that a battle chip is called what the '
              'chip catalogue calls it (메톨가드, not 메트가드)'),
    'limitation': 'these prove the gate refuses; they do not prove a passing line was drawn on screen',
    'commands': commands,
    'log': log.relative_to(p).as_posix(),
    'log_sha256': sha(log.read_bytes()),
    'tests': 51,
    'inputs': {name: sha((p / name).read_bytes()) for name in [
        'tools/test_story_gate.py', 'tools/test_story_prepare.py', 'tools/test_option_widths.py',
        'tools/test_glossary_terms.py', 'tools/check_glossary_terms.py', 'translations/glossary.tsv',
        'tools/check_option_widths.py', 'tools/prepare_story_batch.py',
        'tools/check_story_translation.py', 'tools/extract_story_text.py',
        'tools/survey_dialogue_layout.py', 'tools/survey_dialogue_population.py',
        'translations/story_source.jsonl', 'external/textpet-plugins/exe4-utf8.tbl']},
}
(p / 'analysis/story_bench.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('story bench PASS; 51 cases over the gate, the wording-resolution rule, the option-row rule '
      'and the glossary-term rule')
