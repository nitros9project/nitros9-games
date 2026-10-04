#!/usr/bin/env python3
"""Compare all Sierra engine binaries against an explicit Git revision."""
import argparse
import io
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, help='Git revision before refactoring')
    parser.add_argument('--assembler', default=shutil.which('lwasm.orig') or shutil.which('lwasm'))
    parser.add_argument('--defs', type=Path, help='NitrOS-9 defs directory')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    defs = (args.defs or repo.parent / 'nitros9' / 'defs').resolve()
    if not args.assembler or not (defs / 'os9.d').is_file():
        parser.error('provide an installed lwasm assembler and NitrOS-9 --defs directory')
    assembler = str(Path(args.assembler).resolve())
    archive = subprocess.check_output(['git', 'archive', args.baseline, 'sierra/objs'], cwd=repo)
    games = sorted(p for p in (repo / 'sierra').iterdir()
                   if (p / 'Makefile').is_file() and (p / 'defsfile').is_file())
    flags = ['--no-warn=ifp1', '--6309', '--format=os9',
             '--pragma=pcaspcr,nosymbolcase,condundefzero,undefextern,dollarnotlocal,noforwardrefmax',
             '-I' + str(defs)]
    count = 0
    with tempfile.TemporaryDirectory(prefix='sierra-platform-') as temporary:
        work = Path(temporary)
        baseline = work / 'baseline'
        baseline.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            for member in tar.getmembers():
                if not member.isfile():
                    continue
                relative = Path(member.name).relative_to('sierra/objs')
                if '..' in relative.parts:
                    raise ValueError('unsafe archive path')
                destination = baseline / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(tar.extractfile(member).read())
        for game in games:
            directory = work / game.name
            directory.mkdir()
            shutil.copyfile(game / 'defsfile', directory / 'defsfile')
            for module in ('sierra', 'mnln', 'scrn', 'shdw'):
                outputs = []
                for label, sources in [('before', baseline), ('after', repo / 'sierra/objs')]:
                    output = directory / (module + '-' + label)
                    subprocess.run([assembler, *flags, '-I' + str(directory),
                                    '-I' + str(sources), str(sources / (module + '.asm')),
                                    '-o' + str(output)], cwd=directory, check=True)
                    outputs.append(output.read_bytes())
                if outputs[0] != outputs[1]:
                    raise SystemExit('Binary mismatch: ' + game.name + '/' + module)
                count += 1
        if not games:
            raise SystemExit('No Sierra game definitions found')
        for module in ('sierra', 'mnln', 'scrn', 'shdw'):
            sources = repo / 'sierra/objs'
            result = subprocess.run(
                [assembler, *flags, '-DWILDBITS=1', '-I' + str(directory),
                 '-I' + str(sources), str(sources / (module + '.asm')),
                 '-o' + str(directory / (module + '-unsupported'))],
                cwd=directory, capture_output=True, text=True)
            if result.returncode == 0 or 'Wild Bits' not in result.stderr:
                raise SystemExit('Missing unsupported-platform diagnostic: ' + module)
    print(f'PASS: {count} engine binaries across {len(games)} games match {args.baseline}')
    print('PASS: all four modules reject the unimplemented Wild Bits backend')


if __name__ == '__main__':
    main()
