#!/usr/bin/env python3
"""Execute shared fill eligibility in both actual picture engines."""
import tempfile
from pathlib import Path
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom, start_cpu


def main():
    cases={(mask,color) for mask in range(256) for color in (0,15,64,79,255)}
    cases|={(mask,color) for mask in (0,15,240,255) for color in range(256)}
    with tempfile.TemporaryDirectory(prefix='sierra-fill-selection-') as name:
        tmp=Path(name)
        owners=[('CoCo',*compile_module(ROOT/'objs/shdw.asm',tmp/'shdw')),
                ('Wild Bits',*compile_module(ROOT/'objs/sierra.asm',tmp/'wbgame',defines=('WILDBITS=1',)))]
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=900)
        calls=0
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            for owner,code,syms in owners:
                private=0x1000 if owner=='Wild Bits' else 0
                for base in (0x8000,0x9000):
                    d.write(base,code)
                    selected=base+syms['FillSelectDone']
                    skipped=base+syms['FillDone' if private else 'SbuffPicFillRet']
                    d.breakpoint(selected);d.breakpoint(skipped)
                    color_address=private+syms['DrawColor']
                    for mask,color in sorted(cases):
                        d.write(color_address-1,bytes((0xa5,color,0x5a)))
                        d.write(0x7ef0,b'STACK')
                        cc=0x50|(4 if not mask else 0)|(8 if mask&128 else 0)
                        d.regs(pc=base+syms['FillSelectBegin'],s=0x7ef0,x=0x3456,
                               y=0x7654,u=0x4567,a=mask,b=0x93 if private else color,
                               dp=private>>8,cc=cc)
                        d.call('c');regs=d.regs()
                        priority=mask==240
                        unchanged=(color>>4==4) if priority else (color&15==15)
                        skip=not mask or unchanged
                        assert regs['pc']==(skipped if skip else selected),(owner,mask,color,regs)
                        if not skip:
                            assert regs['a']==(240 if priority else 15)
                            wanted=(64 if priority else 15) if private else color&(240 if priority else 15)
                            assert regs['b']==wanted,(owner,mask,color,regs)
                        for reg,value in [('s',0x7ef0),('x',0x3456),('u',0x4567),('y',0x7654)]:assert regs[reg]==value,(owner,reg,regs)
                        assert d.read(color_address-1,3)==bytes((0xa5,color,0x5a))
                        assert d.read(0x7ef0,5)==b'STACK'
                        calls+=1
                    d.breakpoint(selected,False);d.breakpoint(skipped,False)
                    assert d.read(base,len(code))==code,owner
            print(f'PASS: {calls} actual fill selections in both picture owners at two addresses; every mask, every color for all supported planes, priority/color choice, no-op rejection, guards/context and immutable code')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except Exception:emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
