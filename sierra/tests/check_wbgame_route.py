#!/usr/bin/env python3
"""Drive unmodified KQ1 through the castle's east exit on a real 6809 CPU.

OS calls are mocked here; check_wbgame_mame.py covers the real driver.
This deliberately longer acceptance test is separate from the fixture suite.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile
from check_wbres import exercise,idle_rom,start_cpu


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game',type=Path,default=Path(__file__).resolve().parents[1]/'kingsquest1')
    a=ap.parse_args()
    files={'/game/'+p.name:p.read_bytes() for p in a.game.iterdir()
           if p.is_file() and (p.name.startswith('vol.') or p.name in
            ('logDir','picDir','viewDir','sndDir','object','words.tok'))}
    with tempfile.TemporaryDirectory(prefix='wbgame-route-') as tmp:
        d,emu=start_cpu(idle_rom(Path(tmp)/'idle.rom'),timeout=5000)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            error,frame,state=exercise(d,files,module='wbgame',arguments=b'/game 0\r',
                base=0xa000,database=0x0000,window=0x8000,blocks=None,multiple=True,
                firstblock=0x10,capture=True,frame_capture=True,cycle_limit=110,
                os_call_limit=600000,clock=tuple(range(60))*100,
                keyboard_by_cycle={1:(b' \r',0),2:(b'\x09',0x40),
                                   40:(b'\x0a',0x10),75:(b'\x09',0x40)})
            assert error==228, ('unexpected exit',error,state['vmopcode'].hex())
            assert state['vmvariables'][0:2]==bytes([8,1]), ('castle exit did not reach room 8',state['vmvariables'][:27].hex())
            assert len(set(frame))>=8, 'new room did not render'
            assert state['vmobjects'][3]>0, 'ego did not move inside the new room'
            print('PASS: actual KQ1 Right/Down/Right route moves from room 1 into room 8, draws the new scene and continues movement; controlled abort, restored terminal options and complete cleanup')
        finally:
            d.s.close(); emu.terminate()
            try:
                emu.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emu.kill(); emu.wait(timeout=5)

if __name__=='__main__':main()
