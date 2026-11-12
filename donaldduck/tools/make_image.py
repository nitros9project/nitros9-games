#!/usr/bin/env python3
"""Install the native port in a private copy of a Wildbits Jr2 SD image."""
from pathlib import Path
import argparse,subprocess,shutil,tempfile
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('base',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
assert not a.output.exists(),'choose a new output file'
assert a.base.resolve()!=a.output.resolve()
shutil.copyfile(a.base,a.output)
def os9(*args):subprocess.run(['os9',*map(str,args)],check=True,stdout=subprocess.DEVNULL)
os9('makdir',str(a.output)+',ddp');os9('makdir',str(a.output)+',ddp/PIC')
for src in (root/'build/game').rglob('*'):
 if src.is_file():
  relative=src.relative_to(root/'build/game')
  target=str(a.output)+','+('' if relative.parts[0]=='CMDS' else 'ddp/')+str(relative)
  os9('copy','-r',src,target)
  if relative.parts[0]=='CMDS':os9('attr',target,'-e','-pe')
with tempfile.TemporaryDirectory() as temp:
 for name,target,data in [('startup','startup',b'load utilpak1\rload vt\rlink shell\rload grfdrv256\rchd /s0/ddp\r'),('feustartup','FEU/startup',b'bootos9 /s0/OS9Boot\r')]:
  src=Path(temp)/name;src.write_bytes(data);os9('copy','-r',src,str(a.output)+','+target)
with a.output.open('ab') as stream:stream.truncate(1<<(a.output.stat().st_size-1).bit_length())
print('Created',a.output,'Run DONALD at the shell prompt.')
