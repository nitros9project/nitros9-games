#!/usr/bin/env python3
"""Check one-Space KQ4 intro progression, Rosella movement and UI."""
import argparse
import json
import math
import os
import re
from pathlib import Path
import struct
import subprocess
import wave

from check_kq3_mame import text_rows
from check_wbpic_mame import png_rgb
from check_instances import symbols

ROOT = Path(__file__).resolve().parents[1]


def red_components(image):
    width, height, pixels = image
    pending = set()
    for y in range(120, 300):
        for x in range(width):
            r, g, b = pixels[(y * width + x) * 3:(y * width + x) * 3 + 3]
            if r > 180 and g < 100 and b < 100:
                pending.add((x, y))
    components = []
    while pending:
        stack = [pending.pop()]
        points = []
        while stack:
            x, y = stack.pop()
            points.append((x, y))
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbor in pending:
                    pending.remove(neighbor)
                    stack.append(neighbor)
        if 24 <= len(points) <= 300:
            components.append(points)
    assert components, 'Rosella red sprite pixels not found'
    sprite = max(components, key=len)
    return sum(x for x, _ in sprite) / len(sprite)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('mame', 'disk', 'firmware', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--module-file', type=Path)
    parser.add_argument('--helper-file', type=Path)
    parser.add_argument('--ui-helper-file', type=Path)
    parser.add_argument('--audio-trace', action='store_true',
                        help='require KQ4 intro sound commands to write owned PSG registers')
    parser.add_argument('--audio-wav', action='store_true',
                        help='capture MAME mixed output and require nonzero WAV samples')
    parser.add_argument('--direction-trace', action='store_true',
                        help='record Rosella object direction/loop/view while walking right')
    parser.add_argument('--psg-driver', type=Path,
                        help='PSGdrv module to install for the private MAME image')
    parser.add_argument('--psg-device', type=Path,
                        help='fPSG descriptor to install for the private MAME image')
    parser.add_argument('--persistence', action='store_true',
                         help='save KQ4, move Rosella, restore and verify the saved position')
    parser.add_argument('--help-screen', dest='help_screen', action='store_true',
                         help='open and dismiss KQ4 Sierra Help from the original game menu')
    parser.add_argument('--os9', default='os9')
    args = parser.parse_args()
    if args.persistence and args.help_screen:
        parser.error('--persistence and --help-screen cannot be combined')
    output = args.output.resolve()

    prepare = [
        os.environ.get('PYTHON', 'python3'), str(ROOT / 'tests/check_wbgame_mame.py'),
        '--prepare-play', '--mame', str(args.mame.resolve()),
        '--disk', str(args.disk.resolve()), '--firmware', str(args.firmware.resolve()),
        '--game', str(ROOT / 'kingsquest4'), '--output', str(output), '--os9', args.os9,
    ]
    for flag, path in (('--module-file', args.module_file),
                       ('--helper-file', args.helper_file),
                       ('--ui-helper-file', args.ui_helper_file)):
        if path:
            prepare += [flag, str(path.resolve())]
    psg_driver, psg_device = args.psg_driver, args.psg_device
    if psg_driver is None and psg_device is None:
        candidate_root = args.firmware.resolve().parent
        candidate_driver = candidate_root / 'l2/.mods/PSGdrv'
        candidate_device = candidate_root / 'l2/.mods/fPSG'
        if candidate_driver.is_file() and candidate_device.is_file():
            psg_driver, psg_device = candidate_driver, candidate_device
    elif psg_driver is None or psg_device is None:
        parser.error('--psg-driver and --psg-device must be supplied together')
    if psg_driver is not None:
        prepare += ['--psg-driver', str(psg_driver.resolve()),
                    '--psg-device', str(psg_device.resolve())]
    subprocess.run(prepare, cwd=ROOT, check=True)

    persistence_events = ''
    help_events = ''
    room_look_events = ''
    end_frame = 39500
    seconds_to_run = 650
    if not args.persistence and not args.help_screen:
        room_look_events = ''' if frames==38800 then post("look room\\r") end
 if frames==41700 then shot("kq4-look-room") end
 if frames==41800 then post(" ") end
 if frames==43300 then shot("kq4-look-room-restored") end
'''
        end_frame = 44500
        seconds_to_run = 755
    if args.help_screen:
        help_events = ''' if frames==39000 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:set_value(1) end
 if frames==39010 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:clear_value() end
 if frames==39100 then keys["Down"]:set_value(1) end
 if frames==39110 then keys["Down"]:clear_value() end
 if frames==39600 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:set_value(1) end
 if frames==39610 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:clear_value() end
 if frames==40500 then shot("kq4-help") end
 if frames==40600 then post(" ") end
 if frames==42100 then shot("kq4-help-restored") end
'''
        end_frame = 43000
        seconds_to_run = 740
    if args.persistence:
        persistence_events = ''' if frames==39000 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:set_value(1) end
 if frames==39010 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:clear_value() end
 if frames==39100 then keys["Right"]:set_value(1) end
 if frames==39110 then keys["Right"]:clear_value() end
 if frames==39200 then keys["Up"]:set_value(1) end
 if frames==39210 then keys["Up"]:clear_value() end
 if frames==39300 then keys["Up"]:set_value(1) end
 if frames==39310 then keys["Up"]:clear_value() end
 if frames==39400 then keys["Up"]:set_value(1) end
 if frames==39410 then keys["Up"]:clear_value() end
 if frames==39500 then keys["Up"]:set_value(1) end
 if frames==39510 then keys["Up"]:clear_value() end
 if frames==39600 then keys["Up"]:set_value(1) end
 if frames==39610 then keys["Up"]:clear_value() end
 if frames==39800 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:set_value(1) end
 if frames==39810 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:clear_value() end
 if frames==40500 then shot("kq4-save-prompt") end
 if frames==40600 then post("/s0/kq4save\\n") end
 if frames==42500 then shot("kq4-save-scene") end
 if frames==43000 then keys["Left"]:set_value(1) end
 if frames==43500 then keys["Left"]:clear_value() end
 if frames==44000 then shot("kq4-save-moved") end
 if frames==44500 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:set_value(1) end
 if frames==44510 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:clear_value() end
 if frames==44600 then keys["Right"]:set_value(1) end
 if frames==44610 then keys["Right"]:clear_value() end
 if frames==44700 then keys["Up"]:set_value(1) end
 if frames==44710 then keys["Up"]:clear_value() end
 if frames==44800 then keys["Up"]:set_value(1) end
 if frames==44810 then keys["Up"]:clear_value() end
 if frames==44900 then keys["Up"]:set_value(1) end
 if frames==44910 then keys["Up"]:clear_value() end
 if frames==45000 then keys["Up"]:set_value(1) end
 if frames==45010 then keys["Up"]:clear_value() end
 if frames==45200 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:set_value(1) end
 if frames==45210 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:clear_value() end
 if frames==46000 then shot("kq4-restore-prompt") end
 if frames==46100 then post("/s0/kq4save\\n") end
 if frames==48000 then shot("kq4-restore-scene") end
 if frames==48100 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:set_value(1) end
 if frames==48110 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:clear_value() end
 if frames==48200 then keys["Right"]:set_value(1) end
 if frames==48210 then keys["Right"]:clear_value() end
 if frames==48300 then keys["Up"]:set_value(1) end
 if frames==48310 then keys["Up"]:clear_value() end
 if frames==48400 then keys["Up"]:set_value(1) end
 if frames==48410 then keys["Up"]:clear_value() end
 if frames==48500 then keys["Up"]:set_value(1) end
 if frames==48510 then keys["Up"]:clear_value() end
 if frames==48600 then keys["Up"]:set_value(1) end
 if frames==48610 then keys["Up"]:clear_value() end
 if frames==48700 then keys["Up"]:set_value(1) end
 if frames==48710 then keys["Up"]:clear_value() end
 if frames==48900 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:set_value(1) end
 if frames==48910 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:clear_value() end
 if frames==49600 then shot("kq4-postrestore-save-prompt") end
 if frames==49700 then post("/s0/kq4after\\n") end
 if frames==51500 then shot("kq4-postrestore-save") end
 if frames==51600 then post("look\\r") end
 if frames==54500 then shot("kq4-restore-response") end
 if frames==54550 then post(" ") end
 if frames==56000 then shot("kq4-restore-final") end
'''
        end_frame = 57000
        seconds_to_run = 970

    lua = output / 'drive.lua'
    lua.write_text(f'''local frames=0
local keys=manager.machine.ioport.ports[":KEY3"].fields
local function post(s) manager.machine.natkeyboard:post(s) end
local function shot(name)
 manager.machine.screens[":screen"]:snapshot({json.dumps(str(output) + "/")}..name..".png")
end
sub=emu.add_machine_frame_notifier(function()
 frames=frames+1
 if frames==1000 then post("wbgame /s0/game 0\\n") end
 if frames==1800 then post("\\n") end
'''+''.join(f' if frames=={frame} then post(" ") end\n'
             for frame in (2200,))+f''' if frames==16900 then shot("kq4-after-one-space") end\n if frames==17000 then post("\\r") end
 if frames==22000 then shot("kq4-after-one-return") end
 if frames==26000 then shot("kq4-gameplay-start") end
 if frames==27500 then post("\\r") end
 if frames==29000 then shot("kq4-before-walk") end
 if frames==29500 then keys["Right"]:set_value(1) end
 if frames==30000 then keys["Right"]:clear_value() end
 if frames==30500 then shot("kq4-after-walk") end
 -- Movement toggles off when the same direction is pressed again. Stop
 -- Rosella here so later dialog, menu and Inventory checks stay in one room.
 if frames==30600 then keys["Right"]:set_value(1) end
 if frames==30610 then keys["Right"]:clear_value() end
 if frames==30700 then shot("kq4-after-stop") end
 if frames==31000 then post("look\\r") end
 if frames==34000 then shot("kq4-look") end
 if frames==34500 then post(" ") end
 if frames==36000 then shot("kq4-look-restored") end
 if frames==36200 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:set_value(1) end
 if frames==36210 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:clear_value() end
 if frames==36700 then shot("kq4-menu") end
'''+''.join(f' if frames=={frame} then keys["Right"]:set_value(1) end\n'
             f' if frames=={frame+30} then keys["Right"]:clear_value() end\n'
             for frame in range(36800, 36901, 100))+''' if frames==37300 then shot("kq4-inventory-selected") end
 if frames==37400 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:set_value(1) end
 if frames==37410 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:clear_value() end
 if frames==38000 then shot("kq4-inventory") end
 if frames==38100 then post(" ") end
 if frames==38700 then shot("kq4-inventory-restored") end
'''+help_events+persistence_events+room_look_events+f''' if frames=={end_frame} then manager.machine:exit() end
end)
''')

    apply_fields = (11, 62, 63, 133)
    if args.persistence:
        module = (args.module_file or (ROOT / 'objs/wbgame')).resolve()
        module_code = module.read_bytes()
        module_syms = symbols(module.with_suffix('.map'))
        module_base = (8 - (len(module_code) + 8191) // 8192) * 8192
        apply_guard = (f'w@{module_base:x} == 87cd && '
                       f'w@{module_base+2:x} == {len(module_code):x}')
        apply_values = ','.join(
            f'b@(u+{module_syms["vmvariables"]+index:x})'
            for index in apply_fields)
        apply_action = (
            f'printf "KQ4 STATE SUCCESS OP=%d VARS=%d,%d,%d,%d",'
            f'b@{module_syms["vmopcode"]:x},{apply_values}; g')
        apply_event = (
            ' if frames==950 then\n'
            f'  cpu.debug:bpset({module_base+module_syms["GameStateSuccess"]+2},'
            f'{json.dumps(apply_guard)},{json.dumps(apply_action)})\n'
            ' end')
        source = lua.read_text().replace(
            ' frames=frames+1', ' frames=frames+1\n' + apply_event, 1)
        source = ('local cpu=manager.machine.devices[":maincpu"]\n'
                  'manager.machine.debugger.execution_state="run"\n'
                  'kq4_persistence_stop=emu.add_machine_stop_notifier(function() '
                  'local log=manager.machine.debugger.consolelog;'
                  'for index=1,#log do if log[index] then print(log[index]) end end end)\n'
                  + source)
        lua.write_text(source)

    if args.audio_trace:
        module = (args.module_file or (ROOT / 'objs/wbgame')).resolve()
        module_map = module.with_suffix('.map')
        code = module.read_bytes()
        syms = symbols(module_map)
        base = (8 - (len(code) + 8191) // 8192) * 8192
        condition = f'w@{base:x} == 87cd && w@{base+2:x} == {len(code):x}'
        action = (f'printf "AUDIO COMMAND %d %d %d",b@{syms["vmopcode"]:x},'
                  f'b@(u+{syms["vmarguments"]:x}),'
                  f'b@(u+{syms["vmarguments"]+1:x}); g')
        events = [
            ' if frames==950 then',
            f'  audio_bp=cpu.debug:bpset({base+syms["GameSoundCommand"]},{json.dumps(condition)},'
            f'{json.dumps(action)})',
            '  audio_wp=cpu.debug:wpset(cpu.spaces["program"],"w",0x4200,1,'
            '"b@1a != 0 && ((b@pc == f7 && w@(pc+1) == 4200) || (b@(pc-3) == f7 && w@(pc-2) == 4200))",'
            '\'printf "AUDIO PSG %02X OWNER %02X",wpdata,b@1a; g\')',
            ' end',
            # Bound this assertion to the original logo/credits intro. The
            # frame is the same checkpoint that captures the one-Space result.
            ' if frames==16900 then cpu.debug:bpclear(audio_bp); cpu.debug:wpclear(audio_wp) end',
        ]
        trace = lua.read_text().replace(' frames=frames+1',
                                        ' frames=frames+1\n'+'\n'.join(events), 1)
        if not args.persistence:
            trace = ('local cpu=manager.machine.devices[":maincpu"]\n'
                     'manager.machine.debugger.execution_state="run"\n'
                     'audio_stop=emu.add_machine_stop_notifier(function() '
                     'local log=manager.machine.debugger.consolelog;'
                     'for index=1,#log do if log[index] then print(log[index]) end end end)\n'
                     + trace)
        lua.write_text(trace)

    if args.direction_trace:
        module = (args.module_file or (ROOT / 'objs/wbgame')).resolve()
        code = module.read_bytes()
        syms = symbols(module.with_suffix('.map'))
        base = (8 - (len(code) + 8191) // 8192) * 8192
        condition = (f'w@{base:x} == 87cd && '
                     f'w@{base+2:x} == {len(code):x} && b@(u+2) == 0')
        flags=symbols(module.with_suffix('.map'))
        action = (f'printf "KQ4 SPRITE DIR=%d LOOP=%d LOOPS=%d VIEW=%d X=%d Y=%d CEL=%d FLAG20=%d",'
                  'b@(u+0x21),b@(u+0x0a),b@(u+0x0b),b@(u+0x05),'
                  'b@(u+0x03),b@(u+0x04),b@(u+0x0e),'
                  f'b@(u-0x{flags["vmobjects"]:x}+0x{flags["vmflags"]+20:x}); g')
        events = [
            ' if frames==29500 then',
            f'  cpu.debug:bpset({base+syms["SpriteRenderObject"]},'
            f'{json.dumps(condition)},{json.dumps(action)})',
            ' end',
            ' if frames==30000 then cpu.debug:bpclear() end',
        ]
        trace = lua.read_text().replace(' frames=frames+1',
                                        ' frames=frames+1\n'+'\n'.join(events), 1)
        trace = ('local cpu=manager.machine.devices[":maincpu"]\n'
                 'manager.machine.debugger.execution_state="run"\n'
                 'direction_stop=emu.add_machine_stop_notifier(function() '
                 'local log=manager.machine.debugger.consolelog;'
                 'for index=1,#log do if log[index] then print(log[index]) end end end)\n'
                 + trace)
        lua.write_text(trace)

    command = [
        str(args.mame.resolve()), 'wbjr2', '-bios', 'turbo', '-rompath', str(output / 'roms'),
        '-hard', str(output / 'test.dsk'), '-skip_gameinfo', '-noui_mouse',
        '-mouseprovider', 'none', '-keyboardprovider', 'none', '-video', 'none',
        # Keep normal regression runs silent, but enable MAME's audio mixer
        # when explicitly capturing a WAV. Otherwise -wavwrite records silence
        # even though the driver trace proves that the game writes PSG data.
        '-sound', 'auto' if args.audio_wav else 'none', '-nothrottle',
        '-autoboot_script', str(lua), '-seconds_to_run', str(seconds_to_run),
        '-nvram_directory', str(output / 'nvram'), '-cfg_directory', str(output / 'cfg'),
    ]
    wav_path = output / 'audio.wav'
    if args.audio_wav:
        command += ['-wavwrite', str(wav_path)]
    if args.audio_trace or args.persistence or args.direction_trace:
        command += ['-debug', '-debugger', 'none']
    (output / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
    env = os.environ.copy()
    env.setdefault('SDL_VIDEODRIVER', 'dummy')
    with (output / 'mame.log').open('w') as log:
        subprocess.run(command, cwd=output, env=env, stdout=log,
                       stderr=subprocess.STDOUT, check=True, timeout=180)

    if args.direction_trace:
        log_text=(output/'mame.log').read_text(errors='replace')
        rows=[tuple(map(int,row)) for row in re.findall(
            r'KQ4 SPRITE DIR=(\d+) LOOP=(\d+) LOOPS=(\d+) VIEW=(\d+) '
            r'X=(\d+) Y=(\d+) CEL=(\d+) FLAG20=(\d+)',
            log_text)]
        right=[row for row in rows if row[0]==3 and row[3]==0]
        assert right,('no rightward Rosella sprite-state samples',log_text[-4000:])
        assert all(row[1]==0 and row[2]==5 and row[7]==1 for row in right),(
            'rightward five-loop animation did not select loop 0 under flag 20',
            sorted(set((row[1],row[2],row[7]) for row in right)))
        assert max(row[4] for row in right)>min(row[4] for row in right),(
            'Rosella direction trace did not advance X',right)
        errors=re.findall(r'wbgame error, opcode: ([0-9A-F]{2})',log_text)
        assert not errors,('Wild Bits game reported an error during movement',errors)
        (output/'direction-trace.json').write_text(json.dumps([
            dict(zip(('direction','loop','loop_count','view','x','y','cel','flag20'),row))
            for row in rows
        ],indent=2)+'\n')
        print('PASS: original KQ4 rightward movement advances Rosella with direction 3, '
              'view 0 loop 0 of 5 while AGI flag 20 is set')
        return

    restore_apply_snapshots = None
    if args.persistence:
        log_text = (output / 'mame.log').read_text(errors='replace')
        matches = re.findall(
            r'KQ4 STATE SUCCESS OP=(\d+) VARS=(\d+),(\d+),(\d+),(\d+)',
            log_text)
        restore_apply_snapshots = [
            dict(zip(apply_fields, map(int, match[1:])))
            for match in matches if int(match[0]) == 126
        ]
        assert restore_apply_snapshots, (
            'KQ4 restore-apply variable checkpoint', matches, log_text[-4000:])

    if args.audio_trace:
        log_text = (output / 'mame.log').read_text(errors='replace')
        writes = [(int(value, 16), int(owner, 16))
                  for value, owner in re.findall(
                      r'AUDIO PSG ([0-9A-F]{2}) OWNER ([0-9A-F]{2})', log_text)]
        commands = [tuple(map(int, match)) for match in re.findall(
            r'AUDIO COMMAND (\d+) (\d+) (\d+)', log_text)]
        assert commands == [(99,2,220),(99,100,154),(99,101,154),(99,102,154)], \
            ('KQ4 intro sound-command sequence changed', commands)
        assert writes and all(owner for value, owner in writes), \
            ('KQ4 intro produced no process-owned PSG writes', commands, writes)
        assert any(value & 0x90 == 0x90 and value & 15 != 15
                   for value, owner in writes), ('only PSG mute writes observed', writes)
        (output / 'audio-writes.json').write_text(json.dumps({
            'sound_commands': [
                {'opcode':opcode,'sound_resource':sound_id,'completion_flag':flag}
                for opcode,sound_id,flag in commands],
            'owned_psg_writes': writes,
        }, indent=2) + '\n')

    if args.audio_wav:
        with wave.open(str(wav_path), 'rb') as audio_file:
            params = audio_file.getparams()
            assert params.sampwidth == 2, ('unexpected MAME WAV sample width', params)
            sample_count = 0
            sample_sum = 0
            square_sum = 0
            low = 32767
            high = -32768
            intro_start = 30
            intro_end = min(16900 / 60, params.nframes / params.framerate)
            assert intro_end > intro_start, ('WAV ends before KQ4 intro audio window', params)
            audio_file.setpos(intro_start * params.framerate)
            remaining = int((intro_end - intro_start) * params.framerate)
            while remaining:
                frame_count = min(32768, remaining)
                chunk = audio_file.readframes(frame_count)
                if not chunk:
                    break
                remaining -= len(chunk) // (params.nchannels * 2)
                samples = struct.unpack('<' + 'h' * (len(chunk) // 2), chunk)
                sample_count += len(samples)
                sample_sum += sum(samples)
                square_sum += sum(value * value for value in samples)
                low = min(low, min(samples))
                high = max(high, max(samples))
        mean = sample_sum / sample_count if sample_count else 0.0
        ac_rms = math.sqrt(max(0.0, square_sum / sample_count - mean * mean)) \
            if sample_count else 0.0
        peak_to_peak = high - low if sample_count else 0
        assert sample_count and ac_rms > 5 and peak_to_peak > 32, (
            'MAME intro WAV has no varying audio signal', params,
            sample_count, ac_rms, peak_to_peak)
        (output / 'audio-summary.json').write_text(json.dumps({
            'channels': params.nchannels,
            'sample_rate': params.framerate,
            'sample_width_bytes': params.sampwidth,
            'frames': params.nframes,
            'intro_window_seconds': [intro_start, intro_end],
            'intro_sample_count': sample_count,
            'intro_ac_rms': ac_rms,
            'intro_peak_to_peak': peak_to_peak,
        }, indent=2) + '\n')

    one_space = png_rgb(output / 'kq4-after-one-space.png')
    after_one_return = png_rgb(output / 'kq4-after-one-return.png')
    start = png_rgb(output / 'kq4-gameplay-start.png')
    before = png_rgb(output / 'kq4-before-walk.png')
    after = png_rgb(output / 'kq4-after-walk.png')
    stopped = png_rgb(output / 'kq4-after-stop.png')
    look = png_rgb(output / 'kq4-look.png')
    restored = png_rgb(output / 'kq4-look-restored.png')
    menu = png_rgb(output / 'kq4-menu.png')
    inventory_selected = png_rgb(output / 'kq4-inventory-selected.png')
    inventory = png_rgb(output / 'kq4-inventory.png')
    inventory_restored = png_rgb(output / 'kq4-inventory-restored.png')
    assert all((image[0], image[1]) == (640, 480)
               for image in (one_space, after_one_return, start, before, after, stopped, look, restored, menu,
                             inventory_selected, inventory, inventory_restored))
    opening = text_rows(output / 'kq4-after-one-space.png', (ROOT / 'objs/sierrafont').read_bytes())
    # This automated key sequence leaves the game at the original opening
    # fruit narration. The Genesta line belongs to a later intro phase and is
    # not a reliable oracle for a single-space capture.
    opening_text = re.sub(r'\?', '', '\n'.join(opening))
    assert 'this is no ordinary fruit;' in opening_text, opening
    # The opening line is printed over the title artwork. A full-page text
    # transition here would hide the logo even though OCR still finds the text.
    opening_pixels = one_space[2]
    opening_logo_colors = set(
        opening_pixels[(y * one_space[0] + x) * 3:(y * one_space[0] + x) * 3 + 3]
        for y in range(32, 232) for x in range(180, 460))
    assert len(opening_logo_colors) >= 8, \
        ('KQ4 opening dialogue hid the title artwork', len(opening_logo_colors))
    assert 450 <= red_components(after_one_return) <= 520, \
        'one Space followed by one Return did not reach gameplay before further keys'
    before_x, after_x = red_components(before), red_components(after)
    stopped_x = red_components(stopped)
    assert 450 <= before_x <= 520, ('Rosella not at the expected beach position', before_x)
    # The room camera scrolls as Rosella travels right from the beach into the
    # woodland. Screen X therefore is not her world X and can move left while
    # the scenery scrolls in the opposite direction.
    assert abs(after_x-before_x) >= 80, \
        ('Right-arrow movement did not scroll Rosella into the next scene',
         before_x,after_x)
    font = (ROOT / 'objs/sierrafont').read_bytes()
    dialogue = text_rows(output / 'kq4-look.png', font)
    for phrase in ('A cold shallow', 'river carves its',
                   'lush flowery', 'meadow.'):
        assert any(phrase in row for row in dialogue), (phrase, dialogue)
    # Modal print text uses a full-width, 15-row white panel. The frame is
    # black, text remains inside it, and scene pixels remain visible above
    # and below the window.
    _, _, look_pixels = look
    def region_stats(x0, y0, x1, y1, image=look):
        image_width, _, image_pixels = image
        colors = set()
        light = total = 0
        for y in range(y0, y1):
            for x in range(x0, x1):
                i = (y * image_width + x) * 3
                color = tuple(image_pixels[i:i + 3])
                colors.add(color)
                light += min(color) > 220
                total += 1
        return len(colors), light / total
    panel_x0, panel_y0, panel_x1, panel_y1 = 16, 80, 624, 320
    popup_colors, popup_light = region_stats(
        panel_x0, panel_y0, panel_x1, panel_y1)
    top_colors, _ = region_stats(16, 16, 624, panel_y0)
    bottom_colors, _ = region_stats(16, panel_y1, 624, 384)
    assert popup_colors == 2 and 0.70 < popup_light < 0.90, \
        ('KQ4 look text did not use a white, black-text panel',
         popup_colors, popup_light)
    assert all(look_pixels[(y * 640 + x) * 3:(y * 640 + x) * 3 + 3] ==
               b'\x00\x00\x00'
               for x, y in ((320, 80), (320, 319), (16, 180), (623, 180))), \
        'KQ4 look panel is missing a black tile border'
    assert top_colors >= 5 and bottom_colors >= 8, \
        ('KQ4 look panel hid the scene outside its bounds',
         top_colors, bottom_colors)
    room_look_result = None
    if room_look_events:
        room_look = png_rgb(output / 'kq4-look-room.png')
        room_look_restored = png_rgb(output / 'kq4-look-room-restored.png')
        assert (room_look[0], room_look[1]) == (640, 480)
        room_popup_colors, room_popup_light = region_stats(
            panel_x0, panel_y0, panel_x1, panel_y1, room_look)
        room_top_colors, _ = region_stats(16, 16, 624, panel_y0, room_look)
        room_bottom_colors, _ = region_stats(16, panel_y1, 624, 384, room_look)
        assert room_popup_colors == 2 and 0.70 < room_popup_light < 0.90, \
            ('KQ4 look room did not use the white text panel',
             room_popup_colors, room_popup_light)
        assert room_top_colors >= 4 and room_bottom_colors >= 6, \
            ('KQ4 look room obscured the scene outside the panel',
             room_top_colors, room_bottom_colors)
        assert len(set(room_look_restored[2][i:i + 3]
                       for i in range(0, len(room_look_restored[2]), 3))) >= 8, \
            'Space did not restore the scene after look room'
        room_look_result = {
            'popup_colors': room_popup_colors,
            'popup_light_fraction': room_popup_light,
            'scene_colors_above': room_top_colors,
            'scene_colors_below': room_bottom_colors,
            'scene_restored': True,
        }
    look_restored_x=red_components(restored)
    assert abs(look_restored_x-stopped_x) <= 2, \
        ('Rosella moved after the second Right press while dismissing look',
         stopped_x, look_restored_x)
    assert len(set(restored[2][i:i + 3] for i in range(0, len(restored[2]), 3))) >= 8, \
        'fresh Space did not restore the KQ4 gameplay scene after look'
    menu_colors = set(menu[2][i:i + 3] for i in range(0, len(menu[2]), 3))
    assert bytes(3) in menu_colors and bytes([255]) * 3 in menu_colors, \
        'Escape did not open the KQ4 game menu'
    menu_text = text_rows(output / 'kq4-menu.png', font)
    assert menu_text[1].strip() == 'Game menu', menu_text
    assert menu_text[5].strip() == 'File: Save     (5)', menu_text
    assert menu_text[6].strip() == 'File: Restore  (7)', menu_text
    # Transparent scene pixels outside the menu bounds can be decoded as an
    # unknown glyph at the far edge of this row; require the complete menu
    # item at its left edge without treating that artwork as text.
    assert menu_text[12].strip().startswith('Action: Inventory  (->)'), menu_text
    assert re.fullmatch(r'Arrows select; E.TER opens; ESC cancel',
                        menu_text[24].strip()), menu_text
    assert menu != restored, 'KQ4 menu did not change the displayed scene'
    selected_text = text_rows(output / 'kq4-inventory-selected.png', font)
    assert selected_text[12].strip().startswith('Action: Inventory  (->)'), selected_text
    inventory_text = text_rows(output / 'kq4-inventory.png', font)
    assert inventory_text[1].strip() == 'You are carrying:', inventory_text
    assert inventory_text[3].strip() == 'nothing', inventory_text
    assert inventory_text[24].strip() == 'Press a key to return to the game', inventory_text
    assert inventory != inventory_selected, 'Return did not open the selected Inventory action'
    # KQ4 Inventory uses status -> text.screen, which is intentionally a
    # full-screen white text page on both owners. Keep it distinct from the
    # centered print popup asserted above; a picture-colored pixel here means
    # graphics leaked through the opaque text-screen transition.
    inventory_colors = set(inventory[2][i:i + 3]
                           for i in range(0, len(inventory[2]), 3))
    assert inventory_colors == {bytes(3), bytes([255]) * 3}, \
        ('KQ4 Inventory text.screen must replace the picture with black/white text pixels',
         inventory_colors)
    inventory_restored_x = red_components(inventory_restored)
    assert abs(inventory_restored_x-stopped_x) <= 2, \
        ('Rosella moved after the second Right press while dismissing Inventory',
         stopped_x, inventory_restored_x)
    assert len(set(inventory_restored[2][i:i + 3]
                   for i in range(0, len(inventory_restored[2]), 3))) >= 8, \
        'fresh key did not dismiss KQ4 inventory and restore the gameplay scene'
    assert inventory_restored != inventory, 'KQ4 inventory dismissal did not change the display'
    persistence_result = None
    if args.persistence:
        names = ('kq4-save-prompt', 'kq4-save-scene', 'kq4-save-moved',
                 'kq4-restore-prompt', 'kq4-restore-scene',
                 'kq4-postrestore-save-prompt', 'kq4-postrestore-save',
                 'kq4-restore-response', 'kq4-restore-final')
        persistence_images = {name: png_rgb(output / (name + '.png')) for name in names}
        assert all((image[0], image[1]) == (640, 480)
                   for image in persistence_images.values())
        for name in ('kq4-save-prompt', 'kq4-restore-prompt',
                     'kq4-postrestore-save-prompt'):
            rows = text_rows(output / (name + '.png'), font)
            assert any('File:' in row for row in rows) and \
                   not any('Game menu' in row for row in rows), (name, rows)
        saved_pixels = persistence_images['kq4-save-scene'][2]
        moved_pixels = persistence_images['kq4-save-moved'][2]
        changed_pixels = sum(saved_pixels[i:i + 3] != moved_pixels[i:i + 3]
                             for i in range(0, len(saved_pixels), 3))
        assert changed_pixels > 1000, 'KQ4 changed scene was not visible after save'
        restore_image = persistence_images['kq4-restore-response']
        restore_rows = text_rows(output / 'kq4-restore-response.png', font)
        restore_text = re.sub(r'\s+', ' ',
                              re.sub(r'\?', '', '\n'.join(restore_rows)))
        assert 'A cold shallow' in restore_text and \
               'river carves its way through this lush flowery meadow.' in restore_text, \
            restore_rows
        restore_pixels = restore_image[2]
        restore_left = set(restore_pixels[(y * 640 + x) * 3:(y * 640 + x) * 3 + 3]
                           for y in range(80, 360) for x in range(160))
        restore_right = set(restore_pixels[(y * 640 + x) * 3:(y * 640 + x) * 3 + 3]
                            for y in range(80, 360) for x in range(480, 640))
        assert len(restore_left) >= 8 and len(restore_right) >= 8, \
            ('KQ4 restored look popup obscured the scene',
             len(restore_left), len(restore_right))
        save_file = output / 'kq4save.bin'
        subprocess.run([args.os9, 'copy', f'{output / "test.dsk"},kq4save',
                        str(save_file)], check=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
        save_data = save_file.read_bytes()
        assert save_data[:3] == b'WS\x01' and save_data[8:11] == b'KQ4', save_data[:18]
        assert len(save_data) == 18 + int.from_bytes(save_data[4:6], 'big')
        restore_apply_saved_values = {
            index: save_data[18 + index] for index in apply_fields
        }
        matching_apply_snapshots = [
            snapshot for snapshot in restore_apply_snapshots
            if snapshot == restore_apply_saved_values
        ]
        assert len(matching_apply_snapshots) == 1, (
            'KQ4 restore did not reproduce saved variables at the apply return',
            restore_apply_snapshots, restore_apply_saved_values)
        restore_apply_vars = matching_apply_snapshots[0]
        restored_file = output / 'kq4after.bin'
        subprocess.run([args.os9, 'copy', f'{output / "test.dsk"},kq4after',
                        str(restored_file)], check=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
        restored_data = restored_file.read_bytes()
        assert restored_data[:3] == b'WS\x01' and restored_data[8:11] == b'KQ4', restored_data[:18]
        assert len(restored_data) == 18 + int.from_bytes(restored_data[4:6], 'big')
        assert save_data[:6] + save_data[8:18] == \
               restored_data[:6] + restored_data[8:18], \
            ('KQ4 restore changed invariant save-header fields', save_data[:18],
             restored_data[:18])
        variable_differences = [
            {'index': index, 'saved': save_data[18 + index],
             'resaved': restored_data[18 + index]}
            for index in range(256)
            if save_data[18 + index] != restored_data[18 + index]
        ]
        flag_differences = [
            {'index': index, 'saved': save_data[18 + 256 + index],
             'resaved': restored_data[18 + 256 + index]}
            for index in range(256)
            if save_data[18 + 256 + index] != restored_data[18 + 256 + index]
        ]
        object_start = 18 + 512 + 480
        non_variable_differences = []
        animation_differences = []
        for offset in range(18 + 512, len(save_data)):
            if save_data[offset] == restored_data[offset]:
                continue
            relative = offset - object_start
            if 0 <= relative < 64 * 43:
                object_number, field = divmod(relative, 43)
                flags_offset = object_start + object_number * 43 + 38
                animated_before = bool(save_data[flags_offset] & 0x20)
                animated_after = bool(restored_data[flags_offset] & 0x20)
                if object_number and animated_before and animated_after and \
                   field in (14, 16, 17, 32):
                    # cel index, current cel offset, and cycle countdown can
                    # advance while the restored original logic is running.
                    animation_differences.append({
                        'object': object_number, 'field': field,
                        'saved': save_data[offset], 'resaved': restored_data[offset],
                    })
                    continue
            non_variable_differences.append(offset)
        assert not flag_differences, ('KQ4 restore/resave changed saved flags',
                                      flag_differences)
        assert not non_variable_differences, \
            ('KQ4 restore/resave changed non-variable persisted data',
             non_variable_differences[:32], len(non_variable_differences))
        # WS v1 stream: 18-byte header, 512 variable bytes, 480 string bytes,
        # then 43-byte AGI object records; object 0 is the ego.
        original_position = (save_data[18], save_data[object_start + 3], save_data[object_start + 4])
        restored_position = (restored_data[18], restored_data[object_start + 3], restored_data[object_start + 4])
        assert restored_position == original_position, (original_position, restored_position)
        persistence_result = {
            'save_header': save_data[:18].hex(),
            'saved_game_id': save_data[8:11].decode('ascii'),
            'file_bytes': len(save_data),
            'changed_pixels_after_save': changed_pixels,
            'all_saved_flags_unchanged': True,
            'non_animation_payload_bytes_unchanged': True,
            'live_animation_fields_advanced_after_restore': animation_differences,
            'changed_variable_values': variable_differences,
            'variables_at_restore_apply': restore_apply_vars,
            'restore_apply_variables_match_save': True,
            'room_x_y_before_restore': original_position,
            'room_x_y_after_restore': restored_position,
            'restore_followed_by_original_look': True,
            'restore_popup_scene_colors_left_right': [len(restore_left), len(restore_right)],
            'exact_resumed_position_compared': True,
        }
        (output / 'persistence.json').write_text(json.dumps(persistence_result, indent=2) + '\n')
    help_result = None
    if args.help_screen:
        help_image = png_rgb(output / 'kq4-help.png')
        help_restored = png_rgb(output / 'kq4-help-restored.png')
        assert (help_image[0], help_image[1]) == (640, 480)
        assert (help_restored[0], help_restored[1]) == (640, 480)
        help_rows = text_rows(output / 'kq4-help.png', font)
        # The original help panel overlays scene artwork, so graphics can
        # produce undecodable cells. Require complete, distinctive text from
        # separate rows after discarding only those ambiguous cells.
        help_text = re.sub(r'\?', '', '\n'.join(help_rows))
        for phrase in ('(1) displays this message.',
                       '(5) saves your current game.',
                       'CTRL-BREAK activates menus.'):
            assert phrase in help_text, (phrase, help_rows)
        assert help_image != help_restored, 'Space did not dismiss KQ4 Help'
        help_restored_x = red_components(help_restored)
        assert abs(help_restored_x - inventory_restored_x) <= 2, \
            ('KQ4 Help dismissal did not restore Rosella to the gameplay scene',
             help_restored_x, inventory_restored_x)
        assert len(set(help_restored[2][i:i + 3]
                       for i in range(0, len(help_restored[2]), 3))) >= 8, \
            'KQ4 Help dismissal did not restore scene graphics'
        help_result = {
            'recognized_lines': ['(1) displays this message.',
                                 '(5) saves your current game.',
                                 'CTRL-BREAK activates menus.'],
            'dismissed_by': 'Space',
            'restored_rosella_x_pixels': help_restored_x,
        }
        (output / 'help.json').write_text(json.dumps(help_result, indent=2) + '\n')
    (output / 'movement.json').write_text(json.dumps({
        'original_title': 'King\'s Quest IV', 'intro_space_presses': 1, 'key': 'Right',
        'before_x_pixels': before_x, 'after_x_pixels': after_x,
        'screen_shift_pixels': after_x - before_x,
        'emulated_hold_frames': 500, 'second_right_stops_motion': True,
        'stopped_x_pixels': stopped_x,
        'look_restored_x_pixels': look_restored_x,
        'menu_opened': menu != restored,
        'inventory_opened': inventory != inventory_selected,
        'inventory_dismissed': inventory_restored != inventory,
        'inventory_restored_rosella_x_pixels': inventory_restored_x,
        'persistence_probe': persistence_result,
        'help_probe': help_result,
    }, indent=2) + '\n')
    print('PASS: KQ4 single-Space intro advance, gameplay, movement, look popup, menu/Inventory and scene restoration',
          {'before_x': round(before_x, 1), 'after_x': round(after_x, 1),
           'look_restored_x': round(look_restored_x, 1),
           'inventory_restored_x': round(inventory_restored_x, 1),
           'look_room': room_look_result})
    if args.audio_trace:
        print('PASS: KQ4 intro sound command reaches owned Wild Bits PSG registers',
              len(writes))
    if persistence_result:
        print('PASS: KQ4 save file has a valid KQ4 header, movement changes the scene, and restore continues into original logic',
              persistence_result)
    if help_result:
        print('PASS: KQ4 Help renders original instructions and Space restores the gameplay scene',
              help_result)


if __name__ == '__main__':
    main()
