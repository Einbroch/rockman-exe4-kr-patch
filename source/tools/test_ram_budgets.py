"""Every budgeted archive, decoded through each of its claims in the final ROMs,
must fit its fixed RAM buffer, and the mail header buffer must sit past archive 7."""
import json,sys,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'tools'))
from analyze_project import PROFILES,sha
from verify_tpi_index import parse_tpi,lz77_decompress
spec=json.loads((p/'tools/specs/exe4_ram_budgets_v1.json').read_text(encoding='utf-8'))
INDEX={'blue_moon':'exe4bm-v10.tpi','red_sun':'exe4rs-v11.tpi'}

def product(key):
    path=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_menu_descriptions_story_korean_development.gba'
    return path.read_bytes()

class RamBudgets(unittest.TestCase):
    def test_each_claim_decodes_within_its_budget(self):
        for key in PROFILES:
            rom=product(key);rows=parse_tpi(p/'external/textpet-indexes'/INDEX[key])
            for archive,limit in spec['budgets'].items():
                for claim in rows[int(archive)]['pointers']:
                    at=int.from_bytes(rom[claim:claim+4],'little')&0x01FFFFFF
                    size=len(lz77_decompress(rom,at)[0])
                    self.assertLessEqual(size,limit,(key,archive,hex(claim)))
    def test_mail_header_buffer_moved_past_archive_7(self):
        move=spec['mail_header_move']
        self.assertGreaterEqual(move['to'],0x02028000+spec['budgets']['7'])
        self.assertLessEqual(move['to']+spec['budgets']['6'],0x0202DE00)
        for key in PROFILES:
            rom=product(key)
            for at in move['profiles'][key]['literals']:
                self.assertEqual(int.from_bytes(rom[at:at+4],'little'),move['to'],(key,hex(at)))
            self.assertNotIn(move['from'].to_bytes(4,'little'),[rom[i:i+4] for i in move['profiles'][key]['literals']])

if __name__=='__main__':unittest.main(verbosity=2)
