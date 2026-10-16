#!/usr/bin/env python3
"""Run the common executor with real CoCo/native command and condition handlers."""
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_wbres import idle_rom,start_cpu

ROOT=Path(__file__).resolve().parents[1]
CASES=[
    (b'\0',{},set()),
    # Operand bytes resemble return/branch opcodes: both must be consumed.
    *[(bytes([155,a,b,3,250,42,0]),{250:42},set())
      for a,b in ((0,0),(254,255),(255,254),(3,255),(255,3))],
    # CoCo PC-compatibility stubs and zero-operand no-ops. Operand bytes
    # deliberately resemble VM return/branch/condition markers. A command
    # after each stub proves exact consumption through both real executors.
    *[(bytes([3,249,73,12,221,opcode,*operands,4,250,249,0]),
       {249:73,250:73},{221})
      for opcode,count in ((144,1),(175,1),(179,4),(180,2))
      for operands in (bytes(count),bytes([255])*count,bytes([254])*count,
                       bytes((3+i)%256 for i in range(count)),
                       bytes((255-i)%256 for i in range(count)))],
    *[(bytes([3,249,73,12,221,opcode,4,250,249,0]),
       {249:73,250:73},{221})
      for opcode in (127,163,164,173,176,178,181)],
    # AGI bytecode can have two legal decodings of the same bytes. This
    # models Manhunter I logic 159's jump into a condition's skip operand.
    *[(prefix+bytes.fromhex('ff 01 00 00 ff 03 00 fe 05 00 ff 01 00 01 ff 08 00 84 03 fa 2a 00 00 00 00 03 fa 49 00'),wanted,set())
      for prefix,wanted in ((b'',{250:42}),(bytes([3,0,1]),{0:1,250:42}),
                            (bytes([3,0,2]),{0:2,250:73}))],
    # Predicate zero is CoCo's constant-true catalog entry, not return.
    (bytes.fromhex('ff 00 ff 03 00 03 fa 2a 00'),{250:42},set()),
    (bytes.fromhex('ff fd 00 ff 03 00 03 fa 2a 00'),{},set()),
    (bytes.fromhex('ff fc 00 fd 00 fc ff 03 00 03 fa 2a 00'),{250:42},set()),
    (bytes.fromhex('ff 01 00 01 00 ff 03 00 03 fa 2a 00'),{},set()),
    (bytes.fromhex('ff 01 00 00 00 ff 03 00 03 fa 2a 00'),{250:42},set()),
    (bytes([3,255,250,1,255,2,0,3,0,7,5,0,250,7,0,2,12,255,14,255,12,200,0]),{0:255,255:251},{200}),
    (bytes([254,3,0,3,0,99,3,0,42,0]),{0:42},set()),
    (bytes([3,0,0,1,0,255,3,0,3,255,3,0,254,244,255,0]),{0:3},set()),
    (bytes([3,0,7,3,1,8,12,200,255,252,1,0,8,1,0,7,252,253,1,1,9,255,3,0,3,250,99,0]),{0:7,1:8,250:99},{200}),
    (bytes([3,0,7,255,1,0,8,1,1,255,255,3,0,3,250,99,0]),{0:7},set()),
    (bytes([12,255,255,253,253,7,255,255,3,0,3,250,99,0]),{250:99},{255}),
    (bytes([3,0,7,255,252,1,0,8,1,0,9,252,255,3,0,3,250,99,0]),{0:7},set()),
]


def compile_module(source,target,defines=(),listing=False):
    subprocess.run(['lwasm.orig','--6809','--format=os9','--no-warn=ifp1',
        '--pragma=pcaspcr,nosymbolcase,condundefzero','-I'+str(ROOT/'kingsquest1'),
        '-I'+str(ROOT/'objs'),'-I'+str(ROOT.parent.parent/'nitros9/defs'),
        '--map='+str(target)+'.map',*(['--list='+str(target)+'.list'] if listing else []),'-o'+str(target),*['-D'+value for value in defines],str(source)],check=True)
    return target.read_bytes(),symbols(Path(str(target)+'.map'))


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-executor-') as tmp:
        tmp=Path(tmp);coco,cs=compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
        native,ns=compile_module(ROOT/'objs/sierra.asm',tmp/'native',defines=('WILDBITS=1',))
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            for owner,code,syms,bases in [('CoCo',coco,cs,(0x8000,0x9000)),('native',native,ns,(0x9000,0xa000))]:
                for base in bases:
                    d.write(base,code)
                    if owner=='CoCo':
                        d.write(0x2e,base.to_bytes(2,'big'))
                        d.run(base+syms['PatchCmdTable']);d.run(base+syms['FixupEvalTbl'])
                    initialized_code=d.read(base,len(code))
                    for script,wanted,flagset in CASES:
                        variables=bytearray(256)
                        for index,value in wanted.items():variables[index]=value
                        if owner=='CoCo':
                            d.write(0x0431,bytes(256));d.write(0x01ae,bytes(32));d.write(0x68,b'\0')
                            d.write(0x62,b'\x30\x00');d.write(0x3000,bytes(10));d.write(0x3008,b'\x20\x00')
                            d.write(0x2000,script+b'GUARD')
                            entry=base+syms['ExecLogicScript'];private=0
                            page_callback=base+syms['SetLogicPage'];d.breakpoint(page_callback)
                        else:
                            private=0x1000;d.write(private,bytes(syms['size'])+b'GUARD')
                            for field,value in [('resourcebase',private),('assetmapbase',0x7a00),('vmip',2),('vmend',len(script)+2)]:
                                d.write(private+syms[field],value.to_bytes(2,'big'))
                            d.write(private+syms['assetmapped'],b'\1')
                            d.write(0x7a00,b'\0\0'+script+b'GUARD');entry=base+syms['ExecuteLogic']
                        d.write(0x7ef0,b'\x7e\x00STACK');d.breakpoint(0x7e00)
                        d.regs(pc=entry,s=0x7ef0,dp=private>>8,u=private,cc=0x50)
                        pages=0
                        for _ in range(10):
                            d.call('c');r=d.regs()
                            if r['pc']==0x7e00:break
                            assert owner=='CoCo' and r['pc']==page_callback,r
                            # Only the physical page service is substituted;
                            # table dispatch, argument reads and handlers run.
                            pages+=1;ret=int.from_bytes(d.read(r['s'],2),'big')
                            d.regs(pc=ret,s=r['s']+2)
                        else:raise AssertionError('executor did not return')
                        d.breakpoint(0x7e00,False)
                        assert r['s']==0x7ef2 and d.read(0x7ef2,5)==b'STACK'
                        if owner=='CoCo':
                            d.breakpoint(page_callback,False);assert pages==1
                            actual=d.read(0x0431,256);packed=d.read(0x01ae,32)
                            flags={index for index in range(256) if packed[index>>3]&(128>>(index&7))}
                            assert d.read(0x2000+len(script),5)==b'GUARD'
                        else:
                            assert not r['cc']&1 and r['b']==0
                            actual=d.read(private+syms['vmvariables'],256)
                            flags={index for index,value in enumerate(d.read(private+syms['vmflags'],256)) if value}
                            assert d.read(private+syms['size'],5)==b'GUARD'
                            assert d.read(0x7a02+len(script),5)==b'GUARD'
                        assert actual==variables,(owner,script,actual[:8],variables[:8])
                        assert flags==flagset,(owner,script,flags,flagset)
                        assert d.read(base,len(code))==initialized_code
            print('PASS: common complete executor in both real owners at two code bases; actual command/test table dispatch and mapped native byte fetch, all CoCo PC stubs/zero-operand no-ops and fixed-origin set.upper.left operand consumption, saturating/wrapping arithmetic, packed/byte flags, forward/backward jumps, bounded loop, mixed condition groups, return/frame guards and post-initialization code immutability')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
