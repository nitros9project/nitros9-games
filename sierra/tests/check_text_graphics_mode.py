#!/usr/bin/env python3
"""Verify CoCo text.screen/graphics mode calls preserve the graphics page."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom, start_cpu


def run_with_display_service(debugger):
    for _ in range(16):
        debugger.call('c')
        regs = debugger.regs()
        if regs['pc'] == 0x7e00:
            return regs
        assert regs['pc'] == 0x0701, ('unexpected CoCo display service entry', regs)
        ret = int.from_bytes(debugger.read(regs['s'], 2), 'big')
        debugger.regs(pc=ret, s=regs['s'] + 2)
    raise AssertionError('CoCo mode command did not return')


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-text-graphics-mode-') as name:
        tmp = Path(name)
        coco, syms = compile_module(ROOT / 'objs/mnln.asm', tmp / 'mnln')
        debugger, emulator = start_cpu(idle_rom(tmp / 'idle.rom'), timeout=180)
        calls = 0
        try:
            debugger.write(0xffdf, b'\0')
            debugger.write(0xff90, b'\x4c')
            debugger.write(0xff91, b'\x01')
            debugger.write(0xffa8, bytes(range(8)))
            debugger.breakpoint(0x0701)
            debugger.breakpoint(0x7e00)
            picture = bytes((i * 29 + 7) & 255 for i in range(8192))
            for base in (0x8000, 0x9000):
                debugger.write(base, coco)
                debugger.write(0x4000, picture)
                debugger.write(0x05b9, b'\0')  # no cursor to erase
                debugger.write(0x01ad, b'\0')
                debugger.write(0x01d5, b'\0')  # graphics-mode input redraw is inert
                debugger.write(0x0246, b'\0')  # status redraw is inert
                debugger.write(0x05ec, b'\0')
                debugger.write(0x7ef0, b'\x7e\x00STACK')
                debugger.regs(pc=base + syms['cmd_text_screen'], s=0x7ef0,
                              dp=0, cc=0x50)
                regs = run_with_display_service(debugger)
                assert debugger.read(0x05ec, 1) == b'\x01'
                assert debugger.read(0x19, 1) == b'\x15'
                assert debugger.read(0x4000, len(picture)) == picture
                assert regs['s'] == 0x7ef2 and debugger.read(0x7ef2, 5) == b'STACK'
                calls += 1
                debugger.write(0x7ef0, b'\x7e\x00STACK')
                debugger.regs(pc=base + syms['cmd_graphics'], s=0x7ef0,
                              dp=0, cc=0x50)
                regs = run_with_display_service(debugger)
                assert debugger.read(0x05ec, 1) == b'\0'
                assert debugger.read(0x19, 1) == b'\x09'
                assert debugger.read(0x4000, len(picture)) == picture
                assert regs['s'] == 0x7ef2 and debugger.read(0x7ef2, 5) == b'STACK'
                calls += 1
            print(f'PASS: {calls} actual CoCo text.screen/graphics calls at two code bases; '
                  'mode pages, picture-memory retention, display-service returns and stack guards')
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
