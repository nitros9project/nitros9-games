#!/usr/bin/env python3
"""Compare public load.logics commands when the requested logic is resident."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module
from check_wbres import exercise, idle_rom, start_cpu

ROOT=Path(__file__).resolve().parents[1]


def invoke(d,entry,stop,**registers):
    stack=0x7ef0
    d.write(stack,stop.to_bytes(2,'big')+b'STACK')
    d.breakpoint(stop)
    state={'pc':entry,'s':stack,'dp':0,'cc':0x50}
    state.update(registers)
    d.regs(**state);d.call('c');result=d.regs()
    assert result['pc']==stop and result['s']==stack+2,result
    assert d.read(stack+2,5)==b'STACK'
    d.breakpoint(stop,False)
    return result


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-load-logic-hit-') as directory:
        tmp=Path(directory)
        coco,cs=compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
        native,ns=compile_module(ROOT/'objs/sierra.asm',tmp/'wbgame',defines=('WILDBITS=1',))
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=300)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01')
            d.write(0xffa8,bytes(range(8)))
            stop=0x7e00;logic=42;node=0x3000;private=0x1000;dp=private>>8
            for base in (0x8000,0x9000):
                patched=bytearray(coco)
                patched[cs['LogicTableData']:cs['LogicTableData']+2]=node.to_bytes(2,'big')
                d.write(base,patched)
                d.write(node,bytes(2)+bytes([logic])+bytes(9))
                buffer=0x5000
                d.write(buffer,bytes(12)+b'GUARD')
                d.write(0x05af,buffer.to_bytes(2,'big'))
                d.write(0x0244,b'\0');d.write(0x0245,b'\x03');d.write(0x05b1,b'\x01')
                d.write(0x0057,b'\0\0');d.write(base+cs['ScriptWritePtr'],buffer.to_bytes(2,'big'))
                d.write(0x01ae,b'\0')
                for command,operands in (('cmd_load_logics',bytes([logic])),
                                         ('cmd_load_logics_v',bytes([77]))):
                    d.write(0x0431+77,bytes([logic]))
                    d.write(0x6100,operands+b'GUARD')
                    result=invoke(d,base+cs[command],stop,y=0x6100)
                    assert result['y']==0x6100+len(operands), (command,result)
                    assert d.read(0x6100+len(operands),5)==b'GUARD'
                    assert d.read(base+cs['LogicTableData'],2)==node.to_bytes(2,'big')
                assert d.read(buffer,4)==bytes([0,logic,0,logic]),('CoCo replay',d.read(buffer,4))
                assert d.read(0x0244,1)==b'\x02'
                expected_code=bytearray(patched)
                expected_code[cs['ScriptWritePtr']:cs['ScriptWritePtr']+2]=(buffer+4).to_bytes(2,'big')
                assert d.read(base,len(coco))==bytes(expected_code)

            for base in (0x8000,0xa000):
                d.write(base,native)
                d.write(private,bytes(ns['size'])+b'GUARD')
                d.write(private+ns['resourcebase'],private.to_bytes(2,'big'))
                d.write(private+ns['assetmapped'],b'\0')
                d.write(private+ns['replaylimit'],b'\x03')
                d.write(private+ns['replayused'],b'\0\0')
                d.write(private+ns['replaybuffer'],bytes(510)+b'GUARD')
                d.write(private+ns['vmcurrent'],b'\0')
                d.write(private+ns['vmip'],bytes.fromhex('0002'))
                cache=private+ns['vmcache']
                current=bytes([9,1])+bytes.fromhex('1234')+bytes([2,0])+bytes.fromhex('00400020')+bytes.fromhex('0002')
                resident=bytes([logic,1])+bytes.fromhex('5678')+bytes([1,0])+bytes.fromhex('01000100')+bytes.fromhex('0002')
                d.write(cache,current+resident+bytes(30*12))
                for command,arguments in (('VmCommandLoadLogic',bytes([logic])),
                                          ('VmCommandLoadLogicVariable',bytes([77]))):
                    d.write(private+ns['vmarguments'],arguments)
                    d.write(private+ns['vmvariables']+77,bytes([logic]))
                    result=invoke(d,base+ns[command],stop,dp=dp,u=private,y=0x6200)
                    assert result['b']==0 and not (result['cc']&1),(command,result)
                    assert d.read(private+ns['vmcurrent'],1)==b'\0'
                    assert d.read(private+ns['vmcache'],24)==current+resident
                    assert d.read(private+ns['assetfirst'],2)==bytes.fromhex('1234')
                    assert d.read(private+ns['assetblocks'],1)==b'\x02'
                    assert d.read(private+ns['resourcekind'],1)==b'\0'
                    assert d.read(private+ns['resourcelength'],2)==bytes.fromhex('0040')
                    assert d.read(private+ns['resourcestored'],2)==bytes.fromhex('0020')
                    assert d.read(private+ns['vmip'],2)==bytes.fromhex('0002')
                assert d.read(private+ns['replayused'],2)==b'\0\x04'
                assert d.read(private+ns['replaybuffer'],4)==bytes([0,logic,0,logic])
                assert d.read(private+ns['size'],5)==b'GUARD'
                assert d.read(base,len(native))==native

            # A real miss already records inside VmLoadLogic. Follow it with
            # a hit through the public opcode to prove the wrapper does not
            # append a duplicate record for the miss.
            scripts=(bytes([142,3,20,1,20,1,0]),b'\0')
            volume=bytearray();directory=bytearray()
            for script in scripts:
                directory.extend(len(volume).to_bytes(3,'big'))
                payload=len(script).to_bytes(2,'little')+script
                size=len(payload).to_bytes(2,'little')
                volume.extend(b'\x12\x34\0'+size+size+payload)
            error,output,state=exercise(d,{'/game/logDir':bytes(directory),
                '/game/vol.0':bytes(volume)},arguments=b'/game 0\r',module='wbexec',
                module_root=ROOT/'objs',base=0xa000,database=0x0000,
                blocks=None,multiple=True,capture=True)
            assert not error and len(output)==512,(error,len(output))
            assert state['replayused']==b'\0\x04',state['replayused']
            assert state['replaybuffer'][:4]==bytes([0,1,0,1]),state['replaybuffer'][:4]
            print('PASS: actual literal/variable CoCo and Wild Bits load.logics handlers find resident logic and match replay entries; actual native miss-then-hit loads record each request exactly once; caller context, cache links, stacks and guards pass at two code addresses')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except Exception:emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
