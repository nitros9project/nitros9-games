#!/usr/bin/env python3
"""Actual-6809 checks for the portable bytecode control/arithmetic layer."""
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-logic-') as temp:
        temp = Path(temp)
        binary = temp / 'vmtest'
        subprocess.run(['lwasm.orig', '--6809', '--format=os9',
            '--pragma=pcaspcr,nosymbolcase,condundefzero',
            '-I' + str(ROOT / 'objs'), '-I' + str(ROOT.parent.parent / 'nitros9/defs'),
            '--map=' + str(binary) + '.map', '-o', str(binary),
            str(ROOT / 'tests/logic-harness.asm')], check=True)
        syms = symbols(Path(str(binary) + '.map'))
        code = binary.read_bytes()
        d, emulator = start_cpu(idle_rom(temp / 'idle.rom'))
        try:
            d.write(0xffdf, b'\0')
            def run(script, success=True, base=0xe000, database=0x8000):
                d.write(base, code)
                d.write(database, bytes(syms['size']) + b'GUARD')
                d.write(0x2000, b'\0\0' + script)
                for field, value in [('scriptbase', 0x2000), ('vmip', 2), ('vmend', len(script) + 2)]:
                    d.write(database + syms[field], value.to_bytes(2, 'big'))
                finish = base + syms['finish']
                d.breakpoint(finish)
                d.regs(pc=base + syms['start'], s=0xc000, dp=database >> 8,
                       u=database, cc=0x50)
                d.call('c')
                r = d.regs()
                assert r['pc'] == finish
                assert r['s'] == 0xc000, 'executor frame leaked on success/error'
                assert bool(r['cc'] & 1) != success, (r, script)
                assert d.read(base, len(code)) == code
                assert d.read(database + syms['size'], 5) == b'GUARD'
                d.breakpoint(finish, False)
                return (d.read(database + syms['vmvariables'], 256),
                        d.read(database + syms['vmflags'], 256))
            arithmetic = bytes([3,0,255,1,0,2,0,5,0,3,7,0,4,
                                3,1,7,4,2,1,6,2,1,8,2,1,
                                3,3,4,9,3,1,10,5,3,11,3,99,
                                12,200,14,200,14,200,3,6,201,
                                15,6,17,6,16,6,2,250,0])
            variables, flags = run(arithmetic)
            assert variables[:7] == bytes([253,7,7,4,99,7,201]), variables[:7]
            assert flags[200] == 1 and flags[201] == 0 and variables[250] == 0
            assert run(arithmetic, base=0xd000, database=0x9000) == (variables, flags)
            # Last-byte indices and aliased indirect operands share CoCo bodies.
            edge = bytes([3,255,255,1,255,2,255,5,255,2,7,255,1,
                          3,254,255,4,253,255,9,254,253,10,252,254,
                          11,254,42,0])
            edgevars, _ = run(edge)
            assert edgevars[252:256] == bytes([255,255,255,42]), edgevars[252:256]
            # IF expression, false branch skips assign; evaluate AND, OR, NOT.
            def condition(expression):
                return run(bytes([3,0,7,3,1,8,12,200,3,2,200,255]) +
                           bytes(expression) + bytes([255,3,0,3,250,99,0]))[0][250]
            for test in [([1,0,7],99), ([1,0,8],0), ([2,0,1],0),
                         ([3,0,8],99), ([4,0,1],99), ([5,1,7],99),
                         ([6,1,0],99), ([7,200],99), ([8,2],99),
                         ([253,1,0,7],0), ([252,1,0,8,1,0,7,252],99),
                         ([1,0,7,1,1,8],99), ([1,0,7,1,1,9],0)]:
                assert condition(test[0]) == test[1], test
            # Forward/backward relative jumps and the instruction budget.
            assert run(bytes([254,3,0,3,0,99,3,0,42,0]))[0][0] == 42
            for script in [b'\x03\x00', b'\xff\x01\x00', b'\xfe\xff\x7f',
                           b'\xfe\xfd\xff', b'\xff\xfc\xff\0\0',
                           b'\xff\xfd\xff\0\0', b'\xb6', b'\x65\x01',
                           b'\xff\x0d\xff\0\0\0',
                           # Malformed controls must fail even after an AND
                           # result or an OR arm has short-circuited evaluation.
                           bytes([255,1,0,0,253,255,0,0,0]),
                           bytes([255,1,0,0,252,255,0,0,0]),
                           bytes([255,1,0,0,254,255,0,0,0]),
                           bytes([255,252,1,0,7,253,252,255,0,0,0]),
                           bytes([255,252,1,0,7,255,0,0,0])]:
                run(bytes([3,0,7])+script, False)
            print('PASS: AGI arithmetic/indirection/flags, AND/OR/NOT tests, bounded branches/arguments/instruction budget, relocation and immutable code')
        finally:
            d.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill()
                emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
