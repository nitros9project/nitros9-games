#!/usr/bin/env python3
"""Compare native F0-F7 decoding against the existing actual 6809 renderer."""
from pathlib import Path
import random
import shutil
import socket
import subprocess
import sys
import time
from check_instances import Debugger
from check_wbres import exercise, fixture

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
    rng = random.Random(6809)
    data = bytearray()
    for _ in range(40):
        data.extend([0xF0, rng.randrange(16), 0xF2, rng.randrange(16), 0xF6])
        for _ in range(5):
            data.extend([rng.randrange(160), rng.randrange(168)])
    data.append(255)
    yield bytes(data)


def main():
    assembler = shutil.which('lwasm.orig') or shutil.which('lwasm')
    defs = SIERRA.parents[1] / 'nitros9' / 'defs'
    references = [(payload, render(SIERRA / 'kingsquest1', payload, assembler, defs)) for payload in pictures()]
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    emulator = subprocess.Popen(['xroar', '-machine', 'coco3', '-ui', 'null', '-ao', 'null',
        '-ram', '2048', '-gdb', '-gdb-port', str(port), '-timeout', '300',
        '-no-bas', '-no-extbas', '-no-altbas'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = None
    try:
        time.sleep(.01)
        for _ in range(50):
            try:
                d = Debugger(port)
                break
            except ConnectionRefusedError:
                time.sleep(.1)
        assert d is not None
        d.write(0xFFDF, b'\0')
        d.write(0xFF90, b'\x4c')
        d.write(0xFF91, b'\x01')
        for address in (0xFF92, 0xFF93, 0xFF01, 0xFF03, 0xFF21, 0xFF23):
            d.write(address, b'\0')
        d.write(0xFFA8, bytes(range(8)))
        for base, database in ((0xE000, 0x2000), (0xD000, 0x1000)):
            for payload, reference in references:
                error, actual = exercise(d, fixture(payload), base=base, database=database, module='wbdecode')
                assert not error, (error, payload.hex(), base, database)
                assert actual == reference, f'decoder pixels differ for {payload.hex()}'
        for payload in (b'\xf8\xff', b'\xf9\x00\xff', b'\xfa\xff', b'\xfb\xff',
                        b'\xf0\xff', b'\xf0\x10\xff', b'\xf2\x10\xff',
                        b'\xf6\x01\xff', b'\xf6\xff', b'\xff\xff', b'\x00\xff'):
            error, output = exercise(d, fixture(payload), module='wbdecode')
            assert error and not output, payload.hex()
        print('PASS: native F0-F7 decoding matches every CoCo reference pixel at two code/data locations; immutable code, bounded malformed/unsupported input')
    finally:
        if d:
            d.s.close()
        emulator.terminate()
        try:
            emulator.wait(timeout=2)
        except subprocess.TimeoutExpired:
            emulator.kill()
            emulator.wait(timeout=2)


if __name__ == '__main__':
    main()
