#!/usr/bin/env python3
"""Compare actual CoCo and Wild Bits program/player control handlers."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-player-control-') as name:
        tmp = Path(name)
        coco, cs = compile_module(ROOT/'objs/mnln.asm', tmp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame',
                                    defines=('WILDBITS=1',))
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=900)
        calls = 0
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            d.breakpoint(0x7e00)
            cases = (
                ('program', 'cmd_program_control', 'VmProgramControl', 0, 2),
                ('player', 'cmd_player_control', 'VmSetPlayerControl', 1, 0),
            )
            for label, coco_symbol, native_symbol, control, motion in cases:
                for owner, code, syms, bases in (
                    ('CoCo', coco, cs, (0x8000, 0x9000)),
                    ('Wild Bits', native, ns, (0x9000, 0xa000)),
                ):
                    private = 0x1000 if owner == 'Wild Bits' else 0
                    objects = private + syms['vmobjects'] if private else 0x4000
                    if private:
                        d.write(private, bytes(syms['size']) + b'GUARD')
                        d.write(private + syms['resourcebase'], private.to_bytes(2, 'big'))
                        player = private + syms['vmplayercontrol']
                        d.write(private + syms['vmopcode'],
                                bytes([131 if control == 0 else 132]))
                    else:
                        d.write(0x30, objects.to_bytes(2, 'big'))
                        player = 0x0250
                    ego = bytearray([0x5a] * 43)
                    ego[0x21] = 7
                    ego[0x22] = 2
                    d.write(objects - 1, b'G' + ego + b'H')
                    d.write(player, b'\x00')
                    d.write(0x7ef0, b'\x7e\x00STACK')
                    d.regs(pc=bases[0] + syms[coco_symbol if not private else native_symbol],
                           s=0x7ef0, y=0x2000 if not private else 0,
                           u=private, dp=private >> 8, cc=0x50)
                    d.write(bases[0], code)
                    d.call('c')
                    regs = d.regs()
                    assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2, (owner, label, regs)
                    expected = bytearray(ego)
                    expected[0x22] = motion
                    assert d.read(objects - 1, 45) == b'G' + expected + b'H', (owner, label, d.read(objects,43).hex())
                    assert d.read(player, 1) == bytes([control]), (owner, label)
                    assert d.read(0x7ef2, 5) == b'STACK'
                    if private:
                        assert d.read(private + syms['size'], 5) == b'GUARD'
                    calls += 1
            print(f'PASS: {calls} actual CoCo/Wild Bits program/player control calls; '
                  'player.control restores player input and normalizes ego motion '
                  'without changing direction, guards or caller stack')
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
