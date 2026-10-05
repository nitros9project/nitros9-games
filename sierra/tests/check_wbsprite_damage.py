#!/usr/bin/env python3
"""Erase/move sprites across pages and clips without leaving stale pixels."""
from pathlib import Path
import subprocess
import tempfile
from check_wbres import exercise, idle_rom, start_cpu
from check_wbplay import fixture


def view(width, height):
    row = bytes([0x10 | 15] * (width // 15) +
                ([0x10 | (width % 15)] if width % 15 else []) + [0])
    return bytes([0,0,1,0,0,7,0,1,3,0,width,height,15]) + row*height


def main():
    with tempfile.TemporaryDirectory(prefix='wb-sprite-damage-') as tmp:
        d, emu = start_cpu(idle_rom(Path(tmp)/'idle.rom'), timeout=900)
        try:
            d.write(0xffdf,b'\0'); d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01'); d.write(0xffa8,bytes(range(8)))
            for width,height,x,y in ((4,3,30,52),(4,3,159,1),
                                      (4,3,159,167),(4,3,255,255),
                                      (160,70,0,100)):
                script=bytes([3,0,1,24,0,25,0,33,0,41,0,0,
                    37,0,x,y,54,0,15,35,0,
                    37,0,20,100,35,0,36,0,26,134,1,0])
                error,frame=exercise(d,fixture(script,b'\xff',view(width,height)),
                    module='wbgame',base=0xa000,database=0x1000,window=0x8000,
                    blocks=None,multiple=True,firstblock=0x10,frame_capture=True)
                expected=bytearray([1])*76800
                expected[8*320:176*320]=bytes([16])*(168*320)
                assert not error and frame==expected, ('sprite trail',width,height,x,y,error)
            print('PASS: moved/erased sprites leave no trails across mapping pages, screen clips, offscreen positions or large-cel fallback; complete cleanup')
        finally:
            d.s.close(); emu.terminate()
            try:
                emu.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emu.kill(); emu.wait(timeout=5)


if __name__=='__main__':main()
