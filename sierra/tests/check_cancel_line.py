#!/usr/bin/env python3
"""Execute cancel.line/echo.line with input bounds, prompt and state guards."""
import argparse
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_logic_executor import compile_module
from check_wbres import idle_rom,start_cpu

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--module-root',type=Path)
    args=ap.parse_args();root=args.module_root or Path(__file__).resolve().parents[1]/'objs'
    code=(root/'wbgame').read_bytes();syms=symbols(root/'wbgame.map')
    private=0x1000;stack=0x7ef0;finish=0x7e00
    with tempfile.TemporaryDirectory(prefix='sierra-cancel-line-') as name:
        temp=Path(name)
        coco_code,coco_syms=compile_module(Path(__file__).resolve().parents[1]/'objs/mnln.asm',temp/'mnln')
        d,proc=start_cpu(idle_rom(temp/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            d.breakpoint(finish);count=0;native_lines={}
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
                    put('presentationconfigured',b'\x01');put('rowoutput',b'U'*80)
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
                        expected[syms['presentationconfigured']]=0x81
                        at=syms['rowoutput'];expected[at:at+80]=bytes([0xcc])*80
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
                    line=d.read(private+syms['parserline'],39).split(b'\0',1)[0]
                    result=(d.read(private+syms['parserlength'],1)[0],line)
                    key=(entry,enabled,length,history)
                    assert key not in native_lines or native_lines[key]==result,(key,native_lines.get(key),result)
                    native_lines[key]=result
                    count+=1
                # ParserDrawInput owns a platform refresh before row work.
                # Mock that service only; row snapshot/damage code runs real.
                screen=base+syms['ScreenCommand'];d.breakpoint(screen)
                def refresh_call(error=0):
                    d.call('c');regs=d.regs()
                    assert regs['pc']==screen and d.read(private+syms['vmopcode'],1)==b'\0',regs
                    resume=int.from_bytes(d.read(regs['s'],2),'big')
                    d.regs(pc=resume,s=regs['s']+2,b=error,cc=(regs['cc']&~1)|bool(error))
                    d.call('c');return d.regs()
                for row in (0,23,24):
                    for length in (0,1,38):
                        for color_change in (False,True):
                            data=bytearray([0xcc])*syms['size']
                            def put(field,value):data[syms[field]:syms[field]+len(value)]=value
                            put('resourcebase',private.to_bytes(2,'big'))
                            put('vminputenabled',b'\x01');put('vminputrow',bytes([row]))
                            put('vmtextforeground',b'\x03');put('vmtextbackground',b'\x07');put('vmcursor',b'_')
                            put('vmstrings',b'> \0');put('parserlength',bytes([length]));put('parserline',b'x'*length+b'\0')
                            put('presentationconfigured',b'\x01');put('rowoutput',b'U'*80)
                            at=syms['textcharacters']+row*40
                            text=(b'> '+b'x'*length+b'_'+b' '*40)[:40]
                            data[at:at+40]=text;data[at+1000:at+1040]=bytes([0x37])*40
                            if color_change:data[at+1039]=0x36
                            expected=bytearray(data)
                            expected[syms['vmopcode']]=0
                            shadow=bytes(value for pair in zip(data[at:at+40],data[at+1000:at+1040]) for value in pair)
                            expected[syms['rowoutput']:syms['rowoutput']+80]=shadow
                            expected[at+1000:at+1040]=bytes([0x37])*40
                            expected[syms['presentationconfigured']]=0x81 if color_change else 1
                            d.write(private,data+b'GUARD');d.write(stack,finish.to_bytes(2,'big')+b'STACK')
                            d.regs(pc=base+syms['ParserDrawInput'],u=private,s=stack,dp=private>>8,cc=0x51)
                            regs=refresh_call()
                            assert regs['pc']==finish and regs['s']==stack+2 and not regs['cc']&1
                            assert d.read(private,len(data)+5)==expected+b'GUARD',('prompt damage',row,length,color_change)
                            assert d.read(stack+2,5)==b'STACK'
                            count+=1
                for enabled in (0,1):
                    data[syms['vminputenabled']]=enabled
                    expected=bytearray(data);expected[syms['vmopcode']]=0
                    d.write(private,data+b'GUARD');d.write(stack,finish.to_bytes(2,'big')+b'STACK')
                    d.regs(pc=base+syms['ParserDrawInput'],u=private,s=stack,dp=private>>8,cc=0x50)
                    regs=refresh_call(207)
                    assert regs['pc']==finish and regs['s']==stack+2 and regs['cc']&1 and regs['b']==207,regs
                    assert d.read(private,len(data)+5)==expected+b'GUARD'
                    assert d.read(stack+2,5)==b'STACK'
                    count+=1
                d.breakpoint(screen,False)
                assert d.read(base,len(code))==code,'code changed'
            # Compare the CoCo command bodies with Wild Bits' matching core
            # input-buffer transformations. Only the MMU character-output
            # service is stubbed; both engines execute their command/input code.
            d.breakpoint(0x0701)
            for base in (0x8000,0x9000):
                d.write(base,coco_code)
                for entry in ('cmd_cancel_line','cmd_echo_line'):
                    enabled_values=(0,1)
                    for enabled in enabled_values:
                        lengths=(0,1,38) if entry=='cmd_cancel_line' else (0,1,7,38)
                        for length in lengths:
                            histories=(0,) if entry=='cmd_cancel_line' else (0,1,7,38)
                            for history in histories:
                                shown=b'x'*length
                                raw=b'h'*history
                                d.write(0x012b,shown+b'\0'+bytes(40-len(shown)-1))
                                d.write(0x01d5,bytes([enabled]));d.write(0x01d7,b'\x0a')
                                d.write(0x05b9,b'\0');d.write(0x01ad,b'\0')
                                d.write(0x0449,b'\x26')
                                d.write(base+coco_syms['InputBufLen'],bytes([length]))
                                d.write(base+coco_syms['InputBuf'],raw+b'\0'+bytes(49-len(raw)))
                                d.write(stack,finish.to_bytes(2,'big')+b'STACK')
                                d.regs(pc=base+coco_syms[entry],s=stack,y=0x2000,u=0x3000,dp=0,cc=0x50)
                                for _ in range(160):
                                    d.call('c');regs=d.regs()
                                    if regs['pc']==finish:break
                                    assert regs['pc']==0x0701,(entry,enabled,length,history,regs)
                                    ret=int.from_bytes(d.read(regs['s'],2),'big')
                                    d.regs(pc=ret,s=regs['s']+2)
                                else:raise AssertionError(('CoCo command did not return',entry,enabled,length,history))
                                actual=(d.read(base+coco_syms['InputBufLen'],1)[0],d.read(0x012b,40).split(b'\0',1)[0])
                                key=('GameCancelLine' if entry=='cmd_cancel_line' else 'GameEchoLine',enabled,length,history)
                                expected=native_lines[key]
                                assert actual==expected,('CoCo/native input command result',base,key,actual,expected)
                                assert regs['s']==stack+2 and d.read(stack+2,5)==b'STACK'
                                count+=1
                image=bytearray(coco_code)
                for label,size in (('InputBufLen',1),('InputBuf',50)):
                    offset=coco_syms[label]
                    image[offset:offset+size]=d.read(base+offset,size)
                assert d.read(base,len(coco_code))==image
            print(f'PASS: {count} native cancel/echo and paired CoCo/native command cases; input enable state, cancel-to-empty, typed-prefix/history suffix merge, lengths through 38, service-boundary return, stack and relocated-code guards')
        finally:
            d.s.close();proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)

if __name__=='__main__':main()
