#!/usr/bin/env python3
"""Compare native F0-FA mapped decoding against the existing actual 6809 renderer."""
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
from check_instances import symbols
from check_wbres import exercise, fixture, idle_rom, start_cpu

SIERRA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIERRA / 'wildbits'))
from export_picture import render


def pictures():
    yield b'\xff'
    yield bytes([0xF0, 2, 0xF2, 7, 0xF5, 0, 0, 159, 167, 0, 0,
                 0xF4, 159, 167, 0, 0, 167, 159, 0xFF])
    yield bytes([0xF0, 4, 0xF6, 20, 20, 150, 140, 10, 140, 150, 10, 20, 20,
                 0xF1, 0xF2, 12, 0xF7, 0, 0, 0x11, 0x99, 0xE1, 0x17,
                 0xF3, 0xF0, 5, 0xF6, 239, 239, 0, 0, 0xFF])
    yield bytes([0xF0, 3, 0xF8, 0, 0, 0xFF])
    yield bytes([0xF0, 2, 0xF2, 9, 0xF6, 20, 20, 140, 20, 140, 150, 20, 150, 20, 20,
                 0xF0, 6, 0xF8, 21, 21, 0, 0, 0xF1, 0xF2, 12, 0xF8, 0, 0, 0xFF])
    rng = random.Random(6809)
    data = bytearray()
    for _ in range(8):
        data.extend([0xF0, rng.randrange(16), 0xF2, rng.randrange(16), 0xF6])
        for _ in range(5):
            data.extend([rng.randrange(160), rng.randrange(168)])
    data.append(255)
    yield bytes(data)


    data = bytearray([0xF0, 3, 0xF2, 11])
    for style in (0, 0x10, 0x20, 0x30):
        for size in range(8):
            data.extend([0xF9, style | size, 0xFA])
            for x, y in ((0, 0), (159, 167), (80, 51), (80, 102), (35 + size * 12, 75)):
                if style & 0x20:
                    data.append((size * 17 + x) % 240)
                data.extend([x, y])
    data.append(255)
    yield bytes(data)


def main():
    assembler = shutil.which('lwasm.orig') or shutil.which('lwasm')
    defs = SIERRA.parents[1] / 'nitros9' / 'defs'
    references = [(payload, render(SIERRA / 'kingsquest1', payload, assembler, defs)) for payload in pictures()]
    bootrom = tempfile.NamedTemporaryFile(prefix='sierra-cpu-idle-', suffix='.rom')
    idle_rom(bootrom.name)
    d = None
    emulator = None
    try:
        d, emulator = start_cpu(bootrom.name, timeout=900)
        d.write(0xFFDF, b'\0')
        d.write(0xFF90, b'\x4c')
        d.write(0xFF91, b'\x01')
        for address in (0xFF92, 0xFF93, 0xFF01, 0xFF03, 0xFF21, 0xFF23):
            d.write(address, b'\0')
        d.write(0xFFA8, bytes(range(8)))
        for base, database in ((0xE000, 0x2000), (0xD000, 0x1000)):
            for payload, reference in references:
                error, actual = exercise(d, fixture(payload), base=base, database=database, module='wbdecode', window=0x8000 if database == 0x2000 else 0xA000)
                assert not error, (error, payload.hex(), base, database)
                assert actual == reference, f'decoder pixels differ for {payload.hex()}'
        for payload in (b'\xf9\xff', b'\xfa\x01\xff', b'\xfb\xff',
                        b'\xf0\xff', b'\xf0\x10\xff', b'\xf2\x10\xff',
                        b'\xf6\x01\xff', b'\xf6\xff', b'\xff\xff', b'\x00\xff'):
            error, output = exercise(d, fixture(payload), module='wbdecode')
            assert error and not output, payload.hex()
        for options in ({'terminal': False}, {'allocation_error': True}, {'map_failure': 1}, {'map_failure': 6}, {'unmap_error': True}, {'write_error': True}):
            error, output = exercise(d, fixture(b'\xf0\x03\xf8\x00\x00\xff'), module='wbdecode', **options)
            assert error and not output, options
        # Execute the work-stack guard itself: the last seed fits; the next
        # must report exhaustion without overwriting the adjacent stage buffer.
        syms = symbols(SIERRA / 'wildbits/wbdecode.map')
        base, database = 0xE000, 0x2000
        d.write(base, (SIERRA / 'wildbits/wbdecode').read_bytes())
        d.write(database, bytes(syms['size']))
        d.write(database + syms['resourcebase'], database.to_bytes(2, 'big'))
        d.write(database + syms['filltop'], (4094).to_bytes(2, 'big'))
        guard = database + syms['fillstack'] + 4096
        d.write(guard, b'guard')
        for expected_error in (0, syms['E$MemFul']):
            d.write(0x1DF0, bytes.fromhex('1d00'))
            d.breakpoint(0x1D00)
            d.regs(cc=0x50, dp=database >> 8, s=0x1DF0,
                   pc=base + syms['FillPush'], a=159, b=167)
            d.call('c')
            assert d.regs()['pc'] == 0x1D00
            assert d.read(database + syms['filltop'], 2) == b'\x10\x00'
            assert d.read(database + syms['decodeerror'], 1)[0] == expected_error
            assert d.read(guard, 5) == b'guard'
            assert d.read(guard - 2, 2) == bytes([159, 167])
            d.breakpoint(0x1D00, False)
        print('PASS: native F0-FA mapped decoding matches every CoCo reference pixel at two code/data locations; immutable code, bounded malformed/unsupported input')
    finally:
        if d:
            d.s.close()
        bootrom.close()
        if emulator is not None:
            emulator.terminate()
            try:
                emulator.wait(timeout=2)
            except subprocess.TimeoutExpired:
                emulator.kill()
                emulator.wait(timeout=2)


if __name__ == '__main__':
    main()
