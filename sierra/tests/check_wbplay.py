#!/usr/bin/env python3
"""Exercise native gameplay math, following, placement and modal restoration."""
import subprocess
from pathlib import Path
import tempfile
from check_wbres import exercise, idle_rom, start_cpu


def queued_menu_script(request,continuation):
    """First cycle issues a request; the next cycle inspects its outcome.

    v250 is a fixture-only guard. Returning from logic is essential: commands
    following menu_input still run before the event loop displays the menu.
    """
    first=request+bytes([3,250,1,0])
    return bytes([255,253,1,250,1,255])+len(first).to_bytes(2,'little')+first+continuation


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


def run_coco_motion_reference(d, temp_dir, records=None, ticks=10,
                              dispatch_motion=False, completion_flag=255):
    """Run actual CoCo motion code with only its MMU terrain service mocked."""
    from check_logic_executor import compile_module

    source=Path(__file__).resolve().parents[1]/'objs/mnln.asm'
    code,syms=compile_module(source,Path(temp_dir)/'coco-motion-reference')
    # UpdateAllMotion and FindObjPos call the CoCo MMU placement service.
    # Redirect just those two JSR operands to a tiny test shim that reports a
    # successful placement on walkable terrain; leave motion/collision code
    # and both original routines assembled from mnln.asm.
    sites=[]
    for start,end in ((syms['UpdateAllMotion'],syms['SetObjMotion']),
                      (syms['FindObjPos'],syms['FindObjPosDone'])):
        offset=start
        while True:
            offset=code.find(bytes.fromhex('bd0701'),offset)
            if offset<0 or offset>=end:
                break
            sites.append(offset)
            offset+=1
    assert len(sites)==2,('unexpected CoCo MMU calls in motion routines',sites)

    base=0x8000
    shim=base+len(code)+0x10
    assert shim+5<0xfe00
    image=bytearray(code)
    for offset in sites:
        image[offset+1:offset+3]=shim.to_bytes(2,'big')
    d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c')
    d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
    d.write(base,image)
    # lda #1; sta <$5c; rts. The CoCo placement contract uses this flag to
    # accept the candidate after its bounds/collision checks.
    d.write(shim,bytes.fromhex('8601975c39'))

    objects=0x3000
    if records is None:
        records=bytearray(3*43)
        for index,x,direction in ((1,10,3),(2,30,7)):
            offset=index*43
            records[offset+2]=index       # CoCo collision filtering uses identity
            records[offset+3:offset+5]=bytes((x,60))
            records[offset+0x1c:offset+0x1e]=bytes((1,1))
            records[offset+0x1e]=1         # step size
            records[offset+0x21]=direction
            records[offset+0x26]=0x51      # animated, visible, updated
    else:
        records=bytearray(records)
        assert len(records)==2*43
    d.write(0x30,objects.to_bytes(2,'big'))
    d.write(0x32,(objects+len(records)).to_bytes(2,'big'))
    d.write(objects,records)
    d.write(0x01ae,bytes(32))          # clear flags, including follow result 255
    d.write(0x01d6,b'\0')             # test scene has no horizon line
    d.write(0x005c,b'\0')
    d.breakpoint(0x7e00)
    try:
        for _ in range(ticks):
            if dispatch_motion:
                d.write(0x7ef0,b'\x7e\0STACK')
                d.regs(pc=base+syms['DispatchMotion'],s=0x7ef0,u=0,
                       dp=0,cc=0x50)
                d.call('c')
                regs=d.regs()
                assert regs['pc']==0x7e00 and regs['s']==0x7ef2,regs
                assert d.read(0x7ef2,5)==b'STACK'
            d.write(0x7ef0,b'\x7e\0STACK')
            d.regs(pc=base+syms['UpdateAllMotion'],s=0x7ef0,u=0,
                   dp=0,cc=0x50)
            d.call('c')
            regs=d.regs()
            assert regs['pc']==0x7e00 and regs['s']==0x7ef2,regs
            assert d.read(0x7ef2,5)==b'STACK'
        result=d.read(objects,len(records))
        assert d.read(base,len(image))==image,'CoCo motion routine changed code'
        if dispatch_motion:
            flag_byte,flag_bit=divmod(completion_flag,8)
            motion_flag=bool(d.read(0x01AE+flag_byte,1)[0]&(1<<(7-flag_bit)))
            return result[43:86],motion_flag
        return (result[46:48],result[89:91])
    finally:
        d.breakpoint(0x7e00,False)


def run_controlled_wander_pair(d, temp_dir):
    """Compare CoCo/native wander ticks with the random service held constant."""
    from check_logic_executor import compile_module

    root=Path(__file__).resolve().parents[1]/'objs'
    snapshots=[]
    d.breakpoint(0x7e00)
    for source,defines,base,private in (
            (root/'mnln.asm',(),0x8000,0),
            (root/'sierra.asm',('WILDBITS=1',),0xa000,0x1000)):
        code,syms=compile_module(source,Path(temp_dir)/source.stem,
                                  defines=defines)
        image=bytearray(code)
        # Both production owners have different random generators. Replace
        # only this service for the deterministic direction/counter test.
        image[syms['InitRandSeed']:syms['InitRandSeed']+3]=bytes.fromhex('c60739')
        d.write(base,image)
        obj=0x3000 if not private else private+syms['vmobjects']
        record=bytearray(43)
        record[2]=0                         # ego identity
        record[0x22]=1                      # wander motion
        record[0x26]=0x51                   # animated, visible, updated
        record[0x27]=0                      # force initial random direction
        if private:
            memory=bytearray(syms['size']+5)
            memory[syms['resourcebase']:syms['resourcebase']+2]=private.to_bytes(2,'big')
            memory[syms['vmobjects']:syms['vmobjects']+43]=record
            memory[syms['size']:]=b'GUARD'
            d.write(private,memory)
            variables=private+syms['vmvariables']
            dp=private>>8
        else:
            d.write(0x30,obj.to_bytes(2,'big'))
            d.write(0x32,(obj+43).to_bytes(2,'big'))
            d.write(0x0437,b'\0')
            variables=0x0431
            dp=0
        d.write(obj,record)
        trace=[]
        for tick in range(3):
            if tick==1:
                # A delay of one expires without another random roll when
                # random animation is off; the following tick rolls again.
                d.write(obj+0x27,b'\1')
                d.write(obj+0x25,b'\0')
            d.write(0x7ef0,b'\x7e\0STACK')
            d.regs(pc=base+syms['ObjAnimStep'],s=0x7ef0,u=obj,
                   x=private,dp=dp,cc=0x50)
            d.call('c')
            regs=d.regs()
            assert regs['pc']==0x7e00 and regs['s']==0x7ef2,regs
            assert d.read(0x7ef2,5)==b'STACK'
            current=d.read(obj,43)
            if tick==0:
                assert current[0x21]==7 and current[0x27]==7, (source.name,tick,current.hex())
            elif tick==1:
                assert current[0x21]==7 and current[0x27]==0, (source.name,tick,current.hex())
            else:
                assert current[0x21]==7 and current[0x27]==7, (source.name,tick,current.hex())
        # With random-animation enabled, direction selection is retried while
        # the delay counts down; short delays are raised to the minimum 6.
        d.write(obj+0x25,b'\x40')
        for tick in range(16):
            d.write(0x7ef0,b'\x7e\0STACK')
            d.regs(pc=base+syms['ObjAnimStep'],s=0x7ef0,u=obj,
                   x=private,dp=dp,cc=0x50)
            d.call('c')
            regs=d.regs()
            assert regs['pc']==0x7e00 and regs['s']==0x7ef2,regs
            current=d.read(obj,43)
            assert current[0x21]==7 and current[0x27] in (6,7) and current[0x25]&0x40,(
                source.name,'random-animation tick',tick,current.hex())
            trace.append((current[0x21],current[0x27],current[0x25]&0x40))
        direction=d.read(variables+6,1)[0] if private else d.read(0x0437,1)[0]
        assert direction==7,(source.name,'ego direction',direction)
        if private:
            assert d.read(private+syms['size'],5)==b'GUARD'
        snapshots.append((tuple(trace),direction))
    d.breakpoint(0x7e00,False)
    assert snapshots[0]==snapshots[1],snapshots
    print('PASS: CoCo and Wild Bits match 19 controlled wander ticks, including delay expiry, random-animation rerolls, ego direction publication, stack and native private guard')


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
            # Keep the target far enough away that the follower can finish
            # without either engine entering its platform-specific blocked
            # recovery path. The separate collision tests below cover that
            # policy; this case compares ordinary follow completion.
            setup=bytes([3,0,1,24,0,25,0,33,0,41,0,0,37,0,24,60,35,0,
                         33,1,41,1,0,37,1,10,60,35,1,67,1,83,1,2,255,26])
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
            follow_start={}
            def capture_follow_start(cpu,regs,syms):
                if 'objects' not in follow_start:
                    follow_start['objects']=cpu.read(syms['vmobjects'],2*43)
                return False
            error,_,s=run(fixture(script,b'\xff',view),
                          breakpoint_hooks={'GameNextCycle':capture_follow_start})
            follower=s['vmobjects'][43:86]
            assert not error and s['vmflags'][255]==1 and follower[0x21:0x23]==bytes(2), (error,follower.hex())
            # Follow motion uses the shared eight-way direction quantizer.
            # A nearly horizontal target can therefore advance one pixel on
            # Y while closing the X gap; assert progress and the bounded
            # diagonal error instead of requiring a cardinal-only path.
            assert abs(follower[3]-24)<=2 and abs(follower[4]-60)<=1, follower.hex()
            # The hook snapshots at the first GameNextCycle boundary, before
            # that cycle's native motion update; include that pending update
            # when replaying the same cycle count in the CoCo routines.
            coco_follower,coco_follow_flag=run_coco_motion_reference(
                d,tmp,follow_start['objects'],s['cycles']+1,dispatch_motion=True)
            assert (abs(coco_follower[3]-follower[3])<=1 and
                    abs(coco_follower[4]-follower[4])<=1),(
                'CoCo/Wild Bits follow position exceeds one-pixel tolerance',
                coco_follower[3:5],follower[3:5])
            assert coco_follower[0x21:0x23]==follower[0x21:0x23],(
                'CoCo/Wild Bits follow stop state mismatch',
                coco_follower[0x21:0x23],follower[0x21:0x23])
            assert coco_follow_flag, 'CoCo did not set the follow-complete flag'
            # When the ego blocks the follower's next step and ignore.objs is
            # off, neither owner may turn random-animation bit 6 into synthetic
            # collision state. Both should remain in follow motion at the last
            # collision-free coordinate, without completing the follow flag.
            setup=bytes([3,0,1,24,0,25,0,33,0,41,0,0,37,0,20,60,35,0,
                         33,1,41,1,0,37,1,10,60,35,1,83,1,2,255,26])
            script=bytes([255,7,11,255])+len(setup).to_bytes(2,'little')+setup
            script+=bytes([1,250,255,7,255,255,2,0,134,1,
                           255,1,250,30,255,2,0,134,1,0])
            follow_start={}
            def capture_blocked_start(cpu,regs,syms):
                if 'objects' not in follow_start:
                    follow_start['objects']=cpu.read(syms['vmobjects'],2*43)
                return False
            error,_,s=run(fixture(script,b'\xff',view),
                          breakpoint_hooks={'GameNextCycle':capture_blocked_start})
            follower=s['vmobjects'][43:86]
            coco_follower,coco_blocked_flag=run_coco_motion_reference(
                d,tmp,follow_start['objects'],s['cycles']+1,dispatch_motion=True)
            assert not error and s['vmflags'][255]==0 and not coco_blocked_flag,(
                'blocked follow unexpectedly completed',error,s['vmflags'][255],
                coco_blocked_flag)
            assert follower[3:5]==coco_follower[3:5],(
                'blocked follow moved differently',follower[3:5],coco_follower[3:5])
            assert follower[0x21:0x23]==coco_follower[0x21:0x23],(
                'blocked follow direction/state mismatch',
                follower[0x21:0x23],coco_follower[0x21:0x23])
            assert not follower[0x25]&0x40 and not coco_follower[0x25]&0x40,(
                'blocked follow altered random-animation flag',
                follower[0x25],coco_follower[0x25])
            # Drive move.obj to its exact target in the real loaded Wild Bits
            # event loop, then replay those object records through CoCo's
            # DispatchMotion/UpdateAllMotion pair with its terrain service
            # stubbed to this empty, walkable test scene.
            setup=bytes([3,0,1,24,0,25,0,33,1,41,1,0,37,1,10,60,35,1,
                         81,1,20,60,1,200])
            script=bytes([255,7,11,255])+len(setup).to_bytes(2,'little')+setup
            script+=bytes([255,7,200,255,2,0,134,1,0])
            move_start={}
            def capture_move_start(cpu,regs,syms):
                if 'objects' not in move_start:
                    move_start['objects']=cpu.read(syms['vmobjects'],2*43)
                return False
            error,_,s=run(fixture(script,b'\xff',view),cycle_limit=48,
                breakpoint_hooks={'GameNextCycle':capture_move_start})
            mover=s['vmobjects'][43:86]
            coco_mover,coco_move_flag=run_coco_motion_reference(
                d,tmp,move_start['objects'],s['cycles']+1,
                dispatch_motion=True,completion_flag=200)
            assert not error and s['vmflags'][200]==1 and coco_move_flag,(
                'CoCo/Wild Bits move.obj did not complete',error,
                s['vmflags'][200],coco_move_flag,mover.hex(),s['cycles'])
            assert mover[3:5]==coco_mover[3:5]==bytes([20,60]),(
                'CoCo/Wild Bits move.obj target position mismatch',
                mover[3:5],coco_mover[3:5])
            assert mover[0x21:0x23]==coco_mover[0x21:0x23],(
                'CoCo/Wild Bits move.obj final direction/state mismatch',
                mover[0x21:0x23],coco_mover[0x21:0x23])
            print('PASS: original CoCo motion routines and loaded Wild Bits cycle complete move.obj at the same target and set completion flag 200')
            run_controlled_wander_pair(d,tmp)
            # Exercise two simultaneously active movers through the loaded
            # game cycle. They approach on the same row; the first actor's
            # committed move must be visible to the second actor's collision
            # scan, and neither actor may finish inside the other's bounds.
            setup=bytes([3,0,1,3,3,3,3,4,7,24,0,25,0,
                         33,1,41,1,0,37,1,10,60,35,1,68,1,86,1,3,
                         33,2,41,2,0,37,2,30,60,35,2,68,2,86,2,4])
            script=bytes([255,7,11,255])+len(setup).to_bytes(2,'little')+setup
            script+=bytes([1,250,255,7,255,255,2,0,134,1,
                           255,1,250,30,255,2,0,134,1,0])
            error,_,s=run(fixture(script,b'\xff',view))
            left=s['vmobjects'][43:86];right=s['vmobjects'][86:129]
            assert not error,('two moving actors',error,s.get('vmerror'),s.get('asseterror'),s.get('vmobjects',b'')[:129].hex())
            assert left[3:5]==bytes([19,60]) and right[3:5]==bytes([21,60]), \
                ('ordered collision resolution',left.hex(),right.hex())
            coco_left,coco_right=run_coco_motion_reference(d,tmp)
            assert (coco_left,coco_right)==(left[3:5],right[3:5]), \
                ('CoCo/Wild Bits ten-tick movement mismatch',coco_left,coco_right,
                 left[3:5],right[3:5])
            print('PASS: ten actual CoCo UpdateAllMotion ticks match the loaded Wild Bits two-mover game cycle; both actors stop at the shared collision edge')
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
            # The first menu item is disabled. CoCo's Up event wraps from the
            # head to the final (enabled) item; Down intentionally returns to
            # the head, so use Up before Enter in this case.
            for keys, selected in [(b'\x0c\r',True),(b'\x1b',False),(b'\x05',False),(b'\r\x0c\r',True)]:
                body=queued_menu_script(bytes([12,14,3,0,1,24,0,25,0,26,156,1,157,2,254,157,3,255,158,160,254,161]),
                            bytes([255,12,255,255,2,0,12,200,134,1,0]))
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
            # word.to.string takes destination slot first, then the one-based
            # parsed-word index. Put parsed word 2 ("tree") into string 1,
            # which the following %s1 message reads.
            body=bytes([114,0,1,117,0,116,1,2,103,3,0,2,134,1,0])
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
            # A missing logic now displays the native not-found dialog before
            # the loader returns E$PNNF; provide the dismissal key explicitly.
            error,_,state = run(files,arguments=b"/game 1\r",keyboard=b"\r")
            assert error and state["vmcurrent"] == b"\0" and state["vmend"] == b"\0\x10", "missing global resource damaged caller"
            # Space Quest II logic 82 message 4 contains the original `%m`
            # missing-operand form. Preserve its actual message table while
            # replacing only the script with a controlled print-and-quit.
            from audit_game_scripts import logic_resource, message_formats
            def original_logic_message(game_name,logic_number,message_number):
                game = Path(__file__).resolve().parents[1]/game_name
                directory = (game/"logDir").read_bytes()
                entry = int.from_bytes(directory[logic_number*3:logic_number*3+3],"big")
                payload, encrypted = logic_resource(game,logic_number,entry)
                code_end = 2+int.from_bytes(payload[:2],"little")
                count = payload[code_end]
                base = code_end+1
                start = base+2+2*count
                end = base+int.from_bytes(payload[base:base+2],"little")
                offset = int.from_bytes(payload[base+2+(message_number-1)*2:
                                                base+4+(message_number-1)*2],"little")
                strings = bytearray(payload[start:end])
                if encrypted:
                    strings = bytearray(value ^ key[i%11] for i,value in enumerate(strings))
                position = base+offset-start
                return bytes(strings[position:strings.find(0,position)]), payload, encrypted

            original_message_four, original, encrypted = original_logic_message("spacequest2",82,4)
            assert encrypted and original_message_four.startswith(b"%m") and any(
                item["message"] == 4 and item["directive"] == "m" and not item["operand"]
                for item in message_formats(original,encrypted)), "Space Quest II original `%m` sample changed"
            body = bytes([101,1,134,1,0])
            def original_message_files(text):
                return fixture(body,message=text)
            visible_without_operand = original_message_four[2:]
            error,frame,state = run(original_message_files(original_message_four),keyboard=b"\r",frame_capture=True)
            assert not error and state["vmcurrent"] == b"\0", ("Space Quest II original `%m` missing operand",error,state.get("vmerror"),state.get("asseterror"))
            literal_error,literal_frame,literal_state = run(original_message_files(visible_without_operand),
                                                              keyboard=b"\r",frame_capture=True)
            assert not literal_error and literal_state["vmcurrent"] == b"\0", ("Space Quest II literal control",literal_error)
            assert frame == literal_frame, "original `%m` did not expand to the same text as its literal suffix"
            print("PASS: original Space Quest II logic 82 `%m` without an operand matches the literal suffix pixel-for-pixel and exits cleanly")
            original_message_twenty_nine, original, encrypted = original_logic_message("spacequest1",0,29)
            assert encrypted and b"%s" in original_message_twenty_nine and any(
                item["message"] == 29 and item["directive"] == "s" and not item["operand"]
                for item in message_formats(original,encrypted)), "Space Quest I original `%s` sample changed"
            literal_without_slot_zero = original_message_twenty_nine.replace(b"%s",b"",1)
            error,frame,state = run(original_message_files(original_message_twenty_nine),
                                    keyboard=b"\r",frame_capture=True)
            assert not error and state["vmcurrent"] == b"\0", ("Space Quest I original `%s` missing operand",error)
            literal_error,literal_frame,literal_state = run(original_message_files(literal_without_slot_zero),
                                                              keyboard=b"\r",frame_capture=True)
            assert not literal_error and literal_state["vmcurrent"] == b"\0", ("Space Quest I literal control",literal_error)
            assert frame == literal_frame, "original `%s` did not match its literal text with empty string slot zero"
            print("PASS: original Space Quest I logic 0 `%s` without an operand matches the literal text with empty slot zero and exits cleanly")
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
            # These edge spellings are valid bounded/literal cases for the
            # CoCo-compatible formatter; supply Enter because print remains
            # modal even when the expansion is empty.
            for edge_case in (b'%m1',b'%s12',b'%v220|255'*9):
                error,_,state=run(fixture(bytes([101,1,134,1,0]),message=edge_case),
                                  keyboard=b'\r')
                assert not error and state['vmerror']==b'\0' and state['vmcurrent']==b'\0', \
                    ('formatter edge cleanup',edge_case,error,state.get('vmerror'))
            print('PASS: byte math, CoCo zero-divisor results and continuation, random range edges, completed and collision-blocked follow versus CoCo, random-animation flag preservation, two active movers and ordered collision resolution, signed/absolute placement and blocked-position search, stop/start/force update and retained sprites, pause/resume clock freezing, modal restoration, formatted variables/strings/words/object names/global messages, nested global/local contexts, lazy plain/LZW root loads, original Larry %g176 pixels and error restoration, high item indices, repeated cold calls, 511/512-byte name bounds and rejection bounds, and ownership cleanup')
        finally:
            d.s.close()
            emu.terminate()
            try:
                emu.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emu.kill()
                emu.wait(timeout=5)

if __name__=='__main__':main()
