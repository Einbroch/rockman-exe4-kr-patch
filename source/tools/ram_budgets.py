"""Fixed RAM destinations of compressed text archives and their size budgets.

Translation makes an archive grow (a syllable is four bytes, a kana one), and an
archive the game decodes to a fixed address can run into the next buffer. The
mail screen decodes archive 7 (bodies) at 0x02028000 and archive 6 (header
names) at 0x0202B000, 12,288 bytes later; the Korean archive 7 is 17,492 bytes,
so the header names overwrote the later mails. The header buffer is moved past
it, and every build checks each archive in the budget table.
"""
import json
from verify_tpi_index import lz77_decompress

SPEC='tools/specs/exe4_ram_budgets_v1.json'


def header_move(p,key,rom):
    s=json.loads((p/SPEC).read_text(encoding='utf-8'))['mail_header_move']
    writes=[]
    for at in s['profiles'][key]['literals']:
        if int.from_bytes(rom[at:at+4],'little')!=s['from']:raise ValueError('mail header buffer literal drift')
        writes.append((at,s['to'].to_bytes(4,'little'),'mail header archive 6 decode buffer moved past archive 7'))
    return writes


def check(p,archive,decoded_size):
    budgets=json.loads((p/SPEC).read_text(encoding='utf-8'))['budgets']
    limit=budgets.get(str(archive))
    if limit is not None and decoded_size>limit:
        raise ValueError(f'archive {archive} decodes to {decoded_size} bytes, over its {limit}-byte RAM budget')
    return limit


def audit(p,rom,pointer_words):
    """Decoded size of every budgeted archive as the ROM's own claims point."""
    out={}
    for archive,at in pointer_words.items():
        ptr=int.from_bytes(rom[at:at+4],'little')&0x01FFFFFF
        data,_=lz77_decompress(rom,ptr)
        out[archive]=(len(data),check(p,archive,len(data)))
    return out
