#!/usr/bin/env python3
"""Install a built Sierra game and its resources into a private Wild Bits disk."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


RESOURCE_NAMES = {'logDir', 'picDir', 'viewDir', 'sndDir', 'words.tok', 'object'}
MODULES = ('sierra', 'sierraui', 'sierrastate', 'sierrafont')


def run_os9(os9, *args):
    subprocess.run([os9, *map(str, args)], check=True)


def pad_sd_image(path):
    """Round a raw image up to the next SDHC-representable sector count."""
    sector_size = 512
    size = path.stat().st_size
    if size % sector_size:
        raise ValueError(f'disk image size is not sector aligned: {size} bytes')
    blocks = size // sector_size
    capacity_blocks = 1 << (blocks - 1).bit_length()
    with path.open('r+b') as image:
        image.truncate(capacity_blocks * sector_size)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--os9', default='os9')
    parser.add_argument('--base-disk', required=True, type=Path)
    parser.add_argument('--game', required=True, type=Path)
    parser.add_argument('--modules', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--psg-driver', type=Path)
    parser.add_argument('--psg-device', type=Path)
    args = parser.parse_args()

    base = args.base_disk.resolve(strict=True)
    game = args.game.resolve(strict=True)
    modules = args.modules.resolve(strict=True)
    output = args.output.resolve()
    if not game.is_dir():
        parser.error(f'game resource path is not a directory: {game}')
    if output == base:
        parser.error('output disk must not overwrite the base NitrOS-9 image')
    sources = sorted(p for p in game.iterdir() if p.is_file() and
                     (p.name.startswith('vol.') or p.name in RESOURCE_NAMES))
    if not any(p.name.startswith('vol.') for p in sources):
        parser.error(f'no AGI volume files found in {game}')
    missing = [name for name in MODULES if not (modules / name).is_file()]
    if missing:
        parser.error('missing Wild Bits build outputs: ' + ', '.join(missing))
    psg_driver = args.psg_driver or (base.parent / '.mods' / 'PSGdrv')
    psg_device = args.psg_device or (base.parent / '.mods' / 'fPSG')
    if psg_driver.is_file() != psg_device.is_file():
        parser.error('PSGdrv and fPSG must both be available; set --psg-driver '
                     'and --psg-device together or build both in recipes/wildbits/l2/.mods')
    have_psg = psg_driver.is_file() and psg_device.is_file()

    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=output.name + '.', suffix='.tmp',
                                     dir=output.parent)
    os.close(fd)
    temp_disk = Path(temp_name)
    try:
        shutil.copyfile(base, temp_disk)
        shutil.copystat(base, temp_disk)
        run_os9(args.os9, 'makdir', f'{temp_disk},game')
        for source in sources:
            run_os9(args.os9, 'copy', '-r', source,
                    f'{temp_disk},game/{source.name}')
        for name in MODULES:
            run_os9(args.os9, 'copy', '-r', modules / name,
                    f'{temp_disk},CMDS/{name}')
            run_os9(args.os9, 'attr', f'{temp_disk},CMDS/{name}', '-e', '-pe')
        if have_psg:
            for name, source in (('PSGdrv', psg_driver), ('fPSG', psg_device)):
                run_os9(args.os9, 'copy', '-r', source, f'{temp_disk},CMDS/{name}')
                run_os9(args.os9, 'attr', f'{temp_disk},CMDS/{name}', '-e', '-pe')
        pad_sd_image(temp_disk)
        temp_disk.replace(output)
    except BaseException:
        temp_disk.unlink(missing_ok=True)
        raise
    print(f'Created {output}')
    print(f'SDHC image size: {output.stat().st_size // (1024 * 1024)} MiB')
    if have_psg:
        print('For sound, load PSGdrv and fPSG at the shell before the game.')
    print('Launch from the Wild Bits shell with: sierra /s0/game 0')


if __name__ == '__main__':
    main()
