#!/usr/bin/env python3
"""Run wbpic's actual 6809 code on XRoar with mocked OS-9/graphics services.

This checks conversion, relocation, chunk boundaries and resource cleanup;
it does not emulate VICKY or verify the Wild Bits driver implementation.
"""
import argparse
from pathlib import Path
import re
import socket
import subprocess
import time
from check_instances import Debugger, symbols

VIEWER = Path(__file__).resolve().parents[1] / 'wildbits'


def exercise(d, base, payload, allocation_error=False, map_failure=0, unmap_failure=False, database=0x2000, terminal=b"v1", window=0x4000, terminal_mismatch=False):
    syms = symbols(VIEWER / 'wbpic.map')
    calls = {base + int(m[1], 16): int(m[2], 16) for m in re.finditer(
        r'^([0-9A-F]{4}) 103F([0-9A-F]{2}).*os9',
        (VIEWER / 'wbpic.list').read_text(), re.M)}
    d.write(base, (VIEWER / 'wbpic').read_bytes())
    d.write(database + 0x1000, b'picture\r')
    for address in calls:
        d.breakpoint(address)
    d.regs(pc=base + syms['start'], s=database + 0x1EF0, dp=database >> 8, u=database, x=database + 0x1000, cc=0x50)
    position = 0
    mapped = None
    maps = 0
    freed = closed = 0
    unmap_failed = False
    frame = bytearray(10 * 8192)
    owned = False
    opened = False
    registrations = sleeps = 0
    for iteration in range(2500):
        d.call('c')
        r = d.regs()
        service = calls[r['pc']]
        updates = {'cc': r['cc'] & ~1, 'pc': r['pc'] + 3}
        if service == syms['F$Exit']:
            assert mapped is None
            assert closed == int(opened)
            assert freed == int(owned)
            assert registrations == 0
            if owned and not map_failure:
                assert sleeps == 1
            for address in calls:
                d.breakpoint(address, False)
            return r['b'], frame
        if service == syms['I$Open']:
            updates['a'] = 3
            opened = True
        elif service == syms['I$Close']:
            closed += 1
        elif service == syms['I$SetStt'] and r['b'] == syms['SS.AScrn']:
            if allocation_error:
                updates.update(cc=r['cc'] | 1, b=syms['E$WADef'])
            else:
                owned = True
                updates['x'] = 99  # allocation return is deliberately not the block
        elif service == syms['I$GetStt']:
            if r['b'] == syms['SS.DevNm']:
                name = b'other' if terminal_mismatch and r['a'] == 1 else terminal
                d.write(r['x'], name + b'\0')
            else:
                assert r['b'] == 0xE4
                updates['x'] = 0x30
        elif service == syms['F$MapBlk']:
            assert mapped is None and r['b'] == 1
            maps += 1
            if maps == map_failure:
                updates.update(cc=r['cc'] | 1, b=syms['E$MemFul'])
            else:
                mapped = r['x'] - 0x30
                assert 0 <= mapped < 10
                d.write(window, frame[mapped * 8192:(mapped + 1) * 8192])
                updates['u'] = window
        elif service == syms['F$ClrBlk']:
            assert mapped is not None and r['u'] == window and r['b'] == 1
            if unmap_failure and not unmap_failed:
                unmap_failed = True
                updates.update(cc=r['cc'] | 1, b=syms['E$MemFul'])
            else:
                frame[mapped * 8192:(mapped + 1) * 8192] = d.read(window, 8192)
                mapped = None
        elif service == syms['I$Read']:
            if r['a'] == 0:
                d.write(r['x'], b'q')
                updates['y'] = 1
            elif position == len(payload):
                updates.update(cc=r['cc'] | 1, b=syms['E$EOF'])
            else:
                count = min(r['y'], len(payload) - position, 97)  # short reads
                d.write(r['x'], payload[position:position + count])
                position += count
                updates['y'] = count
        elif service == syms['I$SetStt'] and r['b'] == 0xE1:
            if r['x']:
                assert r['x'] == 0x8182 and registrations == 0
                registrations = 1
                d.write(database + syms['paused'], b'\x81')
            else:
                assert registrations == 1
                registrations = 0
        elif service == syms['F$Sleep']:
            assert r['x'] == 2
            sleeps += 1
            d.write(database + syms['paused'], b'\0')
        elif service == syms['I$SetStt'] and r['b'] == syms['SS.FScrn']:
            assert mapped is None and owned
            freed += 1
        elif service == syms['I$SetStt'] and r['b'] == 0xCF:
            assert r['u'] == 17 and r['y'] == 0
            assert len(d.read(r['x'], 68)) == 68
        else:
            assert service in (syms['F$Icpt'], syms['I$SetStt']), (service, r)
        d.regs(**updates)
    raise AssertionError('viewer did not exit')


def check_signals(d):
    syms = symbols(VIEWER / 'wbpic.map')
    base = 0x8000
    d.write(base, (VIEWER / 'wbpic').read_bytes())
    for database in (0x2000, 0x6000):
        d.write(database + syms['paused'], b'\0\0')
        d.write(database + syms['aborted'], b'\0')
    d.breakpoint(0x1D00)
    for database, signal, expected in [(0x2000, 0x81, 0x81), (0x6000, 0x81, 0x81),
                                        (0x2000, 0x82, 0), (0x6000, 0x82, 0)]:
        # RTI restores a full 6809 interrupt frame; DP is deliberately unrelated.
        frame = bytes.fromhex('d00000770000000000001d00')
        d.write(0x1DD0, frame)
        d.regs(pc=base + syms['intercept'], u=database, b=signal, dp=0x77, s=0x1DD0)
        d.call('c')
        assert d.regs()['pc'] == 0x1D00
        assert d.read(database + syms['paused'], 1) == bytes([expected])
    d.breakpoint(0x1D00, False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--picture', type=Path, help='also test a real exported combined buffer')
    args = parser.parse_args()
    picture = args.picture.read_bytes() if args.picture else None
    if picture is not None and len(picture) != 160 * 168:
        parser.error('exported picture must contain exactly 26880 combined bytes')
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    emulator = subprocess.Popen(['xroar', '-machine', 'coco3', '-ui', 'null', '-ao', 'null',
        '-ram', '2048', '-gdb', '-gdb-port', str(port), '-timeout', '300',
        '-no-bas', '-no-extbas', '-no-altbas'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(.1)
        for attempt in range(50):
            try:
                d = Debugger(port)
                break
            except ConnectionRefusedError:
                time.sleep(.1)
        else:
            raise RuntimeError('XRoar debugger did not start')
        d.write(0xFFDF, b'\0')
        d.write(0xFF90, b'\x4c')
        d.write(0xFF91, b'\x01')
        for address in (0xFF92, 0xFF93, 0xFF01, 0xFF03, 0xFF21, 0xFF23):
            d.write(address, b'\0')
        d.write(0xFFA8, bytes(range(8)))
        check_signals(d)
        payload = bytes((i * 17 + i // 160) & 255 for i in range(160 * 168))
        expected = bytes(value for byte in payload for value in ((byte & 15) + 1,) * 2)
        code, frame = exercise(d, 0x8000, payload)
        assert code == 0 and frame[:len(expected)] == expected
        assert frame[len(expected):] == bytes([1]) * (len(frame) - len(expected))
        code, frame = exercise(d, 0xA000, payload, database=0x6000, terminal=b'v2', window=0xC000)
        assert code == 0 and frame[:len(expected)] == expected
        for bad in (payload[:-1], payload + b'!'):
            code, frame = exercise(d, 0x8000, bad)
            assert code != 0
        code, frame = exercise(d, 0x8000, payload, unmap_failure=True)
        assert code == symbols(VIEWER / 'wbpic.map')['E$MemFul']
        code, frame = exercise(d, 0xA000, payload, map_failure=12)
        assert code == symbols(VIEWER / 'wbpic.map')['E$MemFul']
        if picture is not None:
            code, frame = exercise(d, 0xA000, picture, database=0x6000, terminal=b'v2', window=0xC000)
            reference = bytes(value for byte in picture for value in ((byte & 15) + 1,) * 2)
            assert code == 0 and frame[:len(reference)] == reference
            print('PASS: real exported game picture through native viewer')
        code, frame = exercise(d, 0x8000, payload, terminal_mismatch=True)
        assert code == symbols(VIEWER / 'wbpic.map')['E$IllArg']
        code, frame = exercise(d, 0xA000, payload, allocation_error=True)
        assert code == symbols(VIEWER / 'wbpic.map')['E$WADef']
        print('PASS: actual 6809 pixels, short reads, mapping boundaries, relocation/error cleanup, ownership refusal, private visibility signals')
    finally:
        if 'd' in locals():
            d.s.close()
        emulator.terminate()
        try:
            emulator.wait(timeout=2)
        except subprocess.TimeoutExpired:
            emulator.kill()
            emulator.wait(timeout=2)


if __name__ == '__main__':
    main()
