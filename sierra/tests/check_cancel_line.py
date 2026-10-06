#!/usr/bin/env python3
"""Execute cancel.line with pending-input, prompt-row and state guards."""
import argparse
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_wbres import idle_rom,start_cpu

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--module-root',type=Path)
    args=ap.parse_args();root=args.module_root or Path(__file__).resolve().parents[1]/'objs'
    code=(root/'wbgame').read_bytes();syms=symbols(root/'wbgame.map')
    private=0x1000;stack=0x7ef0;finish=0x7e00
    with tempfile.TemporaryDirectory(prefix='sierra-cancel-line-') as name:
        d,proc=start_cpu(idle_rom(Path(name)/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            d.breakpoint(finish);count=0
            for base in (0x9000,0xa000):
                d.write(base,code)
                cases = [('GameCancelLine', enabled, row, length, 0)
                         for enabled in (0,1) for row in (0,23,24)
                         for length in (0,1,38)]
                cases += [('GameEchoLine', enabled, row, length, history)
                          for enabled in (0,1) for row in (0,23,24)
                          for length in (0,1,7,38)
                          for history in (0,1,7,38,39)]
                for entry,enabled,row,length,history in cases:
                    data=bytearray([0xcc])*syms['size']
                    def put(field,value):data[syms[field]:syms[field]+len(value)]=value
                    put('resourcebase',private.to_bytes(2,'big'))
                    put('vminputenabled',bytes([enabled]));put('vminputrow',bytes([row]))
                    put('vmtextforeground',b'\x03');put('vmtextbackground',b'\x07');put('vmcursor',b'_')
                    put('vmstrings',b'> \0');put('parserlength',bytes([length]));put('parserline',b'x'*length+b'\0')
                    put('parserlastline',b'h'*history+b'\0')
                    expected=bytearray(data)
                    redraw=False
                    if entry == 'GameCancelLine':
                        expected[syms['parserlength']]=0;expected[syms['parserline']]=0
                        line=b'';redraw=bool(enabled)
                    elif enabled and min(history,38)>length:
                        end=min(history,38);line=b'x'*length+b'h'*(end-length)
                        expected[syms['parserlength']]=end
                        at=syms['parserline'];expected[at:at+end+1]=line+b'\0'
                        redraw=True
                    if redraw:
                        at=syms['textcharacters']+row*40
                        text=b'> '+line+b'_'
                        # At maximum capacity the prompt consumes the cursor cell.
                        expected[at:at+40]=(text+b' '*40)[:40]
                        expected[at+1000:at+1040]=bytes([0x37])*40
                    d.write(private,data+b'GUARD');d.write(stack,finish.to_bytes(2,'big')+b'STACK')
                    d.regs(pc=base+syms[entry],u=private,s=stack,dp=private>>8,cc=0x51)
                    d.call('c');regs=d.regs()
                    assert regs['pc']==finish and regs['s']==stack+2 and regs['dp']==private>>8 and not regs['b'] and not regs['cc']&1,regs
                    assert d.read(private,len(data)+5)==expected+b'GUARD',(base,entry,enabled,row,length,history)
                    assert d.read(stack+2,5)==b'STACK'
                    count+=1
                assert d.read(base,len(code))==code,'code changed'
            print(f'PASS: {count} actual cancel.line/echo.line calls; cancellation, history suffix/prefix preservation, 38-byte bounds, prompt redraw and disabled/history/flags/private guards preserved, relocated immutable code')
        finally:
            d.s.close();proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)

if __name__=='__main__':main()
