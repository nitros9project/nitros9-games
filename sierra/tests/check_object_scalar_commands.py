#!/usr/bin/env python3
"""Exercise actual priority/direction commands across the two owner layouts."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = [(54, 'cmd_set_priority'), (55, 'cmd_set_priority_v'),
            (57, 'cmd_get_priority'), (86, 'cmd_set_dir'), (87, 'cmd_get_dir')]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-scalars-') as name:
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
                objects = 0x4000 if not private else private+syms['vmobjects']
                variables = 0x0431 if not private else private+syms['vmvariables']
                args = 0x2000 if not private else private+syms['vmarguments']
                for base in bases:
                    d.write(base, code)
                    if private:
                        d.write(private, bytes(syms['size'])+b'GUARD')
                        d.write(private+syms['resourcebase'], private.to_bytes(2, 'big'))
                    else:
                        d.write(0x30, objects.to_bytes(2, 'big'))
                    for opcode, label in COMMANDS:
                        cases = [(value, value*73 & 255) for value in range(256)]
                        if opcode in (54, 55): cases += [(7, flag) for flag in range(256)]
                        for value, flag in cases:
                            obj = 63 if flag & 2 else 0
                            index = 255 if flag & 1 else 0
                            if opcode == 86 and value & 4: index = 6
                            address = objects+obj*43
                            record = bytearray(range(43)); record[0x26] = flag
                            record[0x24] = value if opcode == 57 else 0x44
                            record[0x21] = value if opcode == 87 else 0x55
                            d.write(address-1, b'G'+record+b'H')
                            original_vars = bytearray(b'\x5a'*256)
                            if opcode in (55, 86): original_vars[index] = value
                            d.write(variables, original_vars)
                            operand = value if opcode == 54 else index
                            operands = bytes([obj, operand])+b'ARGS'
                            d.write(args, operands)
                            if private: d.write(private+syms['vmopcode'], bytes([opcode]))
                            check_all = private and value in (0,1,8,9,15,16,255)
                            check_all |= bool(private and value == 7 and flag in (0,255))
                            before = d.read(private, syms['size']) if check_all else None
                            d.write(0x7ef0, b'\x7e\x00STACK')
                            d.regs(pc=base+syms['ObjectCommand' if private else label],
                                   s=0x7ef0, y=args, u=private, dp=private >> 8, cc=0x50)
                            d.call('c'); regs = d.regs()
                            rejected = bool(private and ((opcode in (54,55) and value > 15)
                                                       or (opcode == 86 and value > 8)))
                            wanted_record = bytearray(record); wanted_vars = bytearray(original_vars)
                            if not rejected:
                                if opcode in (54,55):
                                    wanted_record[0x24] = value; wanted_record[0x26] |= 4
                                elif opcode == 86:
                                    wanted_record[0x21] = value
                                    if private and obj == 0: wanted_vars[6] = value
                                else: wanted_vars[index] = value
                            assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                            assert d.read(0x7ef2, 5) == b'STACK'
                            assert d.read(address-1, 45) == b'G'+wanted_record+b'H', (owner, opcode, value, flag)
                            assert d.read(variables, 256) == wanted_vars, (owner, opcode, value, flag)
                            assert d.read(args, 6) == operands
                            if private:
                                assert bool(regs['cc'] & 1) == rejected
                                assert regs['b'] == (syms['E$IllArg'] if rejected else 0)
                                assert d.read(private+syms['size'], 5) == b'GUARD'
                                if before is not None:
                                    expected = bytearray(before)
                                    start = syms['vmobjects']+obj*43
                                    expected[start:start+43] = wanted_record
                                    expected[syms['vmvariables']:syms['vmvariables']+256] = wanted_vars
                                    assert d.read(private, syms['size']) == expected
                            else: assert regs['y'] == args+2
                            calls += 1
                    if private:
                        for opcode, _ in COMMANDS:
                            for obj in (64,255):
                                d.write(args, bytes([obj,255])+b'ARGS')
                                d.write(private+syms['vmopcode'], bytes([opcode]))
                                before = d.read(private, syms['size'])
                                d.write(0x7ef0, b'\x7e\x00STACK')
                                d.regs(pc=base+syms['ObjectCommand'], s=0x7ef0,
                                       y=args, u=private, dp=private >> 8, cc=0x50)
                                d.call('c'); regs = d.regs()
                                assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                                assert regs['cc'] & 1 and regs['b'] == syms['E$IllArg']
                                assert d.read(private, syms['size']) == before
                                calls += 1
                    assert d.read(base, len(code)) == code
            print(f'PASS: {calls} actual CoCo/native priority/direction calls at two addresses; '
                  'all field/value bytes and priority flags, first/last objects/variables, '
                  'native range/index rejection, ego direction policy and variable-six alias, '
                  'unrelated record/private-state preservation, guards/stack and immutable code')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except Exception: emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
