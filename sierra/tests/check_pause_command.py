#!/usr/bin/env python3
"""Check CoCo pause sequencing around event clear and the pause modal."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom, start_cpu


def return_from_call(d, regs):
    ret = int.from_bytes(d.read(regs['s'], 2), 'big')
    d.regs(pc=ret, s=regs['s'] + 2)


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-pause-command-') as name:
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
            for base in (0x8000, 0x9000):
                d.write(base, coco)
                d.write(0x0102, b'\0')
                d.write(0x7ef0, b'\x7e\x00STACK')
                for callback in ('events_clear', 'message_box'):
                    d.breakpoint(base + syms[callback])
                d.regs(pc=base + syms['cmd_pause'], s=0x7ef0, dp=0, cc=0x50)
                d.call('c')
                r = d.regs()
                assert r['pc'] == base + syms['events_clear'], r
                assert d.read(0x0102, 1) == b'\1'
                return_from_call(d, r)
                d.call('c')
                r = d.regs()
                assert r['pc'] == base + syms['message_box'], r
                assert d.read(0x0102, 1) == b'\1'
                assert r['u'] == base + syms['PauseMsg'], hex(r['u'])
                return_from_call(d, r)
                d.call('c')
                r = d.regs()
                assert r['pc'] == stop and r['s'] == 0x7ef2, r
                assert d.read(0x0102, 1) == b'\0'
                assert d.read(0x7ef2, 5) == b'STACK'
                assert d.read(base, len(coco)) == coco
                for callback in ('events_clear', 'message_box'):
                    d.breakpoint(base + syms[callback], False)
                calls += 1
            print(f'PASS: {calls} actual CoCo pause command calls at two code bases; '
                  'events clear, paused message and clock-state restoration with stack guards')
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
