#!/usr/bin/env python3
"""Compare actual CoCo/native stop.update and start.update object transitions."""
from pathlib import Path
import tempfile

from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
RECORDS = 64 * 43


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-object-update-') as name:
        tmp = Path(name)
        coco, cs = compile_module(ROOT/'objs/mnln.asm', tmp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame',
                                    defines=('WILDBITS=1',))
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=900)
        calls = 0
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            d.breakpoint(0x7e00)
            for owner, code, syms, bases in (
                    ('CoCo', coco, cs, (0x8000, 0x9000)),
                    ('native', native, ns, (0x9000, 0xa000))):
                private = 0 if owner == 'CoCo' else 0x1000
                objects = 0x4000 if not private else private + syms['vmobjects']
                args = 0x2000 if not private else private + syms['vmarguments']
                if private:
                    d.write(private, bytes(syms['size']) + b'GUARD')
                    d.write(private+syms['resourcebase'], private.to_bytes(2, 'big'))
                else:
                    d.write(0x30, objects.to_bytes(2, 'big'))
                for base in bases:
                    image = bytearray(code)
                    if owner == 'CoCo':
                        # Keep both actual helpers and their flag transition,
                        # but omit the CoCo-only draw-range maintenance calls.
                        # Those routines require initialized MMU range pages,
                        # outside this object's state/command-equivalence test.
                        for helper in ('StopUpdateHelper', 'StartUpdateHelper'):
                            start = syms[helper]
                            end = syms['StartUpdateHelper'] if helper == 'StopUpdateHelper' else syms['StartUpdateReturn']
                            for target in (syms['ClearBothRanges'], syms['SwapObjRanges']):
                                for site in range(start, end-2):
                                    displacement = target - (site + 3)
                                    if image[site] == 0x17 and image[site+1:site+3] == displacement.to_bytes(2, 'big', signed=True):
                                        image[site:site+3] = b'\x12\x12\x12'
                        d.write(base, image)
                    else:
                        d.write(base, image)
                    for opcode, label, mask, value in (
                            (58, 'CmdStopUpdate', 0xef, 0),
                            (59, 'CmdStartUpdate', 0xff, 0x10)):
                        for index in (0, 1, 32, 63):
                            for initial in range(256):
                                records = bytearray((i*29+7)&255 for i in range(RECORDS))
                                at = index*43 + 0x26
                                records[at] = initial
                                wanted = bytearray(records)
                                wanted[at] = (initial & mask) | value
                                d.write(objects-1, b'G'+records+b'H')
                                operand = bytes([index])
                                d.write(args, operand+b'ARGS')
                                if private:
                                    d.write(private+syms['vmopcode'], bytes([opcode]))
                                    entry = base+syms['ObjectCommand']
                                    dp = private >> 8
                                else:
                                    entry = base+syms[label]
                                    dp = 0
                                d.write(0x7ef0, b'\x7e\0STACK')
                                d.regs(pc=entry, s=0x7ef0, y=args, u=private,
                                       dp=dp, cc=0x50)
                                d.call('c')
                                regs = d.regs()
                                assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                                assert d.read(objects-1, RECORDS+2) == b'G'+wanted+b'H', (
                                    owner, opcode, index, initial)
                                assert d.read(0x7ef2, 5) == b'STACK'
                                assert d.read(args, 5) == operand+b'ARGS'
                                if private:
                                    assert regs['b'] == 0 and not regs['cc'] & 1
                                    assert d.read(private+syms['size'], 5) == b'GUARD'
                                else:
                                    assert regs['y'] == args+1
                                calls += 1
                    assert d.read(base, len(code)) == image
            print(f'PASS: {calls} actual CoCo/native stop.update/start.update calls; all 256 initial flag bytes, four object slots, repeated-state cases, two code bases, complete record and stack/argument guards')
        finally:
            d.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except Exception:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
