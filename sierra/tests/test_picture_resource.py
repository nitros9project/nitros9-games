#!/usr/bin/env python3
"""Resource-boundary checks for the host reference-picture bridge."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import export_picture

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

    def test_reference_transport_retry_preserves_result_and_inputs(self):
        arguments=(Path('game'),b'picture','assembler',Path('defs'))
        expected=b'actual-reference-pixels'
        with patch('export_picture._render_once',side_effect=[export_picture._ReferenceDisconnected('transport'),expected]) as runner:
            self.assertEqual(export_picture.render(*arguments),expected)
            self.assertEqual(runner.call_args_list,[unittest.mock.call(*arguments)]*2)

    def test_reference_persistent_disconnect_is_not_hidden(self):
        with patch('export_picture._render_once',side_effect=export_picture._ReferenceDisconnected('persistent')) as runner:
            with self.assertRaises(export_picture._ReferenceDisconnected):
                export_picture.render(Path('game'),b'picture','assembler',Path('defs'))
            self.assertEqual(runner.call_count,4)

    def test_reference_data_failure_and_runtime_timeout_are_not_retried(self):
        for error in (ValueError('bad picture'),AssertionError('wrong pixels'),TimeoutError('render stalled')):
            with patch('export_picture._render_once',side_effect=error) as runner:
                with self.assertRaises(type(error)):
                    export_picture.render(Path('game'),b'picture','assembler',Path('defs'))
                self.assertEqual(runner.call_count,1)


if __name__ == '__main__':
    unittest.main()
