#!/usr/bin/env python3
"""Check wbpic against the real Wild Bits OS/driver in the wbjr2 MAME fork.

Uses a private disk/firmware copy. Requires an already-built emulator, Jr2
Level 2 image, and FEU booter/f0.dsk. No game assets are required.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import zlib

VIEWER = Path(__file__).resolve().parents[1] / 'objs'


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
    parser.add_argument('--module-file', type=Path, help='optional diagnostic build of the selected module')
    parser.add_argument('--ui-module-file', type=Path, help='optional diagnostic build of sierraui')
    parser.add_argument('--interpreter', action='store_true', help='exercise wbgame repeated logic cycles and keyboard-controller exit on both terminals')
    parser.add_argument('--picture-number', type=int, default=1)
    parser.add_argument('--text-modes', action='store_true', help='Switch the second game terminal through text and graphics modes')
    parser.add_argument('--overlay', action='store_true', help='overlay a visual/priority edge on the second game terminal')
    parser.add_argument('--persistence', action='store_true', help='save, change and restore the second terminal through the native file dialog')
    parser.add_argument('--full-disk', action='store_true', help='verify native save failure and recovery on a nearly full disk')
    args = parser.parse_args()
    if args.persistence and args.full_disk:
        parser.error('--persistence and --full-disk use separate timelines')
    if args.persistence and (not args.interpreter or args.text_modes):
        parser.error('--persistence requires --interpreter and its own timeline')
    if args.full_disk and (not args.interpreter or not args.native_game or args.text_modes):
        parser.error('--full-disk requires --native-game and --interpreter')
    if args.overlay and not args.interpreter:
        parser.error('--overlay requires --interpreter')
    if args.text_modes and not args.interpreter:
        parser.error('--text-modes requires --interpreter')
    if args.interpreter and not args.native_game:
        parser.error('--interpreter requires --native-game')
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

    module = 'wbgame' if args.interpreter else ('wbrun' if args.native_game else 'wbpic')
    install(module, (args.module_file or (VIEWER / module)).read_bytes(), 'CMDS/' + module)
    os9('attr', f'{disk},CMDS/{module}', '-e', '-pe')
    if args.interpreter:
        install('sierrafont', (VIEWER / 'sierrafont').read_bytes(), 'CMDS/sierrafont')
        os9('attr', f'{disk},CMDS/sierrafont', '-e', '-pe')
        install('sierrastate',(VIEWER/'sierrastate').read_bytes(),'CMDS/sierrastate')
        os9('attr',f'{disk},CMDS/sierrastate','-e','-pe')
        install('sierraui',(args.ui_module_file or (VIEWER/'sierraui')).read_bytes(),'CMDS/sierraui')
        os9('attr',f'{disk},CMDS/sierraui','-e','-pe')
    bars = bytes((((4 + y // 14) & 15) << 4) | (x // 10) for y in range(168) for x in range(160))
    picture = args.picture.read_bytes() if args.picture else bytes(
        ((y // 14) << 4) | ((x // 10 + y // 7) & 15) for y in range(168) for x in range(160))
    assert len(picture) == 26880, 'reference picture must be exactly 26880 bytes'
    if args.native_game:
        from check_wbres import fixture
        import sys
        from export_picture import resource, render
        payload, volume, offset = resource(args.native_game, args.picture_number)
        picture = render(args.native_game, payload, shutil.which('lwasm.orig') or shutil.which('lwasm'), VIEWER.parents[2] / 'nitros9/defs')
        overlay_commands = bytes([240,3,242,15,246,0,0,159,0,159,167,255])
        if args.overlay:
            picture = bytearray(picture)
            picture[:160] = bytes([243])*160
            for row in range(168):
                picture[row*160+159] = 243
            picture = bytes(picture)
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
        if args.interpreter:
            assert volume != 0, 'diagnostic logic occupies volume zero'
            for directory, number in [('bars-game', 1), ('game', args.picture_number)]:
                body = bytes([111,0,23,0,3,0,number,24,0,25,0,26])
                if (args.persistence or args.full_disk) and directory == 'game':
                    body += bytes([143,1,119,3,40,42,109,15,0,
                        121,ord('s'),0,8])
                    if args.persistence:
                        body += bytes([121,ord('c'),0,9,121,ord('r'),0,10])
                if args.overlay and directory == 'game':
                    body += bytes([3,0,0,24,0,28,0,26,27,0])
                if args.text_modes:
                    body += bytes([119,121,ord('t'),0,8,121,ord('g'),0,9])
                script = bytes([121,ord('x'),0,7,255,7,11,255,len(body),0]) + body
                if args.text_modes:
                    text_body = bytes([119,109,15,7,106,103,0,0,1])
                    graphics_body = bytes([109,15,0,107,119])
                    for controller, part in ((8,text_body),(9,graphics_body)):
                        script += bytes([255,12,controller,255,len(part),0]) + part
                if (args.persistence or args.full_disk) and directory == 'game':
                    state_controllers = [(8,bytes([125]))]
                    if args.persistence:
                        state_controllers += [(9,bytes([3,40,77])),(10,bytes([126]))]
                    for controller,part in state_controllers:
                        script += bytes([255,12,controller,255,len(part),0])+part
                    script += bytes([103,24,0,2])
                script += bytes([255,12,7,255,2,0,134,1,0])
                payload = len(script).to_bytes(2,'little') + script
                if args.text_modes:
                    text = b'Text mode on this terminal.\0'
                    cipher = b'Avis Durgan'
                    encrypted = bytes(v ^ cipher[i%len(cipher)] for i,v in enumerate(text))
                    payload += bytes([1]) + (4+len(text)).to_bytes(2,'little') + bytes([4,0]) + encrypted
                install(directory + '-logDir', bytes(3), directory + '/logDir')
                if (args.persistence or args.full_disk) and directory == 'game':
                    messages=[b'WBTST\0',b'Value: %v40\0']
                    cursor=2+2*len(messages);offsets=bytearray()
                    for text in messages:
                        offsets += cursor.to_bytes(2,'little');cursor += len(text)
                    text=b''.join(messages);cipher=b'Avis Durgan'
                    encrypted=bytes(v^cipher[i%len(cipher)] for i,v in enumerate(text))
                    payload += bytes([len(messages)])+cursor.to_bytes(2,'little')+offsets+encrypted
                data = b'\x12\x34\0' + len(payload).to_bytes(2,'little') * 2 + payload
                if args.overlay and directory == 'game':
                    assert number != 0, 'overlay fixture uses picture zero'
                    entries = bytearray((args.native_game/'picDir').read_bytes())
                    entries[:3] = len(data).to_bytes(3,'big')
                    install('overlay-picDir',entries,'game/picDir')
                    data += b'\x12\x34\0' + len(overlay_commands).to_bytes(2,'little')*2 + overlay_commands
                install(directory + '-logic', data, directory + '/vol.0')
            first_command, second_command = 'wbgame /s0/bars-game 0', 'wbgame /s0/game 0'

    else:
        install('bars.bin', bars)
        install('picture.bin', picture)
        first_command, second_command = 'wbpic /s0/bars.bin', 'wbpic /s0/picture.bin'
    if args.persistence:
        # Exercise header, payload-field and exact-stream-length validation
        # with real files consumed by the interpreter's restore command.
        from check_instances import symbols
        syms=symbols(VIEWER/'sierrastate.map')
        payload=bytearray(syms['StateCoreBytes']+160)
        payload[syms['SavedKeyCount']]=51
        payload[syms['StateCoreBytes']:syms['StateCoreBytes']+5]=b'\x01\0\0\x02\0'
        crc=65535
        for value in payload:
            crc ^= value<<8
            for bit in range(8):
                crc=((crc<<1)^0x1021 if crc&32768 else crc<<1)&65535
        header=b'WS\x01\0'+len(payload).to_bytes(2,'big')+crc.to_bytes(2,'big')+b'WBTST'+bytes(5)
        install('badstate',header+payload)
        install('shortstate',header+payload[:10])
        install('wronggame',header[:8]+b'OTHER'+bytes(3)+payload)
        badcrc=bytearray(header);badcrc[6]^=1
        install('badcrc',bytes(badcrc)+payload)
        badversion=bytearray(header);badversion[2]=2
        install('badversion',bytes(badversion)+payload)
        badlength=bytearray(header);badlength[5]=(badlength[5]+1)&255
        install('badlength',bytes(badlength)+payload)
        install('trailing',header+payload+b'\0')
    install('startup', f'load utilpak1\nload vt\nlink shell\nload {module}\nload grfdrv256\n'.encode(), text=True)
    install('feu.startup', b'bootos9 /s0/OS9Boot\n', 'FEU/startup', text=True)
    # Asset installation may extend a sparse disk: pad after all copies.
    with disk.open('ab') as stream:
        stream.truncate(1 << (disk.stat().st_size - 1).bit_length())
    if args.full_disk:
        from check_instances import symbols
        snapshot_size = 18 + symbols(VIEWER / 'sierrastate.map')['StateCoreBytes'] + 160
        free_output = os9('free', disk).decode()
        free_match = re.search(r'\((\d+) bytes\)', free_output)
        assert free_match, f'cannot read initial disk free space: {free_output}'
        filler_size = int(free_match.group(1)) - 8192
        assert filler_size > 0, f'disk unexpectedly has little free space: {free_output}'
        # OS-9 directory segment tables cap one file below the whole device;
        # split the filler so every component remains a valid file.
        chunk_limit = 20 * 1024 * 1024
        chunk_number = 0
        while filler_size:
            chunk_size = min(chunk_limit, filler_size)
            filler = out / f'disk-fill-{chunk_number:02d}.bin'
            with filler.open('wb') as stream:
                stream.truncate(chunk_size)
            os9('copy', '-r', filler, f'{disk},diskfill{chunk_number:02d}')
            filler_size -= chunk_size
            chunk_number += 1
        free_output = os9('free', disk).decode()
        free_match = re.search(r'\((\d+) bytes\)', free_output)
        assert free_match and int(free_match.group(1)) < snapshot_size, (
            f'disk still has room for the expected {snapshot_size:,}-byte snapshot: {free_output}')
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
    if args.text_modes:
        del commands[2600]
        commands.update({2550:'t',2650:'g',2800:'x\n'})
        shots.update({2625:'picture-text-mode',2775:'picture-graphics-mode'})
    if args.persistence:
        commands={600:'iniz /vt1\n',720:'shell i=/vt1&\n',800:'mfree >/s0/free-before\n',
            900:first_command+'\n',1500:second_command+'\n',
            2550:'s',3150:'s',3250:'/s0/state1\n',3500:' ',
            3700:'r',4050:'c',4300:'r',4400:'/s0/state1\n',
            5200:'r',5300:'/s0/badstate\n',5700:' ',
            5850:'r',5950:'/s0/wronggame\n',6350:' ',
            6750:'r',6850:'/s0/shortstate\n',7250:' ',
            7550:'r',7650:'/s0/badcrc\n',8050:' ',
            8450:'r',8550:'/s0/badversion\n',8950:' ',
            9100:'r',9200:'/s0/badlength\n',9600:' ',
            9750:'r',9850:'/s0/trailing\n',10250:' ',
            10500:'x\n',10800:'x\n',
            11200:first_command+'\n',11700:second_command+'\n',12100:'x\n',13000:'x\n',
            13500:'mfree >/s0/free-after\n',13700:'echo WBTEST-DONE >/s0/wbtest-done\n'}
        switches={1200:'Right',1950:'Left',2300:'Right',10650:'Left',11650:'Right',12850:'Left'}
        shots={1150:'bars-initial',1800:'picture-initial',2200:'bars-restored',2500:'picture-restored',
            2800:'save-cancelled',2900:'cancel-resumed',3500:'existing-save',3650:'existing-restored',
            3900:'restore-cancelled',
            4150:'picture-changed',4750:'picture-loaded',
            5600:'invalid-error',5800:'invalid-restored',6250:'wronggame-error',6550:'wronggame-restored',
            7150:'short-error',7450:'short-restored',7950:'badcrc-error',8250:'badcrc-restored',
            8850:'badversion-error',9050:'badversion-restored',9500:'badlength-error',9700:'badlength-restored',
            10150:'trailing-error',10350:'trailing-restored',
            10700:'bars-survives',10900:'picture-closed',11150:'both-closed',
            11600:'bars-relaunch',12000:'picture-relaunch',12900:'bars-survives-again'}
    if args.full_disk:
        commands={600:'iniz /vt1\n',720:'shell i=/vt1&\n',
            900:first_command+'\n',1500:second_command+'\n',
            2550:'s',3250:'/s0/fullfail\n',4500:' ',
            5200:'x\n',5700:'x\n',6200:'echo WBTEST-DONE >/s0/wbtest-done\n'}
        switches={1200:'Right',1950:'Left',2300:'Right'}
        shots={1150:'bars-initial',1800:'picture-initial',
            3800:'full-disk-error',4600:'full-disk-resumed'}
    factor = 2 if args.native_game else 1
    commands = {frame * factor: command for frame, command in commands.items()}
    switches = {frame * factor: direction for frame, direction in switches.items()}
    shots = {frame * factor: name for frame, name in shots.items()}
    table = lambda values: '{' + ','.join(f'[{key}]={json.dumps(value)}' for key, value in values.items()) + '}'
    cancel_event = (''.join(
        f' if frames == {frame * factor} then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:set_value(1) end\n'
        f' if frames == {(frame + 10) * factor} then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:clear_value() end\n'
        for frame in (2650, 3800)) if args.persistence else '')
    script = f'''frames = 0
local keys = manager.machine.ioport.ports[":KEY3"].fields
local commands = {table(commands)}
local switches = {table(switches)}
local shots = {table(shots)}
local held
sub = emu.add_machine_frame_notifier(function()
 frames = frames + 1
 if commands[frames] then manager.machine.natkeyboard:post(commands[frames]) end
{cancel_event} if switches[frames] then
   held = switches[frames]; keys["Alt"]:set_value(1); keys[held]:set_value(1)
 end
 if held and switches[frames-5] then
   keys[held]:clear_value(); keys["Alt"]:clear_value(); held = nil
 end
 if shots[frames] then
   manager.machine.screens[":screen"]:snapshot({json.dumps(str(out) + '/')} .. shots[frames] .. ".png")
 end
 if frames == {(14000 if args.persistence else 6500) * factor} then manager.machine:exit() end
end)
'''
    lua = out / 'drive.lua'
    lua.write_text(script)
    command = [str(mame), 'wbjr2', '-bios', 'turbo', '-rompath', str(roms.parent),
               '-hard', str(disk), '-skip_gameinfo', '-noui_mouse', '-mouseprovider', 'none', '-video', 'none', '-sound', 'none',
               '-nothrottle', '-autoboot_script', str(lua), '-seconds_to_run', str((260 if args.persistence else 120) * factor),
               '-nvram_directory', str(out / 'nvram'), '-cfg_directory', str(out / 'cfg')]
    (out / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
    with (out / 'mame.log').open('w') as log:
        subprocess.run(command, cwd=out, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    if args.full_disk:
        log_text = (out / 'mame.log').read_text(errors='replace')
        assert 'echo WBTEST-DONE >/s0/wbtest-done' in log_text, 'shell did not resume after the save failure'
        assert 'ERROR #248' in log_text, 'full disk was not preserved through the end of the run'
    else:
        assert 'WBTEST-DONE' in os9('list', f'{disk},wbtest-done').decode(), 'shell did not resume after both viewers'
    images = {name: png_rgb(out / (name + '.png')) for name in shots.values()}
    if args.full_disk:
        assert images['full-disk-error'] != images['picture-initial'], 'full-disk save error dialog missing'
        assert images['full-disk-resumed'] == images['picture-initial'], 'dismissing the full-disk error did not restore the scene'
        listing = os9('dir', f'{disk},').decode()
        assert 'fullfail' not in listing, 'failed full-disk save left a partial snapshot'
        free_output = os9('free', disk).decode()
        free_match = re.search(r'\((\d+) bytes\)', free_output)
        assert free_match and int(free_match.group(1)) < snapshot_size, f'test disk unexpectedly has room: {free_output}'
        print('PASS: actual Wild Bits full-disk save fails visibly, dismisses cleanly, preserves the scene and creates no partial file')
        print(f'Artifacts: {out}')
        return
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
        if args.persistence and name == 'picture-initial':
            expected=bytearray(expected);font=(VIEWER/'sierrafont').read_bytes()
            for column,char in enumerate(b'Value: 42'):
                for row in range(8):
                    for x in range(8):
                        color=colors[15] if font[char*8+row]&(128>>x) else colors[0]
                        for dy in range(2):
                            for dx in range(2):
                                offset=((384+row*2+dy)*width+column*16+x*2+dx)*3
                                expected[offset:offset+3]=color
        assert pixels == expected, f'{name}: real driver output differs from combined buffer'
    if args.text_modes:
        assert images['picture-graphics-mode'] == images['picture-initial'], 'graphics did not restore the game picture'
        width,height,pixels = images['picture-text-mode']
        # CoCo text.screen switches to its text plane without erasing the
        # existing graphics page. The text row is opaque; the rest of the
        # saved picture must remain visible underneath and around it.
        wanted = bytearray(images['picture-initial'][2])
        font = (VIEWER/'sierrafont').read_bytes()
        for column,char in enumerate(b'Text mode on this terminal.'):
            for row in range(8):
                for x in range(8):
                    color = colors[15] if font[char*8+row] & (128>>x) else colors[7]
                    for dy in range(2):
                        for dx in range(2):
                            offset = ((row*2+dy)*width+column*16+x*2+dx)*3
                            wanted[offset:offset+3] = color
        assert pixels == wanted, 'text mode colors/glyphs differ on the second terminal'
    if args.persistence:
        assert images['save-cancelled']==images['cancel-resumed'], 'Escape did not cancel the save-name dialog cleanly'
        assert images['cancel-resumed']==images['picture-initial'], 'canceled save altered the scene'
        assert images['restore-cancelled']==images['picture-initial'], 'Escape did not cancel the restore-name dialog cleanly'
        assert images['picture-changed']!=images['save-cancelled'], 'change controller did not change the variable'
        assert images['picture-loaded']==images['save-cancelled'], 'restore did not recover the variable and pixels'
        for name in ('invalid','wronggame','short','badcrc','badversion','badlength','trailing'):
            assert images[name+'-restored']==images['save-cancelled'], name+' failure altered the game'
            assert images[name+'-error']!=images['save-cancelled'], name+' error dialog missing'
        assert images['existing-save']==images['save-cancelled'], 'saving over an existing snapshot changed the scene or showed an error'
        assert images['existing-restored']==images['save-cancelled'], 'existing snapshot replacement did not leave the scene intact'
        try:
            os9('list', f'{disk},cancelled')
        except subprocess.CalledProcessError:
            pass
        else:
            raise AssertionError('cancelled save unexpectedly created a file')
        saved=out/'state1.bin'
        os9('copy',f'{disk},state1',saved)
        data=saved.read_bytes()
        assert data[:3]==b'WS\x01' and data[8:16]==b'WBTST'+bytes(3), 'snapshot identity/version'
        assert len(data)==18+int.from_bytes(data[4:6],'big'), 'snapshot length'
        crc=65535
        for value in data[18:]:
            crc ^= value<<8
            for bit in range(8):
                crc=((crc<<1)^0x1021 if crc&32768 else crc<<1)&65535
        assert crc==int.from_bytes(data[6:8],'big'), 'snapshot checksum'
    memory = {}
    for name in ('free-before', 'free-after'):
        memory[name] = os9('list', f'{disk},{name}')
        (out / (name + '.txt')).write_bytes(memory[name])
    assert memory['free-before'] == memory['free-after'], 'free-memory map changed after two viewer cycles'
    print('PASS: real Wild Bits drivers, every displayed pixel, two terminals, restored pictures, independent exit, relaunch, free-memory map')
    print(f'Artifacts: {out}')


if __name__ == '__main__':
    main()
