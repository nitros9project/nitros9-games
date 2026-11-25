#!/usr/bin/env python3
"""Compare actual CoCo/native posn, box, center and right predicates."""
from itertools import product
from pathlib import Path
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
MODES = [(11, 'TestPosition'), (16, 'TestBox'),
         (17, 'TestCenter'), (18, 'TestRight')]
POSITIONS = [(0, 0), (1, 1), (127, 128), (254, 255), (255, 254)]
WIDTHS = [0, 1, 2, 127, 255]
RECTS = [(0, 0, 255, 255), (0, 0, 0, 0), (1, 1, 1, 1),
         (0, 0, 127, 127), (128, 128, 255, 255), (255, 255, 255, 255),
         (254, 0, 255, 255), (100, 100, 100, 100)]
OBJECTS = (0, 63)


def expected(opcode, x, y, width, rect):
    left, top, right, bottom = rect
    if opcode == 11:
        xleft = xright = x
    elif opcode == 16:
        xleft, xright = x, (x + width - 1) & 255
    elif opcode == 17:
        xleft = xright = (x + (width >> 1)) & 255
    else:
        xleft = xright = (x + width - 1) & 255
    return int(xleft >= left and y >= top and xright <= right and y <= bottom)


def main():
    cases = [(opcode, label, obj, x, y, width, rect)
             for opcode, label in MODES
             for obj in OBJECTS
             for (x, y), width, rect in product(POSITIONS, WIDTHS, RECTS)]
    with tempfile.TemporaryDirectory(prefix='sierra-object-position-') as directory:
        tmp = Path(directory)
        coco, cs = compile_module(ROOT/'objs/mnln.asm', tmp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame',
                                    defines=('WILDBITS=1',))
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=900)
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            all_results = []
            for owner, code, symbols, base in (
                    ('CoCo', coco, cs, 0x8000),
                    ('native', native, ns, 0xa000)):
                d.write(base, code)
                private = 0 if owner == 'CoCo' else 0x1000
                objects = 0x4000 if owner == 'CoCo' else private + ns['vmobjects']
                args = 0x2000 if owner == 'CoCo' else private + ns['vmarguments']
                if private:
                    d.write(private, bytes(ns['size']) + b'GUARD')
                    d.write(private + ns['resourcebase'], private.to_bytes(2, 'big'))
                else:
                    d.write(0x30, objects.to_bytes(2, 'big'))
                d.breakpoint(0x7e00)
                results = []
                for opcode, label, obj, x, y, width, rect in cases:
                    records = bytearray((i * 29 + 7) & 255 for i in range(64 * 43))
                    offset = obj * 43
                    records[offset + 3] = x
                    records[offset + 4] = y
                    records[offset + 0x1c] = width
                    d.write(objects - 1, b'G' + records + b'H')
                    operands = bytes([obj, *rect])
                    d.write(args, operands + b'GUARD')
                    if private:
                        d.write(private + ns['vmopcode'], bytes([opcode]))
                    d.write(0x7ef0, b'\x7e\x00STACK')
                    handler = 'ObjectPositionTest' if private else label
                    d.regs(pc=base + symbols[handler], s=0x7ef0, y=args,
                           u=private, dp=private >> 8, cc=0x50)
                    d.call('c')
                    regs = d.regs()
                    assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2, (owner, opcode, obj, x, y, width, rect, regs)
                    assert regs['y'] == args + 5, (owner, opcode, regs)
                    assert d.read(0x7ef2, 5) == b'STACK'
                    assert d.read(args, 10) == operands + b'GUARD'
                    assert d.read(objects - 1, len(records) + 2) == b'G' + records + b'H'
                    if private:
                        assert not regs['cc'] & 1 and regs['b'] in (0, 1), (opcode, regs)
                        assert d.read(private + ns['size'], 5) == b'GUARD'
                        value = regs['b']
                    else:
                        value = regs['a']
                    want = expected(opcode, x, y, width, rect)
                    assert value == want, (owner, opcode, obj, x, y, width, rect, value, want)
                    results.append(value)
                assert d.read(base, len(code)) == code
                d.breakpoint(0x7e00, False)
                all_results.append(results)
            assert all_results[0] == all_results[1]
            print(f'PASS: {len(cases)*2} actual CoCo/native position predicate calls; posn/box/center/right, edge objects, byte-coordinate and width wrap, inclusive rectangle edges, records/arguments/stack/code guards')
        finally:
            d.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except Exception:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
