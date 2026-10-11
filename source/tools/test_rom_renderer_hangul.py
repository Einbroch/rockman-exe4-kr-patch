"""The ROM renderer's F9 slot points at the Hangul hook in both final ROMs, the
hook's bytes reassemble exactly, it returns with pop {pc} (the table calls with
mov lr, pc), and its bank literal is the dialogue Hangul bank minus one glyph."""
import json,sys,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'tools'))
from analyze_project import PROFILES,sha
from extended_dialogue import assemble_verified
spec=json.loads((p/'tools/specs/exe4_rom_renderer_hangul_v1.json').read_text(encoding='utf-8'))

class RomRendererHangul(unittest.TestCase):
    def test_slot_hook_bytes_and_bank(self):
        for key in PROFILES:
            path=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_descriptions_korean_development.gba'
            rom=path.read_bytes();m=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
            self.assertEqual(sha(rom),m['output_sha256'])
            e=m['extension'];isa=e['rom_renderer_hangul']['machine_code'];prof=spec['profiles'][key]
            self.assertEqual(int.from_bytes(rom[prof['slot']:prof['slot']+4],'little'),isa['address']|1)
            code,_=assemble_verified('\n'.join(x['mnemonic']+' '+x['operands'] for x in isa['instructions']),isa['address'],isa['literal_values'])
            at=isa['address']-0x08000000;self.assertEqual(rom[at:at+len(code)],code)
            ops=[(x['mnemonic'],x['operands']) for x in isa['instructions']]
            self.assertIn(('pop','{pc}'),ops);self.assertNotIn(('bx','r7'),ops[ops.index(('pop','{pc}'))-3:])
            self.assertEqual(isa['literal_values']['bank'],0x08000000+e['normal_font_offset']+spec['legacy_glyphs']*0x60-0x60)
            self.assertEqual(isa['literal_values']['legacy'],prof['legacy_handler'])

if __name__=='__main__':unittest.main(verbosity=2)
