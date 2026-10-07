#!/usr/bin/env python3
"""Exercise static cel painting and persistence through real native commands."""
import argparse
from pathlib import Path
import subprocess
import tempfile
from check_wbres import exercise, idle_rom, start_cpu
from check_instances import symbols

ROWS=((1,1,None,2),(3,4,4,4),(5,None,None,None))

def assets(script,view):
    logic=len(script).to_bytes(2,'little')+script
    data=bytearray();offsets=[]
    for payload in (logic,b'\xff',view):
        offsets.append(len(data));data+=b'\x12\x34\0'+len(payload).to_bytes(2,'little')*2+payload
    return {'/game/vol.0':bytes(data),'/game/logDir':b'\xff'*3+offsets[0].to_bytes(3,'big'),
            '/game/picDir':b'\xff'*3+offsets[1].to_bytes(3,'big'),'/game/viewDir':offsets[2].to_bytes(3,'big')}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--module-root',type=Path)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='sierra-addpic-') as name:
        d,proc=start_cpu(idle_rom(Path(name)/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            count=0
            syms=symbols((args.module_root or Path(__file__).resolve().parents[1]/"objs")/"wbgame.map")
            for variable in (False,True):
                for priority in (0,3,15):
                    for x,y,control in ((20,30,4),(159,1,4),(20,48,0),(20,30,1),(20,30,2),(20,30,3)):
                        operands=[0,0,0,x,y,priority,control]
                        setup=[3,0,1,24,0,25,0,12,1]
                        if variable:
                            for index,value in enumerate(operands):setup += [3,200+index,value]
                            command=[123]+list(range(200,207))
                        else:command=[122]+operands
                        # Force background restoration by drawing then erasing a
                        # separate animated object after the static decoration.
                        script=bytes(setup+command+[33,1,41,1,0,37,1,40,60,54,1,15,35,1,36,1,26,134,1,0])
                        view=bytes([0,0,2,0,0,9,0,9,0,1,3,0,4,3,0x1f,0x12,0xf1,0x21,0,0x31,0x43,0,0x51,0])
                        files=assets(script,view)
                        error,frame,state=exercise(d,files,module='wbgame',module_root=args.module_root,base=0xa000,
                            database=0x0000,window=0x8000,blocks=None,multiple=True,firstblock=0x10,frame_capture=True,capture=True)
                        assert not error,(variable,priority,x,y,error)
                        assert state['vmflags'][1]==1,'static decoration overwrote ego-hidden flag'
                        expected=bytearray([1])*76800
                        expected[8*320:176*320]=bytes([16])*(168*320)
                        cx=min(x,156);cy=max(y,2)
                        combined=bytearray([0x4f])*26880
                        if priority != 3:
                            for rownum,row in enumerate(ROWS):
                                for col,color in enumerate(row):
                                    if color is not None:
                                        address=(cy-2+rownum+8)*320+(cx+col)*2
                                        expected[address:address+2]=bytes([color+1])*2
                                        combined[(cy-2+rownum)*160+cx+col]=(priority or (4 if cy<48 else cy//12+1))*16+color
                        assert frame==expected,(variable,priority,x,y,next((i for i,(a,b) in enumerate(zip(frame,expected)) if a!=b),None))
                        if control <= 3:
                            height=min(3,cy+1 if cy<48 else (cy-48)%12+1)
                            for py in range(cy-height+1,cy+1):
                                for px in range(cx,cx+4):
                                    if py in (cy-height+1,cy) or px in (cx,cx+3):
                                        at=py*160+px
                                        combined[at]=control*16+(combined[at]&15)
                        first=int.from_bytes(d.read(0x0000+syms['picturefirst'],2),'big')
                        actual=bytearray()
                        for page in range(4):
                            d.write(0xffac,bytes([first+page]))
                            actual+=d.read(0x8000,8192)
                        d.write(0xffac,b'\x04')
                        assert actual[:26880]==combined,(variable,priority,x,y,control,'combined priority/color mismatch',[(i%160,i//160,a,b) for i,(a,b) in enumerate(zip(actual,combined)) if a!=b][:12])
                        count+=1
            for operands in ([0,0,0,20,168,15,4],[0,0,0,20,30,16,4],
                             [0,0,0,20,30,15,16],[0,2,0,20,30,15,4],[0,0,1,20,30,15,4]):
                script=bytes([3,0,1,24,0,25,0,122]+list(operands)+[134,1,0])
                error,_=exercise(d,assets(script,view),module='wbgame',module_root=args.module_root,base=0xa000,
                    database=0x0000,window=0x8000,blocks=None,multiple=True,firstblock=0x10)
                assert error,(operands,error)
            # A bounded replay log must report overflow before painting.
            script=bytes([3,0,1,24,0,25,0,142,1,122,0,0,0,20,30,15,4,134,1,0])
            error,_=exercise(d,assets(script,view),module='wbgame',module_root=args.module_root,base=0xa000,
                database=0x0000,window=0x8000,blocks=None,multiple=True,firstblock=0x10)
            assert error==207,error
            print(f'PASS: {count} immediate/variable static cel draws, default/hidden/fixed priority, clipping, persistent background and preserved ego flag')
        finally:
            d.s.close();proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)

if __name__=='__main__':main()
