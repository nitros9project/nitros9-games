#!/usr/bin/env python3
"""Run the shared said matcher through real CoCo and native owner adapters."""
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_wbres import idle_rom, start_cpu
ROOT = Path(__file__).resolve().parents[1]
CASES = [([2,4],[2,4],True), ([2],[2,4],False), ([2,4],[2],False),
         ([3],[2],False), ([1,4],[2,4],True), ([1],[2,4],False),
         ([9999],[2,4],True), ([2,9999],[2],True),
         ([9999,3],[2,4],True), ([2],[],False),
         ([65535,256],[65535,256],True), ([256],[1],False)]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-said-') as folder:
        folder=Path(folder); image=folder/'mnln'
        subprocess.run(['lwasm.orig','--6809','--format=os9','--no-warn=ifp1',
                        '--pragma=pcaspcr,nosymbolcase,condundefzero',
                        '-I'+str(ROOT/'kingsquest1'), '-I'+str(ROOT/'objs'),
                        '-I'+str(ROOT.parent.parent/'nitros9/defs'),
                        '--map='+str(image)+'.map','-o'+str(image),
                        str(ROOT/'objs/mnln.asm')],check=True)
        owners=[('CoCo',image.read_bytes(),symbols(Path(str(image)+'.map')),0x8000),
                ('native',(ROOT/'wildbits/wbgame').read_bytes(),symbols(ROOT/'wildbits/wbgame.map'),0xa000)]
        d, emulator=start_cpu(idle_rom(folder/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0'); d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01'); d.write(0xffa8,bytes(range(8)))
            for owner,code,syms,base in owners:
                d.write(base,code)
                # Exhaustive byte folding also protects non-ASCII dictionary bytes.
                for value in range(256):
                    result=d.run(base+syms['ToLower' if owner=='CoCo' else 'ParserLower'],
                                 a=value,b=0x5a,x=0x2000,y=0x3000,u=0x1234)
                    wanted=value+32 if 65<=value<=90 else value
                    assert result['a']==wanted and result['b']==0x5a
                    assert (result['x'],result['y'],result['u'])==(0x2000,0x3000,0x1234)
                for expected,actual,match in CASES:
                    operands=b''.join(n.to_bytes(2,'little') for n in expected)
                    words=b''.join(n.to_bytes(2,'big') for n in actual)
                    for enabled,accepted in [(True,False),(False,False),(True,True)]:
                        if owner=='CoCo':
                            d.write(0x2000,bytes([len(expected)])+operands+b'GUARD')
                            d.write(0x0194,words)
                            d.write(0x015a,bytes([len(actual)]))
                            d.write(0x01ae,bytes([(0x20 if enabled else 0)|(8 if accepted else 0)]))
                            entry=base+syms['TestSaid']
                            result=d.run(entry,y=0x2000)
                            got=result['a']
                            assert result['y']==0x2001+len(operands)
                            flag=bool(d.read(0x01ae,1)[0]&8)
                            assert d.read(0x2001+len(operands),5)==b'GUARD'
                        else:
                            d.write(syms['resourcebase'],b'\0\0')
                            d.write(syms['vmarguments'],operands+b'GUARD')
                            d.write(syms['vmargcount'],bytes([len(operands)]))
                            d.write(syms['parserids'],words)
                            d.write(syms['parsercount'],bytes([len(actual)]))
                            d.write(syms['vmflags']+2,bytes([enabled]))
                            d.write(syms['vmflags']+4,bytes([accepted]))
                            entry=base+syms['ParserSaid']
                            result=d.run(entry,u=0)
                            assert not result['cc']&1
                            got=result['b'];flag=bool(d.read(syms['vmflags']+4,1)[0])
                            assert d.read(syms['vmarguments']+len(operands),5)==b'GUARD'
                        wanted=match and enabled and not accepted
                        assert got==wanted,(owner,expected,actual,enabled,accepted,got)
                        assert flag==(accepted or wanted)
                        if wanted:
                            result=d.run(entry,**({'y':0x2000} if owner=='CoCo' else {'u':0}))
                            assert result['a' if owner=='CoCo' else 'b']==0,'repeated acceptance'
            print('PASS: exhaustive ASCII folding, shared said matching, little/big-endian IDs, both wildcards, mismatch/length edges, input gates, cursor guards and single acceptance in both engines')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__=='__main__': main()
