#!/usr/bin/env python3
"""Compare real owner condition traversal and observable predicate call order."""
from itertools import product
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_wbres import idle_rom,start_cpu

ROOT=Path(__file__).resolve().parents[1]


def compile_module(source,image):
    subprocess.run(['lwasm.orig','--6809','--format=os9','--no-warn=ifp1',
        '--pragma=pcaspcr,nosymbolcase,condundefzero',
        '-I'+str(ROOT/'kingsquest1'),'-I'+str(ROOT/'objs'),
        '-I'+str(ROOT.parent.parent/'nitros9/defs'),
        '--map='+str(image)+'.map','-o'+str(image),str(source)],check=True)
    return image.read_bytes(),symbols(Path(str(image)+'.map'))


def main():
    cases=[]
    expr=bytes([252,1,0,0,1,1,0,252,252,253,1,2,0,1,3,0,252])
    for values in product((False,True),repeat=4):
        trace=[]
        def call(index):trace.append(index);return values[index]
        expected=(call(0) or call(1)) and ((not call(2)) or call(3))
        cases.append((expr,dict(enumerate(values)),expected,trace))
    said=bytes([14,2,255,254,253,252])
    cases += [(bytes([1,0,0])+said+bytes([13]),{0:False,14:True,13:True},False,[0]),
              (bytes([252,1,0,0])+said+bytes([253,13,252,1,1,0]),{0:True,1:True,14:True,13:True},True,[0,1]),
              (bytes([252,1,0,0])+said+bytes([252]),{0:False,14:True},True,[0,14]),
              (bytes([253,253,1,0,0]),{0:True},True,[0]),
              (bytes([252,13,14,0,252]),{13:False,14:False},False,[13,14])]
    with tempfile.TemporaryDirectory(prefix='sierra-condition-flow-') as tmp:
        tmp=Path(tmp)
        coco,cs=compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
        native,ns=compile_module(ROOT/'tests/logic-harness.asm',tmp/'vmtest')
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            for owner,code,syms,bases in [('CoCo',coco,cs,(0x8000,0x9000)),('native',native,ns,(0xe000,0xd000))]:
                for base in bases:
                    d.write(base,code)
                    for expression,values,expected,wanted_trace in cases:
                        script=bytes([255])+expression+bytes([255,3,0,3,250,99,0])
                        d.write(0x2000,b'\0\0'+script+b'GUARD');trace=[]
                        if owner=='CoCo':
                            entry=base+syms['ExecScriptIf'];callback=base+syms['EvalExpr']
                            stop=base+syms['ExecScriptLoop']
                            d.regs(pc=entry,s=0x1dee,dp=0,y=0x2003,cc=0x50)
                            d.write(0x1df0,b'END')
                        else:
                            private=0x8000
                            d.write(private,bytes(syms['size'])+b'END')
                            for field,value in [('scriptbase',0x2000),('vmip',2),('vmend',len(script)+2)]:
                                d.write(private+syms[field],value.to_bytes(2,'big'))
                            entry=base+syms['start'];callback=base+syms['VmEvaluateTest'];stop=base+syms['finish']
                            d.regs(pc=entry,s=0xc000,dp=private>>8,u=private,cc=0x50)
                        d.breakpoint(callback);d.breakpoint(stop)
                        for _ in range(100):
                            d.call('c');r=d.regs()
                            if r['pc']==stop:break
                            assert r['pc']==callback,r
                            if owner=='CoCo':
                                opcode=r['a'];cursor=r['y']
                                count={1:2,13:0}.get(opcode)
                                if opcode==14:count=1+2*d.read(cursor,1)[0]
                                key=d.read(cursor,1)[0] if opcode==1 else opcode
                            else:
                                opcode=d.read(private+syms['vmopcode'],1)[0]
                                key=d.read(private+syms['vmarguments'],1)[0] if opcode==1 else opcode
                            trace.append(key);answer=int(values[key])
                            ret=int.from_bytes(d.read(r['s'],2),'big')
                            if owner=='CoCo':d.regs(pc=ret,s=r['s']+2,y=cursor+count,a=answer)
                            else:d.regs(pc=ret,s=r['s']+2,b=answer,cc=r['cc']&0xfe)
                        else:raise AssertionError('condition did not finish')
                        d.breakpoint(callback,False);d.breakpoint(stop,False)
                        assert trace==wanted_trace,(owner,expression,trace,wanted_trace)
                        if owner=='CoCo':
                            body=0x2000+2+len(script)-4
                            assert r['y']==body+(0 if expected else 3),(owner,expression,r,expected)
                            assert r['s']==0x1dee and d.read(0x1df0,3)==b'END'
                        else:
                            assert not r['cc']&1
                            assert d.read(private+syms['vmvariables']+250,1)==bytes([99 if expected else 0])
                            assert r['s']==0xc000 and d.read(private+syms['size'],3)==b'END'
                        assert d.read(0x2000+2+len(script),5)==b'GUARD'
                        assert d.read(base,len(code))==code
            print('PASS: shared short-circuit traversal in both real owners; all 16 mixed AND/OR/NOT combinations, exact predicate call order, skipped said/key callbacks, control bytes inside operands, relocation, branch targets, stack balance and immutable code')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
