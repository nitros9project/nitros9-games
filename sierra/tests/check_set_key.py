#!/usr/bin/env python3
"""Compare CoCo and Wild Bits set.key storage and first-match event behavior."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def call(d, entry, stop, stack=0x7ef0, **registers):
    d.write(stack, stop.to_bytes(2, 'big') + b'STACK')
    d.breakpoint(stop)
    state={'pc':entry,'s':stack,'dp':0,'cc':0x50}
    state.update(registers)
    d.regs(**state)
    d.call('c')
    result=d.regs()
    assert result['pc']==stop and result['s']==stack+2,result
    assert d.read(stack+2,5)==b'STACK'
    d.breakpoint(stop,False)
    return result


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-set-key-') as directory:
        tmp=Path(directory)
        coco,cs=compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
        native,ns=compile_module(ROOT/'objs/sierra.asm',tmp/'wbgame',defines=('WILDBITS=1',))
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=300)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01')
            d.write(0xffa8,bytes(range(8)))
            stop=0x7e00; private=0x1000; dp=private>>8
            for base in (0x8000,0x9000):
                d.write(base,coco)
                d.write(0x01d8,bytes(100))
                for args in (bytes([0x41,0,1]),bytes([0x41,0,2])):
                    d.write(0x6000,args+b'GUARD')
                    result=call(d,base+cs['CmdSetKey'],stop,y=0x6000)
                    assert result['y']==0x6003,result
                assert d.read(0x01d8,4)==bytes([0x41,1,0x41,2]),d.read(0x01d8,8)
                d.write(0x6100,b'\x01\x41')
                result=call(d,base+cs['RemapKeyEvent'],stop,x=0x6100)
                assert d.read(0x6100,2)==b'\x03\x01',d.read(0x6100,2)
                assert d.read(base,len(coco))==coco

            for base in (0x8000,0xa000):
                d.write(base,native)
                d.write(private,bytes(ns['size'])+b'GUARD')
                d.write(private+ns['resourcebase'],private.to_bytes(2,'big'))
                d.write(private+ns['vmarguments']-1,b'G'+bytes([0x41,0,1])+b'H')
                d.write(private+ns['vmkeycount'],b'\0')
                first=base+ns['SetKeyCommand']
                result=call(d,first,stop,dp=dp,u=private,y=0x6300)
                assert d.read(private+ns['vmkeycount'],1)==b'\x01'
                d.write(private+ns['vmarguments']-1,b'G'+bytes([0x41,0,2])+b'H')
                result=call(d,first,stop,dp=dp,u=private,y=0x6300)
                entries=d.read(private+ns['vmkeys'],6)
                assert entries==bytes([0x41,0,1,0x41,0,2]),entries
                assert d.read(private+ns['vmkeycount'],1)==b'\x02'
                d.write(private+ns['vmkeybyte'],b'A')
                d.write(private+ns['gamekeyscan'],b'\0')
                d.write(private+ns['vmcontrollers'],bytes(32))
                d.write(private+ns['vmvariables']+19,b'\x55')
                result=call(d,base+ns['GameKeyBinding'],stop,dp=dp,u=private,
                            x=private+ns['vmkeys'],y=0)
                controllers=d.read(private+ns['vmcontrollers'],32)
                assert controllers[0]==2 and controllers[1:]==bytes(31),controllers
                assert d.read(private+ns['vmvariables']+19,1)==b'\0'
                assert d.read(private+ns['vmarguments']-1,5)==b'GA\0\x02H'
                assert d.read(base,len(native))==native

            # Both owners have 50 entries. The next command consumes its
            # operand but leaves the table and caller state unchanged.
            full_coco=bytes(value for key in range(1,51) for value in (key,key))
            base=0x8000;d.write(base,coco);d.write(0x01d8,bytes(100))
            for key in range(1,51):
                d.write(0x6200,bytes([key,0,key]))
                result=call(d,base+cs['CmdSetKey'],stop,y=0x6200)
                assert result['y']==0x6203,result
            d.write(0x6200,b'\xee\0\x01')
            result=call(d,base+cs['CmdSetKey'],stop,y=0x6200)
            assert result['y']==0x6203,result
            assert d.read(0x01d8,100)==full_coco
            assert d.read(base,len(coco))==coco

            base=0xa000;d.write(base,native)
            d.write(private,bytes(ns['size'])+b'GUARD')
            d.write(private+ns['resourcebase'],private.to_bytes(2,'big'))
            d.write(private+ns['vmkeycount'],b'\0')
            for key in range(1,51):
                d.write(private+ns['vmarguments']-1,b'G'+bytes([key,0,key])+b'H')
                call(d,base+ns['SetKeyCommand'],stop,dp=dp,u=private,y=0x6300)
            assert d.read(private+ns['vmkeycount'],1)==b'\x32'
            full_native=bytes(value for key in range(1,51) for value in (key,0,key))
            assert d.read(private+ns['vmkeys'],150)==full_native
            d.write(private+ns['vmarguments']-1,b'G\xee\0\x01H')
            call(d,base+ns['SetKeyCommand'],stop,dp=dp,u=private,y=0x6300)
            assert d.read(private+ns['vmkeycount'],1)==b'\x32'
            assert d.read(private+ns['vmkeys'],150)==full_native
            assert d.read(private+ns['size'],5)==b'GUARD'
            assert d.read(base,len(native))==native
            assert d.read(private+ns['vmarguments']-1,5)==b'G\xee\0\x01H'
            print('PASS: actual CoCo set.key appends duplicate bindings, remaps by first match, and silently ignores entry 51; Wild Bits matches storage, event behavior and capacity at two code bases')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except Exception:emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
