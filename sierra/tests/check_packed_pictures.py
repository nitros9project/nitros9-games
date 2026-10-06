#!/usr/bin/env python3
"""Compare bounded native packed-picture loading with CoCo and a nibble oracle."""
from pathlib import Path
import argparse
import subprocess
import tempfile
from export_picture import unpack_picture
from check_instances import symbols
from check_lzw import exercise_coco
from check_wbres import exercise, fixture, idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]

def files(data, length):
    return fixture(data, header=b'\x12\x34\x81'+length.to_bytes(2,'little')+len(data).to_bytes(2,'little'))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--fixtures-only',action='store_true')
    args=parser.parse_args()
    coco = (ROOT/'kingsquest1/mnln').read_bytes()
    syms = symbols(ROOT/'kingsquest1/mnln.map')
    with tempfile.TemporaryDirectory(prefix='sierra-packed-') as temp:
        d, proc = start_cpu(idle_rom(Path(temp)/'idle.rom'),timeout=1800)
        try:
            d.write(0xffdf,b'\0'); d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01'); d.write(0xffa8,bytes(range(8)))
            count = 0
            for game in ([] if args.fixtures_only else sorted(ROOT.iterdir())):
                directory = game/'picDir'
                if not directory.exists(): continue
                entries = directory.read_bytes()
                for i in range(0,len(entries)-2,3):
                    e = entries[i:i+3]
                    if e == b'\xff'*3: continue
                    volume = e[0] >> 4
                    offset = ((e[0]&15)<<16)|(e[1]<<8)|e[2]
                    source = (game/f'vol.{volume}').read_bytes()
                    h = source[offset:offset+7]
                    if not h[2]&128: continue
                    size = int.from_bytes(h[3:5],'little')
                    stored = int.from_bytes(h[5:7],'little')
                    data = source[offset+7:offset+7+stored]
                    expected = unpack_picture(data)
                    assert len(expected)==size,(game.name,i//3,size,len(expected))
                    assert exercise_coco(d,coco,syms,data,size,entry='RenderPicStrip')==expected
                    assert exercise(d,files(data,size),module='wbasset',resource_kind=1,blocks=(size+8191)//8192)==(0,expected),(game.name,i//3)
                    count += 1
                    print(f'Checked {count}: {game.name} picture {i//3}',flush=True)
            # F0/F2 color nibbles exercise both byte alignments and padded ends.
            for data,expected in [(b'\xff',b'\xff'),(b'\xf0\x2f\xf0',b'\xf0\x02\xff'),
                                  (b'\xf0\x2f\x23\xff',b'\xf0\x02\xf2\x03\xff')]:
                for base,database,window in [(0xe000,0x2000,0x8000),(0xd000,0x1000,0xa000)]:
                    assert exercise(d,files(data,len(expected)),module='wbasset',resource_kind=1,
                                    blocks=1,base=base,database=database,window=window)==(0,expected)
            for data,size in [(b'\xf0\x2f',3),(b'\xff',2),(b'\xff\x00',1),(b'\xf0\x2f\xf0',2)]:
                error,output=exercise(d,files(data,size),module='wbasset',resource_kind=1,blocks=1)
                assert error and not output,(data,size)
            for kind in (0,2,3):
                wrong=files(b'\xff',1)
                suffix=('logDir','viewDir','sndDir')[{0:0,2:1,3:2}[kind]]
                wrong['/game/'+suffix]=wrong.pop('/game/picDir')
                error,output=exercise(d,wrong,module='wbasset',resource_kind=kind,blocks=1)
                assert error and not output,kind
            for options in (dict(zero_read=True),dict(map_failure=1),dict(unmap_error=True),
                            dict(allocation_error=True),dict(write_error=True)):
                error,output=exercise(d,files(b'\xf0\x2f\xf0',3),module='wbasset',resource_kind=1,blocks=1,**options)
                assert error and not output,options
            print(f'PASS: {count} actual packed pictures match CoCo and independent oracle; bounded malformed inputs rejected')
        finally:
            d.s.close();proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: proc.kill();proc.wait(timeout=5)

if __name__=='__main__': main()
