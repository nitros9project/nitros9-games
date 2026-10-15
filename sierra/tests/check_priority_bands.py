#!/usr/bin/env python3
"""Compare actual CoCo/native priority arithmetic and native band boundaries."""
import argparse
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_instances import symbols
from check_wbres import exercise, idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def priorities(base):
    divisor = (168-base)*168//10
    return bytes(4 if y < base else min(15,5+(y-base)*168//divisor) for y in range(168))


def check_sorting(d):
    from check_add_to_picture import assets
    view=bytes([0,0,1,0,0,7,0,2,5,0,72,0])
    for color in (1,2): view+=bytes([1,32,15])+bytes([(color<<4)|1,0])*32
    for base,fixed_y,auto_y in ((80,100,85),(None,80,55)):
        setup=([174,base] if base is not None else [])+[3,0,1,24,0,25,0,
            33,0,41,0,0,37,0,20,fixed_y,54,0,5,35,0,
            33,1,41,1,0,47,1,1,37,1,20,auto_y,35,1,26,134,1,0]
        error,frame=exercise(d,assets(bytes(setup),view),module='wbgame',base=0xa000,
                            database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,frame_capture=True)
        assert not error,('fixed priority sort',base,error)
        wanted=bytearray([1])*76800;wanted[8*320:176*320]=bytes([16])*(168*320)
        for baseline,color in ((fixed_y,2),(auto_y,3)):
            for row in range(baseline-31,baseline+1):
                start=(row+8)*320+40;wanted[start:start+2]=bytes([color])*2
        assert frame==wanted,('fixed-priority projection order',base,
            next((i for i,(a,b) in enumerate(zip(frame,wanted)) if a!=b),None))
    print('PASS: actual default/custom fixed-priority projection sorts overlapping sprites like CoCo')


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--sort-only",action="store_true");args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='sierra-priority-') as name:
        tmp = Path(name)
        if not args.sort_only: coco, cs = compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
        game = (ROOT/'objs/wbgame').read_bytes(); gs = symbols(ROOT/'objs/wbgame.map')
        helper = (ROOT/'objs/wbstate').read_bytes(); hs = symbols(ROOT/'objs/wbstate.map')
        d,proc = start_cpu(idle_rom(tmp/'idle.rom'),timeout=1800)
        try:
            d.write(0xffdf,b'\0'); d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\1'); d.write(0xffa8,bytes(range(8)))
            if args.sort_only:
                check_sorting(d)
                return
            d.write(0x8000,coco); d.breakpoint(0x7e00)
            for base in range(168):
                d.write(0x7400,bytes([base])); d.write(0x05ed,b'G'+bytes(168)+b'H')
                d.write(0x5f60,b'\x7e\0STACK')
                d.regs(pc=0x8000+cs['SetPriBase'],s=0x5f60,x=0x05ee,y=0x7400,dp=0,cc=0x51)
                d.call('c'); r=d.regs()
                assert r['pc']==0x7e00 and r['s']==0x5f62
                assert d.read(0x05ed,170)==b'G'+priorities(base)+b'H',('CoCo',base)
                assert d.read(0x5f62,5)==b'STACK'
            d.breakpoint(0x7e00,False); d.breakpoint(0x9000)
            d.write(0,bytes(gs['size'])); d.write(0xa000,game); d.write(0x6000,helper)
            d.write(gs['screenentry'],(0x6000+hs['AuxScreenCommand']).to_bytes(2,'big'))
            obj=gs['vmobjects']; count=0
            for base in range(168):
                d.write(gs['vmarguments'],bytes([base])); d.write(0x5f60,b'\x90\0STACK')
                d.regs(pc=0x6000+hs['AuxPrioritySet'],s=0x5f60,u=0,dp=0,cc=0x51)
                d.call('c'); r=d.regs()
                assert r['pc']==0x9000 and r['s']==0x5f62 and not r['cc']&1
                assert d.read(gs['prioritybase'],3)==bytes([base])+((168-base)*168//10).to_bytes(2,'big')
                table=priorities(base)
                rows=set(range(168)) if base in (0,1,47,48,49,166,167) else {0,base,167}
                for y in range(1,168):
                    if table[y]!=table[y-1]: rows.update((y-1,y))
                for row in sorted(rows):
                    record=bytearray([0xa5]*43); record[4]=row;record[0x26]=0x40
                    d.write(obj,record); d.write(0x5f60,b'\x90\0STACK')
                    d.regs(pc=0xa000+gs['SpriteCalculatePriority'],s=0x5f60,x=0x7777,y=0x5555,u=obj,dp=0,cc=0x51)
                    d.call('c');r=d.regs();record[0x24]=table[row]
                    assert (r['pc'],r['s'],r['x'],r['y'],r['u'])==(0x9000,0x5f62,0x7777,0x5555,obj)
                    assert d.read(obj,43)==record,('native',base,row)
                    assert (r['a'],r['b'])==(table[row],row)
                    assert d.read(0x5f62,5)==b'STACK'
                    boundary=row
                    while boundary and table[boundary-1]==table[row]:boundary-=1
                    stack=b'\x90\0\x77\x77\x55\x55'+obj.to_bytes(2,'big')+b'STACK'
                    d.write(0x5f60,stack)
                    d.regs(pc=0x6000+hs['AuxPriorityHeight'],s=0x5f60,u=0,dp=0,cc=0x51)
                    d.call('c');r=d.regs()
                    assert r['pc']==0x9000 and r['s']==0x5f62 and r['b']==row-boundary,('height',base,row,r)
                    assert d.read(0x5f68,5)==b'STACK'
                    count+=1
            before=d.read(gs['prioritybase'],3)
            for base in range(168,256):
                d.write(gs['vmarguments'],bytes([base]));d.write(0x5f60,b'\x90\0STACK')
                d.regs(pc=0x6000+hs['AuxPrioritySet'],s=0x5f60,u=0,dp=0,cc=0x50)
                d.call('c');r=d.regs()
                assert r['cc']&1 and r['b']==gs['E$BMode'] and d.read(gs['prioritybase'],3)==before
            d.write(gs['priorityscale'],bytes(2))
            for row in range(168):
                record=bytearray(43);record[4]=row;record[0x26]=0x40
                d.write(obj,record);d.write(0x5f60,b'\x90\0STACK')
                d.regs(pc=0xa000+gs['SpriteCalculatePriority'],s=0x5f60,x=0x7777,y=0x5555,u=obj,dp=0,cc=0x51)
                d.call('c');r=d.regs();record[0x24]=priorities(48)[row]
                assert d.read(obj,43)==record and r['x']==0x7777 and r['y']==0x5555 and r['u']==obj
            for base in (None,*range(168)):
                scale=0 if base is None else (168-base)*168//10
                d.write(gs['prioritybase'],bytes([base or 0])+scale.to_bytes(2,'big'))
                for priority in range(16):
                    record=bytearray(43);record[4]=167;record[0x24]=priority;record[0x26]=4
                    d.write(obj,record);d.write(0x5f60,b'\x90\0STACK')
                    d.regs(pc=0xa000+gs['SpriteCalculatePriority'],s=0x5f60,x=0x7777,y=0x5555,u=obj,dp=0,cc=0x51)
                    d.call('c');r=d.regs()
                    projected=(48+12*(priority-5))&255 if base is None else next((row for row,value in enumerate(priorities(base)) if value>=priority),168)
                    assert d.read(obj,43)==record,'fixed priority changed'
                    assert (r['a'],r['b'])==(priority,projected),('projection',base,priority,r)
                    assert (r['x'],r['y'],r['u'],r['s'])==(0x7777,0x5555,obj,0x5f62)
                    assert d.read(0x5f62,5)==b'STACK'
            assert d.read(0xa000,len(game))==game and d.read(0x6000,len(helper))==helper
            d.breakpoint(0x9000,False)
            check_sorting(d)
            print(f'PASS: all 168 CoCo tables, {count} native custom priorities/band heights, all transitions, all default rows, default-equivalent base 48, fixed priority, invalid bases, stack/register guards and immutable native code')
        finally:
            d.s.close();proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)

if __name__=='__main__':main()
