#!/usr/bin/env python3
"""Compare actual cel cycle transitions, substituting only view selection."""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT=Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-cel-advance-') as name:
        tmp=Path(name)
        coco,cs=compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
        native,ns=compile_module(ROOT/'objs/wbgame.asm',tmp/'wbgame')
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            for owner,code,syms,bases in [('CoCo',coco,cs,(0x8000,0x9000)),
                                         ('native',native,ns,(0x9000,0xa000))]:
                for base in bases:
                    d.write(base,code)
                    private=0 if owner=='CoCo' else 0x1000
                    objects=0x4000 if not private else private+syms['vmobjects']
                    flagbase=0x01ae if not private else private+syms['vmflags']
                    flagbytes=32 if not private else 256
                    if private:d.write(private,bytes(syms['size']))
                    callback=base+syms['SetCelHelper' if not private else 'MotionSelectView']
                    d.breakpoint(callback);d.breakpoint(0x7e00)
                    counts=[1,2,4,128,255]
                    for count in counts:
                        for current in sorted({0,count//2,count-1}):
                            for mode in range(4):
                                for suppressed in (False,True):
                                    for index in (0,63):
                                        flag=255 if index else 0
                                        before=bytearray((i*37+11)&255 for i in range(64*43))
                                        at=index*43
                                        for field,value in [(2,index),(0xe,current),(0xf,count),(0x21,7),(0x23,mode),(0x25,0xa5|(0x10 if suppressed else 0)),(0x26,255),(0x27,flag)]:before[at+field]=value
                                        expected=bytearray(before)
                                        flags=bytearray([0xaa if not private else 1])*flagbytes
                                        if private:flags[flag]=0
                                        else:flags[flag>>3]&=~(128>>(flag&7))
                                        wantedflags=bytearray(flags);finished=False
                                        if suppressed:
                                            expected[at+0x25]&=~0x10;nextcel=current
                                        elif mode==0:nextcel=(current+1)%count
                                        elif mode==3:nextcel=(current-1)%count
                                        elif mode==1:
                                            nextcel=min(current+1,count-1);finished=nextcel==count-1
                                        else:
                                            nextcel=max(current-1,0);finished=nextcel==0
                                        if finished:
                                            expected[at+0x26]&=~0x20
                                            expected[at+0x21]=0;expected[at+0x23]=0
                                            if private:wantedflags[flag]=1
                                            else:wantedflags[flag>>3]|=128>>(flag&7)
                                        d.write(objects-1,b'G'+before+b'H');d.write(flagbase,flags)
                                        d.write(0x7ef0,b'\x7e\x00STACK')
                                        d.regs(pc=base+syms['AdvanceCelFrame'],s=0x7ef0,u=objects+at,x=private,dp=private>>8,cc=0x50)
                                        d.call('c');r=d.regs()
                                        if not suppressed:
                                            assert r['pc']==callback and r['b']==nextcel,(owner,count,current,mode,r,nextcel)
                                            assert r['u']==objects+at
                                            if private:assert r['a']==47 and r['x']==private
                                            # Actual completion/stop effects are already
                                            # applied; the owner view callback receives
                                            # the next index and refreshes cel metadata.
                                            assert d.read(objects-1,len(before)+2)==b'G'+expected+b'H',(owner,count,current,mode,'record')
                                            ret=int.from_bytes(d.read(r['s'],2),'big')
                                            updates=dict(pc=ret,s=r['s']+2)
                                            if private:updates.update(b=0,cc=r['cc']&~1)
                                            d.regs(**updates)
                                            if ret!=0x7e00:d.call('c')
                                            r=d.regs()
                                        assert r['pc']==0x7e00 and r['s']==0x7ef2
                                        assert d.read(0x7ef2,5)==b'STACK'
                                        assert d.read(objects-1,len(before)+2)==b'G'+expected+b'H'
                                        assert d.read(flagbase,flagbytes)==wantedflags
                                        if private:assert not r['cc']&1 and r['b']==0
                    if private:
                        for mode in (4,255):
                            d.write(objects+0x23,bytes([mode]));d.write(objects+0x25,b'\0')
                            before=d.read(objects,64*43);flags=d.read(flagbase,flagbytes)
                            d.write(0x7ef0,b'\x7e\x00STACK')
                            d.regs(pc=base+syms['AdvanceCelFrame'],s=0x7ef0,u=objects,x=private,dp=private>>8,cc=0x50)
                            d.call('c');r=d.regs()
                            assert r['pc']==0x7e00 and r['s']==0x7ef2 and r['cc']&1
                            assert d.read(objects,64*43)==before and d.read(flagbase,flagbytes)==flags
                        # A failed native view selection must retain its
                        # B/carry status through the common cel routine.
                        for field,value in [(0xe,1),(0xf,4),(0x23,0),(0x25,0)]:
                            d.write(objects+field,bytes([value]))
                        d.write(0x7ef0,b'\x7e\x00STACK')
                        d.regs(pc=base+syms['AdvanceCelFrame'],s=0x7ef0,u=objects,x=private,dp=private>>8,cc=0x50)
                        d.call('c');r=d.regs()
                        assert r['pc']==callback and r['a']==47 and r['b']==2
                        ret=int.from_bytes(d.read(r['s'],2),'big')
                        d.regs(pc=ret,s=r['s']+2,b=203,cc=r['cc']|1)
                        if ret!=0x7e00:d.call('c')
                        r=d.regs()
                        assert r['pc']==0x7e00 and r['s']==0x7ef2 and r['b']==203 and r['cc']&1
                    assert d.read(base,len(code))==code
                    d.breakpoint(callback,False);d.breakpoint(0x7e00,False)
            print('PASS: actual common cel advance in both owners at two load addresses; all four modes, first/middle/last and single-cel loops, suppression, completion flags 0/255, whole-record/flag preservation, callback context, unsigned 255-cel wrapping in both owners, invalid native modes, native callback errors, guards/stack and immutable code')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
