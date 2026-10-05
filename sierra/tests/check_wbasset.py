#!/usr/bin/env python3
"""Exercise expanded-resource ownership, partial I/O and failing services."""
from pathlib import Path
import subprocess
import tempfile
from check_wbres import exercise, fixture, idle_rom, start_cpu
from check_lzw import expand, packed, resources


def asset_fixture(data, length):
    header = b'\x12\x34\x01' + length.to_bytes(2, 'little') + len(data).to_bytes(2, 'little')
    files = fixture(data, header=header)
    files['/game/logDir'] = files.pop('/game/picDir')
    return files


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-asset-') as temp:
        d, emulator = start_cpu(idle_rom(Path(temp) / 'idle.rom'))
        try:
            d.write(0xffdf, b'\0')
            d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01')
            d.write(0xffa8, bytes(range(8)))
            _, data, reference = next(resources())  # real KQ1 logic 0, 8950 bytes
            files = asset_fixture(data, len(reference))
            for base, database, window in [(0xe000, 0x2000, 0x8000), (0xd000, 0x1000, 0xa000)]:
                assert exercise(d, files, module='wbasset', blocks=2,
                                base=base, database=database, window=window) == (0, reference)
            plain = bytes(range(256)) * 64  # exact two-block boundary
            assert exercise(d, asset_fixture(plain, len(plain)), module='wbasset', blocks=2) == (0, plain)
            # A long KwKwK chain grows output to the full 16-bit length limit.
            codes = [256,65] + list(range(258,618))
            produced = sum(range(1,362))
            codes += [65] * (65535 - produced) + [257]
            width, nextcode, previous, stream = 9, 258, False, []
            for value in codes:
                stream.append((value, width))
                if value == 256:
                    width, nextcode, previous = 9, 258, False
                elif value != 257:
                    if previous:
                        nextcode += 1
                        if nextcode == 1 << width and width < 11:
                            width += 1
                    previous = True
            data = packed(stream)
            reference = expand(data)
            assert len(reference) == 65535
            assert exercise(d, asset_fixture(data, len(reference)), module='wbasset', blocks=8) == (0, reference)
            for options in [dict(zero_read=True), dict(seek_error=True), dict(write_error=True),
                            dict(allocation_error=True), dict(map_failure=1),
                            dict(map_failure=2), dict(unmap_error=True), dict(terminal=False)]:
                error, output = exercise(d, files, module='wbasset', blocks=2, **options)
                assert error and not output, options
            invalid = packed([(n, 9) for n in [256, 65, 260, 257]])
            error, output = exercise(d, asset_fixture(invalid, 3), module='wbasset', blocks=1)
            assert error and not output
            print('PASS: native mapped logic 0, relocation, exact 16KB plain and 65535-byte expanded resources, partial I/O, malformed LZW, allocation/map/unmap/read/write errors and cleanup')
        finally:
            d.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
