#!/usr/bin/env python3
"""Check CoCo text commands' message lookup and display handoff contracts."""
from pathlib import Path
import tempfile

from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-text-command-') as name:
        tmp = Path(name)
        coco, syms = compile_module(ROOT / 'objs/mnln.asm', tmp / 'mnln')
        d, emulator = start_cpu(idle_rom(tmp / 'idle.rom'), timeout=180)
        try:
            d.write(0xffdf, b'\0')
            d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01')
            d.write(0xffa8, bytes(range(8)))
            stop, logic, table, message = 0x7e00, 0x7000, 0x7100, 0x7106
            d.breakpoint(stop)
            for base in (0x8000, 0x9000):
                d.write(base, coco)
                d.breakpoint(base + syms['message_box'])
                d.breakpoint(base + syms['PrintFmtStrToScr'])
                # One-message logic table. Message offsets are relative to
                # the table, as GetMsgPtr expects.
                d.write(logic, bytes([0, 0, 0, 1]) + bytes(6) + table.to_bytes(2, 'big'))
                # The CoCo message-offset table stores the offset low byte
                # first, matching the original engine's GetMsgPtr contract.
                d.write(table, bytes(2) + b'\x06\x00' + b'\0\0')
                d.write(message, b'Hello, Rosella!\0')
                cases = (
                    ('cmd_print', bytes([1]), 1, False, None),
                    ('cmd_print_v', bytes([7]), 7, True, None),
                    ('cmd_print_at', bytes([1, 3, 8, 5]), 1, False, (3, 8, 5)),
                    ('cmd_print_at_v', bytes([7, 3, 8, 5]), 7, True, (3, 8, 5)),
                )
                for command, operands, operand, variables, position in cases:
                    if variables:
                        d.write(0x0431 + operand, b'\x01')
                    for label in ('PrintAtRow', 'PrintAtCol', 'PrintAtHeight'):
                        d.write(base + syms[label], b'\xff')
                    d.write(0x0062, logic.to_bytes(2, 'big'))
                    d.write(0x2000, operands + b'GUARD')
                    d.write(0x7ef0, stop.to_bytes(2, 'big') + b'STACK')
                    d.regs(pc=base + syms[command], s=0x7ef0, y=0x2000,
                           dp=0, cc=0x50)
                    d.call('c')
                    r = d.regs()
                    consumed = len(operands)
                    assert r['pc'] == base + syms['message_box'], (command, r)
                    assert r['u'] == message, (command, hex(r['u']))
                    assert r['y'] == 0x2000 + consumed
                    assert d.read(r['y'], 5) == b'GUARD'
                    assert d.read(0x7ef2, 5) == b'STACK'
                    if position:
                        actual_position = tuple(d.read(base + syms[label], 1)[0]
                                                for label in ('PrintAtRow', 'PrintAtCol', 'PrintAtHeight'))
                        expected_position = (position[1], position[0], position[2])
                        assert actual_position == expected_position, (command, actual_position)
                    # message_box is covered by the original-game visual MAME
                    # tests. Skip its blocking implementation here, then let
                    # the actual command epilogue return to the caller.
                    return_pc = int.from_bytes(d.read(r['s'], 2), 'big')
                    d.regs(pc=return_pc, s=r['s'] + 2)
                    d.call('c')
                    r = d.regs()
                    assert (r['pc'], r['s'], r['y']) == (stop, 0x7ef2, 0x2000 + consumed)
                    assert d.read(0x7ef2, 5) == b'STACK'
                    if position:
                        assert all(d.read(base + syms[label], 1) == b'\xff'
                                   for label in ('PrintAtRow', 'PrintAtCol', 'PrintAtHeight'))
                # display/display.v format the selected message into a local
                # text buffer and hand that buffer to CoCo's screen renderer.
                for command, operands, variable_values in (
                        ('cmd_display', bytes([3, 8, 1]), None),
                        ('cmd_display_v', bytes([20, 21, 22]), (3, 8, 1))):
                    if variable_values:
                        for index, value in zip((20, 21, 22), variable_values):
                            d.write(0x0431 + index, bytes([value]))
                    d.write(0x0166, b'\0')
                    d.write(0x0040, b'\x0a\x0a')
                    d.write(0x2000, operands + b'GUARD')
                    d.write(0x7ef0, stop.to_bytes(2, 'big') + b'STACK')
                    d.regs(pc=base + syms[command], s=0x7ef0, y=0x2000,
                           dp=0, cc=0x50)
                    d.call('c')
                    r = d.regs()
                    consumed = len(operands)
                    assert r['pc'] == base + syms['PrintFmtStrToScr'], (command, r)
                    buffer = int.from_bytes(d.read(r['s'] + 2, 2), 'big')
                    assert d.read(buffer, 16).split(b'\0', 1)[0] == b'Hello, Rosella!', \
                        (command, r, hex(buffer), d.read(buffer, 24))
                    assert d.read(0x0040, 2) == b'\x03\x08'
                    assert r['y'] == 0x2000 + consumed and d.read(r['y'], 5) == b'GUARD'
                    assert d.read(0x7ef2, 5) == b'STACK'
                    return_pc = int.from_bytes(d.read(r['s'], 2), 'big')
                    d.regs(pc=return_pc, s=r['s'] + 2)
                    d.call('c')
                    r = d.regs()
                    assert (r['pc'], r['s'], r['y']) == (stop, 0x7ef2, 0x2000 + consumed)
                    assert d.read(0x0040, 2) == b'\x0a\x0a'
                    assert d.read(0x7ef2, 5) == b'STACK'
                d.breakpoint(base + syms['message_box'], False)
                d.breakpoint(base + syms['PrintFmtStrToScr'], False)
            print('PASS: actual CoCo print/display literal and variable handlers resolve message-table entries, hand text to message_box/PrintFmtStrToScr, preserve requested geometry, consume operands and return with caller stack intact at two code bases')
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
