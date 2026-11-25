#!/usr/bin/env python3
"""Call the public CoCo parse command with a real indexed words.tok."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom, start_cpu


def vocabulary():
    data=bytearray(52)
    previous=''
    for word,group in [('look',2),('tree',0x8004)]:
        data[(ord(word[0])-97)*2:(ord(word[0])-96)*2]=len(data).to_bytes(2,'big')
        prefix=0
        while prefix<min(len(previous),len(word)) and previous[prefix]==word[prefix]:
            prefix+=1
        suffix=bytearray(ord(c)^127 for c in word[prefix:])
        suffix[-1]|=128
        data.extend(bytes([prefix])+suffix+group.to_bytes(2,'big'))
        previous=word
    return bytes(data)+b'\0'


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-parse-command-') as tmp:
        code,syms=compile_module(ROOT/'objs/mnln.asm',Path(tmp)/'mnln')
        d,emulator=start_cpu(idle_rom(Path(tmp)/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01')
            d.write(0xffa8,bytes(range(8)));d.write(0x8000,code);d.breakpoint(0x7e00)
            d.write(0x6000,vocabulary())
            # cmd_parse's normal CoCo dictionary-page fields all select this
            # already-mapped fixture page, so the public command runs unchanged.
            d.write(0x01a8,b'\x60\0');d.write(0x01aa,b'\x60\0');d.write(0x000a,b'\x60\0')
            d.write(0x0251,b'look tree\0'+bytes(30))
            d.write(0x7ef0,b'\x7e\0STACK')
            d.regs(pc=0x8000+syms['cmd_parse'],s=0x7ef0,y=0x3000,u=0,dp=0,cc=0x50)
            d.write(0x3000,b'\0')
            d.call('c');r=d.regs()
            assert r['pc']==0x7e00 and r['s']==0x7ef2 and r['y']==0x3001,r
            assert d.read(0x0194,2)==b'\0\x02'
            token=0x8000+syms['SortObjsBuf']
            assert d.read(0x0180,4)==token.to_bytes(2,'big')+(token+9).to_bytes(2,'big')
            assert d.read(token,10)==b'look\0tree\0'
            assert d.read(0x015a,1)==b'\x02' and d.read(0x043a,1)==b'\x02'
            assert d.read(0x01ae,1)==b'\xf7'
            assert d.read(0x7ef2,5)==b'STACK'
            d.write(0x3000,b'\x0c');d.write(0x01ae,b'\xff')
            d.regs(pc=0x8000+syms['cmd_parse'],s=0x7ef0,y=0x3000,u=0,dp=0,cc=0x50)
            d.call('c');r=d.regs()
            assert r['pc']==0x7e00 and r['s']==0x7ef2 and r['y']==0x3001
            assert d.read(0x01ae,1)==b'\xd7' # invalid index clears parse flags only
            assert d.read(0x0194,2)==b'\0\x02'
            assert d.read(0x0180,4)==token.to_bytes(2,'big')+(token+9).to_bytes(2,'big')
            print('PASS: actual CoCo cmd_parse indexes the 40-byte string table, stores dictionary word IDs and noun pointers, consumes one operand, preserves stack, and rejects index 12')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except Exception:emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
