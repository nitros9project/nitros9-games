#!/usr/bin/env python3
"""Execute matching CoCo/native object flag commands and check whole records."""
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
# Independent expectations for the public AGI commands, not generated from rules.
RULES = [(45,'CmdFixLoop',0x25,255,32), (46,'CmdReleaseLoop',0x25,223,0),
         (56,'cmd_release_priority',0x26,251,0),
         (61,'cmd_ignore_horizon',0x26,255,8), (62,'cmd_observe_horizon',0x26,247,0),
         (64,'cmd_obj_on_water',0x25,255,1), (65,'cmd_obj_on_land',0x25,255,8),
         (66,'cmd_obj_on_anything',0x25,246,0), (67,'CmdIgnoreObjects',0x25,255,2),
         (68,'CmdObserveObjects',0x25,253,0), (70,'CmdStopCycling',0x26,223,0),
         (71,'CmdStartCycling',0x26,255,32), (88,'CmdIgnoreBlocks',0x26,255,2),
         (89,'CmdObserveBlocks',0x26,253,0)]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-object-flags-') as folder:
        folder = Path(folder)
        image = folder / 'mnln'
        subprocess.run(['lwasm.orig','--6809','--format=os9','--no-warn=ifp1',
                        '--pragma=pcaspcr,nosymbolcase,condundefzero',
                        '-I'+str(ROOT/'kingsquest1'), '-I'+str(ROOT/'objs'),
                        '-I'+str(ROOT.parent.parent/'nitros9/defs'),
                        '--map='+str(image)+'.map', '-o'+str(image),
                        str(ROOT/'objs/mnln.asm')], check=True)
        coco, cs = image.read_bytes(), symbols(Path(str(image)+'.map'))
        native = (ROOT/'wildbits/wbgame').read_bytes()
        ns = symbols(ROOT/'wildbits/wbgame.map')
        d, emulator = start_cpu(idle_rom(folder/'idle.rom'), timeout=900)
        try:
            d.write(0xffdf,b'\0'); d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01'); d.write(0xffa8,bytes(range(8)))
            for owner, code, syms, base, objects in [
                ('CoCo',coco,cs,0x8000,0x4000),
                ('native',native,ns,0xa000,ns['vmobjects'])]:
                d.write(base,code)
                if owner == 'CoCo':
                    d.write(0x30,objects.to_bytes(2,'big'))
                else:
                    d.write(ns['resourcebase'],b'\0\0')
                for opcode, name, field, mask, bits in RULES:
                    for index in (0,63):
                        for value in (0,255,0x55,0xaa):
                            before = bytearray((i*37+11)&255 for i in range(64*43))
                            before[index*43+field] = value
                            d.write(objects-1,b'G'+before+b'H')
                            expected = bytearray(before)
                            expected[index*43+field] = (value & mask) | bits
                            if owner == 'CoCo':
                                d.write(0x2000,bytes([index]))
                                result = d.run(base+syms[name],y=0x2000)
                                assert result['y']==0x2001
                            else:
                                d.write(ns['vmarguments'],bytes([index]))
                                d.write(ns['vmopcode'],bytes([opcode]))
                                result = d.run(base+ns['ObjectFlagCommand'],u=0)
                                assert not result['cc']&1 and result['b']==0, result
                            assert d.read(objects-1,len(before)+2)==b'G'+expected+b'H', (owner,opcode,index,value)
                if owner == 'native':
                    d.write(ns['vmarguments'],b'\x40')
                    d.write(ns['vmopcode'],b'\x3d')
                    assert d.run(base+ns['ObjectFlagCommand'],u=0)['cc']&1
                    d.write(ns['vmopcode'],b'\xfc')
                    assert d.run(base+ns['ObjectFlagCommand'],u=0)['cc']&1
            print('PASS: 14 CoCo/native object flag commands, first/last records, bit preservation, record guards and bounded native errors')
        finally:
            d.s.close(); emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__=='__main__':
    main()
