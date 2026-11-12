#!/usr/bin/env python3
"""Execute shared directory/header decoding in both actual resource owners."""
import tempfile
from pathlib import Path
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom, start_cpu


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-resource-format-') as name:
        tmp=Path(name)
        owners=[('CoCo',*compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')),
                ('Wild Bits',*compile_module(ROOT/'objs/sierra.asm',tmp/'wbgame',defines=('WILDBITS=1',)))]
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=900)
        calls=0
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            for owner,code,syms in owners:
                for base in (0x8000,0x9000):
                    d.write(base,code)
                    for field in ('Volume','DecodedLength','StoredLength'):
                        prefix='Resource'+field
                        stop=base+syms[prefix+'Done'];d.breakpoint(stop)
                        values=range(256) if field=='Volume' else sorted({v for byte in range(256) for v in (byte,byte<<8,byte|0xff00,0xff|byte<<8)})
                        for value in values:
                            source=bytearray(b'HEADER!')
                            if field=='Volume':source[:3]=bytes((value,0xa5,0x5a));address=0x7000
                            else:
                                offset=3 if field=='DecodedLength' else 5
                                source[offset:offset+2]=value.to_bytes(2,'little')
                                address=0x7ef0+9 if owner=='CoCo' else 0x7000
                            d.write(address-1,b'G'+source+b'H')
                            d.regs(pc=base+syms[prefix+'Begin'],s=0x7ef0,x=0x7000,
                                   y=0x7654,u=0x7000,a=0x93,b=0xa7,dp=0,cc=0x50)
                            d.call('c');regs=d.regs()
                            assert regs['pc']==stop,(owner,field,value,regs)
                            expected=value>>4 if field=='Volume' else value
                            actual=regs['a'] if field=='Volume' else regs['a']<<8|regs['b']
                            assert actual==expected,(owner,field,value,actual)
                            if field=='Volume':assert regs['b']==0xa7
                            for reg,wanted in [('s',0x7ef0),('x',0x7000),('u',0x7000),('y',0x7654)]:assert regs[reg]==wanted,(owner,field,reg,regs)
                            assert d.read(address-1,9)==b'G'+source+b'H'
                            calls+=1
                        d.breakpoint(stop,False)
                    assert d.read(base,len(code))==code,owner
            print(f'PASS: {calls} actual directory/header decoding calls in both owners at two code bases; every directory byte, every low/high size byte with zero/255 companions, endianness, source guards, preserved context and immutable code')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except Exception:emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
