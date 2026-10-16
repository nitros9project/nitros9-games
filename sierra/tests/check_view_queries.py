#!/usr/bin/env python3
"""Run actual view queries in both owners and check record/private-state preservation."""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
QUERIES = [('cmd_last_cel', 15), ('cmd_current_cel', 14),
           ('cmd_current_loop', 10), ('cmd_current_view', 5),
           ('cmd_number_of_loops', 11)]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-view-query-') as name:
        tmp = Path(name)
        coco, cs = compile_module(ROOT/'objs/mnln.asm', tmp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame', defines=('WILDBITS=1',))
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=900)
        calls = 0
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            d.breakpoint(0x7e00)
            for owner, code, syms, bases in [('CoCo', coco, cs, (0x8000, 0x9000)),
                                            ('native', native, ns, (0x9000, 0xa000))]:
                private = 0 if owner == 'CoCo' else 0x1000
                objects = 0x4000 if not private else private + syms['vmobjects']
                variables = 0x0431 if not private else private + syms['vmvariables']
                args = 0x2000 if not private else private + syms['vmarguments']
                if private:
                    d.write(private, bytes(syms['size']) + b'GUARD')
                    d.write(private+syms['resourcebase'], private.to_bytes(2, 'big'))
                else:
                    d.write(0x30, objects.to_bytes(2, 'big'))
                for base in bases:
                    d.write(base, code)
                    for opcode, (label, field) in enumerate(QUERIES, 49):
                        for value in range(256):
                            obj = 63 if value & 2 else 0
                            dest = 255 if value & 1 else 0
                            records = bytearray(b'\xa5' * (64*43))
                            records[obj*43+field] = value
                            d.write(objects-1, b'G'+records+b'H')
                            d.write(variables, b'\x5a'*256)
                            operands = bytes([obj, dest])+b'ARGS'
                            d.write(args, operands)
                            if private:
                                d.write(private+syms['vmopcode'], bytes([opcode]))
                                before = d.read(private, syms['size'])
                            d.write(0x7ef0, b'\x7e\x00STACK')
                            d.regs(pc=base+syms['ViewCommand' if private else label],
                                   s=0x7ef0, y=args, u=private, dp=private >> 8, cc=0x50)
                            d.call('c'); regs = d.regs()
                            assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                            assert d.read(0x7ef2, 5) == b'STACK'
                            rejected = bool(private and opcode == 49 and value == 0)
                            wanted = bytearray(b'\x5a'*256)
                            if not rejected: wanted[dest] = (value-1)&255 if opcode == 49 else value
                            assert d.read(variables, 256) == wanted, (owner, opcode, value, obj, dest)
                            assert d.read(objects-1, len(records)+2) == b'G'+records+b'H'
                            assert d.read(args, 6) == operands
                            if private:
                                assert bool(regs['cc'] & 1) == rejected
                                assert regs['b'] == (syms['E$BMode'] if rejected else 0)
                                expected = bytearray(before)
                                expected[syms['vmvariables']:syms['vmvariables']+256] = wanted
                                expected[syms['viewobject']:syms['viewobject']+2] = (objects+obj*43).to_bytes(2, 'big')
                                assert d.read(private, syms['size']) == expected
                                assert d.read(private+syms['size'], 5) == b'GUARD'
                            if not rejected: assert regs['y'] == args+2
                            calls += 1
                    if private:
                        # Resolve/validate before reading a record or touching output.
                        for opcode in range(49, 54):
                            for obj in (64, 255):
                                d.write(args, bytes([obj, 255])+b'ARGS')
                                d.write(private+syms['vmopcode'], bytes([opcode]))
                                before = d.read(private, syms['size'])
                                d.write(0x7ef0, b'\x7e\x00STACK')
                                d.regs(pc=base+syms['ViewCommand'], s=0x7ef0,
                                       y=args, u=private, dp=private >> 8, cc=0x50)
                                d.call('c'); regs = d.regs()
                                assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                                assert regs['cc'] & 1 and regs['b'] == syms['E$IllArg']
                                assert d.read(private, syms['size']) == before
                                assert d.read(0x7ef2, 5) == b'STACK'
                                calls += 1
                    assert d.read(base, len(code)) == code
            print(f'PASS: {calls} actual CoCo/native view queries; every field byte, first/last object and variable, last-cel decrement, native empty-loop/index rejection, two load addresses, whole-record/private-state preservation, argument/stack guards and immutable code')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
