#!/usr/bin/env python3
"""Run the deterministic startup/exit checkpoint for every bundled game."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TITLES = (
    'blackcauldron', 'christmas86', 'goldrush', 'kingsquest1', 'kingsquest2',
    'kingsquest3', 'kingsquest4', 'leisuresuitlarry', 'manhunter1',
    'manhunter2', 'policequest1', 'spacequest0', 'spacequest1', 'spacequest2',
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mame', type=Path, required=True)
    parser.add_argument('--disk', type=Path, required=True)
    parser.add_argument('--firmware', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    parser.add_argument('--module-file', type=Path, required=True)
    parser.add_argument('--helper-file', type=Path, required=True)
    parser.add_argument('--ui-helper-file', type=Path, required=True)
    parser.add_argument('--os9', default='os9')
    parser.add_argument('--games-root', type=Path, default=ROOT)
    parser.add_argument('--title', choices=TITLES, action='append',
                        help='Run selected title(s); default runs all fourteen')
    args = parser.parse_args()
    titles = args.title or list(TITLES)
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env.setdefault('SDL_VIDEODRIVER', 'dummy')
    runner = ROOT/'tests/check_wbgame_mame.py'
    for title in titles:
        output = output_root/title
        command = [sys.executable, str(runner), '--startup-only',
                   '--mame', str(args.mame.resolve()), '--disk', str(args.disk.resolve()),
                   '--firmware', str(args.firmware.resolve()), '--game',
                   str((args.games_root/title).resolve()), '--output', str(output),
                   '--module-file', str(args.module_file.resolve()), '--helper-file',
                   str(args.helper_file.resolve()), '--ui-helper-file',
                   str(args.ui_helper_file.resolve()), '--os9', args.os9]
        print(f'[{title}] running', flush=True)
        subprocess.run(command, cwd=ROOT, env=env, check=True)
        print(f'[{title}] PASS', flush=True)
    print(f'PASS: startup/display/exit cleanup for {len(titles)} title(s); artifacts: {output_root}')


if __name__ == '__main__':
    main()
