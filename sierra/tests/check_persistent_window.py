#!/usr/bin/env python3
"""Check print-without-wait and close.window across workspace reuse/redraw."""
import argparse
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_lzw import resources
from check_wbplay import fixture
from check_wbres import exercise,idle_rom,start_cpu

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--module-root',type=Path)
    a=ap.parse_args();root=a.module_root or Path(__file__).resolve().parents[1]/'objs'
    syms=symbols(root/'wbgame.map')
    messages=[b'Original text',b'A persistent question',b'A second modal']
    prefix=bytes([103,5,4,1])
    with tempfile.TemporaryDirectory(prefix='sierra-window-') as name:
        d,proc=start_cpu(idle_rom(Path(name)/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            def run(body,keys=b'',extra=False,**options):
                files=fixture(body,message=messages)
                if extra:
                    _,data,expanded=next(resources())
                    offset=len(files['/game/vol.0'])
                    files['/game/logDir']+=offset.to_bytes(3,'big')
                    files['/game/vol.0']+=b'\x12\x34\0'+len(expanded).to_bytes(2,'little')+len(data).to_bytes(2,'little')+data
                return exercise(d,files,module='wbgame',module_root=root,base=0xa000,database=0x1000,
                    window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,frame_capture=True,keyboard=keys,**options)
            error,baseline,_=run(prefix+bytes([134,1,0]));assert not error
            plane=d.read(0x1000+syms['textcharacters'],2000)
            for middle,keys,extra in [(b'',b'',False),(bytes([20,2]),b'',True),
                                      (bytes([101,3]),b'\r',False),
                                      (bytes([105,0,24,1]),b'',False)]:
                body=prefix+bytes([12,15,101,2,12,200])+middle+bytes([169,169,134,1,0])
                error,frame,state=run(body,keys,extra)
                assert not error and state['vmflags'][200]==1 and state['vmflags'][15]==0,(error,state['vmflags'][15])
                assert frame==baseline,('persistent window failed to restore the original frame',middle,[(i%320,i//320,x,y) for i,(x,y) in enumerate(zip(frame,baseline)) if x!=y][:10],d.read(0x1000+syms['textcharacters'],2000)==plane)
                assert d.read(0x1000+syms['textcharacters'],2000)==plane,'original character/color snapshot lost'
                assert d.read(0x1000+syms['dialogactive'],1)==b'\0'
            # Faults are armed at real handler boundaries, so allocation and
            # earlier rendering still succeed and cleanup of the dialog is tested.
            for boundary,option in [('GameHoldDialog','map_failure'),('GameWindowCloseReady','map_failure'),
                                    ('GameWindowSave','unmap_error'),('GameWindowRestore','unmap_error')]:
                armed=[False]
                def arm(debugger,regs,symbols):armed[0]=True
                def fault(debugger,regs,symbols):
                    value=armed[0];armed[0]=False;return value
                body=prefix+bytes([12,15,101,2,169,134,1,0])
                error,_,_=run(body,breakpoint_hooks={boundary:arm},**{option:fault})
                assert error==207,(boundary,option,error)
            print('PASS: nonblocking print continues without input, clears flag 15, restores all original character/color bytes and pixels after LZW workspace reuse/full redraw/nested modal; repeated close is harmless and allocations are released')
        finally:
            d.s.close();proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)

if __name__=='__main__':main()
