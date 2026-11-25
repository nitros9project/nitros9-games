#!/usr/bin/env python3
"""Compare the public CoCo/native distance command and its shared arithmetic."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom,start_cpu

ROOT=Path(__file__).resolve().parents[1]
CASES=[
    # first (visible, x, y, width), second (...), expected Manhattan distance
    ((1,10,20,8),(1,30,40,10),41),
    ((1,250,2,3),(1,1,240,5),254),
    ((0,10,20,8),(1,30,40,10),255),
    ((1,0,0,0),(1,255,0,0),254),
    ((1,0,0,255),(1,255,255,255),254),
    ((1,77,88,12),(1,77,88,12),0),
]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-object-distance-') as folder:
        folder=Path(folder)
        coco,cs=compile_module(ROOT/'objs/mnln.asm',folder/'mnln')
        native,ns=compile_module(ROOT/'objs/sierra.asm',folder/'wbgame',defines=('WILDBITS=1',))
        d,emulator=start_cpu(idle_rom(folder/'idle.rom'),timeout=900)
        calls=0
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            d.breakpoint(0x7e00)
            for owner,code,syms,base in (('CoCo',coco,cs,0x8000),('native',native,ns,0xa000)):
                private=0 if owner=='CoCo' else 0x1000
                objects=0x4000 if owner=='CoCo' else private+ns['vmobjects']
                variables=0x0431 if owner=='CoCo' else private+ns['vmvariables']
                args=0x2000 if owner=='CoCo' else private+ns['vmarguments']
                d.write(base,code)
                if private:
                    d.write(private,bytes(ns['size'])+b'GUARD')
                    d.write(private+ns['resourcebase'],private.to_bytes(2,'big'))
                else:d.write(0x30,objects.to_bytes(2,'big'))
                for first_index,second_index in ((0,63),(63,0)):
                    for first,second,wanted in CASES:
                        before=bytearray((i*37+11)&255 for i in range(64*43))
                        for index,item in ((first_index,first),(second_index,second)):
                            at=index*43
                            before[at+0x26]=(before[at+0x26]&0xfe)|(item[0]&1)
                            before[at+0x04]=item[1];before[at+0x03]=item[2]
                            before[at+0x1c]=item[3]
                        d.write(objects-1,b'G'+before+b'H')
                        var_before=bytearray((i*19+7)&255 for i in range(256))
                        var_before[0]=0xa5;var_before[255]=0x5a
                        d.write(variables,var_before)
                        operands=bytes([first_index,second_index,255])
                        d.write(args,operands)
                        if private:d.write(private+ns['vmopcode'],b'\x45')
                        d.write(0x7ef0,b'\x7e\x00STACK')
                        entry=base+(cs['CmdDistance'] if owner=='CoCo' else ns['ObjectDistanceCommand'])
                        d.regs(pc=entry,s=0x7ef0,y=args,u=private,dp=private>>8,cc=0x50)
                        d.call('c');regs=d.regs()
                        assert regs['pc']==0x7e00 and regs['s']==0x7ef2,(owner,first_index,second_index,first,second,regs)
                        if owner=='CoCo':assert regs['y']==args+3
                        else:assert not regs['cc']&1 and regs['b']==0
                        expected_vars=bytearray(var_before);expected_vars[255]=wanted
                        assert d.read(variables,256)==expected_vars,(owner,first_index,second_index,first,second,wanted)
                        assert d.read(objects-1,len(before)+2)==b'G'+before+b'H'
                        assert d.read(0x7ef2,5)==b'STACK'
                        if private:assert d.read(private+ns['size'],5)==b'GUARD'
                        calls+=1
                assert d.read(base,len(code))==code
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except Exception:emulator.kill();emulator.wait(timeout=5)
    print(f'PASS: {calls} actual CoCo/native distance calls; visible/invisible, reversed, saturated and boundary coordinates; records, variables, stack and guards preserved')


if __name__=='__main__':main()
