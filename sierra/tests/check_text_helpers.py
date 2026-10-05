#!/usr/bin/env python3
"""Execute shared copying and decimal conversion in their actual owners."""
from pathlib import Path
import re
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT=Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-text-') as name:
        tmp=Path(name)
        coco,cs=compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
        native,ns=compile_module(ROOT/'objs/sierra.asm',tmp/'wbgame',defines=('WILDBITS=1',))
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            for owner,code,syms,bases in [('CoCo',coco,cs,(0x8000,0x9000)),
                                         ('native',native,ns,(0x9000,0xa000))]:
                for base in bases:
                    d.write(base,code);d.breakpoint(0x7e00)
                    limits=[1,2,39,40,127,255]+([256,257] if owner=='CoCo' else [])
                    for limit in limits:
                        for length in sorted({0,1,limit-1,limit,limit+5}):
                            text=bytes(i%255+1 for i in range(length))
                            source=text+b'\0';dest=bytearray(b'\x5a'*(limit+1))
                            copied=min(length,limit);dest[:copied]=text[:copied];dest[copied]=0
                            d.write(0x1fff,b'S'+source+b'T')
                            d.write(0x3fff,b'G'+b'\x5a'*(limit+1)+b'H')
                            d.write(0x7ef0,b'\x7e\x00STACK')
                            if owner=='CoCo':
                                regs=dict(pc=base+syms['MemCopyNull'],a=limit>>8,b=limit&255,u=0x4000,y=0x4321)
                            else:
                                regs=dict(pc=base+syms['StringCopy'],b=limit,y=0x4000,u=0x1234)
                            d.regs(x=0x2000,s=0x7ef0,dp=0,cc=0x50,**regs)
                            d.call('c');r=d.regs()
                            assert r['pc']==0x7e00 and r['s']==0x7ef2
                            assert d.read(0x7ef2,5)==b'STACK'
                            assert d.read(0x3fff,limit+3)==b'G'+dest+b'H',(owner,limit,length)
                            assert d.read(0x1fff,len(source)+2)==b'S'+source+b'T'
                            destination_end=0x4000+copied+(length<limit)
                            if owner=='CoCo':
                                assert r['x']==0x4000 and r['u']==destination_end and r['y']==0x4321
                            else:
                                assert r['x']==0x2000+copied+(length<limit)
                                assert r['y']==destination_end and r['u']==0x1234 and r['b']==0
                    cases=[str(value).encode() for value in range(256)]
                    cases += [b'',b' ',b'   ',b'000',b'256',b'511',b'999',b'1234567890',
                              b'9'*39,b'  255x',b'12 34',b'-1',b'+2',b'x99',b'\xff123']
                    for char in range(1,256):
                        if not 48<=char<=57:cases.append(bytes([char])+b'12')
                    for text in cases:
                        source=text+b'\0';match=re.match(rb' *([0-9]*)',text)
                        digits=match.group(1);expected=int(digits or b'0')&255
                        consumed=match.end()+1
                        d.write(0x1fff,b'S'+source+b'T');d.write(0x7ef0,b'\x7e\x00STACK')
                        d.regs(pc=base+syms['AtoI'],x=0x2000,u=0x1234,y=0x4321,
                               s=0x7ef0,dp=0,cc=0x50)
                        d.call('c');r=d.regs()
                        assert r['pc']==0x7e00 and r['s']==0x7ef2
                        assert r['a']==expected and r['x']==0x2000+consumed,(owner,text,r,expected,consumed)
                        assert r['u']==0x1234 and r['y']==0x4321
                        assert d.read(0x7ef2,5)==b'STACK'
                        assert d.read(0x1fff,len(source)+2)==b'S'+source+b'T'
                    assert d.read(base,len(code))==code
                    d.breakpoint(0x7e00,False)
            print('PASS: real CoCo/native bounded-copy and decimal routines at two code bases; copy termination/truncation, all nonzero byte values, 8/16-bit count edges, guards/register conventions, every byte value 0–255, decimal overflow/leading spaces/invalid prefixes, all nondigit byte classes, source cursors, stack balance and immutable code')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
