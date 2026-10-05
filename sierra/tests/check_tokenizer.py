#!/usr/bin/env python3
"""Execute both owner adapters for the shared sentence tokenizer on a 6809."""
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
DELIMITERS = b' ,.?!();:[]{}'
DROPPED = b"'`-\""


def reference(source, fold):
    words = bytearray()
    pending = False
    for byte in source:
        if byte in DELIMITERS:
            pending = bool(words)
        elif byte not in DROPPED:
            if pending:
                words.append(32)
                pending = False
            words.append(byte + 32 if fold and 65 <= byte <= 90 else byte)
    return bytes(words)


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-tokenizer-') as tmp:
        tmp = Path(tmp)
        module = tmp/'mnln'
        subprocess.run(['lwasm.orig','--6809','--format=os9','--no-warn=ifp1',
            '--pragma=pcaspcr,nosymbolcase,condundefzero',
            '-I'+str(ROOT/'kingsquest1'),'-I'+str(ROOT/'objs'),
            '-I'+str(ROOT.parent.parent/'nitros9/defs'),
            '--map='+str(module)+'.map','-o'+str(module),str(ROOT/'objs/mnln.asm')],check=True)
        owners = [('CoCo',module.read_bytes(),symbols(Path(str(module)+'.map'))),
                  ('native',(ROOT/'objs/wbgame').read_bytes(),symbols(ROOT/'objs/wbgame.map'))]
        cases = [b'', b'LOOK', b'  LOOK, at  tree! ', b"'`--\"", b' ,.?!();:[]{}',
                 b"  lo-'`\"ok,,  at- - - tree; ", b'A'*39, b' '*39,
                 b'a'+b'.'*37+b'b', b'a'+b'-'*37+b'b']
        # Every non-NUL byte as a leading, interior and trailing character.
        for byte in range(1,256):
            cases.extend([bytes([byte])+b'x', b'x'+bytes([byte])+b'y', b'x'+bytes([byte])])
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0'); d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01'); d.write(0xffa8,bytes(range(8)))
            for owner,code,syms in owners:
                for base,private in ((0x8000,0),(0x9000,0x1000)):
                    d.write(base,code)
                    for source in cases:
                        wanted = reference(source,owner=='native')
                        if owner=='CoCo':
                            input_address=0x3000
                            output_address=base+syms['SortObjsBuf']
                            entry=base+syms['TokenizeString']
                        else:
                            input_address=output_address=private+syms['parserline']
                            d.write(private+syms['resourcebase'],private.to_bytes(2,'big'))
                            entry=base+syms['ParserNormalize']
                        d.write(input_address-1,b'G'+source+b'\0'+b'H'*(40-len(source)))
                        if owner=='CoCo': d.write(output_address,b'Z'*40+b'END')
                        d.write(0x1df0,b'\x1d\x00')
                        d.breakpoint(0x1d00)
                        d.regs(pc=entry,s=0x1df0,dp=private>>8,u=input_address,cc=0x50)
                        d.call('c')
                        assert d.regs()['pc']==0x1d00
                        d.breakpoint(0x1d00,False)
                        assert d.read(output_address,len(wanted)+1)==wanted+b'\0',(owner,source,wanted)
                        assert d.read(input_address-1,1)==b'G'
                        if owner=='CoCo':
                            assert d.read(input_address,len(source)+1)==source+b'\0'
                            assert d.read(output_address+40,3)==b'END'
                        else:
                            assert d.read(private+syms['parserlength'],1)==bytes([len(wanted)])
                            assert d.read(output_address+40,1)==b'H'
                            assert d.read(base,len(code))==code
            print('PASS: shared tokenizer in both real owners, all 255 non-NUL bytes in three positions, delimiter/drop/trim rules, empty and 39-byte inputs, in-place guards, native lengths, relocation and native immutable code')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__=='__main__': main()
