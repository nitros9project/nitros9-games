#!/usr/bin/env python3
"""Run CoCo condition dispatch and shared predicates on an actual 6809."""
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_wbres import idle_rom, start_cpu
from check_logic_executor import compile_module

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
        native, ns = compile_module(ROOT / 'objs/sierra.asm', folder / 'wbgame',
                                    defines=('WILDBITS=1',))
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

            # Compare the actual shared CoCo and Wild Bits handlers, not just
            # the CoCo dispatch table. Exercise unsigned boundary pairs through
            # both immediate and variable operands and all byte flag indexes.
            d.write(0x8000, code)
            d.write(0xa000, native)
            private = 0x1000
            nvars = private + ns['vmvariables']
            nflags = private + ns['vmflags']
            narguments = private + ns['vmarguments']
            d.write(private, bytes(ns['size']) + b'GUARD')
            d.write(private + ns['resourcebase'], private.to_bytes(2, 'big'))
            d.breakpoint(0x7e00)
            calls = 0

            def invoke(owner, base, image_code, table, label, operands,
                       variables, flags):
                nonlocal calls
                args = 0x2000 if owner == 'CoCo' else narguments
                varbase = 0x0431 if owner == 'CoCo' else nvars
                flagbase = 0x01ae if owner == 'CoCo' else nflags
                if owner == 'CoCo':
                    d.write(0x002e, base.to_bytes(2, 'big'))
                d.write(varbase, variables)
                d.write(flagbase, flags)
                d.write(args, bytes(operands) + b'GUARD')
                d.write(0x7ef0, b'\x7e\x00STACK')
                d.regs(pc=base + table[label], s=0x7ef0, y=args,
                       u=private if owner == 'native' else 0,
                       dp=private >> 8 if owner == 'native' else 0, cc=0x50)
                d.call('c')
                result = d.regs()
                assert result['pc'] == 0x7e00 and result['s'] == 0x7ef2, (owner, label, result)
                assert result['y'] == args + len(operands), (owner, label, result)
                assert d.read(0x7ef2, 5) == b'STACK'
                assert d.read(args, len(operands) + 5) == bytes(operands) + b'GUARD'
                assert d.read(varbase, 256) == variables
                assert d.read(flagbase, 256 if owner == 'native' else 32) == flags
                if owner == 'native':
                    assert not result['cc'] & 1 and result['b'] in (0, 1), (label, result)
                    boolean = result['b']
                else:
                    boolean = result['a']
                assert boolean in (0, 1), (owner, label, result)
                calls += 1
                return boolean

            compare_cases = [(0,0), (0,1), (1,0), (127,128),
                             (128,127), (255,255), (255,0), (0,255)]
            predicate_labels = ['TestEqualN', 'TestEqualV', 'TestLessN',
                                'TestLessV', 'TestGreaterN', 'TestGreaterV']
            for left, right in compare_cases:
                for variable_index in (0, 255):
                    variables = bytearray(256)
                    variables[variable_index] = left
                    variables[255 if variable_index == 0 else 0] = right
                    variable_rhs = 255 if variable_index == 0 else 0
                    for label, operands, expected in (
                        ('TestEqualN', [variable_index, right], int(left == right)),
                        ('TestEqualV', [variable_index, variable_rhs], int(left == right)),
                        ('TestLessN', [variable_index, right], int(left < right)),
                        ('TestLessV', [variable_index, variable_rhs], int(left < right)),
                        ('TestGreaterN', [variable_index, right], int(left > right)),
                        ('TestGreaterV', [variable_index, variable_rhs], int(left > right))):
                        coco_result = invoke('CoCo', 0x8000, code, syms, label,
                                             operands, variables, bytes(32))
                        native_result = invoke('native', 0xa000, native, ns, label,
                                               operands, variables, bytes(256))
                        assert coco_result == native_result == expected, (label, left, right, variable_index, coco_result, native_result, expected)
            for flag_index in range(256):
                is_set = (flag_index % 3) != 1
                variables = bytearray(256)
                variables[0] = flag_index
                variables[255] = flag_index
                packed = bytearray(32)
                if is_set:
                    packed[flag_index >> 3] |= 0x80 >> (flag_index & 7)
                native_flags = bytearray(256)
                native_flags[flag_index] = int(is_set)
                for label, operands in (('TestIsSet', [flag_index]),
                                        ('TestIsSetV', [0]),
                                        ('TestIsSetV', [255])):
                    coco_result = invoke('CoCo', 0x8000, code, syms, label,
                                         operands, variables, packed)
                    native_result = invoke('native', 0xa000, native, ns, label,
                                           operands, variables, native_flags)
                    assert coco_result == native_result == int(is_set), (label, flag_index, coco_result, native_result, is_set)
            # The two full modules cannot coexist in the 64-KiB test address
            # space. The CoCo predicate bodies and their boolean returns are
            # below 0xA000 and remain resident while the native image occupies
            # the upper portion of the CoCo image.
            coco_start, coco_end = syms['TestEqualN'], syms['RetFalse'] + 1
            assert d.read(0x8000+coco_start, coco_end-coco_start) == code[coco_start:coco_end]
            assert d.read(0xa000, len(native)) == native
            assert d.read(private + ns['size'], 5) == b'GUARD'
            print(f'PASS: {calls} actual CoCo/native comparison and packed-flag predicates; unsigned boundaries at variable indexes 0/255, every flag index 0..255, stack/operand/state guards and immutable code')
            print('PASS: all 19 CoCo condition-table addresses relocate correctly; shared unsigned comparisons and packed flag predicates at two module bases')
        finally:
            d.s.close(); emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
