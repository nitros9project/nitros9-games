#!/usr/bin/env python3
"""Compare the CoCo controller-byte table with native controller bits."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-controller-predicate-') as directory:
        tmp = Path(directory)
        coco, cs = compile_module(ROOT/'objs/mnln.asm', tmp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame',
                                    defines=('WILDBITS=1',))
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=900)
        calls = 0
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            results = []
            for owner, code, symbols, base in (
                    ('CoCo', coco, cs, 0x8000),
                    ('native', native, ns, 0xa000)):
                d.write(base, code)
                private = 0 if owner == 'CoCo' else 0x1000
                args = 0x2000 if owner == 'CoCo' else private + ns['vmarguments']
                d.write(private, bytes(ns['size']) + b'GUARD') if private else None
                if private:
                    d.write(private + ns['resourcebase'], private.to_bytes(2, 'big'))
                d.breakpoint(0x7e00)
                owner_results = []
                for controller in range(256):
                    for key_present, value in ((False, 0), (True, 1),
                                               (True, 0xff)):
                        operands = bytes([controller])
                        d.write(args, operands + b'GUARD')
                        if owner == 'CoCo':
                            # 6809 accumulator indexed offsets are signed;
                            # EventLoopKey stores to this same effective byte.
                            signed_controller = controller if controller < 128 else controller - 256
                            d.write(0x05ba + signed_controller, bytes([value]))
                            pc = base + symbols['TestController']
                            u = dp = 0
                        else:
                            controller_table = bytearray(32)
                            if key_present:
                                controller_table[controller >> 3] |= 1 << (controller & 7)
                            d.write(private + ns['vmcontrollers'], controller_table)
                            d.write(private + ns['vmopcode'], b'\x0c')
                            pc = base + symbols['InputTest']
                            u, dp = private, private >> 8
                        d.write(0x7ef0, b'\x7e\x00STACK')
                        d.regs(pc=pc, s=0x7ef0, y=args, u=u, dp=dp, cc=0x50)
                        d.call('c')
                        regs = d.regs()
                        assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2, (owner, controller, key_present, value, regs)
                        assert d.read(0x7ef2, 5) == b'STACK'
                        assert d.read(args, 6) == operands + b'GUARD'
                        if owner == 'CoCo':
                            assert regs['y'] == args + 1
                            result = int(regs['a'] != 0)
                        else:
                            assert not regs['cc'] & 1 and regs['b'] in (0, 1)
                            assert d.read(private + ns['size'], 5) == b'GUARD'
                            result = regs['b']
                        expected = int(key_present)
                        assert result == expected, (owner, controller, key_present, value, result, expected)
                        owner_results.append((controller, key_present, result))
                        calls += 1
                assert d.read(base, len(code)) == code
                d.breakpoint(0x7e00, False)
                results.append(owner_results)
            assert results[0] == results[1]
            print(f'PASS: {calls} actual CoCo/native controller predicate calls; all 256 key-table indexes, true/false and noncanonical nonzero values, native bit mapping, cursor/stack/guard/code checks')
        finally:
            d.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except Exception:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
