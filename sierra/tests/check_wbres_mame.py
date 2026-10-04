#!/usr/bin/env python3
"""Check native AGI resource reads against the real wbjr2 OS/RBF services."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from check_wbres import fixture

ROOT = Path(__file__).resolve().parents[1] / 'wildbits'
sys.path.insert(0, str(ROOT))
from export_picture import resource, render


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mame', required=True, type=Path)
    parser.add_argument('--disk', required=True, type=Path)
    parser.add_argument('--firmware', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--os9', default='os9')
    parser.add_argument('--game', type=Path, help='optional local game instead of generated diagnostic resource')
    parser.add_argument('--picture-number', type=int, default=1)
    parser.add_argument('--decode', action='store_true', help='test wbdecode F0-F7 combined-buffer output instead of wbres commands')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    disk = out / 'test.dsk'
    shutil.copyfile(args.disk, disk)
    roms = out / 'roms' / 'wbjr2'
    roms.mkdir(parents=True)
    for name in ('booter', 'f0.dsk'):
        shutil.copyfile(args.firmware / name, roms / name)

    def os9(*items):
        return subprocess.check_output([args.os9, *map(str, items)], stderr=subprocess.STDOUT)

    def install(name, payload, target=None, text=False):
        path = out / name
        path.write_bytes(payload)
        os9('copy', '-r', *(['-l'] if text else []), path, f'{disk},{target or name}')

    module = 'wbdecode' if args.decode else 'wbres'
    install(module, (ROOT / module).read_bytes(), 'CMDS/' + module)
    os9('attr', f'{disk},CMDS/{module}', '-e', '-pe')
    os9('makdir', f'{disk},game')
    if args.game:
        payload, volume, offset = resource(args.game, args.picture_number)
        number = args.picture_number
        files = {'picDir': (args.game / 'picDir').read_bytes(),
                 f'vol.{volume}': (args.game / f'vol.{volume}').read_bytes()}
    elif args.decode:
        from check_wbdecode import pictures
        payload = list(pictures())[2]
        number, volume, offset = 1, 1, 32
        files = {Path(name).name: data for name, data in fixture(payload).items()}
    else:
        payload = bytes(range(256)) * 31 + bytes(255) + b'\xff'
        number, volume, offset = 255, 15, 0x23456
        files = {Path(name).name: data for name, data in fixture(payload, number, volume, offset).items()}
    for name, data in files.items():
        install(name, data, 'game/' + name)
    # No keyboard wait in the probe: disk startup is deterministic for this test.
    expected = payload
    if args.decode:
        expected = render(ROOT.parent / 'kingsquest1', payload, shutil.which('lwasm.orig') or shutil.which('lwasm'), ROOT.parents[2] / 'nitros9/defs')
    script = f'load utilpak1\nload {module}\n{module} /s0/game {number} >/s0/commands.bin\necho WBRES-DONE >/s0/wbres-done\n'
    install('startup', script.encode(), text=True)
    install('feu.startup', b'bootos9 /s0/OS9Boot\n', 'FEU/startup', text=True)
    # Installations can extend a sparse image. Apply the mount-size rule last.
    with disk.open('ab') as stream:
        stream.truncate(1 << (disk.stat().st_size - 1).bit_length())
    lua = out / 'drive.lua'
    lua.write_text('''frames = 0
sub = emu.add_machine_frame_notifier(function()
 frames = frames + 1
 if frames == 1600 then manager.machine.video:snapshot(); manager.machine:exit() end
end)
''')
    command = [str(args.mame.resolve()), 'wbjr2', '-bios', 'turbo', '-rompath', str(roms.parent),
               '-hard', str(disk), '-skip_gameinfo', '-video', 'none', '-sound', 'none', '-nothrottle',
               '-autoboot_script', str(lua), '-seconds_to_run', '40', '-snapshot_directory', str(out / 'snap'),
               '-cfg_directory', str(out / 'cfg'), '-nvram_directory', str(out / 'nvram')]
    (out / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
    with (out / 'mame.log').open('w') as log:
        subprocess.run(command, cwd=out, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
    assert b'WBRES-DONE' in os9('list', f'{disk},wbres-done'), 'native probe did not return successfully to startup'
    result = out / 'commands.bin'
    os9('copy', f'{disk},commands.bin', result)
    assert result.read_bytes() == expected, 'native output differs from reference'
    print(f'PASS: {module} with real Wild Bits OS/RBF, picture {number}, vol.{volume}@{offset:#x}, {len(expected)} output bytes')
    print(f'SHA256: {hashlib.sha256(expected).hexdigest()}; artifacts: {out}')


if __name__ == '__main__':
    main()
