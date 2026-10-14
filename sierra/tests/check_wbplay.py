#!/usr/bin/env python3
"""Exercise native gameplay math, following, placement and modal restoration."""
import subprocess
from pathlib import Path
import tempfile
from check_wbres import exercise, idle_rom, start_cpu


def fixture(script, picture=None, view=None, message=None):
    logic = len(script).to_bytes(2,'little') + script
    if message is not None:
        messages=message if isinstance(message,list) else [message]
        clear=b''.join(m+b'\0' for m in messages)
        start=2+2*len(messages); offsets=bytearray(); current=start
        for m in messages:
            offsets.extend(current.to_bytes(2,'little')); current+=len(m)+1
        logic += bytes([len(messages)]) + current.to_bytes(2,'little') + offsets
        logic += bytes(c ^ b'Avis Durgan'[i%11] for i,c in enumerate(clear))
    payloads=[('logDir',logic)]
    if picture is not None: payloads.append(('picDir',picture))
    if view is not None: payloads.append(('viewDir',view))
    volume=bytearray(); files={}
    for kind,payload in payloads:
        files['/game/'+kind]=(b'\xff'*3 if kind!='viewDir' else b'') + len(volume).to_bytes(3,'big')
        volume.extend(b'\x12\x34\0'+len(payload).to_bytes(2,'little')*2+payload)
    files['/game/vol.0']=bytes(volume)
    return files


def main():
    with tempfile.TemporaryDirectory(prefix='wbplay-') as tmp:
        d,emu=start_cpu(idle_rom(Path(tmp)/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            def run(files, **options):
                return exercise(d,files,module='wbgame',base=0xa000,database=0x0000,
                    window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,**options)
            error,_,_=run(fixture(bytes([134,1,0])),option_set_error=True)
            assert error==203, 'failed terminal setup did not retain its error and restore options'
            # A five-second pause must not advance the game clock; the next
            # ordinary second still must. Scene restoration uses the same
            # modal backup path as print, without changing the input editor.
            body=bytes([255,253,7,250,255,4,0,12,250,136,0,
                        255,253,7,251,255,6,0,12,251,4,220,11,0,
                        4,221,11,134,1,0])
            error,_,s=run(fixture(body),keyboard=b'x',clock=(0,5,6))
            assert not error and s['vmvariables'][220:222]==bytes([0,1]), ('pause advanced game time',error,s['vmvariables'][220:222])
            body=bytes([3,220,200,165,220,2,3,221,7,166,220,221,
                        167,220,5,168,220,221,130,255,255,222,130,0,255,223,134,1,0])
            error,_,s=run(fixture(body))
            assert not error and s['vmvariables'][220]==6 and s['vmvariables'][222]==255, (error,s['vmvariables'][220:224])
            error,_,_=run(fixture(bytes([167,0,0,0])))
            assert error, 'division by zero accepted'
            # One-pixel native view and empty walkable picture.
            view=bytes([0,0,1,0,0,7,0,1,3,0,1,1,15,0x11,0])
            setup=bytes([3,0,1,24,0,25,0,33,0,41,0,0,37,0,20,60,35,0,
                         33,1,41,1,0,37,1,10,60,35,1,83,1,2,255,26])
            # stop.update freezes motion/cels but retains the drawn sprite;
            # start.update resumes on the next cycle. force.update only redraws.
            for command in (58,59,60):
                initialization=bytes([3,0,1,24,0,25,0,33,1,41,1,0,
                                      37,1,20,60,35,1,26,3,200,3,86,1,200,58,1,command,1])
                body=bytes([255,7,11,255])+len(initialization).to_bytes(2,'little')+initialization
                body+=bytes([1,250,255,1,250,3,255,2,0,134,1,0])
                error,frame,state=run(fixture(body,b'\xff',view),frame_capture=True)
                actor=state['vmobjects'][43:86]
                assert not error and bool(actor[0x26]&16)==(command==59),(command,error,actor.hex())
                assert actor[3]==(22 if command==59 else 20),(command,actor.hex())
                assert 1 in frame,'stopped sprite disappeared'
                if command==58: frozen_frame=frame;frozen_actor=actor
                elif command==60:
                    assert frame==frozen_frame and actor==frozen_actor,'force.update advanced the object or changed its pixels'
            for command in (58,59,60):
                error,_,_=run(fixture(bytes([command,64,0])))
                assert error==187,('invalid update object accepted',command,error)
            script=bytes([255,7,11,255])+len(setup).to_bytes(2,'little')+setup
            script+=bytes([1,250,255,7,255,255,2,0,134,1,255,1,250,30,255,2,0,134,1,0])
            error,_,s=run(fixture(script,b'\xff',view))
            follower=s['vmobjects'][43:86]
            assert not error and s['vmflags'][255]==1 and follower[0x21:0x23]==bytes(2), (error,follower.hex())
            assert abs(follower[3]-20)<=2 and follower[4]==60, follower.hex()
            for opcode, coords, expected in [(40,[240,241],(0,60)),(147,[25,60],(24,60)),(148,[240,241],(25,60))]:
                body=bytes([3,0,1,24,0,25,0,33,0,41,0,0,37,0,20,60,
                            3,240,236 if opcode==40 else 25,3,241,0 if opcode==40 else 60,
                            opcode,0,*coords,134,1,0])
                picture=bytes([0xf2,0,0xf6,25,60,25,60,0xf3,0xff]) if opcode==147 else b'\xff'
                error,_,s=run(fixture(body,picture,view))
                assert not error and s['vmobjects'][3:5]==bytes(expected),(opcode,error,s['vmobjects'][:43].hex())
            body=bytes([101,1,12,200,134,1,0])
            error,frame,s=run(fixture(body,message=b'A modal response.'),keyboard=b'\r',frame_capture=True)
            assert not error and s['vmflags'][200]==1 and frame==bytes([1])*76800, 'modal dismissal failed to restore blank frame'
            for keys, selected in [(b'\n\r',True),(b'\x1b',False),(b'\x05',False),(b'\r\n\r',True)]:
                body=bytes([3,0,1,24,0,25,0,26,156,1,157,2,254,157,3,255,158,160,254,161,
                            255,12,255,255,2,0,12,200,134,1,0])
                error,frame,s=run(fixture(body,b'\xff',message=[b'File',b'Disabled',b'Pick me']),
                                  keyboard=keys,frame_capture=True)
                assert not error and bool(s['vmflags'][200])==selected, ('menu',keys,error)
                wanted=bytearray([1])*76800
                wanted[8*320:176*320]=bytes([16])*(168*320)
                assert frame==wanted, 'menu dismissal did not restore the original scene'
            for keys, cancelled in [(b'\r',False),(b'\x1b',True),(b'\x05',True)]:
                body=bytes([134,0,1,220,134,1,0])
                error,_,s=run(fixture(body),keyboard=keys)
                assert not error and bool(s['vmvariables'][220])==cancelled, ('quit confirmation',keys,error)
            import re
            font=bytes(int(v,16) for v in re.findall(r'\$([0-9A-F]{2})',
                (Path(__file__).resolve().parents[1]/'objs/font-data.asm').read_text()))
            for messages,body,expected in [
                ([b'%m2:%v220:%s1:%%',b'nested',b'word'],
                 bytes([3,220,255,114,1,3,103,3,0,1,134,1,0]),b'nested:255:word:%'),
                ([b'%w1/%w2',b'look tree'],
                 bytes([114,0,2,117,0,103,3,0,1,134,1,0]),b'look/tree')]:
                files=fixture(body,message=messages)
                if expected==b'look/tree':
                    from check_wbparser import dictionary
                    files['/game/words.tok']=dictionary([('look',2),('tree',4)])
                error,frame,_=run(files,frame_capture=True)
                assert not error, (expected,error)
                wanted=bytearray([1])*76800
                for col,char in enumerate(expected):
                    for row in range(8):
                        for pixel in range(8):
                            wanted[(24+row)*320+col*8+pixel]=16 if font[char*8+row]&(128>>pixel) else 1
                assert frame==wanted, ('formatted glyphs',expected)
            # Modal input never submits dictionary input or overwrites the
            # ordinary pending input line. Script strings survive presentation.
            body=bytes([115,1,1,10,2,5,103,3,0,2,118,1,220,103,4,0,3,134,1,0])
            files=fixture(body,message=[b'Answer:',b'%s1',b'%v220'])
            error,frame,s=run(files,keyboard=b'ABCDEZ\x08E\r255\r',frame_capture=True)
            assert not error and s['vmvariables'][220]==255, ('modal input',error)
            wanted=bytearray([1])*76800
            for text,row in [(b'ABCDE',3),(b'255',4)]:
                for col,char in enumerate(text):
                    for gy in range(8):
                        for pixel in range(8):
                            wanted[(row*8+gy)*320+col*8+pixel]=16 if font[char*8+gy]&(128>>pixel) else 1
            assert frame==wanted, 'bounded get.string/get.num formatting or restore failed'
            for keys, expected in [(b'\r',0),(b'256\r',0),(b'999\r',231),
                                   (b'A2B5C5D\r',255),(b'\x1b',0)]:
                body=bytes([3,255,42,118,1,255,134,1,0])
                error,_,s=run(fixture(body,message=b'Number:'),keyboard=keys)
                assert not error and s['vmvariables'][255]==expected, ('modal number conversion',keys,error,s['vmvariables'][255])
            body=bytes([114,0,1,117,0,116,2,1,103,3,0,2,134,1,0])
            files=fixture(body,message=[b'look tree',b'%s1'])
            from check_wbparser import dictionary
            files['/game/words.tok']=dictionary([('look',2),('tree',4)])
            error,frame,_=run(files,frame_capture=True)
            assert not error, ('word.to.string',error)
            wanted=bytearray([1])*76800
            for col,char in enumerate(b'tree'):
                for gy in range(8):
                    for pixel in range(8):
                        wanted[(24+gy)*320+col*8+pixel]=16 if font[char*8+gy]&(128>>pixel) else 1
            assert frame==wanted, 'word.to.string did not preserve parsed word text'
            # %o resolves a variable to an inventory item and recursively
            # formats the bounded name through the linked cold helper's I/O buffer.
            names = [b""] * 256
            names[0] = b"zero"
            names[128] = b"%v7|2"
            names[255] = b"last"
            table = bytearray(); strings = bytearray()
            for name in names:
                table.extend((768+len(strings)).to_bytes(2, "little") + b"\xff")
                strings.extend(name+b"\0")
            plain = (768).to_bytes(2, "little") + b"\0" + table + strings
            key = b"Avis Durgan"
            objects = bytes(value ^ key[i % len(key)] for i,value in enumerate(plain))
            for item, expected in ((0,b"zero"),(2,b""),(128,b"07"),(255,b"last")):
                body = bytes([3,220,item,3,7,7,103,3,0,1,134,1,0])
                files = fixture(body,message=b"[%o220/%o220]")
                files["/game/object"] = objects
                error,frame,_ = run(files,frame_capture=True)
                assert not error, ("object format", item, error)
                wanted = bytearray([1])*76800
                for col,char in enumerate(b"["+expected+b"/"+expected+b"]"):
                    for gy in range(8):
                        for pixel in range(8):
                            wanted[(24+gy)*320+col*8+pixel] = 16 if font[char*8+gy]&(128>>pixel) else 1
                assert frame == wanted, ("object name/variable indirection/recursion",item)
            # The frame boundary includes the terminator: 511 bytes fit.
            key = b"Avis Durgan"
            plain = b"\x03\0\0\x03\0\xff" + b"A"*511 + b"\0"
            files = fixture(bytes([3,220,0,103,3,0,1,134,1,0]),message=b"%o220")
            files["/game/object"] = bytes(value ^ key[i % len(key)] for i,value in enumerate(plain))
            error,_,_ = run(files)
            assert not error, ("511-byte object name rejected",error)
            for message, item, names in ((b"%o220",1,[b"zero"]),
                                          (b"%o256",0,[b"zero"]),
                                          (b"%o220",0,[b"%o220"]),
                                          (b"%o220",0,[b"A"*512])):
                plain = b"\x03\0\0\x03\0\xff" + names[0]+b"\0"
                files = fixture(bytes([3,220,item,103,3,0,1,134,1,0]),message=message)
                files["/game/object"] = bytes(value ^ key[i % len(key)] for i,value in enumerate(plain))
                error,_,_ = run(files)
                assert error == 203, ("invalid/recursive object format accepted",message,item,error)
            for malformed in (b'%m1',b'%v256',b'%w0',b'%w20',b'%x1',b'%v220|256'):
                error,_,_=run(fixture(bytes([101,1,134,1,0]),message=malformed))
                assert error, ('malformed format accepted',malformed)
            print('PASS: byte math, zero-divisor rejection, random range edges, follow completion/high flag, signed/absolute placement and blocked-position search, stop/start/force update and retained sprites, pause/resume clock freezing, modal restoration, formatted variables/strings/words/object names/nested messages, high item indices, repeated cold calls, 511/512-byte name bounds and rejection bounds, and ownership cleanup')
        finally:
            d.s.close()
            emu.terminate()
            try:
                emu.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emu.kill()
                emu.wait(timeout=5)

if __name__=='__main__':main()
