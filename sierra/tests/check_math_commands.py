#!/usr/bin/env python3
"""Exercise real CoCo/native math handlers, including variable aliasing and rejection."""
from itertools import product
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['cmd_multn', 'cmd_multv', 'cmd_divn', 'cmd_divv']
EDGES = [0, 1, 2, 127, 128, 254, 255]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-math-') as name:
        tmp = Path(name)
        coco, cs = compile_module(ROOT/'objs/mnln.asm', tmp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame', defines=('WILDBITS=1',))
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=900)
        count = 0
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            d.breakpoint(0x7e00)
            for owner, code, syms, bases in [('CoCo', coco, cs, (0x8000, 0x9000)),
                                            ('native', native, ns, (0x9000, 0xa000))]:
                private = 0 if owner == 'CoCo' else 0x1000
                table = 0x0431 if not private else private + syms['vmvariables']
                args = 0x2000 if not private else private + syms['vmarguments']
                if private:
                    d.write(private, bytes(syms['size']) + b'GUARD')
                    d.write(private + syms['resourcebase'], private.to_bytes(2, 'big'))
                for position, base in enumerate(bases):
                    d.write(base, code)
                    vectors = ([(n, (73*n+1) & 255) for n in range(256)]
                               if position == 0 else list(product(EDGES, repeat=2)))
                    for opcode, label in enumerate(NAMES, 165):
                        variable = opcode in (166, 168)
                        division = opcode >= 167
                        cases = [(a, b, False) for a, b in vectors]
                        if variable:
                            cases += [(n, n, True) for n in EDGES]
                        for left, right, alias in cases:
                            if division and right == 0 and not private:
                                # CoCo's existing zero-divisor behavior is outside
                                # the nonzero arithmetic contract; native rejects it.
                                continue
                            dest = 255 if left & 1 else 0
                            source = dest if alias else 255-dest
                            values = bytearray(b'\xa5' * 256)
                            if variable: values[source] = right
                            values[dest] = left
                            operands = bytes([dest, source if variable else right])
                            d.write(table-1, b'G' + values + b'H')
                            d.write(args, operands + b'ARGS')
                            if private:
                                d.write(private+syms['vmopcode'], bytes([opcode]))
                            d.write(0x7ef0, b'\x7e\x00STACK')
                            entry = base + syms['GameMathCommand' if private else label]
                            d.regs(pc=entry, s=0x7ef0, y=args, u=private,
                                   dp=private >> 8, cc=0x50)
                            d.call('c'); regs = d.regs()
                            assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                            assert regs['u'] == private
                            assert d.read(0x7ef2, 5) == b'STACK'
                            rejected = division and right == 0
                            expected = bytearray(values)
                            if not rejected:
                                expected[dest] = left // right if division else left*right & 255
                            assert d.read(table-1, 258) == b'G'+expected+b'H', (owner, opcode, left, right, alias)
                            assert d.read(args, 6) == operands + b'ARGS'
                            if private:
                                assert bool(regs['cc'] & 1) == rejected
                                assert regs['b'] == (syms['E$IllArg'] if rejected else 0)
                                assert d.read(private+syms['size'], 5) == b'GUARD'
                            if not rejected:
                                assert regs['y'] == args+2
                            count += 1
                    assert d.read(base, len(code)) == code
            print(f'PASS: {count} real CoCo/native math calls; every byte dividend, boundary products/quotients, variable indices 0/255 and aliasing, two load addresses, native zero-divisor rejection, stack/table/operand guards and immutable code')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
