#!/usr/bin/env python3
"""Launch Donald Duck's Playground in an interactive Wildbits Jr2 terminal."""
import argparse
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mame', required=True, type=Path)
    parser.add_argument('--disk', required=True, type=Path)
    parser.add_argument('--firmware', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path,
                        help='new working directory for a private disk copy')
    parser.add_argument('--speed', type=float, default=2,
                        help='emulation speed multiplier (default: 2)')
    args = parser.parse_args()
    if args.speed <= 0:
        parser.error('--speed must be positive')
    for path in (args.mame, args.disk, args.firmware / 'booter',
                 args.firmware / 'f0.dsk'):
        if not path.is_file():
            parser.error(f'missing file: {path}')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    roms = output / 'roms' / 'wbjr2'
    roms.mkdir(parents=True)
    for name in ('booter', 'f0.dsk'):
        shutil.copyfile(args.firmware / name, roms / name)
    disk = output / 'DDP-Wildbits-Jr2.dsk'
    shutil.copyfile(args.disk, disk)
    script = output / 'launch.lua'
    script.write_text('''local frames=0
local commands={[900]='iniz /vt1\\n',[1150]='shell i=/vt1&\\n',
                [1500]='chd /s0/ddp\\n',[2200]='donald\\n'}
ddp_launch_subscription=emu.add_machine_frame_notifier(function()
    frames=frames+1
    if commands[frames] then
        manager.machine.natkeyboard:post(commands[frames])
    end
end)
''')
    return subprocess.run([
        str(args.mame.resolve()), 'wbjr2', '-bios', 'turbo',
        '-rompath', str(roms.parent), '-hard', str(disk),
        '-skip_gameinfo', '-window', '-speed', str(args.speed),
        '-noui_active', '-nonatural', '-autoboot_script', str(script),
        '-nvram_directory', str(output / 'nvram'),
        '-cfg_directory', str(output / 'cfg'),
    ], cwd=output).returncode


if __name__ == '__main__':
    raise SystemExit(main())
