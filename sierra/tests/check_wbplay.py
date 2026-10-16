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
            body=bytes([3,220,7,167,220,0,3,221,0,168,220,221,
                        3,222,42,134,1,0])
            error,_,s=run(fixture(body))
            assert not error and s['vmvariables'][220:223]==bytes([255,0,42]), ('zero-divisor continuation',error,s['vmvariables'][220:223])
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
                body=bytes([12,14,3,0,1,24,0,25,0,26,156,1,157,2,254,157,3,255,158,160,254,161,
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
                 bytes([3,220,255,114,1,3,103,3,0,1,134,1,0]),b'nested:255:word:'),
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
            for item, expected, operand in ((0,b"zero",220),(2,b"",220),(128,b"07",220),(255,b"last",220),
                                            (0,b"zero",256),(128,b"07",476),(255,b"last",732)):
                body = bytes([3,operand&255,item,3,7,7,103,3,0,1,134,1,0])
                files = fixture(body,message=f"[%o{operand}/%o{operand}]".encode())
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
                                          (b"%o220",0,[b"%o220"]),
                                          (b"%o220",0,[b"A"*512])):
                plain = b"\x03\0\0\x03\0\xff" + names[0]+b"\0"
                files = fixture(bytes([3,220,item,103,3,0,1,134,1,0]),message=message)
                files["/game/object"] = bytes(value ^ key[i % len(key)] for i,value in enumerate(plain))
                error,_,_ = run(files)
                assert error == 203, ("invalid/recursive object format accepted",message,item,error)
            # Root logic 0 and caller logic 1 deliberately use different
            # message tables. Nested %g must restore both message and VM state.
            def global_files(root_messages, local_message=b"%g1", boot_caller=False, compressed_root=False):
                payloads = []
                for number,(code,messages) in enumerate(((bytes([22,1,134,1,0]),root_messages),
                                      (bytes([103,3,0,1,103,4,0,2,3,230,42]+([134,1] if boot_caller else [])+[0]),
                                       [local_message,b"%m3",b"local"]))):
                    clear = b"".join(message+b"\0" for message in messages)
                    position = 2+2*len(messages); offsets = bytearray()
                    for message in messages:
                        offsets.extend(position.to_bytes(2,"little")); position+=len(message)+1
                    payloads.append(len(code).to_bytes(2,"little")+code+bytes([len(messages)])+
                                    position.to_bytes(2,"little")+offsets+
                                    (clear if number==0 and compressed_root else
                                     bytes(value ^ key[i%11] for i,value in enumerate(clear))))
                volume = bytearray(); directory = bytearray()
                for number,payload in enumerate(payloads):
                    directory.extend(len(volume).to_bytes(3,"big"))
                    stored = payload
                    if number==0 and compressed_root:
                        from check_lzw import packed
                        stored = packed([(256,9)]+[(value,9) for value in payload]+[(257,9)])
                    volume.extend(b"\x12\x34\0"+len(payload).to_bytes(2,"little")+
                                  len(stored).to_bytes(2,"little")+stored)
                return {"/game/logDir":bytes(directory),"/game/vol.0":bytes(volume)}
            for messages, expected, boot, compressed, source in (
                    ([b"global-%g2",b"%m3",b"root"],b"global-root",False,False,b"%g1"),
                    ([b"%o220/%m3",b"unused",b"root"],b"key/root",False,False,b"%g1"),
                    ([b"global-%g2",b"%m3",b"root"],b"global-root",True,False,b"%g1"),
                    ([b"global-%g2",b"%m3",b"root"],b"global-root",True,True,b"%g1"),
                    *[([b"root"],expected,False,False,source) for source,expected in
                      ((b"%g2",b""),(b"%g0",b""),(b"%g256",b""),(b"%g257",b"root"),
                       (b"%m99",b""),(b"%m0",b""),(b"%m",b""),(b"%m2",b"local"))]):
                files = global_files(messages,source,boot_caller=boot,compressed_root=compressed)
                plain = b"\x03\0\0\x03\0\xffkey\0"
                files["/game/object"] = bytes(value ^ key[i%11] for i,value in enumerate(plain))
                error,frame,state = run(files,arguments=b"/game 1\r" if boot else b"/game 0\r",frame_capture=True)
                assert not error and state["vmvariables"][230] == 42, ("global caller resume",error)
                wanted = bytearray([1])*76800
                for row,text in ((3,expected),(4,b"local")):
                    for col,char in enumerate(text):
                        for gy in range(8):
                            for pixel in range(8):
                                wanted[(row*8+gy)*320+col*8+pixel] = 16 if font[char*8+gy]&(128>>pixel) else 1
                assert frame == wanted, "global/local message context or object expansion corrupted"
            for messages, source in (([b"%g1"],b"%g1"),):
                restored = []
                def before_unwind(debug,registers,syms):
                    restored.append((debug.read(syms["vmcurrent"],1),debug.read(syms["vmend"],2)))
                error,_,state = run(global_files(messages,source),arguments=b"/game 0\r",
                                    breakpoint_hooks={"VmCallRestore":before_unwind})
                assert error == 203, ("invalid/recursive global format",source,error)
                assert restored == [(b"\x01",b"\0\x0e")], ("global error did not restore caller",restored)
                assert state["vmcurrent"] == b"\0" and state["vmend"] == b"\0\x07", "VM failed to unwind to root"
            files = global_files([b"root"],boot_caller=True)
            files["/game/logDir"] = b"\xff"*3 + files["/game/logDir"][3:]
            error,_,state = run(files,arguments=b"/game 1\r")
            assert error and state["vmcurrent"] == b"\0" and state["vmend"] == b"\0\x10", "missing global resource damaged caller"
            # Keep Larry's original global/local message tables unchanged;
            # only the two instruction bodies are controlled bootstraps.
            from audit_game_scripts import logic_resource
            from check_lzw import packed
            game = Path(__file__).resolve().parents[1]/"leisuresuitlarry"
            original_directory = (game/"logDir").read_bytes()
            directory = bytearray(b"\xff"*39); volume = bytearray()
            expected = None
            for number,body in ((0,bytes([22,12,134,1,0])),
                                (12,bytes([103,3,0,42,3,230,42,0]))):
                original, encrypted = logic_resource(game,number,int.from_bytes(
                    original_directory[number*3:number*3+3],"big"))
                at = 2+int.from_bytes(original[:2],"little")
                if number == 0:
                    base = at+1; start = base+2+2*original[at]
                    end = base+int.from_bytes(original[base:base+2],"little")
                    text = original[start:end]
                    if encrypted: text = bytes(value ^ key[i%11] for i,value in enumerate(text))
                    offset = base+int.from_bytes(original[base+352:base+354],"little")-start
                    expected = text[offset:].split(b"\0")[0]
                    assert 0 < len(expected) <= 80 and b"%" not in expected
                payload = len(body).to_bytes(2,"little")+body+original[at:]
                stored = payload
                if not encrypted:
                    codes = []
                    for position in range(0,len(payload),200):
                        codes += [(256,9)]+[(value,9) for value in payload[position:position+200]]
                    stored = packed(codes+[(257,9)])
                directory[number*3:number*3+3] = len(volume).to_bytes(3,"big")
                volume.extend(b"\x12\x34\0"+len(payload).to_bytes(2,"little")+
                              len(stored).to_bytes(2,"little")+stored)
            error,frame,state = run({"/game/logDir":bytes(directory),"/game/vol.0":bytes(volume)},
                                    arguments=b"/game 0\r",frame_capture=True)
            assert not error and state["vmvariables"][230] == 42, ("original Larry global message",error)
            wanted = bytearray([1])*76800
            for position,char in enumerate(expected):
                row,column = divmod(position,40)
                for gy in range(8):
                    for pixel in range(8):
                        wanted[((3+row)*8+gy)*320+column*8+pixel] = 16 if font[char*8+gy]&(128>>pixel) else 1
            assert frame == wanted, "original Larry %g176 text differs from original root message"
            for malformed in (b'%m1',b'%s12',b'%v220|255'*9):
                error,_,_=run(fixture(bytes([101,1,134,1,0]),message=malformed))
                assert error, ('malformed format accepted',malformed)
            print('PASS: byte math, CoCo zero-divisor results and continuation, random range edges, follow completion/high flag, signed/absolute placement and blocked-position search, stop/start/force update and retained sprites, pause/resume clock freezing, modal restoration, formatted variables/strings/words/object names/global messages, nested global/local contexts, lazy plain/LZW root loads, original Larry %g176 pixels and error restoration, high item indices, repeated cold calls, 511/512-byte name bounds and rejection bounds, and ownership cleanup')
        finally:
            d.s.close()
            emu.terminate()
            try:
                emu.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emu.kill()
                emu.wait(timeout=5)

if __name__=='__main__':main()
