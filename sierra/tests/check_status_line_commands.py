#!/usr/bin/env python3
"""Verify CoCo status-line commands request draw/clear at the right state."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom, start_cpu


def return_from_probe(d, regs):
    """Return from a trapped internal JSR without executing its body."""
    ret = int.from_bytes(d.read(regs['s'], 2), 'big')
    d.regs(pc=ret, s=regs['s'] + 2)


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-status-line-') as name:
        tmp = Path(name)
        coco, syms = compile_module(ROOT / 'objs/mnln.asm', tmp / 'mnln')
        d, emulator = start_cpu(idle_rom(tmp / 'idle.rom'), timeout=180)
        calls = 0
        try:
            d.write(0xffdf, b'\0')
            d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01')
            d.write(0xffa8, bytes(range(8)))
            stop = 0x7e00
            d.breakpoint(stop)
            d.breakpoint(0x0701)
            for base in (0x8000, 0x9000):
                d.write(base, coco)
                for on in (True, False):
                    d.write(0x0246, b'\0' if on else b'\1')
                    d.write(0x0247, b'\x16')
                    d.write(0x0040, b'\x12\x34')
                    d.write(0x7ef0, b'\x7e\x00STACK')
                    command = 'cmd_status_line_on' if on else 'cmd_status_line_off'
                    callback = 'StatusLineWrite' if on else 'ClearTextLine'
                    d.breakpoint(base + syms[callback])
                    d.regs(pc=base + syms[command], s=0x7ef0, dp=0, cc=0x50)
                    d.call('c')
                    r = d.regs()
                    assert r['pc'] == base + syms[callback], (command, r)
                    assert d.read(0x0246, 1) == (b'\1' if on else b'\0')
                    if not on:
                        assert (r['a'], r['b']) == (0x16, 0), (command, r)
                    return_from_probe(d, r)
                    d.call('c')
                    r = d.regs()
                    assert r['pc'] == stop and r['s'] == 0x7ef2, (command, r)
                    assert d.read(0x7ef2, 5) == b'STACK'
                    assert d.read(base, len(coco)) == coco
                    d.breakpoint(base + syms[callback], False)
                    calls += 1
            print(f'PASS: {calls} actual CoCo status-line command calls at two code bases; '
                  'enable/draw and disable/clear effects, row arguments and stack guards')
        finally:
            d.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except Exception:
                emulator.kill()
                emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
