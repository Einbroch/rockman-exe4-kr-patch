#!/usr/bin/env python3
"""Record the story runtime evidence, and make the screen prove itself.

Looking at a capture and reading Korean is worth something, but it is not a
measurement. This renders the expected line out of the Hangul glyph bitmaps
that are in the product ROM, then searches the capture for that exact ink
pattern: a match is only accepted when every pixel the glyphs say is ink holds
one single colour, and no other pixel inside the line's box holds that colour.
That rules out a partial draw, a clipped tail and a lookalike.

The glyph record is the same 96-byte, 12-row, two-pixels-per-byte cell the
dialogue extension wrote, with 3 meaning ink, 2 the shadow and 1 the
background, and every syllable advancing a fixed 12 pixels.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from analyze_project import PROFILES, sha
from build_story_batch import PRODUCT, GATE
from survey_dialogue_layout import load_table, advances

p = Path(__file__).resolve().parents[1]
RECORD_BYTES = 96
GLYPH_ROWS = 12
LEGACY_RECORDS = 442
HANGUL_ADVANCE = 12
HANGUL_FIRST = 0xAC00
LINE_PITCH = 14        # measured on the captures
LEFT_MARGIN = 51       # measured on the captures
BASELINES = (108, 122, 136)  # the three-line page this game draws
# The room scene the established cold route walks through, and the message that
# follows it. Step numbers are 1-based action indices of that route.
SCENE = {
    443: [(68, 0), (69, 1), (71, 2), (72, 3), (75, 4), (76, 5), (77, 6), (78, 7)],
    230: [(86, 0), (87, 0)],
    # The mail notification. Three scripts of archive 008 hold this same line and
    # the route does not say which one ran, so the check is against the wording,
    # which is identical in all three.
    8: [(88, 10)],
}


def glyph_ink(rom: bytes, font_at: int, index: int) -> set[tuple[int, int]]:
    cell = rom[font_at + index * RECORD_BYTES:font_at + (index + 1) * RECORD_BYTES]
    ink = set()
    for y in range(GLYPH_ROWS):
        for x in range(16):
            value = (cell[y * 8 + x // 2] >> (4 * (x % 2))) & 15
            if value == 3:
                ink.add((x, y))
    return ink


def line_mask(rom: bytes, font_at: int, line: str, table: dict[str, int],
              width_table: list[int]) -> tuple[set[tuple[int, int]], int, int]:
    """Lay the line out exactly as the renderer does: the extension's bank keeps
    the original 442 records in place and appends the syllables after them, so a
    mixed Korean/native line is one bank and two advance rules."""
    mask: set[tuple[int, int]] = set()
    pen = 0
    for ch in line:
        if HANGUL_FIRST <= ord(ch) <= 0xD7A3:
            index, advance = LEGACY_RECORDS + ord(ch) - HANGUL_FIRST, HANGUL_ADVANCE
        elif ch in table:
            index, advance = table[ch], width_table[table[ch]]
        else:
            return set(), 0, 0
        # The stored cell is 16 columns wide but the typeset width is the
        # advance, and what sits past it is not drawn. The space record, for
        # one, carries six ink pixels in columns 14 and 15 behind an advance of
        # eight; counting them would make every line with a space unmatchable.
        for x, y in glyph_ink(rom, font_at, index):
            if x < advance:
                mask.add((pen + x, y))
        pen += advance
    if not mask:
        return set(), 0, 0
    width = max(x for x, _ in mask) + 1
    height = max(y for _, y in mask) + 1
    return mask, width, height


def locate(image: Image.Image, mask: set[tuple[int, int]], width: int, height: int):
    pixels = image.load()
    iw, ih = image.size
    first = min(mask)
    hits = []
    for oy in range(ih - height + 1):
        for ox in range(iw - width + 1):
            colour = pixels[ox + first[0], oy + first[1]]
            ok = True
            for x, y in mask:
                if pixels[ox + x, oy + y] != colour:
                    ok = False
                    break
            if not ok:
                continue
            # The box must hold that colour nowhere else, or a flat block of the
            # same colour would "match" any mask.
            for y in range(height):
                for x in range(width):
                    if (x, y) not in mask and pixels[ox + x, oy + y] == colour:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                hits.append((ox, oy, colour))
    return hits


def main() -> int:
    gate = json.loads(GATE.read_text(encoding='utf-8'))
    batches = [json.loads((p / b['path']).read_text(encoding='utf-8')) for b in gate['batches']]
    wording = {e['id']: e for batch in batches for e in batch['entries']}
    verification = json.loads((p / 'analysis/story_verification.json').read_text(encoding='utf-8'))
    report = {'schema': 1, 'status': 'PASS bounded runtime: rendered-glyph pixel match on the room scene',
              'scope': 'the archive 443 morning scene and the archive 230 pickup message, on the established cold route',
              'reviewer': 'Claude direct native-resolution contact sheets of both revisions, 2026-09-20',
              'verification': {'path': 'analysis/story_verification.json',
                               'sha256': sha((p / 'analysis/story_verification.json').read_bytes())},
              'not_claimed': ['the other translated archives were reached', 'the rest of the story text is translated',
                              'whole-game/device QA', 'independent language review'],
              'profiles': {}, 'sheets': []}
    table = load_table()

    for key in PROFILES:
        product = p / 'poc/output' / (PRODUCT.format(key=key) + '.gba')
        rom = product.read_bytes()
        m = json.loads(product.with_suffix('.json').read_text(encoding='utf-8'))
        if m['output_sha256'] != sha(rom) or verification['profiles'][key]['rom_sha256'] != sha(rom):
            raise SystemExit('story product identity drift')
        font_at = m['extension']['layout'][0]['offset']
        width_table = advances(rom, m['extension']['advance_offset'] & 0x1FFFFFF)
        root = p / 'analysis/runtime' / f"{key}_story_cold_01_{m['output_sha256'][:8]}"
        receipt = json.loads((root / 'result.json').read_text(encoding='utf-8'))
        if (not receipt['complete'] or receipt['return_code'] or receipt['rom_sha256'] != sha(rom)
                or receipt['steps_expected'] != receipt['steps_captured']):
            raise SystemExit('story runtime receipt identity/completion')
        for name, digest in receipt['artifacts'].items():
            if sha((root / name).read_bytes()) != digest:
                raise SystemExit('story runtime artifact drift ' + name)

        checks, reported = [], []
        for archive, steps in SCENE.items():
            for step, script in steps:
                key_id = f'archive/{archive:03d}/script/{script}/literal/0'
                if archive == 230 and step == 87:
                    key_id = f'archive/{archive:03d}/script/0/literal/2'
                entry = wording[key_id]
                image = Image.open(root / f'step_{step:03d}.png').convert('RGB')
                matched = []
                for number, line in enumerate(entry['ko'].split('\n')):
                    mask, width, height = line_mask(rom, font_at, line, table, width_table)
                    if not mask:
                        reported.append({'step': step, 'id': key_id, 'line': number, 'text': line,
                                         'reason': 'line holds a character with no glyph record'})
                        continue
                    hits = locate(image, mask, width, height)
                    if len(hits) != 1:
                        raise SystemExit(f'{key}: {len(hits)} pixel matches for {key_id} line {number}')
                    ox, oy, colour = hits[0]
                    # Found somewhere is not found where it belongs: every line
                    # must sit on the page's baseline grid. The left margin is a
                    # separate claim and only holds for a literal that starts a
                    # message; a continuation literal resumes after whatever the
                    # game inserted before it, as the pickup line does after the
                    # item name.
                    if oy not in BASELINES:
                        raise SystemExit(f'{key}: {key_id} line {number} is off the baseline grid at y={oy}')
                    if int(key_id.rsplit('/', 1)[1]) == 0 and number == 0 and ox != LEFT_MARGIN:
                        raise SystemExit(f'{key}: {key_id} does not start at the left margin (x={ox})')
                    matched.append({'line': number, 'text': line, 'origin': [ox, oy], 'ink_rgb': list(colour),
                                    'ink_pixels': len(mask)})
                checks.append({'step': step, 'id': key_id, 'ko': entry['ko'], 'ja': entry['ja'],
                               'screenshot': f'step_{step:03d}.png',
                               'screenshot_sha256': sha((root / f'step_{step:03d}.png').read_bytes()),
                               'pixel_matched_lines': matched})
        starts = {line['origin'][0] for c in checks for line in c['pixel_matched_lines']
                  if int(c['id'].rsplit('/', 1)[1]) == 0 and line['line'] == 0}
        if starts != {LEFT_MARGIN}:
            raise SystemExit('message-opening lines did not share the left margin: ' + str(sorted(starts)))
        sheet = Image.new('RGB', (960, 180 * ((len(checks) + 3) // 4)), 'white')
        draw = ImageDraw.Draw(sheet)
        for i, check in enumerate(checks):
            x, y = i % 4 * 240, i // 4 * 180
            draw.text((x + 3, y + 3), f"{key} step {check['step']}", fill='black')
            sheet.paste(Image.open(root / check['screenshot']), (x, y + 20))
        out = p / 'analysis/visual_qa' / f'{key}_story_room_01.png'
        sheet.save(out)
        report['sheets'].append({'path': out.relative_to(p).as_posix(), 'sha256': sha(out.read_bytes())})
        report['profiles'][key] = {
            'rom_sha256': m['output_sha256'], 'route': root.relative_to(p).as_posix(),
            'receipt_sha256': sha((root / 'result.json').read_bytes()),
            'steps': receipt['steps_captured'], 'checks': checks,
            'lines_pixel_matched': sum(len(c['pixel_matched_lines']) for c in checks),
            'lines_reported_only': reported,
            'text_left_margin': LEFT_MARGIN, 'line_pitch': LINE_PITCH, 'baselines': list(BASELINES),
        }
    report['tool_sha256'] = sha(Path(__file__).read_bytes())
    (p / 'analysis/STORY_RUNTIME_QA.json').write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                      encoding='utf-8')
    for key, item in report['profiles'].items():
        print(key, 'PASS', len(item['checks']), 'messages,', item['lines_pixel_matched'],
              'lines matched pixel-exactly against the ROM glyphs,',
              len(item['lines_reported_only']), 'mixed lines reported only')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
