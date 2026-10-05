#!/usr/bin/env python3
"""Exercise both real random handlers with every possible generator byte."""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def main():
    ranges = [(0, 255), (0, 0), (255, 255), (37, 193), (128, 255), (250, 255)]
    with tempfile.TemporaryDirectory(prefix='sierra-random-') as name:
        tmp = Path(name)
        coco, cs = compile_module(ROOT / 'objs/mnln.asm', tmp / 'mnln')
        native, ns = compile_module(ROOT / 'objs/wbgame.asm', tmp / 'wbgame')
        d, emulator = start_cpu(idle_rom(tmp / 'idle.rom'), timeout=900)
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            for owner, code, syms, bases in [
                ('CoCo', coco, cs, (0x8000, 0x9000)),
                ('native', native, ns, (0x9000, 0xa000)),
            ]:
                for base in bases:
                    d.write(base, code)
                    private = 0 if owner == 'CoCo' else 0x1000
                    if private:
                        d.write(private, bytes(syms['size']) + b'GUARD')
                        d.write(private + syms['resourcebase'], private.to_bytes(2, 'big'))
                    table = 0x0431 if not private else private + syms['vmvariables']
                    args = 0x2000 if not private else private + syms['vmarguments']
                    entry = base + syms['CmdRandomImpl' if not private else 'GameRandomCommand']
                    generator = base + syms['InitRandSeed']
                    d.breakpoint(generator); d.breakpoint(0x7e00)
                    for minimum, maximum in ranges:
                        for random_byte in range(256):
                            destination = 0 if random_byte & 1 else 255
                            d.write(table, b'\xa5' * 256)
                            d.write(args, bytes([minimum, maximum, destination]) + b'ARGS')
                            d.write(0x7ef0, b'\x7e\x00STACK')
                            d.regs(pc=entry, s=0x7ef0, y=args, u=private,
                                   dp=private >> 8, cc=0x50)
                            d.call('c'); r = d.regs()
                            assert r['pc'] == generator
                            # Substitute only the random source, retaining the
                            # real divisor, stream reads and variable store.
                            ret = int.from_bytes(d.read(r['s'], 2), 'big')
                            d.regs(pc=ret, s=r['s'] + 2, b=random_byte)
                            d.call('c'); r = d.regs()
                            expected = bytearray(b'\xa5' * 256)
                            expected[destination] = minimum + random_byte % (maximum - minimum + 1)
                            assert r['pc'] == 0x7e00 and r['s'] == 0x7ef2
                            assert d.read(0x7ef2, 5) == b'STACK'
                            assert d.read(table, 256) == expected, (owner, minimum, maximum, random_byte)
                            assert d.read(args + 3, 4) == b'ARGS'
                            if private:
                                assert not r['cc'] & 1 and r['b'] == 0
                                assert d.read(private + syms['size'], 5) == b'GUARD'
                            else:
                                assert r['y'] == args + 3
                    if private:
                        # Native validation must reject a reversed range
                        # before requesting a random byte or storing a value.
                        d.write(args, bytes([200, 10, 255]))
                        d.write(table, b'\xa5' * 256)
                        d.write(0x7ef0, b'\x7e\x00STACK')
                        d.regs(pc=entry, s=0x7ef0, dp=private >> 8, u=private, cc=0x50)
                        d.call('c'); r = d.regs()
                        assert r['pc'] == 0x7e00 and r['cc'] & 1
                        assert r['s'] == 0x7ef2 and d.read(table, 256) == b'\xa5' * 256
                    assert d.read(base, len(code)) == code
                    d.breakpoint(generator, False); d.breakpoint(0x7e00, False)
            print('PASS: both real random handlers at two load addresses; all 256 generator bytes across six inclusive ranges, destination variables 0/255, whole-byte and singleton edges, native reversed-range rejection, stack/buffer guards and immutable code')
        finally:
            d.s.close(); emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
