#!/usr/bin/env python3
"""Check CoCo get.string setup and native get.string editing/commit behavior."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module, ROOT
from check_wbres import exercise, idle_rom, start_cpu


def logic_file(script):
    text=b'Name?\0';key=b'Avis Durgan'
    messages=bytes([1])+(4+len(text)).to_bytes(2,'little')+bytes([4,0])+bytes(
        value^key[index%len(key)] for index,value in enumerate(text))
    logic=len(script).to_bytes(2,'little')+script+messages
    return {'/game/logDir':b'\0\0\0'+bytes(3),
            '/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic}


def check_coco(d,tmp):
    code,syms=compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
    base=0x8000;args=0x3000;stop=0x7e00;edit=base+syms['EditString']
    patched=('PushRowCol','InputEditOn','MsgTextSetup',
             'PrintFmtStrToScr','PopRowCol')
    callbacks={base+syms[name] for name in patched}
    getmsg=base+syms['GetMsgPtr']
    for row,col,maximum in ((7,9,5),(24,39,39)):
        d.write(base,code)
        for address in callbacks:d.write(address,b'\x39') # RTS external UI stubs
        d.write(0x0251,b'X'*480);d.write(0x05b9,b'\0');d.write(0x0040,b'\xaa\xbb')
        d.write(args,bytes([3,1,row,col,maximum])+b'GUARD')
        d.write(0x7ef0,b'\x7e\0STACK')
        d.breakpoint(stop);d.breakpoint(edit);d.breakpoint(getmsg)
        d.regs(pc=base+syms['cmd_get_string'],s=0x7ef0,y=args,u=0,dp=0,cc=0x50)
        d.call('c');r=d.regs()
        assert r['pc']==getmsg and r['b']==1,(row,col,maximum,'prompt',r)
        ret=int.from_bytes(d.read(r['s'],2),'big')
        d.breakpoint(getmsg,False);d.regs(pc=ret,s=r['s']+2,u=0x5000)
        d.call('c');r=d.regs()
        wanted=min(maximum+1,40)
        assert r['pc']==edit and r['x']==0x0251+3*40 and r['b']==wanted,(row,col,maximum,r)
        assert d.read(0x0251+3*40,1)==b'\0'
        assert d.read(args+5,5)==b'GUARD' and r['y']==args+5
        assert d.read(0x0040,2)==(bytes([row,col]) if row<24 else b'\xaa\xbb')
        # Skip the interactive editor after checking its real entry parameters.
        ret=int.from_bytes(d.read(r['s'],2),'big')
        d.breakpoint(edit,False);d.regs(pc=ret,s=r['s']+2)
        d.call('c');r=d.regs()
        assert r['pc']==stop and r['s']==0x7ef2 and d.read(0x7ef2,5)==b'STACK'
        d.breakpoint(stop,False)
    print('PASS: actual CoCo cmd_get_string selects the prompt, forwards slot and bounded length to EditString, clears the target, advances five operands, and returns with a balanced stack')


def check_native(d):
    cases=[('enter',b'BOb\r',5,b'BOb'),
           ('backspace',b'BObx\x08!\r',8,b'BOb!'),
           ('length bound',b'ABCDE\r',3,b'ABC'),
           ('escape',b'\x1b',5,None)]
    for label,keys,maximum,expected in cases:
        args=bytes([3,1,5,3,maximum])
        script=bytes([115])+args+bytes([134,1,0])
        initial=b'old\0'+bytes(36)
        if expected is None: initial=b'keep\0'+bytes(35)
        original_slot=b'keep\0'+bytes(35)
        def seed(cpu,regs,syms):
            cpu.write(syms['parserline'],initial)
            cpu.write(syms['parserlength'],bytes([3 if expected is not None else 4]))
            cpu.write(syms['vmstrings']+120,original_slot)
            return False
        prompt=[]
        def capture_prompt(cpu,regs,syms):
            if cpu.read(syms['dialogactive'],1)==b'\1':
                pointer=int.from_bytes(cpu.read(syms['textpointer'],2),'big')
                prompt.append(cpu.read(pointer,40))
            return False
        key_schedule={cycle:(bytes([value]),0) for cycle,value in enumerate(keys,5)}
        error,output,state=exercise(d,logic_file(script),arguments=b'/game 0\r',module='wbgame',
            base=0xa000,database=0,window=0x8000,blocks=None,multiple=True,
            firstblock=0x10,capture=True,keyboard_by_cycle=key_schedule,
            breakpoint_hooks={'GameGetInput':seed,'GameTextPresent':capture_prompt},os_call_limit=50000)
        assert not error and not output,(label,error,output)
        slot=state['vmstrings'][120:160]
        if expected is None:assert slot==b'\0eep\0'+bytes(35),(label,slot)
        else:assert slot.startswith(expected+b'\0'),(label,slot,expected)
        restored=initial.split(b'\0')[0]
        assert state['dialoginputmode']==b'\0'
        assert any(b'Name?' in screen for screen in prompt),(label,len(prompt),
            [screen[:300] for screen in prompt])
        # The input editor restores the command line it suspended around the
        # modal prompt, including its explicit length.
        assert state['parserline'][:len(restored)+1]==restored+b'\0',(label,state['parserline'],restored,state['parserlength'])
        print(f'PASS: native get.string {label}',flush=True)


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-get-string-') as name:
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
