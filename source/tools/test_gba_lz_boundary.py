"""Format contract fixtures for the literal LZ encoder and strict decoder."""
import unittest
from build_opening_poc import lz_literal
from verify_tpi_index import lz77_decompress

class LzBoundary(unittest.TestCase):
    def test_all_group_boundaries_and_empty(self):
        for size in [0,1,7,8,9,15,16,17,255,256,4095,4096]:
            source=bytes(i%256 for i in range(size))
            stream=lz_literal(source)
            decoded,consumed=lz77_decompress(stream,0)
            self.assertEqual(decoded,source)
            self.assertEqual(consumed,len(stream))
    def test_truncated_and_invalid_backref_rejected(self):
        good=lz_literal(bytes(range(17)))
        for stream in [good[:-1],b'\x10\x03\x00\x00\x80\x00\x00',b'\x10\x01',b'\x11\x00\x00\x00']:
            with self.assertRaises(ValueError):lz77_decompress(stream,0)
if __name__=='__main__':unittest.main()
