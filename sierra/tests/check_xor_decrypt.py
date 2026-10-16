#!/usr/bin/env python3
"""Execute real shared AGI XOR helpers at two addresses in both owners."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
KEY = b'Avis Durgan'


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-xor-') as name:
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
                for base in bases:
                    d.write(base, code)
                    assert d.read(base+syms['XorKeyStr'], 12) == KEY+b'\0'
                    for length in list(range(257))+[511, 512, 1023, 1024, 2047, 2048]:
                        original = bytes((i*73+length) & 255 for i in range(length))
                        cipher = bytes(byte ^ KEY[i % 11] for i, byte in enumerate(original))
                        d.write(0x6fff, b'G'+original+b'H')
                        for wanted in [cipher, original]:
                            d.write(0x7ef0, b'\x7e\x00STACK')
                            d.regs(pc=base+syms['XorDecrypt'], s=0x7ef0,
                                   x=0x7000, u=0x7000+length, y=0x4567, dp=0x10, cc=0x50)
                            d.call('c'); regs = d.regs()
                            assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                            assert regs['x'] == 0x7000+length and regs['y'] == 0x4567
                            key_cursor = 0 if not length else (length-1) % 11+1
                            assert regs['u'] == base+syms['XorKeyStr']+key_cursor
                            assert regs['dp'] == 0x10
                            assert d.read(0x6fff, length+2) == b'G'+wanted+b'H', (owner, base, length)
                            assert d.read(0x7ef2, 5) == b'STACK'
                            calls += 1
                    # An exclusive end before start must also perform no write.
                    d.write(0x6fff, b'GuntouchedH')
                    d.write(0x7ef0, b'\x7e\x00STACK')
                    d.regs(pc=base+syms['XorDecrypt'], s=0x7ef0,
                           x=0x7000, u=0x6ffe, y=0x4567, dp=0x10, cc=0x50)
                    d.call('c'); regs = d.regs()
                    assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                    assert regs['x'] == 0x7000 and regs['y'] == 0x4567
                    assert d.read(0x6fff, 11) == b'GuntouchedH'
                    assert d.read(base, len(code)) == code, (owner, 'modified code/key')
                    calls += 1
            print(f'PASS: {calls} real CoCo/native XOR calls, all byte-length values, '
                  'key-wrap boundaries, 2048-byte inventory limit, symmetric round trips, '
                  'empty/reversed spans, guards/stack, cursor/register contract and immutable code/key')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except Exception: emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
