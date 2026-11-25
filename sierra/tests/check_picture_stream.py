#!/usr/bin/env python3
"""Exercise owned picture input beyond the private 8-KiB staging window."""
import argparse
import shutil
from pathlib import Path
import subprocess
import tempfile
from check_wbres import exercise,idle_rom,start_cpu
from check_wbplay import fixture
from export_picture import render,unpack_picture

ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--module-root',type=Path)
    ap.add_argument('--fixtures-only',action='store_true')
    a=ap.parse_args()
    with tempfile.TemporaryDirectory(prefix='sierra-pic-stream-') as name:
        d,proc=start_cpu(idle_rom(Path(name)/'idle.rom'),timeout=1800)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            def run(picture,**options):
                body=bytes([3,0,1,24,0,25,0,26,12,200,134,1,0])
                return exercise(d,fixture(body,picture),module='wbgame',module_root=a.module_root,base=0xa000,
                    database=0x0000,window=0x8000,blocks=None,multiple=True,firstblock=0x10,frame_capture=True,capture=True,**options)
            count=0
            for offset in (0,8189,8190,8191,8192,16381,16382,16383,16384,65527):
                # Commands and coordinate operands cross both sides of page boundaries.
                picture=b'\xf1'*offset+bytes([0xf0,2,0xf6,10,20,12,20,0xff])
                error,frame,state=run(picture)
                assert not error and state['vmflags'][200]==1,(offset,error)
                expected=bytearray([1])*76800
                expected[8*320:176*320]=bytes([16])*(168*320)
                start=(20+8)*320+10*2
                expected[start:start+6]=bytes([3])*6
                assert frame==expected,offset
                count+=1
            for picture in (b'\xf1'*8191+b'\xf0',b'\xf1'*8191+b'\xf6\x01',
                            b'\xf1'*8192,b'\xf1'*65535):
                error,_,_=run(picture)
                assert error,'truncated stream accepted'
            base_picture=bytes([0xf0,2,0xf6,10,20,12,20,0xff])
            overlay_picture=bytes([0xf0,3,0xf6,10,21,12,21,0xff])
            script=bytes([3,0,1,24,0,25,0,3,1,2,24,1,28,1,26,12,200,134,1,0])
            files=fixture(script,base_picture)
            volume=bytearray(files['/game/vol.0'])
            overlay_offset=len(volume)
            volume.extend(b'\x12\x34\0'+len(overlay_picture).to_bytes(2,'little')*2+overlay_picture)
            files['/game/vol.0']=bytes(volume)
            files['/game/picDir']+=overlay_offset.to_bytes(3,'big')
            native_picture=[]
            def capture_picture(cpu,regs,syms):
                first=int.from_bytes(cpu.read(syms['picturefirst'],2),'big')
                for page in range(4):
                    cpu.write(0xffac,bytes([first+page]))
                    native_picture.append(cpu.read(0x8000,8192))
                cpu.write(0xffac,b'\x04')
                return False
            error,frame,state=exercise(d,files,module='wbgame',module_root=a.module_root,base=0xa000,
                database=0x0000,window=0x8000,blocks=None,multiple=True,firstblock=0x10,
                frame_capture=True,capture=True,breakpoint_hooks={'GameShowPicture':capture_picture})
            assert not error and state['vmflags'][200]==1,('overlay script did not complete',error)
            assembler=shutil.which('lwasm.orig') or shutil.which('lwasm')
            assert assembler,'LWASM assembler is required for the CoCo overlay reference'
            coco_defs=ROOT.parent.parent/'nitros9/defs'
            base_reference=render(ROOT/'kingsquest4',base_picture,assembler,coco_defs)
            overlay_reference=render(ROOT/'kingsquest4',overlay_picture,assembler,coco_defs)
            combined=bytearray(base_reference)
            for offset,pixel in enumerate(overlay_reference):
                if pixel&15 != 15:
                    combined[offset]=pixel
            assert len(native_picture)==4,('show.pic combined buffer capture count',len(native_picture))
            actual_combined=b''.join(native_picture)[:26880]
            assert actual_combined==combined,('overlay.pic combined visual/priority bytes differ from CoCo composition',
                next((i for i,(actual,wanted) in enumerate(zip(actual_combined,combined)) if actual!=wanted),None))
            expected=bytearray([1])*76800
            for row in range(168):
                expected[(row+8)*320:(row+9)*320]=bytes(
                    value for pixel in combined[row*160:(row+1)*160]
                    for value in [(pixel&15)+1]*2)
            assert frame==expected,('overlay.pic does not match CoCo-rendered overlay composition',
                next((i for i,(actual,wanted) in enumerate(zip(frame,expected)) if actual!=wanted),None))
            count+=1
            for boundary,option in [('GameReadPictureChunk','map_failure'),('GamePictureChunkCopy','unmap_error')]:
                armed=[False]
                def arm(debugger,regs,symbols):armed[0]=True
                def fault(debugger,regs,symbols):
                    value=armed[0];armed[0]=False;return value
                error,_,_=run(b'\xf1'*8192+b'\xff',breakpoint_hooks={boundary:arm},**{option:fault})
                assert error==207,(boundary,option,error)
            for game in (() if a.fixtures_only else (ROOT/'kingsquest4',ROOT/'spacequest0')):
                entries=(game/'picDir').read_bytes()
                for number in range(len(entries)//3):
                    entry=entries[number*3:number*3+3]
                    if entry==b'\xff'*3:continue
                    volume=entry[0]>>4
                    offset=((entry[0]&15)<<16)|(entry[1]<<8)|entry[2]
                    source=(game/f'vol.{volume}').read_bytes()
                    header=source[offset:offset+7]
                    size=int.from_bytes(header[3:5],'little')
                    if size<=8192:continue
                    stored=int.from_bytes(header[5:7],'little')
                    data=source[offset+7:offset+7+stored]
                    commands=unpack_picture(data) if header[2]&128 else data
                    assert len(commands)==size
                    reference=render(game,commands,'lwasm.orig',ROOT.parent.parent/'nitros9/defs')
                    body=bytes([3,0,1,24,0,25,0,26,12,200,134,1,0])
                    files=fixture(body)
                    address=len(files['/game/vol.0'])
                    files['/game/picDir']=b'\xff'*3+address.to_bytes(3,'big')
                    files['/game/vol.0']+=b'\x12\x34'+bytes([header[2]&128])+header[3:7]+data
                    error,frame,state=exercise(d,files,module='wbgame',module_root=a.module_root,base=0xa000,
                        database=0x0000,window=0x8000,blocks=None,multiple=True,firstblock=0x10,frame_capture=True,capture=True)
                    assert not error and state['vmflags'][200]==1,(game.name,number,error)
                    expected=bytearray([1])*76800
                    for y in range(168):
                        expected[(y+8)*320:(y+9)*320]=bytes(value for pixel in reference[y*160:(y+1)*160] for value in [(pixel&15)+1]*2)
                    assert frame==expected,(game.name,number,'CoCo reference pixel mismatch')
                    print(f'Checked large packed picture {game.name} {number} ({size} bytes)',flush=True)
            print(f'PASS: {count} streamed pictures, exact 8/16-KiB boundaries and 65535-byte length, original logic resumed, malformed commands/operands rejected and ownership released')
        finally:
            d.s.close();proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)

if __name__=='__main__':main()
