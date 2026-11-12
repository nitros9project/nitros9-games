#!/usr/bin/env python3
from pathlib import Path
import argparse, subprocess, re, shutil, hashlib, json
ROOT=Path(__file__).resolve().parents[1]
def crc(data):
 c=0xffffff
 for b in data:
  c ^= b<<16
  for _ in range(8): c=((c<<1)^ (0x800063 if c&0x800000 else 0))&0xffffff
 return c
def main():
 p=argparse.ArgumentParser();p.add_argument('--defs',default='.');p.add_argument('--lwasm',default='lwasm.orig');a=p.parse_args()
 build=ROOT/'build';build.mkdir(exist_ok=True)
 subprocess.run([a.lwasm,'--6809','--format=raw','--pragma=pcaspcr,nosymbolcase,condundefzero,dollarnotlocal','-I'+str(ROOT/'src'),'-I'+a.defs,'--list='+str(build/'platform.list'),'--map='+str(build/'platform.map'),'--symbols','-o',str(build/'platform.bin'),str(ROOT/'src/platform.asm')],check=True)
 syms={m[1]:int(m[2],16) for m in re.finditer(r'^Symbol: (\S+) .* = ([0-9A-F]+)$',(build/'platform.map').read_text(),re.M)}
 original=(ROOT/'original/CMDS/DONALD').read_bytes();assert crc(original)==0x800fe3
 assert hashlib.sha256(original).hexdigest()=='177627658fa3b7657df382b2928614a37c0c4ee9b329bed55a73adf07b8c0a43', 'unsupported original DONALD revision'
 b=bytearray(original[:-3]);b.extend((build/'platform.bin').read_bytes())
 patches=[]
 def patch(offset,expected,dest,opcode):
  old=bytes.fromhex(expected);assert b[offset:offset+len(old)]==old,(hex(offset),b[offset:offset+len(old)].hex())
  diff=(syms[dest]-offset-3)&65535
  b[offset:offset+3]=bytes([opcode])+diff.to_bytes(2,'big')
  patches.append(dict(offset=offset,original=old.hex(),destination=dest))
 patch(0x13,'df0833','NativeStart',0x16)
 patch(0x679,'308d0c','NativeInit',0x16)
 patch(0x54f,'0d7727','NativeFlip',0x16)
 patch(0xbd,'170356','TownDraw',0x17)
 patch(0x1f4,'170d09','NativeCleanup',0x17)
 patch(0x55,'103f8d','NativeJoy',0x17)
 patch(0x302,'103f8d','NativeJoy',0x17)
 patch(0xf21,'86f130','NoSoundLoad',0x16)
 patch(0xf42,'0d4e26','NativeSound',0x16)
 patch(0xfaf,'de4f27','NoSound',0x16)
 assert b[0x6e9:0x6eb]==bytes.fromhex('8d01')
 b[0x6e9:0x6eb]=b'\x12\x12' # combined SD assets need no side-2 prompt
 patch(0xab5,'103f89','ReadKey',0x17)
 patch(0x2f8,'d70a3b','NativeSignal',0x16)
 assert b.count(b'/D0/CMDS/')==6
 b=b.replace(b'/D0/CMDS/',b'/s0/CMDS/')
 b[11:13]=(0x6c00).to_bytes(2,'big');b[2:4]=(len(b)+3).to_bytes(2,'big')
 b[8]=0xff
 for v in b[:8]:b[8]^=v
 b.extend((crc(b)^0xffffff).to_bytes(3,'big'));assert crc(b)==0x800fe3
 assert len(b)<=8192, 'one code block required to leave room for private screens, submodule, window'
 game=build/'game';game.mkdir(exist_ok=True)
 for src in (ROOT/'original').rglob('*'):
  if src.is_file() and src.name not in ('DONALD','SOUND','DDSND'):
   dst=game/src.relative_to(ROOT/'original');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
 (game/'CMDS/DONALD').write_bytes(b)
 (build/'patches.json').write_text(json.dumps({'original_sha256':hashlib.sha256(original).hexdigest(),'size':len(b),'data_size':0x6c00,'patches':patches},indent=2)+'\n')
 print('Built DONALD:',len(b),'bytes; private data:',0x6c00,'bytes')

if __name__=="__main__":main()
