#!/usr/bin/env python3
"""Run CoCo condition dispatch and shared predicates on an actual 6809."""
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['RetTrue', 'TestEqualN', 'TestEqualV', 'TestLessN', 'TestLessV',
         'TestGreaterN', 'TestGreaterV', 'TestIsSet', 'TestIsSetV',
         'TestHasObject', 'TestObjectRoom', 'TestPosition', 'TestController',
         'TestHaveKey', 'TestSaid', 'TestStrings', 'TestBox', 'TestCenter', 'TestRight']


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-coco-conditions-') as folder:
        folder = Path(folder)
        image = folder / 'mnln'
        subprocess.run(['lwasm.orig', '--6809', '--format=os9', '--no-warn=ifp1',
                        '--pragma=pcaspcr,nosymbolcase,condundefzero',
                        '-I' + str(ROOT / 'kingsquest1'), '-I' + str(ROOT / 'objs'),
                        '-I' + str(ROOT.parent.parent / 'nitros9/defs'),
                        '--map=' + str(image) + '.map', '-o' + str(image),
                        str(ROOT / 'objs/mnln.asm')], check=True)
        code, syms = image.read_bytes(), symbols(Path(str(image) + '.map'))
        table = syms['eval_table']
        for i, name in enumerate(NAMES):
            assert int.from_bytes(code[table + i*4:table + i*4 + 2], 'big') == syms[name], name
        d, emulator = start_cpu(idle_rom(folder / 'idle.rom'), timeout=900)
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            for base in (0x8000, 0x9000):
                d.write(base, code)
                d.write(0x002e, base.to_bytes(2, 'big'))
                d.write(0x0068, b'\0')  # no trace UI
                d.run(base + syms['FixupEvalTbl'])
                for i, name in enumerate(NAMES):
                    assert int.from_bytes(d.read(base+table+i*4, 2), 'big') == base + syms[name]
                def test(opcode, operands):
                    d.write(0x2000, bytes(operands))
                    d.run(base + syms['EvalExpr'], a=opcode, y=0x2000)
                    assert d.regs()['y'] == 0x2000 + len(operands)
                    return d.regs()['a']
                assert test(0, []) == 1
                for left, right in [(0,0), (0,1), (1,0), (127,128),
                                    (128,127), (255,255), (255,0), (0,255)]:
                    variables = bytearray(256)
                    variables[0], variables[255] = left, right
                    d.write(0x0431, variables)
                    for op, expected in [(1,left==right), (3,left<right), (5,left>right)]:
                        assert test(op, [0,right]) == expected, (base,op,left,right)
                        assert test(op+1, [0,255]) == expected, (base,op+1,left,right)
                flags = bytearray(32)
                flags[0], flags[31] = 0x01, 0x01
                d.write(0x01ae, flags)
                for index in (0,1,7,8,127,128,254,255):
                    expected = int(index in (7,255))
                    assert test(7, [index]) == expected, (base, index, expected, d.regs())
                    d.write(0x0431+255, bytes([index]))
                    assert test(8, [255]) == expected
            print('PASS: all 19 CoCo condition-table addresses relocate correctly; shared unsigned comparisons and packed flag predicates at two module bases')
        finally:
            d.s.close(); emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
