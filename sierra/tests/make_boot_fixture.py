#!/usr/bin/env python3
"""Create a disposable two-instance disk from the built King's Quest I disk."""
from pathlib import Path
import os
import subprocess
import sys

shelf = Path(__file__).resolve().parents[3]
game = shelf / 'nitros9-games/sierra/kingsquest1'
modules = shelf / 'nitros9/level2/coco3/modules'
output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, PATH=str(shelf / 'bin') + ':' + os.environ['PATH'])
subprocess.run(['make', '-C', str(shelf / 'nitros9/recipes/coco3/floppy'),
    'NITROS9DIR=' + str(shelf / 'nitros9'), 'MODDIR=' + str(modules),
    str(modules / 'v1.dt'), str(modules / 'v2.dt')], env=env, check=True)
subprocess.run([str(shelf / 'bin/lwasm'), '--format=os9',
    '--pragma=pcaspcr,nosymbolcase,condundefzero,undefextern',
    '-I' + str(shelf / 'nitros9/defs'), '-I' + str(game),
    str(Path(__file__).with_name('two_instances.asm')),
    '-o' + str(output / 'AutoEx'), '--map=' + str(output / 'AutoEx.map')],
    cwd=output, env=env, check=True)
os9 = str(shelf / 'toolshed/build/unix/os9/os9')
disk = output / 'two-instances.dsk'
boot = output / 'OS9Boot'
subprocess.run([os9, 'copy', '-r', str(game / 'KingsQuestI.dsk') + ',OS9Boot', str(boot)], check=True)
with boot.open('ab') as stream:
    for name in ('v1.dt', 'v2.dt'):
        stream.write((modules / name).read_bytes())
kernel = output / 'kerneltrack'
kernel.write_bytes(b''.join((modules / name).read_bytes() for name in ('rel_32', 'boot_1773_6ms', 'krn')))
subprocess.run([os9, 'format', '-e', '-t40', '-ds', '-dd', '-q', str(disk)], check=True)
subprocess.run([os9, 'gen', str(disk), '-b=' + str(boot), '-t=' + str(kernel)], check=True)
subprocess.run([os9, 'makdir', str(disk) + ',CMDS'], check=True)
for name in ('sysgo', 'startup', 'tOC', 'tOC.txt'):
    host = output / name
    subprocess.run([os9, 'copy', '-r', str(game / 'KingsQuestI.dsk') + ',' + name, str(host)], check=True)
    subprocess.run([os9, 'copy', '-r', str(host), str(disk) + ',' + name], check=True)
for name in ('mnln', 'scrn', 'shdw', 'shell'):
    subprocess.run([os9, 'copy', '-r', str(game / name), str(disk) + ',CMDS/' + name], check=True)
for name in ('logDir', 'object', 'picDir', 'sndDir', 'viewDir', 'vol.0', 'vol.1', 'vol.2', 'words.tok'):
    subprocess.run([os9, 'copy', '-r', str(game / name), str(disk) + ',' + name], check=True)
subprocess.run([os9, 'copy', '-r', str(game / 'sierra'), str(disk) + ',CMDS/sierra'], check=True)
subprocess.run([os9, 'copy', '-r', str(output / 'AutoEx'), str(disk) + ',CMDS/AutoEx'], check=True)
for name in ('sysgo', 'CMDS/sierra', 'CMDS/AutoEx', 'CMDS/shell', 'CMDS/mnln', 'CMDS/scrn', 'CMDS/shdw'):
    subprocess.run([os9, 'attr', str(disk) + ',' + name, '-e', '-pe'], check=True)
print(disk)
