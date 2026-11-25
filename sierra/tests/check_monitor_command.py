#!/usr/bin/env python3
"""Run the CoCo toggle-monitor command and capture its 16 palette writes."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom, start_cpu


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-monitor-command-') as name:
        tmp = Path(name)
        coco, syms = compile_module(ROOT / 'objs/mnln.asm', tmp / 'mnln')
        d, emulator = start_cpu(idle_rom(tmp / 'idle.rom'), timeout=180)
        calls = 0
        try:
            d.write(0xffdf, b'\0')
            d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01')
            d.write(0xffa8, bytes(range(8)))
            start=syms['PaletteWriteLoop']
            end=syms['PaletteWriteRet']
            sites=[]
            at=start
            while True:
                at=coco.find(bytes.fromhex('103f8a'),at,end)
                if at<0:break
                sites.append(at);at+=3
            assert len(sites)==1,('palette I$Write sites',sites)
            stop=0x7e00
            d.write(0x7ef0,b'\x7e\x00STACK')
            d.breakpoint(stop)
            d.breakpoint(0x8000+sites[0])
            expected_by_mode={}
            table=syms['PaletteData']
            palette_data=coco[table:table+32]
            assert len(palette_data)==32
            for old_mode in (0,1):
                d.write(0x8000,coco)
                d.write(0x0553,bytes([old_mode]))
                new_mode=old_mode^1
                d.regs(pc=0x8000+syms['cmd_toggle_monitor'],s=0x7ef0,
                       dp=0,cc=0x50)
                d.call('c')
                observed=[]
                for index in range(16):
                    r=d.regs()
                    assert r['pc']==0x8000+sites[0],(old_mode,index,r)
                    assert r['y']==4 and r['a']==1,(old_mode,index,r)
                    chunk=d.read(r['x'],4)
                    assert chunk[:3]==bytes((0x1b,0x31,index)),(old_mode,index,chunk)
                    observed.append(chunk[3])
                    d.regs(pc=r['pc']+3,cc=r['cc']&~1)
                    d.call('c')
                r=d.regs()
                assert r['pc']==stop and r['s']==0x7ef2,(old_mode,r)
                assert d.read(0x0553,1)==bytes([new_mode])
                expected=palette_data[new_mode*16:(new_mode+1)*16]
                assert observed==list(expected),(old_mode,observed,list(expected))
                assert d.read(0x7ef2,5)==b'STACK'
                assert d.read(0x8000,len(coco))==coco
                expected_by_mode[new_mode]=observed
                calls+=16
            print(f'PASS: {calls} actual CoCo I$Write palette bytes across both monitor transitions; '
                  'all 16 colors, mode state, script pointer, caller stack and immutable code verified')
        finally:
            d.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except Exception:
                emulator.kill()
                emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
