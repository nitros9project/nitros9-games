#!/usr/bin/env python3
"""Compare real inventory commands across entry/room-byte storage layouts."""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = [(92,'cmd_get'),(93,'cmd_get_v'),(94,'cmd_drop'),
            (95,'cmd_put'),(96,'cmd_put_v'),(97,'cmd_get_room_v')]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-inventory-') as name:
        tmp=Path(name)
        coco,cs=compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
        native,ns=compile_module(ROOT/'objs/sierra.asm',tmp/'wbgame',defines=('WILDBITS=1',))
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            for owner,code,syms,bases in [('CoCo',coco,cs,(0x8000,0x9000)),
                                         ('native',native,ns,(0x9000,0xa000))]:
                for base in bases:
                    d.write(base,code)
                    private=0 if owner=='CoCo' else 0x1000
                    variables=0x0431 if not private else private+syms['vmvariables']
                    args=0x2000 if not private else private+syms['vmarguments']
                    items=0x4000 if not private else private+syms['inventoryrooms']
                    stride=3 if not private else 1
                    roomfield=2 if not private else 0
                    if private:
                        d.write(private,bytes(syms['size'])+b'GUARD')
                        d.write(private+syms['resourcebase'],private.to_bytes(2,'big'))
                        d.write(private+syms['inventoryloaded'],b'\1')
                        d.write(private+syms['inventorycount'],b'\1\0')
                    else:
                        d.write(0x38,items.to_bytes(2,'big'))
                        d.write(0x3c,(items+768).to_bytes(2,'big'))
                    d.breakpoint(0x7e00)
                    for opcode,label in COMMANDS:
                        entry=base+syms[label if not private else 'InventoryCommand']
                        for item in (0,255):
                            for variable in (0,255):
                                for oldroom in (0,37,255):
                                    for newroom in (0,128,255):
                                        before=bytearray((i*17+5)&255 for i in range(256*stride))
                                        at=item*stride+roomfield;before[at]=oldroom
                                        wanted=bytearray(before)
                                        values=bytearray(b'\x33'*256)
                                        if opcode in (93,96,97):values[variable]=item
                                        operands=[variable if opcode in (93,96,97) else item]
                                        if opcode in (95,96):
                                            roomvariable=255-variable if opcode==96 else variable
                                            values[roomvariable]=newroom;operands.append(roomvariable)
                                        elif opcode==97:operands.append(variable)
                                        expectedvars=bytearray(values)
                                        if opcode in (92,93):wanted[at]=255
                                        elif opcode==94:wanted[at]=0
                                        elif opcode in (95,96):wanted[at]=newroom
                                        else:expectedvars[variable]=oldroom
                                        d.write(items,before);d.write(variables,values)
                                        d.write(args,bytes(operands)+b'ARGS')
                                        if private:
                                            d.write(private+syms['vmopcode'],bytes([opcode]))
                                            expectedprivate=bytearray(d.read(private,syms['size']))
                                            expectedprivate[syms['inventoryrooms']:syms['inventoryrooms']+256]=wanted
                                            expectedprivate[syms['vmvariables']:syms['vmvariables']+256]=expectedvars
                                        else:d.write(items-1,b'G');d.write(items+768,b'H')
                                        d.write(0x7ef0,b'\x7e\x00STACK')
                                        d.regs(pc=entry,s=0x7ef0,y=args,u=private,dp=private>>8,cc=0x50)
                                        d.call('c');r=d.regs()
                                        assert r['pc']==0x7e00 and r['s']==0x7ef2
                                        assert d.read(0x7ef2,5)==b'STACK'
                                        assert d.read(items,len(before))==wanted,(owner,opcode,item,variable,oldroom,newroom)
                                        assert d.read(variables,256)==expectedvars
                                        assert d.read(args+len(operands),4)==b'ARGS'
                                        if private:
                                            assert not r['cc']&1 and r['b']==0
                                            assert d.read(private,syms['size'])==expectedprivate
                                            assert d.read(private+syms['size'],5)==b'GUARD'
                                        else:
                                            assert r['y']==args+len(operands)
                                            assert d.read(items-1,1)==b'G' and d.read(items+768,1)==b'H'
                    for test,label in [(9,'TestHasObject'),(10,'TestObjectRoom')]:
                        entry=base+syms[label if not private else 'InventoryTest']
                        for item in (0,255):
                            for variable in (0,255):
                                for actualroom in (0,37,128,255):
                                    for expectedroom in (0,37,255):
                                        before=bytearray((i*17+5)&255 for i in range(256*stride))
                                        before[item*stride+roomfield]=actualroom
                                        values=bytearray(b'\x33'*256);values[variable]=expectedroom
                                        operands=bytes([item]) if test==9 else bytes([item,variable])
                                        d.write(items,before);d.write(variables,values)
                                        d.write(args,operands+b'ARGS')
                                        if private:
                                            d.write(private+syms['vmopcode'],bytes([test]))
                                            snapshot=d.read(private,syms['size'])
                                        d.write(0x7ef0,b'\x7e\x00STACK')
                                        d.regs(pc=entry,s=0x7ef0,y=args,u=private,dp=private>>8,cc=0x50)
                                        d.call('c');r=d.regs()
                                        wanted=int(actualroom==(255 if test==9 else expectedroom))
                                        assert r['pc']==0x7e00 and r['s']==0x7ef2
                                        assert d.read(0x7ef2,5)==b'STACK'
                                        assert r['b' if private else 'a']==wanted,(owner,test,item,variable,actualroom,expectedroom,r)
                                        assert d.read(items,len(before))==before and d.read(variables,256)==values
                                        assert d.read(args+len(operands),4)==b'ARGS'
                                        if private:
                                            assert not r['cc']&1 and d.read(private,syms['size'])==snapshot
                                        else:assert r['y']==args+len(operands)
                    if private:
                        # Item 255 is invalid when the loaded table has 255 entries.
                        d.write(private+syms['inventorycount'],b'\0\xff')
                        for opcode,_ in COMMANDS:
                            d.write(args,bytes([255,0]))
                            d.write(variables+255,b'\xff')
                            d.write(private+syms['vmopcode'],bytes([opcode]))
                            before=d.read(private,syms['size'])
                            d.write(0x7ef0,b'\x7e\x00STACK')
                            d.regs(pc=base+syms['InventoryCommand'],s=0x7ef0,u=private,dp=private>>8,cc=0x50)
                            d.call('c');r=d.regs()
                            assert r['pc']==0x7e00 and r['cc']&1 and r['s']==0x7ef2
                            assert d.read(private,syms['size'])==before
                        for test in (9,10):
                            d.write(args,bytes([255,0]));d.write(private+syms['vmopcode'],bytes([test]))
                            before=d.read(private,syms['size'])
                            d.write(0x7ef0,b'\x7e\x00STACK')
                            d.regs(pc=base+syms['InventoryTest'],s=0x7ef0,u=private,dp=private>>8,cc=0x50)
                            d.call('c');r=d.regs()
                            assert r['pc']==0x7e00 and r['cc']&1 and r['s']==0x7ef2
                            assert d.read(private,syms['size'])==before
                    assert d.read(base,len(code))==code
                    d.breakpoint(0x7e00,False)
            print('PASS: all six real inventory commands and both possession/room predicates in both owners at two load addresses; items/variables 0 and 255, room edges, variable-indirect items/rooms, aliased get.room.v, immutable CoCo name bytes, whole native private-state preservation, guards/stack/cursor and native bounds errors')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
