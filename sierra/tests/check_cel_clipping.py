#!/usr/bin/env python3
"""Execute selected-cel position reconciliation in both production owners."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def main():
    cases = []
    # Sweep each legal dimension and every position/horizon/flag byte.
    for field, limit in enumerate((256, 256, 161, 169, 256, 256)):
        for value in range(1 if field in (2, 3) else 0, limit):
            case = [150, 1, 20, 20, 48, 0]
            case[field] = value
            cases.append(tuple(case))
    cases += [(x, y, width, height, horizon, flags)
              for x, width in ((159, 1), (159, 2), (255, 160), (0, 160))
              for y, height in ((0, 1), (0, 168), (167, 168), (1, 3))
              for horizon in (0, 48, 167, 255) for flags in (0, 8)]
    with tempfile.TemporaryDirectory(prefix='sierra-cel-clipping-') as name:
        tmp = Path(name)
        coco, cs = compile_module(ROOT/'objs/mnln.asm', tmp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame',
                                    defines=('WILDBITS=1',))
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=900)
        calls = 0
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            for owner, code, syms, bases in (
                    ('CoCo', coco, cs, (0x8000, 0x9000)),
                    ('native', native, ns, (0x9000, 0xa000))):
                private = 0x1000 if owner == 'native' else 0
                for base in bases:
                    d.write(base, code)
                    expected_private = bytearray(syms['size']) if private else None
                    if private:
                        d.write(private, expected_private+b'GH')
                    entry = base+syms['ViewPositionCel' if private else 'SetCelClip']
                    done = base+syms['ViewCelClipDone' if private else 'SetCelRet']
                    d.breakpoint(done)
                    for x, y, width, height, horizon, flags in cases:
                        record = bytearray(range(43))
                        record[3:5] = bytes((x, y))
                        record[0x1c:0x1e] = bytes((width, height))
                        record[0x25:0x27] = bytes((0xa1, flags))
                        expected = bytearray(record)
                        # CoCo's original byte sum is preserved; native also
                        # catches carry, so off-screen positions cannot wrap.
                        right = x+width if private else (x+width) & 255
                        if right > 160:
                            expected[3] = 160-width
                            expected[0x25] |= 4
                        if height-1 > y:
                            expected[4] = height-1
                            expected[0x25] |= 4
                            if height-1 <= horizon and not flags & 8:
                                expected[4] = (horizon+1) & 255
                        d.write(0x6fff, b'G'+record+b'H')
                        address = private+syms['vmhorizon'] if private else 0x1d6
                        d.write(address, bytes((horizon,)))
                        d.write(0x7ef0, b'STACK')
                        d.regs(pc=entry, s=0x7ef0, x=0x7000 if private else 0x4567,
                               u=0x7777 if private else 0x7000, y=0x7654,
                               a=width, b=height, dp=private >> 8, cc=0x50)
                        d.call('c'); regs = d.regs()
                        assert regs['pc'] == done and regs['s'] == 0x7ef0
                        assert d.read(0x6fff, 45) == b'G'+expected+b'H', (
                            owner, (x, y, width, height, horizon, flags))
                        assert regs['x'] == (0x7000 if private else 0x4567)
                        assert regs['u'] == (0x7777 if private else 0x7000)
                        assert regs['y'] == 0x7654 and d.read(0x7ef0, 5) == b'STACK'
                        calls += 1
                    d.breakpoint(done, False)
                    if private:
                        expected_private[syms['vmhorizon']] = cases[-1][4]
                        assert d.read(private, syms['size']) == expected_private
                        assert d.read(private+syms['size'], 2) == b'GH'
                    assert d.read(base, len(code)) == code
            print(f'PASS: {calls} actual CoCo/native cel clipping checks at two '
                  'load addresses; position/dimension/horizon/flag boundaries, '
                  'right-add overflow policy, unchanged unrelated fields, '
                  'private state, code, registers and stack guards')
        finally:
            d.s.close(); emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except Exception:
                emulator.kill(); emulator.wait()


if __name__ == '__main__':
    main()
