#!/usr/bin/env python3
"""Probe CoCo init.joy's prompt, button, Escape and disable paths."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom, start_cpu


def callback(counter):
    return bytes([0x7c, counter >> 8, counter & 255, 0x39])  # INC extended; RTS


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-init-joy-') as name:
        tmp=Path(name)
        code,syms=compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=300)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01')
            d.write(0xffa8,bytes(range(8)))
            stop=0x7e00; counters=(0x7000,0x7001,0x7002,0x7003,0x7004)
            for base in (0x8000,0x9000):
                d.write(base,code)
                d.breakpoint(stop)
                for label,initial,button,key,newstate,expected,expected99 in (
                    ('enable with button',0,True,0,1,(1,1,1,1,1),0),
                    ('escape cancels enable',0,False,0x1b,0,(1,1,0,1,1),0),
                    ('disable without prompt',1,False,0,0,(0,0,0,0,1),0xff)):
                    print('Checking CoCo joystick:',label,flush=True)
                    d.write(0x7000,b'\0'*5)
                    d.write(0x0098,bytes([initial]));d.write(0x0099,b'\xff')
                    d.write(0x0541,b'\0');d.write(0x7ef0,b'\x7e\0STACK')
                    # Keep the command body real; count its platform boundaries.
                    d.write(base+syms['message_box_draw'],callback(counters[0]))
                    if button:
                        getkey=bytes([0x7c,counters[1]>>8,counters[1]&255])+bytes.fromhex('8600c601f7054139')
                    else:
                        getkey=bytes([0x7c,counters[1]>>8,counters[1]&255])+bytes.fromhex('861b7f054139')
                    d.write(base+syms['GetKeyEvent'],getkey)
                    d.write(base+syms['ReadJoyButton'],bytes(
                        [0x7c,counters[2]>>8,counters[2]&255,0x7f,0x05,0x41,0x39]))
                    d.write(base+syms['cmd_close_window'],callback(counters[3]))
                    d.write(base+syms['events_clear'],callback(counters[4]))
                    d.regs(pc=base+syms['cmd_init_joy'],s=0x7ef0,dp=0,cc=0x50)
                    d.call('c');r=d.regs()
                    assert r['pc']==stop and r['s']==0x7ef2,(label,r)
                    assert d.read(0x0098,1)==bytes([newstate]),(label,d.read(0x0098,1))
                    assert d.read(0x0099,1)==bytes([expected99])
                    got=tuple(d.read(address,1)[0] for address in counters)
                    assert got==expected,(base,label,got,expected)
                    assert d.read(0x7ef2,5)==b'STACK'
                d.breakpoint(stop,False)
            print('PASS: actual CoCo cmd_init_joy at two code bases prompts on enable, accepts button, cancels on Escape, skips prompt when disabling, clears events, and balances stack')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except Exception:emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
