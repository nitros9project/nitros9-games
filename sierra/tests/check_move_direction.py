#!/usr/bin/env python3
"""Execute shared target direction and its native stepping adapter."""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom, start_cpu


def direction(cx, cy, tx, ty):
    dx = (tx > cx) - (tx < cx)
    dy = (ty > cy) - (ty < cy)
    return {(0,0):0, (0,-1):1, (1,-1):2, (1,0):3, (1,1):4,
            (0,1):5, (-1,1):6, (-1,0):7, (-1,-1):8}[dx,dy]


def main():
    cases = []
    for field in range(4):
        for value in range(256):
            case = [85,171,171,85]
            case[field] = value
            cases.append(tuple(case))
    edges = (0,1,127,128,254,255)
    cases += [(cx,cy,tx,ty) for cx in edges for cy in edges
              for tx in edges for ty in edges]
    with tempfile.TemporaryDirectory(prefix='sierra-direction-') as name:
        tmp=Path(name)
        coco,cs=compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
        native,ns=compile_module(ROOT/'objs/sierra.asm',tmp/'native',defines=('WILDBITS=1',))
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=900)
        calls=0
        try:
            d.write(0xffdf,b'\0'); d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01'); d.write(0xffa8,bytes(range(8)))
            d.breakpoint(0x7e00)
            for owner,code,syms,bases in [('CoCo',coco,cs,(0x8000,0x9000)),
                                         ('native',native,ns,(0x9000,0xa000))]:
                private=0 if owner=='CoCo' else 0x1000
                for base in bases:
                    d.write(base,code)
                    if private:
                        state=bytearray(syms['size'])
                        state[syms['resourcebase']:syms['resourcebase']+2]=b'\x10\x00'
                        d.write(private,state+b'GUARD')
                    for cx,cy,tx,ty in cases:
                        record=bytearray(range(43))
                        record[3:5]=bytes([cx,cy]); record[0x27:0x29]=bytes([tx,ty])
                        d.write(0x6fff,b'G'+record+b'H')
                        # Production native wrapper supplies these arguments itself.
                        args=b'' if private else bytes([cx,cy,tx,ty,0,1])
                        d.write(0x7ef0,b'\x7e\x00'+args+b'STACK')
                        d.regs(pc=base+syms['MotionMoveDirection' if private else 'CalcMoveDir'],
                               s=0x7ef0,u=0x7000,x=private or 0x4567,y=0x7777,
                               dp=private>>8,cc=0x50)
                        d.call('c'); regs=d.regs()
                        expected=direction(cx,cy,tx,ty)
                        assert regs['pc']==0x7e00 and regs['s']==0x7ef2
                        assert regs['u']==0x7000 and regs['y']==0x7777
                        if private:
                            assert regs['x']==private and regs['b']==expected
                            record[0x21]=expected
                        else:
                            assert regs['a']==expected
                        assert d.read(0x6fff,45)==b'G'+record+b'H',(owner,(cx,cy,tx,ty),regs)
                        assert d.read(0x7ef2+len(args),5)==b'STACK'
                        calls+=1
                    # Test the post-commit gate separately from arrival's
                    # state mutation. CoCo reaches this gate on an edge hit;
                    # native reaches it after each accepted position.
                    arrival = base+syms['TargetReached']
                    continuation = base+syms['MotionNextObject' if private else 'UpdateObjFlags']
                    d.breakpoint(arrival); d.breakpoint(continuation)
                    for mode in range(256):
                        for tx,ty in ((85,171),(84,171),(85,170),(84,170)):
                            record=bytearray(range(43))
                            record[3:5]=bytes([85,171])
                            record[0x27:0x29]=bytes([tx,ty]); record[0x22]=mode
                            d.write(0x6fff,b'G'+record+b'H')
                            d.regs(pc=base+syms['MotionCheckDestination' if private else 'CheckMoveTarget'],
                                   s=0x7ef0,u=0x7000,x=private or 0x4567,y=0x7777,
                                   dp=private>>8,cc=0x50)
                            d.call('c'); regs=d.regs()
                            completes=mode==3 and (not private or (tx,ty)==(85,171))
                            assert regs['pc']==(arrival if completes else continuation),(owner,mode,tx,ty,regs)
                            assert regs['s']==0x7ef0-(2 if completes else 0)
                            assert regs['u']==0x7000 and regs['x']==(private or 0x4567) and regs['y']==0x7777
                            assert d.read(0x6fff,45)==b'G'+record+b'H'
                    d.breakpoint(arrival,False); d.breakpoint(continuation,False)
                    if private:
                        assert d.read(private,syms['size'])==state
                        assert d.read(private+syms['size'],5)==b'GUARD'
                    assert d.read(base,len(code))==code
            print(f'PASS: {calls} actual CoCo/native direction calls at two addresses; '
                  'all coordinate bytes, signed-boundary edges, every direction, '
                  'native context/records, all destination motion modes and coordinate-match cases, private state, stack guards and immutable code')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__=='__main__':
    main()
