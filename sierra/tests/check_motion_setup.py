#!/usr/bin/env python3
"""Compare actual move.obj/.v setup before the owner direction callback."""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-motion-setup-') as name:
        tmp = Path(name)
        coco, cs = compile_module(ROOT/'objs/mnln.asm', tmp/'mnln')
        native, ns = compile_module(ROOT/'objs/wbgame.asm', tmp/'wbgame')
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=900)
        try:
            d.write(0xffdf,b'\0'); d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01'); d.write(0xffa8,bytes(range(8)))
            for owner, code, syms, bases in [
                ('CoCo',coco,cs,(0x8000,0x9000)),
                ('native',native,ns,(0x9000,0xa000))]:
                for base in bases:
                    d.write(base,code)
                    private = 0 if owner=='CoCo' else 0x1000
                    objects = 0x4000 if not private else private+syms['vmobjects']
                    variables = 0x0431 if not private else private+syms['vmvariables']
                    flagbase = 0x01ae if not private else private+syms['vmflags']
                    flagbytes = 32 if not private else 256
                    control = 0x0250 if not private else private+syms['vmplayercontrol']
                    args = 0x2000 if not private else private+syms['vmarguments']
                    if private:
                        d.write(private,bytes(syms['size']))
                        d.write(private+syms['resourcebase'],private.to_bytes(2,'big'))
                    else:
                        d.write(0x30,objects.to_bytes(2,'big'))
                    callback = base+syms['SetObjMotion' if not private else 'MotionMoveDirection']
                    d.breakpoint(callback); d.breakpoint(0x7e00)
                    for opcode in (81,82):
                        entry = base+syms[('cmd_move_obj' if opcode==81 else 'cmd_move_obj_v') if not private else 'GameMoveCommand']
                        for index in (0,63):
                            for step in (0,1,255):
                                for override in (0,1,255):
                                    for flag in (0,255):
                                        before=bytearray((i*37+11)&255 for i in range(64*43))
                                        at=index*43;before[at+2]=index;before[at+0x1e]=step
                                        expected=bytearray(before)
                                        expected[at+0x22]=3;expected[at+0x27:at+0x29]=bytes([20,70])
                                        expected[at+0x29]=step;expected[at+0x2a]=flag
                                        if override:expected[at+0x1e]=override
                                        expected[at+0x26]|=0x10
                                        values=bytearray(b'\x77'*256)
                                        values[0]=20;values[254]=70;values[255]=override
                                        flags=bytearray([255 if not private else 1])*flagbytes
                                        wantedflags=bytearray(flags)
                                        if private:wantedflags[flag]=0
                                        else:wantedflags[flag>>3]&=~(128>>(flag&7))
                                        operands=bytes([index,20,70,override,flag]) if opcode==81 else bytes([index,0,254,255,flag])
                                        d.write(objects-1,b'G'+before+b'H');d.write(variables,values)
                                        d.write(flagbase,flags);d.write(control,b'\x5a')
                                        d.write(args,operands+b'ARGS')
                                        if private:d.write(private+syms['vmopcode'],bytes([opcode]))
                                        d.write(0x7ef0,b'\x7e\x00STACK')
                                        d.regs(pc=entry,s=0x7ef0,y=args,u=private,dp=private>>8,cc=0x50)
                                        d.call('c');r=d.regs()
                                        assert r['pc']==callback and r['u']==objects+at
                                        if private:
                                            assert r['x']==private
                                            assert d.read(private+syms['motionobject'],2)==(objects+at).to_bytes(2,'big')
                                            assert d.read(private+syms['motionid'],1)==bytes([index])
                                        else:assert r['y']==args+5
                                        # Inspect all setup before the owner callback;
                                        # full gameplay tests run actual direction/motion.
                                        assert d.read(objects-1,len(before)+2)==b'G'+expected+b'H',(owner,opcode,index,step,override,flag)
                                        assert d.read(flagbase,flagbytes)==wantedflags
                                        assert d.read(variables,256)==values
                                        assert d.read(control,1)==bytes([0 if index==0 else 0x5a])
                                        ret=int.from_bytes(d.read(r['s'],2),'big')
                                        d.regs(pc=ret,s=r['s']+2);d.call('c');r=d.regs()
                                        assert r['pc']==0x7e00 and r['s']==0x7ef2
                                        assert d.read(0x7ef2,5)==b'STACK' and d.read(args+5,4)==b'ARGS'
                                        if private:assert not r['cc']&1 and r['b']==0
                    if private:
                        for operands in (bytes([64,20,70,1,255]),bytes([0,160,70,1,255]),bytes([0,20,168,1,255])):
                            before=d.read(objects,64*43);flags=d.read(flagbase,flagbytes)
                            d.write(args,operands);d.write(private+syms['vmopcode'],b'Q')
                            d.write(0x7ef0,b'\x7e\x00STACK')
                            d.regs(pc=base+syms['GameMoveCommand'],s=0x7ef0,u=private,dp=private>>8,cc=0x50)
                            d.call('c');r=d.regs()
                            assert r['pc']==0x7e00 and r['cc']&1 and r['s']==0x7ef2
                            assert d.read(objects,64*43)==before and d.read(flagbase,flagbytes)==flags
                    assert d.read(base,len(code))==code
                    d.breakpoint(callback,False);d.breakpoint(0x7e00,False)
            print('PASS: both real move.obj/.v setup handlers at two load addresses; first/last records, variable indexes 0/254/255, saved/override speed, literal completion flags 0/255, ego input effects, direction callback context, guards, balanced stack, native index/coordinate rejection and immutable code')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
