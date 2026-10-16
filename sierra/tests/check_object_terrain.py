#!/usr/bin/env python3
"""Run shared terrain scans/constraints through both production owner bindings."""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom,start_cpu


def scan(pixels, flags, legacy):
    water,signal,blocked=1,0,False
    for value in pixels:
        if value==0:
            blocked=True;break
        if legacy:
            if value==3:continue
            water=0
        if value==1 and not flags&2:
            blocked=True;break
        if value==2:signal=32 if legacy else (signal+1)&255
        if not legacy and value!=3:water=0
    return blocked,water,signal


def main():
    cases=[([p],f) for p in range(16) for f in (0,2,255)]
    cases += [([1],f) for f in range(256)]
    cases += [(list(p),f) for p in ((3,3),(3,0),(3,1),(3,2),(2,3),(2,2),(4,3),(3,4)) for f in (0,2)]
    with tempfile.TemporaryDirectory(prefix='sierra-terrain-') as name:
        tmp=Path(name)
        coco,cs=compile_module(ROOT/'objs/shdw.asm',tmp/'shdw')
        native,ns=compile_module(ROOT/'objs/sierra.asm',tmp/'native',defines=('WILDBITS=1',))
        d,emu=start_cpu(idle_rom(tmp/'idle.rom'),timeout=900)
        calls=0
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            for owner,code,syms,bases in [('CoCo',coco,cs,(0x8000,0x9000)),('native',native,ns,(0x9000,0xa000))]:
                private=0 if owner=='CoCo' else 0x1000
                for base in bases:
                    d.write(base,code)
                    blocked=base+syms['MotionTerrainBlocked' if private else 'ClearFlagControl']
                    done=base+syms['TerrainScanDone'];constraints=base+syms['TerrainConstraintsDone']
                    for stop in (blocked,done,constraints):d.breakpoint(stop)
                    if private:
                        state=bytearray(syms['size'])
                        for field,value in [('resourcebase',private),('motionobject',0x7000),('motionx',10),('motiony',60)]:
                            state[syms[field]:syms[field]+2]=value.to_bytes(2,'big')
                        d.write(private,state+b'GUARD')
                        pointer=base+syms['PicturePointer'];d.breakpoint(pointer)
                    for pixels,flags in cases:
                        record=bytearray(range(43));record[0x1c]=len(pixels);record[0x26]=flags
                        d.write(0x6fff,b'G'+record+b'H')
                        d.write(0x7800,bytes(p<<4 for p in pixels)+b'GUARD')
                        if private:
                            d.write(private+syms['motioncolumn'],bytes([0,1,0]))
                        else:
                            d.write(syms['ScratchA5'],bytes([0,1]));d.write(syms['FlagControl'],b'\1')
                        d.write(0x7ef0,b'\x7e\x00STACK')
                        d.regs(pc=base+syms['TerrainPixelLoop'],s=0x7ef0,x=private or 0x7000,
                               u=0x7000 if private else 0x7800,b=len(pixels),dp=private>>8,cc=0x50)
                        for _ in range(len(pixels)+1):
                            d.call('c');regs=d.regs()
                            if regs['pc'] in (blocked,done):break
                            assert private and regs['pc']==pointer,regs
                            column=d.read(private+syms['motioncolumn'],1)[0]
                            assert (regs['a']<<8)|regs['b']==60*160+10+column
                            ret=int.from_bytes(d.read(regs['s'],2),'big')
                            d.regs(pc=ret,s=regs['s']+2,u=0x7800+column)
                        else:raise AssertionError('scan did not finish')
                        expected,water,signal=scan(pixels,flags,not private)
                        assert regs['pc']==(blocked if expected else done),(owner,pixels,flags,regs)
                        at=private+syms['motionwater'] if private else syms['ScratchA6']
                        sig=private+syms['motiontrigger'] if private else syms['ScratchA5']
                        assert d.read(at,1)==bytes([water]) and d.read(sig,1)==bytes([signal]),(owner,pixels,flags)
                        assert d.read(0x6fff,45)==b'G'+record+b'H'
                        assert regs['s']==0x7ef0 and d.read(0x7ef0,7)==b'\x7e\x00STACK'
                        calls+=1
                    for flags in range(256):
                        for water in (0,1):
                            record=bytearray(range(43));record[0x25]=flags
                            d.write(0x6fff,b'G'+record+b'H')
                            d.write(private+syms['motionwater'] if private else syms['ScratchA6'],bytes([water]))
                            d.regs(pc=base+syms['TerrainCheckConstraints'],s=0x7ef0,
                                   x=private or 0x7000,u=0x7000,dp=private>>8,cc=0x50)
                            d.call('c');regs=d.regs()
                            rejected=bool((flags&1 and not water) or (flags&8 and water))
                            assert regs['pc']==(blocked if rejected else constraints),(owner,flags,water,regs)
                            assert d.read(0x6fff,45)==b'G'+record+b'H'
                            assert regs['s']==0x7ef0 and d.read(0x7ef0,7)==b'\x7e\x00STACK'
                            calls+=1
                    if private:
                        state[syms['motioncolumn']]=len(cases[-1][0])
                        state[syms['motionwater']]=1
                        state[syms['motiontrigger']]=scan(*cases[-1],False)[2]
                        assert d.read(private,syms['size'])==state
                        assert d.read(private+syms['size'],5)==b'GUARD'
                        d.breakpoint(pointer,False)
                    for stop in (blocked,done,constraints):d.breakpoint(stop,False)
                    assert d.read(base,len(code))==code
            print(f'PASS: {calls} real CoCo/native terrain scans and constraints; all priorities, '
                  'control/status bytes, mixed water/trigger/blocking, preserved owner flag policy, '
                  'two code addresses, private state, guards and immutable code; pixel mapping mocked')
        finally:
            d.s.close();emu.terminate()
            try:emu.wait(timeout=5)
            except subprocess.TimeoutExpired:emu.kill();emu.wait(timeout=5)

if __name__=='__main__':main()
