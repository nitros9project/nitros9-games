#!/usr/bin/env python3
"""Execute native AGI picture commands through the integrated game owner."""
from pathlib import Path
import sys
import tempfile
from check_wbres import exercise, idle_rom, start_cpu
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'wildbits'))
from export_picture import resource, render


def main():
    game = ROOT / 'kingsquest1'
    commands, volume, offset = resource(game, 1)
    expected = render(game, commands, 'lwasm.orig', ROOT.parent.parent / 'nitros9/defs')
    script = bytes([3,0,1,24,0,25,0,26,134,1,0])
    logic = len(script).to_bytes(2,'little') + script
    assert volume != 0, 'test logic occupies volume zero'
    files = {
        '/game/logDir': bytes.fromhex('ffffff000000'),
        '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2, 'little') * 2 + logic,
        '/game/picDir': (game / 'picDir').read_bytes(),
        f'/game/vol.{volume}': (game / f'vol.{volume}').read_bytes(),
    }
    with tempfile.TemporaryDirectory(prefix='sierra-game-') as temp:
        d, emulator = start_cpu(idle_rom(Path(temp) / 'idle.rom'))
        try:
            d.write(0xffdf, b'\0')
            d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01')
            d.write(0xffa8, bytes(range(8)))
            error, frame = exercise(d, files, module='wbgame', base=0xb000,
                database=0x1000, window=0x8000, blocks=None, multiple=True,
                firstblock=0x10, frame_capture=True)
            assert not error, error
            failed, unused = exercise(d, files, module='wbgame', base=0xb000,
                database=0x1000, window=0x8000, blocks=None, multiple=True,
                firstblock=0x10, bitmap_error=True)
            assert failed == 32 and not unused, 'bitmap allocation refusal did not clean up'
            expected_frame = bytearray([1]) * 76800
            for y in range(168):
                row = bytes(value for pixel in expected[y*160:(y+1)*160]
                            for value in [(pixel & 15) + 1] * 2)
                expected_frame[(y+8)*320:(y+9)*320] = row
            assert frame == expected_frame, 'integrated AGI picture commands differ from CoCo pixels'
            # A small view makes transparency, clipping, mirroring, depth and
            # erase behavior observable independently of game scripts.
            rows = [[1, 1, None, 2], [3, 4, 4, 4], [5, None, None, None]]
            for mirrored, xpos, ypos, priority, erase in [
                    (False, 20, 30, 15, False),
                    (True, 159, 1, 15, False),
                    (False, 20, 30, 3, False),
                    (False, 20, 30, 15, True)]:
                script = bytes([3,0,1,24,0,25,0,33,0,41,0,0,
                    37,0,xpos,ypos,54,0,priority,35,0] +
                    ([36,0] if erase else []) + [26,134,1,0])
                logic = len(script).to_bytes(2, 'little') + script
                picture = b'\xff'
                view = bytes([0,0,2,0,0,9,0,9,0,1,3,0,4,3,
                    0x9f if mirrored else 0x1f,
                    0x12,0xf1,0x21,0,0x31,0x43,0,0x51,0])
                resources = bytearray()
                offsets = []
                for payload in (logic, picture, view):
                    offsets.append(len(resources))
                    resources.extend(b'\x12\x34\0' + len(payload).to_bytes(2, 'little') * 2 + payload)
                files = {'/game/vol.0': bytes(resources),
                    '/game/logDir': b'\xff' * 3 + offsets[0].to_bytes(3, 'big'),
                    '/game/picDir': b'\xff' * 3 + offsets[1].to_bytes(3, 'big'),
                    '/game/viewDir': offsets[2].to_bytes(3, 'big')}
                error, frame = exercise(d, files, module='wbgame', base=0xb000,
                    database=0x1000, window=0x8000, blocks=None, multiple=True,
                    firstblock=0x10, frame_capture=True)
                assert not error, (error, mirrored, xpos, ypos, priority, erase)
                expected_frame = bytearray([1]) * 76800
                expected_frame[8*320:176*320] = bytes([16]) * (168*320)
                if priority >= 4 and not erase:
                    for rownum, row in enumerate(rows):
                        y = ypos - len(rows) + 1 + rownum
                        for col, color in enumerate(reversed(row) if mirrored else row):
                            x = xpos + col
                            if color is not None and 0 <= x < 160 and 0 <= y < 168:
                                address = (y+8)*320 + x*2
                                expected_frame[address:address+2] = bytes([color+1]) * 2
                assert frame == expected_frame, (mirrored, xpos, ypos, priority, erase,
                    next((i for i, (a,b) in enumerate(zip(frame, expected_frame)) if a != b), None))
            # Repeated cycles must move the ego and stop precisely at a target.
            # An end-of-loop animation must set its completion flag as well.
            for mode in ('normal', 'move', 'animation', 'arrow', 'backspace', 'wall', 'land', 'water'):
                setup = bytes([3,0,1,24,0,25,0,33,0,41,0,0,
                    37,0,20,60,70,0,35,0,26])
                if mode in ('normal', 'wall', 'land', 'water'):
                    setup += bytes([3,6,3])
                    if mode == 'land':
                        setup += bytes([65,0])
                    elif mode == 'water':
                        setup += bytes([64,0])
                    stop = bytes([255,1,250,3,255,2,0,134,1])
                elif mode in ('arrow', 'backspace', 'wall', 'land', 'water'):
                    setup += bytes([132])
                    stop = bytes([255,1,250,4,255,2,0,134,1])
                elif mode == 'move':
                    setup += bytes([81,0,23,60,2,200])
                    stop = bytes([255,7,200,255,2,0,134,1])
                else:
                    setup += bytes([73,0,200])
                    stop = bytes([255,7,200,255,2,0,134,1])
                script = bytes([255,7,11,255]) + len(setup).to_bytes(2,'little') + setup
                script += bytes([1,250]) + stop + bytes([255,1,250,8,255,2,0,134,1,0])
                logic = len(script).to_bytes(2,'little') + script
                # Two 1x1 cels: red followed by green.
                view = bytes([0,0,1,0,0,7,0,2,5,0,10,0,
                    1,1,15,0x11,0,1,1,15,0x21,0])
                resources = bytearray()
                offsets = []
                picture = b'\xff'
                if mode == 'wall':
                    picture = bytes([0xf2,0,0xf6,21,60,21,60,0xf3,0xff])
                elif mode in ('land', 'water'):
                    picture = bytes([0xf2,3,0xf6,21,60,22,60,0xf3,0xff])
                for payload in (logic, picture, view):
                    offsets.append(len(resources))
                    resources.extend(b'\x12\x34\0' + len(payload).to_bytes(2,'little') * 2 + payload)
                files = {'/game/vol.0': bytes(resources),
                    '/game/logDir': b'\xff' * 3 + offsets[0].to_bytes(3,'big'),
                    '/game/picDir': b'\xff' * 3 + offsets[1].to_bytes(3,'big'),
                    '/game/viewDir': offsets[2].to_bytes(3,'big')}
                error, output, state = exercise(d, files, module='wbgame', base=0xb000,
                    database=0x1000, window=0x8000, blocks=None, multiple=True,
                    firstblock=0x10, capture=True,
                    keyboard=b'\x09' if mode == 'arrow' else (b'\x08' if mode == 'backspace' else b''),
                    key_sense=0x40 if mode == 'arrow' else 0)
                assert not error and not output, (mode, error)
                ego = state['vmobjects'][:43]
                if mode in ('backspace', 'wall', 'land'):
                    assert ego[3:5] == bytes([20,60]), (mode, ego.hex())
                elif mode in ('normal', 'arrow', 'water'):
                    assert ego[3:5] == bytes([22,60]), (mode, ego.hex())
                elif mode == 'move':
                    assert ego[3:5] == bytes([23,60]), (mode, ego.hex())
                    assert ego[0x1e] == 1 and ego[0x21] == 0 and ego[0x22] == 0
                    assert state['vmflags'][200] == 1
                else:
                    assert ego[0x0e] == 1 and not (ego[0x26] & 0x20)
                    assert state['vmflags'][200] == 1
            # display writes true 8-by-8 cells, including a row that straddles
            # an 8K frame page, and survives the next show.pic refresh.
            import re
            font = bytes(int(v,16) for v in re.findall(r'\$([0-9A-F]{2})',
                (ROOT / 'objs/font-data.asm').read_text()))
            message = b'Ab!\0'
            key = b'Avis Durgan'
            encrypted = bytes(value ^ key[i % len(key)] for i,value in enumerate(message))
            script = bytes([109,14,1,103,3,39,1,26,134,1,0])
            logic = len(script).to_bytes(2, 'little') + script
            logic += bytes([1]) + (4+len(message)).to_bytes(2,'little') + bytes([4,0]) + encrypted
            files = {'/game/logDir': b'\xff' * 3 + bytes(3),
                '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2,'little') * 2 + logic}
            error, frame = exercise(d, files, module='wbgame', base=0xb000,
                database=0x1000, window=0x8000, blocks=None, multiple=True,
                firstblock=0x10, frame_capture=True)
            assert not error, error
            expected_frame = bytearray([1]) * 76800
            row, column = 3, 39
            for character in message[:-1]:
                for glyphrow in range(8):
                    bits = font[character*8 + glyphrow]
                    for pixel in range(8):
                        expected_frame[(row*8+glyphrow)*320+column*8+pixel] = 15 if bits & (128 >> pixel) else 2
                column += 1
                if column == 40:
                    column, row = 0, row+1
            assert frame == expected_frame, 'native text glyphs/colors/wrapping differ or were erased by show.pic'
            script = bytes([121,ord('q'),0,7,1,250,255,12,7,255,2,0,134,1,0])
            logic = len(script).to_bytes(2, 'little') + script
            files = {'/game/logDir': b'\xff' * 3 + bytes(3),
                '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2, 'little') * 2 + logic}
            error, output, state = exercise(d, files, module='wbgame', base=0xb000,
                database=0x1000, window=0x8000, blocks=None, multiple=True,
                firstblock=0x10, capture=True, keyboard=b'q', clock=(59,0))
            assert not error and not output
            assert state['vmvariables'][250] == 2, 'controller did not reach the next logic cycle'
            assert state['vmvariables'][11] == 1, 'clock lost the second at minute rollover'
            print('PASS: native picture/view composition matches every castle pixel and handles transparent/mirrored/clipped/occluded/erased sprites with persistent native text, repeated logic cycles, keyboard controllers, clock rollover, stepping, move-to completion, end-of-loop animation, arrows/backspace, one mapping and complete cleanup')
        finally:
            d.s.close()
            emulator.terminate()
            emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
