#!/usr/bin/env python3
"""Exercise the actual CoCo get.num command and native modal input route."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module, ROOT
from check_wbres import exercise, idle_rom, start_cpu


def logic_file(script):
    text=b'Number?\0';key=b'Avis Durgan'
    messages=bytes([1])+(4+len(text)).to_bytes(2,'little')+bytes([4,0])+bytes(
        value^key[index%len(key)] for index,value in enumerate(text))
    logic=len(script).to_bytes(2,'little')+script+messages
    return {'/game/logDir':b'\0\0\0'+bytes(3),
            '/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic}


def check_coco(d,tmp):
    code,syms=compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
    base=0x8000;args=0x3000;stop=0x7e00;edit=base+syms['EditString']
    getmsg=base+syms['GetMsgPtr']
    d.write(base,code)
    for name in ('InputEditOn','MsgTextSetup','PrintFmtStrToScr','InputRedraw'):
        d.write(base+syms[name],b'\x39')
    # GetMsgPtr's text lookup is outside this command's numeric-input check.
    d.write(getmsg,b'\xce\x60\x00\x39')  # LDU #$6000; RTS
    d.breakpoint(stop);d.breakpoint(edit)
    for entered,expected in ((b'',0),(b'0',0),(b'255',255),(b'256',0),(b'999',231)):
        d.write(0x0431,bytes(256))
        d.write(args,bytes([1,220])+b'GUARD')
        d.write(0x7ef0,b'\x7e\0STACK')
        d.regs(pc=base+syms['CmdObjStatus'],s=0x7ef0,y=args,u=0,dp=0,cc=0x50)
        d.call('c');r=d.regs()
        assert r['pc']==edit and r['b']==4 and r['y']==args+1,(entered,r)
        d.write(r['x'],entered+b'\0'+bytes(4-len(entered)))
        ret=int.from_bytes(d.read(r['s'],2),'big')
        d.breakpoint(edit,False);d.regs(pc=ret,s=r['s']+2)
        d.call('c');r=d.regs()
        assert r['pc']==stop and r['s']==0x7ef2 and r['y']==args+2,(entered,r)
        assert d.read(0x0431+220,1)==bytes([expected]),(entered,d.read(0x0431+220,1))
        assert d.read(args+2,5)==b'GUARD' and d.read(0x7ef2,5)==b'STACK'
        d.breakpoint(edit)
    d.breakpoint(edit,False);d.breakpoint(stop,False)
    print('PASS: actual CoCo CmdObjStatus prompts through EditString, converts blank/0/255/256/999, writes the requested variable, consumes two operands and balances the stack')


def check_native(d):
    for keys,expected in ((b'\r',0),(b'0\r',0),(b'255\r',255),(b'256\r',0),(b'999\r',231)):
        script=bytes([118,1,220,134,1,0])
        error,output,state=exercise(d,logic_file(script),arguments=b'/game 0\r',module='wbgame',
            base=0xa000,database=0,window=0x8000,blocks=None,multiple=True,
            firstblock=0x10,capture=True,keyboard_by_cycle={cycle:(bytes([value]),0)
                for cycle,value in enumerate(keys,5)},os_call_limit=50000)
        assert not error and not output,(keys,error,output)
        assert state['vmvariables'][220]==expected,(keys,state['vmvariables'][220],expected)
        assert state['dialoginputmode']==b'\0'
    print('PASS: actual Wild Bits get.num opcode 118 stores the same values for blank/0/255/256/999 and exits modal input cleanly')


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-get-number-') as name:
        tmp=Path(name)
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01')
            d.write(0xffa8,bytes(range(8)))
            check_coco(d,tmp)
            check_native(d)
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except Exception:emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
