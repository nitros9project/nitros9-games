#!/usr/bin/env python3
"""Verify the actual CoCo set.text.attribute color packing."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom, start_cpu


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-text-attribute-') as name:
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
                for foreground, background in ((2, 3),):
                    debugger.write(0x024c, b'\x55\xaa')
                    debugger.write(0x2000, bytes([foreground, background]) + b'ARGS')
                    debugger.write(0x7ef0, b'\x7e\x00STACK')
                    debugger.regs(pc=base + syms['cmd_set_text_attribute'],
                                  s=0x7ef0, y=0x2000, dp=0, cc=0x50)
                    debugger.call('c')
                    regs = debugger.regs()
                    assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2, regs
                    assert debugger.read(0x024c, 2) == bytes([
                        foreground * 0x11, background * 0x11])
                    assert regs['y'] == 0x2002
                    assert debugger.read(0x2002, 4) == b'ARGS'
                    assert debugger.read(0x7ef2, 5) == b'STACK'
                    calls += 1
            print(f'PASS: {calls} actual CoCo set.text.attribute calls at two code bases; '
                  'packed color nibbles, operand advancement and caller-stack guard')
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
