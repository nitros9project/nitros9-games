#!/usr/bin/env python3
"""Compare actual CoCo and Wild Bits clear.text.rect cell attributes."""
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_logic_executor import compile_module, ROOT
from check_wbres import exercise, idle_rom, start_cpu


def coco_rectangle(debugger, code, syms, base, color, top=3, left=5,
                   bottom=4, right=7):
    debugger.write(base, code)
    debugger.write(0x2000, bytes([top, left, bottom, right, color]) + b'ARGS')
    debugger.write(0x40, b'\x09\x0a')
    debugger.write(0x24c, b'\x0f\xf0')
    debugger.write(0x7ef0, b'\x7e\x00STACK')
    debugger.regs(pc=base + syms['cmd_clear_text_rect'], s=0x7ef0,
                  y=0x2000, dp=0, cc=0x50)
    rows = []
    for _ in range(12):
        debugger.call('c')
        regs = debugger.regs()
        if regs['pc'] == 0x7e00:
            break
        assert regs['pc'] == 0x0701, ('CoCo clear.text.rect service', regs)
        page = debugger.read(0x19, 1)[0]
        if page == 0x0f:
            row = debugger.read(0x40, 1)[0]
            column = debugger.read(0x41, 1)[0]
            # DrawTextRect stages the actual text bytes at U before its MMU write.
            rows.append((row, column, debugger.read(regs['u'], right-left+1),
                         debugger.read(0x24c, 2)))
        ret = int.from_bytes(debugger.read(regs['s'], 2), 'big')
        debugger.regs(pc=ret, s=regs['s'] + 2)
    else:
        raise AssertionError('CoCo clear.text.rect did not return')
    clipped_bottom = min(bottom, 23)
    wanted_rows = ([(row, left, bytes([0x20]) * (right-left+1),
                     bytes([0xff, color * 0x11]))
                    for row in range(top, clipped_bottom+1)] if top < 24 else [])
    assert rows == wanted_rows, ((top,left,bottom,right,color), rows, wanted_rows)
    assert regs['y'] == 0x2005 and regs['s'] == 0x7ef2, (color, regs)
    assert debugger.read(0x40, 2) == b'\x09\x0a'
    assert debugger.read(0x24c, 2) == b'\x0f\xf0'
    assert debugger.read(0x2005, 4) == b'ARGS'
    return rows


def native_rectangle(debugger, module_root, color, top=3, left=5,
                     bottom=4, right=7):
    native_symbols = symbols(module_root / 'wbgame.map')
    body = bytes([154, top, left, bottom, right, color, 12, 200, 134, 1, 0])
    logic = len(body).to_bytes(2, 'little') + body
    files = {'/game/logDir': b'\xff' * 3 + bytes(3),
             '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2, 'little') * 2 + logic}
    initial_chars = b'A' * 1000
    initial_colors = b'\x12' * 1000
    captured = []

    def seed(cpu, regs, syms):
        cpu.write(syms['textcharacters'], initial_chars)
        cpu.write(syms['textcolors'], initial_colors)
        cpu.write(syms['vmgraphics'], b'\x01')
        return False

    def capture(cpu, regs, syms):
        captured.append((cpu.read(syms['textcharacters'], 1000),
                         cpu.read(syms['textcolors'], 1000)))
        return False

    error, _, state = exercise(debugger, files, module='wbgame',
        module_root=module_root, base=0xa000, database=0, window=0x8000,
        blocks=None, multiple=True, firstblock=0x10, capture=True,
        breakpoint_hooks={'GameClearTextRect': seed, 'GameTextPresent': capture},
        os_call_limit=30000)
    assert error == 0 and state['vmflags'][200] == 1, ('native script continuation', color, error)
    assert len(captured) == 1, ('native text-plane capture count', color, len(captured))
    chars, attrs = captured[0]
    expected_chars = bytearray(initial_chars)
    expected_attrs = bytearray(initial_colors)
    value = 0xf0 | color
    for row in range(top, min(bottom, 23)+1):
        for column in range(left, right+1):
            offset = row * 40 + column
            expected_chars[offset] = 0x20
            expected_attrs[offset] = value
    assert chars == expected_chars, ('native text cells', color)
    assert attrs == expected_attrs, ('native text colors', (top,left,bottom,right,color),
        attrs[3*40+5:3*40+8].hex(), value)
    return chars, attrs


def coco_bounded_inverted_probe(debugger, code, syms, base):
    """Bound the CoCo vertical-inversion path before it can write indefinitely."""
    debugger.write(base, code)
    debugger.write(0x2000, bytes([4, 5, 3, 7, 7]) + b'ARGS')
    debugger.write(0x40, b'\x09\x0a')
    debugger.write(0x24c, b'\x0f\xf0')
    debugger.write(0x7ef0, b'\x7e\x00STACK')
    debugger.regs(pc=base + syms['cmd_clear_text_rect'], s=0x7ef0,
                  y=0x2000, dp=0, cc=0x50)
    requests = []
    returned = False
    for _ in range(8):
        debugger.call('c')
        regs = debugger.regs()
        if regs['pc'] == 0x7e00:
            returned = True
            break
        assert regs['pc'] == 0x0701, ('CoCo inverted rectangle service', regs)
        requests.append((debugger.read(0x40, 1)[0],
                         debugger.read(0x41, 1)[0]))
        ret = int.from_bytes(debugger.read(regs['s'], 2), 'big')
        debugger.regs(pc=ret, s=regs['s'] + 2)
    # The fixture is intentionally abandoned at a text service breakpoint;
    # no actual display writes occur and no unbounded loop is allowed to run.
    debugger.regs(pc=0x7e00, s=0x7ef2)
    assert not returned and len(requests) == 8, requests
    assert requests == [(row, 5) for row in range(4, 12)], requests
    return requests


def coco_clear_lines(debugger, code, syms, base, color, start=3, end=4):
    """Capture the actual CoCo clear.lines text writes and caller state."""
    debugger.write(base, code)
    debugger.write(0x2000, bytes([start, end, color]) + b'ARGS')
    debugger.write(0x40, b'\x09\x0a')
    debugger.write(0x24c, b'\x0f\xf0')
    debugger.write(0x7ef0, b'\x7e\x00STACK')
    debugger.regs(pc=base + syms['cmd_clear_lines'], s=0x7ef0,
                  y=0x2000, dp=0, cc=0x50)
    rows = []
    for _ in range(32):
        debugger.call('c')
        regs = debugger.regs()
        if regs['pc'] == 0x7e00:
            break
        assert regs['pc'] == 0x0701, ('CoCo clear.lines service', regs)
        row = debugger.read(0x40, 1)[0]
        column = debugger.read(0x41, 1)[0]
        rows.append((row, column, debugger.read(regs['u'], 40),
                     debugger.read(0x24c, 2)))
        ret = int.from_bytes(debugger.read(regs['s'], 2), 'big')
        debugger.regs(pc=ret, s=regs['s'] + 2)
    else:
        raise AssertionError('CoCo clear.lines did not return')
    expected = [(row, 0, b' ' * 40, bytes([0xff, color * 0x11]))
                for row in range(start, end + 1)]
    assert rows == expected, (color, rows, expected)
    assert regs['y'] == 0x2003 and regs['s'] == 0x7ef2, (color, regs)
    assert debugger.read(0x40, 2) == b'\x09\x0a'
    assert debugger.read(0x24c, 2) == b'\x0f\xf0'
    assert debugger.read(0x2003, 4) == b'ARGS'
    return rows


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-text-rect-') as name:
        tmp = Path(name)
        coco, coco_symbols = compile_module(ROOT / 'objs/mnln.asm', tmp / 'mnln')
        module_root = ROOT / 'objs'
        debugger, emulator = start_cpu(idle_rom(tmp / 'idle.rom'), timeout=900)
        try:
            debugger.write(0xffdf, b'\0')
            debugger.write(0xff90, b'\x4c')
            debugger.write(0xff91, b'\x01')
            debugger.write(0xffa8, bytes(range(8)))
            debugger.breakpoint(0x0701)
            debugger.breakpoint(0x7e00)
            cases = 0
            for color in (0, 1, 7, 15):
                coco_rows = coco_rectangle(debugger, coco, coco_symbols, 0x8000, color)
                chars, attrs = native_rectangle(debugger, module_root, color)
                coco_foreground = (coco_rows[0][3][0] >> 4) & 15
                coco_background = coco_rows[0][3][1] & 15
                assert (coco_foreground << 4 | coco_background) == (0xf0 | color)
                assert chars[3*40+5:3*40+8] == b'   '
                assert attrs[3*40+5:3*40+8] == bytes([0xf0 | color]) * 3
                cases += 1
            clear_lines_cases = 0
            for color in (0, 1):
                rows = coco_clear_lines(debugger, coco, coco_symbols,
                                        0x8000, color)
                assert [row[0] for row in rows] == [3, 4]
                clear_lines_cases += 1
            for top, bottom, wanted_rows in ((23, 24, [23]), (23, 255, [23]),
                                             (24, 24, []), (25, 25, [])):
                left, right, color = 5, 7, 7
                coco_rows = coco_rectangle(debugger, coco, coco_symbols, 0x8000,
                    color, top, left, bottom, right)
                chars, attrs = native_rectangle(debugger, module_root, color,
                    top, left, bottom, right)
                assert [row[0] for row in coco_rows] == wanted_rows
                for row in range(top, min(bottom, 23)+1):
                    start = row*40+left
                    assert chars[start:start+right-left+1] == b' '*(right-left+1)
                    assert attrs[start:start+right-left+1] == bytes([0xf0|color])*(right-left+1)
                if not wanted_rows:
                    assert chars == b'A'*1000
                    assert attrs == b'\x12'*1000
                cases += 1
            for left, right in ((39, 40), (40, 40)):
                edge = coco_rectangle(debugger, coco, coco_symbols, 0x8000, 7,
                                      3, left, 3, right)
                chars, attrs = native_rectangle(debugger, module_root, 7,
                    3, left, 3, right)
                assert edge == [(3, left, b' '*(right-left+1), b'\xff\x77')], edge
                first = 3*40+left
                assert chars[first:first+right-left+1] == b' '*(right-left+1)
                assert attrs[first:first+right-left+1] == bytes([0xf7])*(right-left+1)
                cases += 1
            inverted = coco_bounded_inverted_probe(debugger, coco,
                coco_symbols, 0x8000)
            print(f'PASS: {cases} clear.text.rect comparisons/probes; '
                  'color nibbles plus row-23 clipping and row-24 no-op, text bytes, '
                  'caller cursor/color, operand advance, script continuation, and '
                  'column-40 linear spill into the next text row; bounded inverted-'
                  f'row probe observed {len(inverted)} CoCo text writes without return; '
                  f'{clear_lines_cases} CoCo clear.lines colors clear inclusive full-width '
                  'rows and preserve cursor/color state')
        finally:
            debugger.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill()
                emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
