#!/usr/bin/env python3
"""Compare public draw/erase state transitions in the actual CoCo and native handlers."""
from pathlib import Path
import tempfile

from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
OBJECT_BYTES = 64 * 43
INITIAL_FLAGS = (0, 0x10, 0x01, 0x11, 0x81, 0x91)
ANIMATION_FLAGS = (0, 0x10, 0x25, 0xff)


def stub_coco_platform_services(image, syms):
    """Leave draw/erase command bodies real; bypass only render/MMU services."""
    spans = ((syms['DrawObjHelper'], syms['CmdEraseImpl']),
             (syms['EraseObjHelper'], syms['EraseObjDone']+4))
    helpers = ('FindObjPos', 'BlitListDraw', 'SetWaterRange', 'SetLandRange')
    for start, end in spans:
        for target_name in helpers:
            target = syms[target_name]
            for site in range(start, min(end, len(image)-2)):
                displacement = target-(site+3)
                if (image[site] == 0x17
                        and image[site+1:site+3] == displacement.to_bytes(2,'big',signed=True)):
                    image[site:site+3] = b'\x12\x12\x12'
        for site in range(start, min(end-2, len(image)-2)):
            if image[site:site+3] == b'\xbd\x07\x01':
                image[site:site+3] = b'\x12\x12\x12'


def expected_record(record, opcode, owner):
    wanted = bytearray(record)
    status = wanted[0x26]
    if opcode == 35:  # draw: already-drawn is a true no-op
        if not status & 0x01:
            wanted[0x26] = status | 0x11
            wanted[0x25] &= 0xef
            if owner == 'CoCo':
                wanted[0x12:0x14] = record[0x10:0x12]
                wanted[0x14:0x16] = record[0x08:0x0a]
                wanted[0x1a:0x1c] = record[0x03:0x05]
    elif status & 0x01:  # erase: an undrawn object is a true no-op
        wanted[0x26] = status & 0xfe
    return wanted


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-object-visibility-') as name:
        temp = Path(name)
        coco, cs = compile_module(ROOT/'objs/mnln.asm', temp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm', temp/'wbgame',
                                    defines=('WILDBITS=1',))
        d, emulator = start_cpu(idle_rom(temp/'idle.rom'), timeout=900)
        calls = 0
        try:
            d.write(0xffdf,b'\0'); d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01'); d.write(0xffa8,bytes(range(8)))
            d.breakpoint(0x7e00)
            for owner, code, syms, bases in (
                    ('CoCo',coco,cs,(0x8000,0x9000)),
                    ('native',native,ns,(0x9000,0xa000))):
                private = 0 if owner=='CoCo' else 0x1000
                objects = 0x4000 if owner=='CoCo' else private+syms['vmobjects']
                args = 0x2000 if owner=='CoCo' else private+syms['vmarguments']
                if private:
                    d.write(private,bytes(syms['size'])+b'GUARD')
                    d.write(private+syms['resourcebase'],private.to_bytes(2,'big'))
                else:
                    d.write(0x30,objects.to_bytes(2,'big'))
                    d.write(0x32,(objects+OBJECT_BYTES).to_bytes(2,'big'))
                for base in bases:
                    image=bytearray(code)
                    if owner=='CoCo': stub_coco_platform_services(image,syms)
                    d.write(base,image)
                    if private:
                        d.breakpoint(base+syms['GameComposeScene'])
                    for opcode in (35,36):
                        for index in (0,63):
                            for status in INITIAL_FLAGS:
                                for animation in ANIMATION_FLAGS:
                                    records=bytearray((i*31+5)&255 for i in range(OBJECT_BYTES))
                                    offset=index*43
                                    records[offset+0x10:offset+0x12]=b'\x60\x00'
                                    records[offset+0x25]=animation
                                    records[offset+0x26]=status
                                    d.write(objects-1,b'G'+records+b'H')
                                    expected=bytearray(records)
                                    expected[offset:offset+43]=expected_record(records[offset:offset+43],opcode,owner)
                                    operand=bytes((index,))
                                    d.write(args,operand+b'ARGS')
                                    if private:
                                        d.write(private+syms['vmopcode'],bytes((opcode,)))
                                        start=base+syms['GameObjectVisibility']
                                        dp=private>>8
                                    else:
                                        start=base+syms['CmdDrawImpl' if opcode==35 else 'CmdEraseImpl']
                                        dp=0
                                    d.write(0x7ef0,b'\x7e\0STACK')
                                    d.regs(pc=start,s=0x7ef0,y=args,u=private,dp=dp,cc=0x50)
                                    d.call('c')
                                    regs=d.regs()
                                    if private and regs['pc']==base+syms['GameComposeScene']:
                                        ret=int.from_bytes(d.read(regs['s'],2),'big')
                                        d.regs(pc=ret,s=regs['s']+2,cc=regs['cc']&0xfe,b=0)
                                        regs=d.regs()
                                    assert regs['pc']==0x7e00 and regs['s']==0x7ef2,(owner,opcode,index,status,animation,regs)
                                    assert d.read(objects-1,OBJECT_BYTES+2)==b'G'+expected+b'H',(owner,opcode,index,status,animation)
                                    assert d.read(args,5)==operand+b'ARGS'
                                    assert d.read(0x7ef2,5)==b'STACK'
                                    if private:
                                        assert not regs['cc']&1 and regs['b']==0
                                        assert d.read(private+syms['size'],5)==b'GUARD'
                                    else:
                                        assert regs['y']==args+1
                                    calls+=1
                    if private: d.breakpoint(base+syms['GameComposeScene'],False)
                    assert d.read(base,len(code))==image
            print(f'PASS: {calls} actual CoCo/native draw/erase calls; drawn/undrawn idempotence, stopped-visible objects, single-advance flag clearing, first/last object slots, all other record bytes, operand/stack/private guards and two code addresses')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except Exception: emulator.kill(); emulator.wait(timeout=5)


if __name__=='__main__': main()
