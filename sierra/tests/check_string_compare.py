#!/usr/bin/env python3
"""Run AGI compare.strings in both owners and through native bytecode dispatch."""
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_wbres import exercise, idle_rom, start_cpu
from check_wbplay import fixture

ROOT = Path(__file__).resolve().parents[1]
# This set intentionally differs from the sentence tokenizer's punctuation.
IGNORED = b" .,;:'!-"


def normalized(value):
    return bytes(byte+32 if 65<=byte<=90 else byte for byte in value if byte not in IGNORED)


def main():
    cases=[(b'',b''),(b'A',b'a'),(b'a',b'ab'),(b'ab',b'a'),(b'',b'a'),
           (b'LOOK, tree!',b'looktree'),(b"'lo-o.k;!'",b'look'),
           (b'A'*39,b'a'*39),(b'A'*38+b'B',b'a'*39),
           (b'`look`',b'look'),(b'"look"',b'look'),(b'look?',b'look'),
           (b'look(tree)',b'looktree'),(b'look\t tree',b'looktree'),
           (b'\x80\xffA',b'\x80\xffa'),(b'\xff',b'\xfe')]
    for byte in range(1,256):
        cases.append((b'A'+bytes([byte])+b'B',b'ab'))
    with tempfile.TemporaryDirectory(prefix='sierra-string-compare-') as folder:
        folder=Path(folder); image=folder/'mnln'
        subprocess.run(['lwasm.orig','--6809','--format=os9','--no-warn=ifp1',
            '--pragma=pcaspcr,nosymbolcase,condundefzero',
            '-I'+str(ROOT/'kingsquest1'),'-I'+str(ROOT/'objs'),
            '-I'+str(ROOT.parent.parent/'nitros9/defs'),
            '--map='+str(image)+'.map','-o'+str(image),str(ROOT/'objs/mnln.asm')],check=True)
        owners=[('CoCo',image.read_bytes(),symbols(Path(str(image)+'.map'))),
                ('native',(ROOT/'objs/wbgame').read_bytes(),symbols(ROOT/'objs/wbgame.map'))]
        d,emulator=start_cpu(idle_rom(folder/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0'); d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01'); d.write(0xffa8,bytes(range(8)))
            for owner,code,syms in owners:
                for base,private in ((0x8000,0),(0x9000,0x1000)):
                    d.write(base,code)
                    table=0x0251 if owner=='CoCo' else private+syms['vmstrings']
                    for left,right in cases:
                        strings=bytearray(480)
                        strings[:len(left)]=left
                        strings[440:440+len(right)]=right
                        d.write(table-1,b'G'+strings+b'H')
                        if owner=='CoCo':
                            operand=0x3000
                            d.write(operand,b'\0\x0bEND')
                            entry=base+syms['TestStrings']
                        else:
                            operand=private+syms['vmarguments']
                            d.write(operand,b'\0\x0bEND')
                            d.write(private+syms['resourcebase'],private.to_bytes(2,'big'))
                            d.write(private+syms['vmopcode'],b'\x0f')
                            entry=base+syms['VmPlatformTest']
                        d.write(0x1df0,b'\x1d\x00');d.breakpoint(0x1d00)
                        d.regs(pc=entry,s=0x1df0,dp=private>>8,u=private,y=operand,cc=0x50)
                        d.call('c');result=d.regs();d.breakpoint(0x1d00,False)
                        assert result['pc']==0x1d00
                        assert result['a' if owner=='CoCo' else 'b']==int(normalized(left)==normalized(right)),(owner,left,right)
                        if owner=='CoCo':assert result['y']==operand+2
                        else:assert not result['cc']&1 and result['u']==private
                        assert d.read(table-1,482)==b'G'+strings+b'H'
                        assert d.read(operand+2,3)==b'END'
                        assert d.read(base,len(code))==code
                    if owner=='native':
                        for operands in (b'\x0c\0',b'\0\x0c',b'\xff\x0b',b'\0\xff'):
                            d.write(operand,operands)
                            d.write(0x1df0,b'\x1d\x00');d.breakpoint(0x1d00)
                            d.regs(pc=entry,s=0x1df0,dp=private>>8,u=private,cc=0x50)
                            d.call('c');result=d.regs();d.breakpoint(0x1d00,False)
                            assert result['cc']&1 and result['b']==syms['E$IllArg']
                            assert d.read(table-1,482)==b'G'+strings+b'H'
            # Actual condition argument decoding and IF branches, loaded strings.
            for left,right in [(b'LOOK, tree!',b'looktree'),(b'look?',b'look')]:
                script=bytes([114,0,1,114,11,2,255,15,0,11,255,2,0,1,220,134,1,0])
                error,output,state=exercise(d,fixture(script,message=[left,right]),
                    module='wbgame',base=0xa000,database=0x1000,window=0x8000,
                    blocks=None,multiple=True,firstblock=0x10,capture=True)
                assert not error and not output,(error,output)
                assert state['vmvariables'][220]==int(normalized(left)==normalized(right))
            print('PASS: common compare.strings in both real owners, 255 byte classes, distinct punctuation rules, empty/prefix/39-byte strings, first/last slots, relocation, guards, native index errors and real IF dispatch')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
