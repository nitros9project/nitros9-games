#!/usr/bin/env python3
"""Resource-boundary checks for the host reference-picture bridge."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'wildbits'))
from export_picture import resource


class ResourceTests(unittest.TestCase):
    def test_header_directory_and_encoding_boundaries(self):
        with tempfile.TemporaryDirectory() as temporary:
            game = Path(temporary)
            (game / 'picDir').write_bytes(b'\xff\xff\xff\x10\x00\x20')
            payload = b'\xf0\x00\xff'
            header = b'\x12\x34\x01\x03\x00\x03\x00'
            volume = game / 'vol.1'
            volume.write_bytes(bytes(32) + header + payload)
            self.assertEqual(resource(game, 1), (payload, 1, 32))
            for number in (-1, 0, 2):
                with self.assertRaises(ValueError):
                    resource(game, number)
            for broken in [b'\x00\x34' + header[2:], header[:2] + b'\x02' + header[3:],
                           header[:2] + b'\x81' + header[3:], header[:3] + b'\x04\x00' + header[5:]]:
                volume.write_bytes(bytes(32) + broken + payload)
                with self.assertRaises(ValueError):
                    resource(game, 1)
            volume.write_bytes(bytes(32) + header + payload[:-1])
            with self.assertRaises(ValueError):
                resource(game, 1)


if __name__ == '__main__':
    unittest.main()
