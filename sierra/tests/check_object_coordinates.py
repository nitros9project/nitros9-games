#!/usr/bin/env python3
"""Execute shared coordinates/animation through both real owner command paths."""
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_wbres import idle_rom,start_cpu

ROOT=Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-object-coordinates-') as tmp:
        tmp=Path(tmp);image=tmp/'mnln'
        subprocess.run(['lwasm.orig','--6809','--format=os9','--no-warn=ifp1',
            '--pragma=pcaspcr,nosymbolcase,condundefzero',
            '-I'+str(ROOT/'kingsquest1'),'-I'+str(ROOT/'objs'),
            '-I'+str(ROOT.parent.parent/'nitros9/defs'),
            '--map='+str(image)+'.map','-o'+str(image),str(ROOT/'objs/mnln.asm')],check=True)
        owners=[('CoCo',image.read_bytes(),symbols(Path(str(image)+'.map')),0x8000,0x4000),
                ('native',(ROOT/'objs/wbgame').read_bytes(),symbols(ROOT/'objs/wbgame.map'),0xa000,None),
                ('probe',(ROOT/'objs/wbexec').read_bytes(),symbols(ROOT/'objs/wbexec.map'),0xa000,None)]
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            for owner,code,syms,base,objects in owners:
                objects=objects if objects is not None else syms['vmobjects']
                variables=0x0431 if owner=='CoCo' else syms['vmvariables']
                d.write(base,code)
                if owner=='CoCo':
                    d.write(0x30,objects.to_bytes(2,'big'))
                    d.write(0x32,(objects+64*43).to_bytes(2,'big'))
                else:d.write(syms['resourcebase'],b'\0\0')
                def run(opcode,name,args,boundary=False):
                    if owner=='CoCo':
                        d.write(0x2000,args);entry=base+syms[name]
                        stop=base+syms['FindObjPos'] if boundary else 0x1d00
                    else:
                        d.write(syms['vmarguments'],args)
                        d.write(syms['vmopcode'],bytes([opcode]))
                        entry=base+syms['GameReposition' if boundary else 'ObjectCommand']
                        stop=base+syms['RepositionPlace'] if boundary else 0x1d00
                    d.write(0x1df0,b'\x1d\x00');d.breakpoint(stop)
                    d.regs(pc=entry,s=0x1df0,dp=0,u=0,y=0x2000,cc=0x50)
                    d.call('c');result=d.regs();d.breakpoint(stop,False)
                    assert result['pc']==stop,(owner,opcode,result)
                    if owner=='CoCo':assert result['y']==0x2000+len(args)
                    elif not boundary:assert not result['cc']&1 and result['b']==0
                    return result
                for index in (0,63):
                    at=index*43
                    for vx,vy in ((0,0),(1,255),(127,128),(255,255),(255,0)):
                        for opcode,name in [(37,'cmd_position'),(38,'cmd_position_v')]:
                            before=bytearray((i*37+11)&255 for i in range(64*43))
                            wanted=bytearray(before)
                            wanted[at+3:at+5]=wanted[at+0x1a:at+0x1c]=bytes([vx,vy])
                            d.write(objects-1,b'G'+before+b'H')
                            vars_before=bytearray((i*19+7)&255 for i in range(256))
                            vars_before[0],vars_before[255]=vx,vy
                            d.write(variables,vars_before)
                            args=bytes([index,vx,vy]) if opcode==37 else bytes([index,0,255])
                            run(opcode,name,args)
                            assert d.read(objects-1,len(before)+2)==b'G'+wanted+b'H',(owner,opcode,index,vx,vy)
                            assert d.read(variables,256)==vars_before
                        for outx,outy in ((0,255),(255,0),(255,255)):
                            before=bytearray((i*37+11)&255 for i in range(64*43))
                            before[at+3:at+5]=bytes([vx,vy])
                            d.write(objects-1,b'G'+before+b'H')
                            vars_before=bytearray((i*19+7)&255 for i in range(256))
                            wanted=bytearray(vars_before);wanted[outx]=vx;wanted[outy]=vy
                            d.write(variables,vars_before)
                            run(39,'cmd_get_position',bytes([index,outx,outy]))
                            assert d.read(objects-1,len(before)+2)==b'G'+before+b'H'
                            assert d.read(variables,256)==wanted,(owner,index,outx,outy)
                    for flags in (0,0x10,0x3f,0x40,0x70,255):
                        before=bytearray((i*37+11)&255 for i in range(64*43))
                        before[at+0x26]=flags;wanted=bytearray(before)
                        if not flags&0x40:
                            wanted[at+0x26]=0x70
                            for field in (0x21,0x22,0x23):wanted[at+field]=0
                        d.write(objects-1,b'G'+before+b'H')
                        run(33,'CmdAnimateObj',bytes([index]))
                        assert d.read(objects-1,len(before)+2)==b'G'+wanted+b'H',(owner,index,flags)
                        run(33,'CmdAnimateObj',bytes([index]))
                        assert d.read(objects-1,len(before)+2)==b'G'+wanted+b'H'
                    if owner=='probe':continue
                    # Stop at the real platform placement boundary: compare the
                    # arithmetic itself without bypassing it with test helpers.
                    for opcode,name in [(40,'cmd_reposition'),(147,'cmd_reposition_to'),(148,'cmd_reposition_to_v')]:
                        for start in (0,1,127,128,255):
                            for value in (0,1,127,128,255):
                                other=255-value
                                before=bytearray((i*37+11)&255 for i in range(64*43))
                                before[at+3:at+5]=bytes([start,start]);wanted=bytearray(before)
                                if opcode==40:
                                    signed=lambda v:v if v<128 else v-256
                                    coords=bytes([max(0,start+signed(value))&255,max(0,start+signed(other))&255])
                                else:coords=bytes([value,other])
                                wanted[at+3:at+5]=coords
                                if owner=='CoCo':wanted[at+0x25]|=4
                                else:wanted[at+0x1a:at+0x1c]=bytes([start,start])
                                d.write(objects-1,b'G'+before+b'H')
                                vars_before=bytearray((i*19+7)&255 for i in range(256))
                                vars_before[0],vars_before[255]=value,other;d.write(variables,vars_before)
                                args=bytes([index,value,other]) if opcode==147 else bytes([index,0,255])
                                result=run(opcode,name,args,boundary=True)
                                assert d.read(objects-1,len(before)+2)==b'G'+wanted+b'H',(owner,opcode,index,start,value)
                                assert d.read(variables,256)==vars_before
                                assert result['s']==(0x1dec if owner=='CoCo' and opcode==40 else 0x1dee if owner=='CoCo' else 0x1df0)
                if owner!='CoCo':
                    for index in (64,255):
                        for opcode in (33,37,38,39):
                            before=d.read(objects-1,64*43+2)
                            d.write(syms['vmarguments'],bytes([index,0,255]));d.write(syms['vmopcode'],bytes([opcode]))
                            result=d.run(base+syms['ObjectCommand'],u=0)
                            assert result['cc']&1 and result['b']==syms['E$IllArg']
                            assert d.read(objects-1,64*43+2)==before
                assert d.read(base,len(code))==code
            print('PASS: shared coordinate and animation commands in both real owners and the native execution probe; first/last records, variable indices 0/255, aliased outputs, repeated animation, signed delta clamp/wrap edges, literal/variable reposition boundaries, stack/record guards, native index errors and immutable code')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
