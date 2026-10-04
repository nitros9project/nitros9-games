#!/usr/bin/env python3
"""Check wbpic against the real Wild Bits OS/driver in the wbjr2 MAME fork.

Uses a private disk/firmware copy. Requires an already-built emulator, Jr2
Level 2 image, and FEU booter/f0.dsk. No game assets are required.
"""
import argparse
import json
from pathlib import Path
import shutil
import struct
import subprocess
import zlib

VIEWER = Path(__file__).resolve().parents[1] / 'wildbits'


def png_rgb(path):
    """Read MAME's non-interlaced RGB8 screenshots using only the stdlib."""
    raw = path.read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    pos, packed = 8, bytearray()
    while pos < len(raw):
        size = int.from_bytes(raw[pos:pos + 4], 'big')
        kind, data = raw[pos + 4:pos + 8], raw[pos + 8:pos + 8 + size]
        if kind == b'IHDR':
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', data)
            assert (depth, color, compression, filtering, interlace) == (8, 2, 0, 0, 0)
        elif kind == b'IDAT':
            packed.extend(data)
        pos += size + 12
    source, result, previous = zlib.decompress(packed), bytearray(), bytearray(width * 3)
    stride = width * 3
    for y in range(height):
        offset = y * (stride + 1)
        mode, row = source[offset], bytearray(source[offset + 1:offset + 1 + stride])
        assert mode <= 4
        for i in range(stride):
            left = row[i - 3] if i >= 3 else 0
            above = previous[i]
            corner = previous[i - 3] if i >= 3 else 0
            if mode == 0:
                prediction = 0
            elif mode == 1:
                prediction = left
            elif mode == 2:
                prediction = above
            elif mode == 3:
                prediction = (left + above) // 2
            else:
                p = left + above - corner
                distances = [abs(p - v) for v in (left, above, corner)]
                prediction = (left, above, corner)[distances.index(min(distances))]
            row[i] = (row[i] + prediction) & 255
        result.extend(row)
        previous = row
    return width, height, bytes(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mame', required=True, type=Path)
    parser.add_argument('--disk', required=True, type=Path)
    parser.add_argument('--firmware', required=True, type=Path, help='directory containing FEU booter and f0.dsk')
    parser.add_argument('--output', required=True, type=Path, help='new directory for copied disk, screenshots and log')
    parser.add_argument('--os9', default='os9')
    parser.add_argument('--picture', type=Path, help='optional 26880-byte real reference picture for /vt1')
    parser.add_argument('--native-game', type=Path, help='test integrated native loading/decoding/presentation using this game directory')
    parser.add_argument('--picture-number', type=int, default=1)
    args = parser.parse_args()
    mame, out = args.mame.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    disk = out / 'test.dsk'
    shutil.copyfile(args.disk, disk)
    # Pad upward only: shrinking a sparse recipe image can destroy its filesystem.
    with disk.open('ab') as stream:
        stream.truncate(1 << (disk.stat().st_size - 1).bit_length())
    roms = out / 'roms' / 'wbjr2'
    roms.mkdir(parents=True)
    for name in ('booter', 'f0.dsk'):
        shutil.copyfile(args.firmware / name, roms / name)

    def os9(*items):
        return subprocess.check_output([args.os9, *map(str, items)], stderr=subprocess.STDOUT)

    def install(name, data, target=None, text=False):
        source = out / name
        source.write_bytes(data)
        os9('copy', '-r', *(['-l'] if text else []), source, f'{disk},{target or name}')

    module = 'wbrun' if args.native_game else 'wbpic'
    install(module, (VIEWER / module).read_bytes(), 'CMDS/' + module)
    os9('attr', f'{disk},CMDS/{module}', '-e', '-pe')
    bars = bytes((((4 + y // 14) & 15) << 4) | (x // 10) for y in range(168) for x in range(160))
    picture = args.picture.read_bytes() if args.picture else bytes(
        ((y // 14) << 4) | ((x // 10 + y // 7) & 15) for y in range(168) for x in range(160))
    assert len(picture) == 26880, 'reference picture must be exactly 26880 bytes'
    if args.native_game:
        from check_wbres import fixture
        import sys
        sys.path.insert(0, str(VIEWER))
        from export_picture import resource, render
        payload, volume, offset = resource(args.native_game, args.picture_number)
        picture = render(args.native_game, payload, shutil.which('lwasm.orig') or shutil.which('lwasm'), VIEWER.parents[2] / 'nitros9/defs')
        os9('makdir', f'{disk},game')
        install('picDir', (args.native_game / 'picDir').read_bytes(), 'game/picDir')
        install(f'vol.{volume}', (args.native_game / f'vol.{volume}').read_bytes(), f'game/vol.{volume}')
        commands_bytes = bytearray()
        for x in range(160):
            commands_bytes.extend([0xF0, x // 10, 0xF6, x, 0, x, 167])
        commands_bytes.append(255)
        os9('makdir', f'{disk},bars-game')
        for filename, data in fixture(bytes(commands_bytes)).items():
            basename = Path(filename).name
            install('bars-' + basename, data, 'bars-game/' + basename)
        first_command, second_command = 'wbrun /s0/bars-game 1', f'wbrun /s0/game {args.picture_number}'
    else:
        install('bars.bin', bars)
        install('picture.bin', picture)
        first_command, second_command = 'wbpic /s0/bars.bin', 'wbpic /s0/picture.bin'
    install('startup', f'load utilpak1\nload vt\nlink shell\nload {module}\nload grfdrv256\n'.encode(), text=True)
    install('feu.startup', b'bootos9 /s0/OS9Boot\n', 'FEU/startup', text=True)
    # Asset installation may extend a sparse disk: pad after all copies.
    with disk.open('ab') as stream:
        stream.truncate(1 << (disk.stat().st_size - 1).bit_length())
    commands = {600: 'iniz /vt1\n', 720: 'shell i=/vt1&\n', 800: 'mfree >/s0/free-before\n',
                900: first_command + '\n', 1500: second_command + '\n',
                2600: 'x\n', 3300: 'x\n', 4000: first_command + '\n',
                4500: second_command + '\n', 4900: 'x\n', 5700: 'x\n',
                6000: 'mfree >/s0/free-after\n', 6200: 'echo WBTEST-DONE >/s0/wbtest-done\n'}
    switches = {1200: 'Right', 1950: 'Left', 2300: 'Right', 3000: 'Left', 4300: 'Right', 5200: 'Left'}
    shots = {1150: 'bars-initial', 1800: 'picture-initial', 2200: 'bars-restored',
             2500: 'picture-restored', 2850: 'picture-closed', 3200: 'bars-survives', 3750: 'both-closed',
             4200: 'bars-relaunch', 4800: 'picture-relaunch', 5500: 'bars-survives-again'}
    factor = 2 if args.native_game else 1
    commands = {frame * factor: command for frame, command in commands.items()}
    switches = {frame * factor: direction for frame, direction in switches.items()}
    shots = {frame * factor: name for frame, name in shots.items()}
    table = lambda values: '{' + ','.join(f'[{key}]={json.dumps(value)}' for key, value in values.items()) + '}'
    script = f'''frames = 0
local keys = manager.machine.ioport.ports[":KEY3"].fields
local commands = {table(commands)}
local switches = {table(switches)}
local shots = {table(shots)}
local held
sub = emu.add_machine_frame_notifier(function()
 frames = frames + 1
 if commands[frames] then manager.machine.natkeyboard:post(commands[frames]) end
 if switches[frames] then
   held = switches[frames]; keys["Alt"]:set_value(1); keys[held]:set_value(1)
 end
 if held and switches[frames-5] then
   keys[held]:clear_value(); keys["Alt"]:clear_value(); held = nil
 end
 if shots[frames] then
   manager.machine.screens[":screen"]:snapshot({json.dumps(str(out) + '/')} .. shots[frames] .. ".png")
 end
 if frames == {6500 * factor} then manager.machine:exit() end
end)
'''
    lua = out / 'drive.lua'
    lua.write_text(script)
    command = [str(mame), 'wbjr2', '-bios', 'turbo', '-rompath', str(roms.parent),
               '-hard', str(disk), '-skip_gameinfo', '-video', 'none', '-sound', 'none',
               '-nothrottle', '-autoboot_script', str(lua), '-seconds_to_run', str(120 * factor),
               '-nvram_directory', str(out / 'nvram'), '-cfg_directory', str(out / 'cfg')]
    (out / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
    with (out / 'mame.log').open('w') as log:
        subprocess.run(command, cwd=out, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    assert 'WBTEST-DONE' in os9('list', f'{disk},wbtest-done').decode(), 'shell did not resume after both viewers'
    images = {name: png_rgb(out / (name + '.png')) for name in shots.values()}
    assert images['bars-initial'] == images['bars-restored'] == images['bars-survives']
    assert images['picture-initial'] == images['picture-restored']
    assert images['bars-initial'] == images['bars-relaunch'] == images['bars-survives-again']
    assert images['picture-initial'] == images['picture-relaunch']
    assert images['picture-closed'] != images['picture-initial']
    assert images['both-closed'] != images['bars-initial']
    # Calibrate against the sixteen bars: MAME applies the boot core's gamma.
    width, height, pixels = images['bars-initial']
    assert (width, height) == (640, 480)
    colors = [pixels[x * 40 * 3:x * 40 * 3 + 3] for x in range(16)]
    assert len(set(colors)) == 16 and colors[0] == b'\0\0\0' and colors[15] == b'\xff\xff\xff'
    for name, payload in [('bars-initial', bars), ('picture-initial', picture)]:
        width, height, pixels = images[name]
        assert (width, height) == (640, 480)
        expected = b''.join(colors[value & 15] * 4 for value in payload)
        expected = b''.join(expected[y * 1920:(y + 1) * 1920] * 2 for y in range(168))
        expected += colors[0] * (640 * (480 - 336))
        assert pixels == expected, f'{name}: real driver output differs from combined buffer'
    memory = {}
    for name in ('free-before', 'free-after'):
        memory[name] = os9('list', f'{disk},{name}')
        (out / (name + '.txt')).write_bytes(memory[name])
    assert memory['free-before'] == memory['free-after'], 'free-memory map changed after two viewer cycles'
    print('PASS: real Wild Bits drivers, every displayed pixel, two terminals, restored pictures, independent exit, relaunch, free-memory map')
    print(f'Artifacts: {out}')


if __name__ == '__main__':
    main()
