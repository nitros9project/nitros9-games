#!/usr/bin/env python3
"""Verify CoCo set.cursor.char reads the first byte of its logic message."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom, start_cpu


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-cursor-char-') as name:
        tmp = Path(name)
        coco, syms = compile_module(ROOT / 'objs/mnln.asm', tmp / 'mnln')
        debugger, emulator = start_cpu(idle_rom(tmp / 'idle.rom'), timeout=180)
        calls = 0
        try:
            debugger.write(0xffdf, b'\0')
            debugger.write(0xff90, b'\x4c')
            debugger.write(0xff91, b'\x01')
            debugger.write(0xffa8, bytes(range(8)))
            debugger.breakpoint(0x7e00)
            for base in (0x8000, 0x9000):
                debugger.write(base, coco)
                debugger.write(0x0062, b'\x70\x00')
                logic = bytearray(12)
                logic[3] = 1
                logic[10:12] = b'\x71\x00'
                debugger.write(0x7000, logic)
                debugger.write(0x7100, b'\0\0\x0a\0' + bytes(6) + b'!prompt\0')
                debugger.write(0x2000, b'\x01ARGS')
                debugger.write(0x7ef0, b'\x7e\x00STACK')
                debugger.regs(pc=base + syms['cmd_set_cursor_char'], s=0x7ef0,
                              y=0x2000, dp=0, cc=0x50)
                debugger.call('c')
                regs = debugger.regs()
                assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2, regs
                assert debugger.read(0x01ad, 1) == b'!'
                assert regs['y'] == 0x2001
                assert debugger.read(0x2001, 4) == b'ARGS'
                assert debugger.read(0x7ef2, 5) == b'STACK'
                calls += 1
            print(f'PASS: {calls} actual CoCo set.cursor.char calls at two code bases; '
                  'message-table lookup, first-character selection, operand advance and stack guard')
        finally:
            debugger.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except Exception:
                emulator.kill()
                emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
