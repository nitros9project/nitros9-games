#!/usr/bin/env python3
"""Verify real string commands keep the terminator inside their 40-byte slot."""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT=Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-string-slots-') as name:
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
                    d.write(base,code)
                    private=0 if owner=='CoCo' else 0x1000
                    table=0x0251 if not private else private+syms['vmstrings']
                    variables=0x0431 if not private else private+syms['vmvariables']
                    args=0x3000 if not private else private+syms['vmarguments']
                    if private:
                        d.write(private,bytes(syms['size'])+b'GUARD')
                        d.write(private+syms['resourcebase'],private.to_bytes(2,'big'))
                    callback=base+syms['GetMsgPtr' if not private else 'ReadLogicMessage']
                    d.breakpoint(callback);d.breakpoint(0x7e00)
                    commands=['cmd_set_string','cmd_word_to_string'] if not private else ['SetStringCommand']
                    for command in commands:
                        for slot in (0,11):
                            for length in (0,1,38,39,40,80):
                                text=b'A'*length;source=text+b'\0'
                                wanted=bytearray(b'\x5a'*480)
                                amount=min(length,39);at=slot*40
                                wanted[at:at+amount]=text[:amount];wanted[at+amount]=0
                                d.write(table,b'\x5a'*480);d.write(variables,b'\x77'*256)
                                d.write(args,bytes([slot,1])+b'ARGS')
                                d.write(0x77ff,b'S'+source+b'T')
                                if command=='cmd_word_to_string':d.write(0x0182,b'\x78\0')
                                d.write(0x7ef0,b'\x7e\x00STACK')
                                d.regs(pc=base+syms[command],s=0x7ef0,y=args,u=private,dp=private>>8,cc=0x50)
                                d.call('c');r=d.regs()
                                if command!='cmd_word_to_string':
                                    assert r['pc']==callback
                                    ret=int.from_bytes(d.read(r['s'],2),'big')
                                    updates=dict(pc=ret,s=r['s']+2,cc=r['cc']&~1)
                                    updates['u' if not private else 'x']=0x7800
                                    d.regs(**updates);d.call('c');r=d.regs()
                                assert r['pc']==0x7e00 and r['s']==0x7ef2
                                assert d.read(0x7ef2,5)==b'STACK'
                                assert d.read(table,480)==wanted,(owner,command,slot,length,'slot overflow')
                                assert d.read(variables,256)==b'\x77'*256,(owner,command,slot,length,'variable overwrite')
                                assert d.read(args+2,4)==b'ARGS'
                                assert d.read(0x77ff,len(source)+2)==b'S'+source+b'T'
                                if private:assert not r['cc']&1 and r['b']==0
                                else:assert r['y']==args+2
                    if private:
                        for slot in (12,255):
                            d.write(args,bytes([slot,1]));before=d.read(table,480)
                            d.write(0x7ef0,b'\x7e\x00STACK')
                            d.regs(pc=base+syms['SetStringCommand'],s=0x7ef0,u=private,dp=private>>8,cc=0x50)
                            d.call('c');r=d.regs()
                            assert r['pc']==0x7e00 and r['cc']&1 and r['s']==0x7ef2
                            assert d.read(table,480)==before
                    assert d.read(base,len(code))==code
                    d.breakpoint(callback,False);d.breakpoint(0x7e00,False)
            print('PASS: actual CoCo set.string/word.to.string and native set.string at two load addresses; slots 0/11, empty/boundary/long text, in-slot termination, adjacent slot/variable preservation, source/argument/stack guards and bounded native slot errors')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
