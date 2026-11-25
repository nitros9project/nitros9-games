#!/usr/bin/env python3
"""Verify CoCo prevent.input/accept.input flag transitions at real handlers."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom, start_cpu


def run_with_display_service(debugger):
    for _ in range(128):
        debugger.call('c')
        regs = debugger.regs()
        if regs['pc'] == 0x7e00:
            return regs
        assert regs['pc'] == 0x0701, ('unexpected CoCo screen-service entry', regs)
        ret = int.from_bytes(debugger.read(regs['s'], 2), 'big')
        debugger.regs(pc=ret, s=regs['s'] + 2)
    raise AssertionError('CoCo input command did not return')


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-screen-input-') as name:
        tmp = Path(name)
        coco, syms = compile_module(ROOT / 'objs/mnln.asm', tmp / 'mnln')
        debugger, emulator = start_cpu(idle_rom(tmp / 'idle.rom'), timeout=300)
        calls = 0
        try:
            debugger.write(0xffdf, b'\0')
            debugger.write(0xff90, b'\x4c')
            debugger.write(0xff91, b'\x01')
            debugger.write(0xffa8, bytes(range(8)))
            debugger.breakpoint(0x0701)
            debugger.breakpoint(0x7e00)
            cases = (('cmd_prevent_input', 0), ('cmd_accept_input', 1))
            for base in (0x8000, 0x9000):
                debugger.write(base, coco)
                for command, expected in cases:
                    for initial in (0, 1):
                        debugger.write(0x01d5, bytes([initial]))
                        debugger.write(0x05b9, b'\0')  # cursor is hidden
                        debugger.write(0x01ad, b'\0')  # no cursor glyph to erase
                        debugger.write(0x01d7, b'\x0a')
                        debugger.write(0x024d, b'\x27')
                        debugger.write(0x05ba, bytes(50))
                        debugger.write(0x024c, b'\x0f\xf0')
                        debugger.write(0x7ef0, b'\x7e\x00STACK')
                        debugger.regs(pc=base + syms[command], s=0x7ef0,
                                      y=0x2000, dp=0, cc=0x50)
                        regs = run_with_display_service(debugger)
                        assert debugger.read(0x01d5, 1) == bytes([expected]), \
                            (command, initial, debugger.read(0x01d5, 1))
                        assert regs['s'] == 0x7ef2, (command, initial, regs)
                        assert debugger.read(0x7ef2, 5) == b'STACK'
                        calls += 1
            print(f'PASS: {calls} actual CoCo prevent.input/accept.input calls at two code bases; '
                  'enabled flag, repeated transitions, display-service returns and caller-stack guards')
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
