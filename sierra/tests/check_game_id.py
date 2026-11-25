#!/usr/bin/env python3
"""Compare CoCo and Wild Bits set.game.id message-copy semantics."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module
from check_wbres import exercise, idle_rom, start_cpu

ROOT=Path(__file__).resolve().parents[1]
CASES=(b'',b'A',b'KQ1',b'1234567',b'12345678',b'LONGERID',bytes([0xC1,0xC2,0xC3,0]))


def logic_resource(message):
    script=bytes([143,1,0])
    plain=message+b'\0'
    message_section=(bytes([1])+(4+len(plain)).to_bytes(2,'little')+
                     bytes([4,0])+bytes(c^b'Avis Durgan'[i%11]
                                         for i,c in enumerate(plain)))
    return len(script).to_bytes(2,'little')+script+message_section


def invoke(d,entry,stop,**registers):
    stack=0x7ef0;d.write(stack,stop.to_bytes(2,'big')+b'STACK')
    d.breakpoint(stop)
    state={'pc':entry,'s':stack,'dp':0,'cc':0x50};state.update(registers)
    d.regs(**state);d.call('c');result=d.regs()
    assert result['pc']==stop and result['s']==stack+2,result
    assert d.read(stack+2,5)==b'STACK'
    d.breakpoint(stop,False)
    return result


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-game-id-') as directory:
        tmp=Path(directory)
        coco,cs=compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=300)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01')
            d.write(0xffa8,bytes(range(8)))
            for base in (0x8000,0x9000):
                d.write(base,coco)
                for text in CASES:
                    node,table=0x3000,0x3100
                    slot=bytearray(12);slot[2]=0;slot[3]=1;slot[10:12]=table.to_bytes(2,'big')
                    d.write(node,slot)
                    d.write(table,b'\0\0\x04\0'+text+b'\0')
                    d.write(0x0062,node.to_bytes(2,'big'))
                    d.write(0x01ce,bytes(8))
                    d.write(0x6000,b'\x01GUARD')
                    result=invoke(d,base+cs['cmd_set_game_id'],0x7e00,y=0x6000)
                    expected=text[:7].ljust(8,b'\0')
                    assert d.read(0x01ce,8)==expected,('CoCo',text,d.read(0x01ce,8),expected)
                    assert result['y']==0x6001 and d.read(0x6001,5)==b'GUARD'
                    assert d.read(base,len(coco))==coco

            for text in CASES:
                payload=logic_resource(text)
                size=len(payload).to_bytes(2,'little')
                files={'/game/logDir':b'\0\0\0',
                       '/game/vol.0':b'\x12\x34\0'+size+size+payload}
                error,output,state=exercise(d,files,arguments=b'/game 0\r',module='wbexec',
                    module_root=ROOT/'objs',base=0xa000,database=0x0000,blocks=None,
                    multiple=True,capture=True)
                expected=text[:7].ljust(8,b'\0')
                assert not error and len(output)==512,(text,error,len(output))
                assert state['vmgameid']==expected,('Wild Bits',text,state['vmgameid'],expected)
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except Exception:emulator.kill();emulator.wait(timeout=5)
    print(f'PASS: actual CoCo cmd_set_game_id and loaded Wild Bits opcode 143 match empty, short, exact-seven, truncated, and high-bit message IDs across {len(CASES)} cases; CoCo operand, stack and code guards checked at two code bases')


if __name__=='__main__':main()
