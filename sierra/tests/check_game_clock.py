#!/usr/bin/env python3
"""Run real CoCo/native clocks and the public-service raster frame gate."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
EDGES = {0, 1, 23, 24, 59, 60, 127, 128, 254, 255}


def advance(clock, ticks=1):
    clock = list(clock)
    for _ in range(ticks):
        for field, modulus in enumerate((60, 60, 24, 256)):
            clock[field] = (clock[field]+1) & 255
            if clock[field] < modulus: break
            clock[field] = 0
    return bytes(clock)


def check_frame_gate(d, code, syms, listing, base=0xa000):
    private=0x1000;stack=0x7ef0;finish=0x7e00
    calls={base+int(m[1],16):int(m[2],16) for m in re.finditer(
        r'^([0-9A-F]{4}) 103F([0-9A-F]{2}).*os9',listing.read_text(),re.M)}
    d.write(base,code)
    for address in calls:d.breakpoint(address)
    d.breakpoint(finish)
    def state(**fields):
        data=bytearray(syms['size'])
        data[syms['resourcebase']:syms['resourcebase']+2]=private.to_bytes(2,'big')
        for name,value in fields.items():
            if isinstance(value,int):value=bytes([value])
            data[syms[name]:syms[name]+len(value)]=value
        d.write(private,data+b'GUARD')
    def byte(name):return d.read(private+syms[name],1)[0]
    def put(name,value):d.write(private+syms[name],bytes([value]))
    def execute(entry,on_sleep=None,capabilities=7,open_error=0,register_error=0,get_error=0,unmap_error=0):
        sleeps=[];statuses=[];paths=set()
        d.write(stack,finish.to_bytes(2,'big')+b'STACK')
        d.regs(pc=base+syms[entry],s=stack,u=private,x=0x1234,y=0x2345,dp=private>>8,cc=0x50)
        for _ in range(1000):
            d.call('c');r=d.regs()
            if r['pc']==finish:
                assert r['s']==stack+2 and d.read(stack+2,5)==b'STACK'
                assert d.read(private+syms['size'],5)==b'GUARD'
                return r,sleeps,statuses,paths
            service=calls[r['pc']];updates={'pc':r['pc']+3,'cc':r['cc']&~1}
            if service==syms['F$Sleep']:
                sleeps.append(r['x'])
                if on_sleep:on_sleep(r)
            elif service==syms['F$ClrBlk']:
                assert r['u']==0x8000 and r['b']==1 and byte('mapped')==1
                if unmap_error:updates.update(b=unmap_error,cc=r['cc']|1)
            elif service==syms['I$Open']:
                assert d.read(r['x'],6)==b'/fSOL\r' and r['a']==syms['UPDAT.']
                if open_error:updates.update(b=open_error,cc=r['cc']|1)
                else:paths.add(7);updates['a']=7
            elif service==syms['I$GetStt']:
                assert r['a']==7 and r['b']==syms['SS.SOLIRQ'] and r['x']==0
                updates.update(x=capabilities,y=byte('gameclockticks'))
                if get_error:updates.update(b=get_error,cc=r['cc']|1)
            elif service==syms['I$SetStt']:
                assert r['a']==7
                if r['b']==syms['SS.SOLMUTE']:assert byte('mapped')==0
                statuses.append((r['b'],r['x'],r['y']))
                if register_error and r['b']==syms['SS.SOLIRQ'] and r['y']:
                    updates.update(b=register_error,cc=r['cc']|1)
            elif service==syms['I$Close']:
                assert r['a']==7
                paths.discard(7)
            elif service==syms['F$Time']:
                d.write(r['x'],bytes([26,10,6,12,0,30]))
            else:raise AssertionError(('unexpected clock service',service,r))
            d.regs(**updates)
        raise AssertionError('unbounded frame gate')
    count=0
    for delay in (0,1,2,85,255):
        state(gameclockpath=255,**{'vmvariables':bytes(10)+bytes([delay])})
        before=d.read(private,syms['size'])
        r,sleeps,statuses,paths=execute('GameClockGate')
        assert not r['cc']&1 and sleeps==[3*delay+1] and not statuses and not paths
        assert d.read(private,syms['size'])==before
        count+=1
    for delay,seen,ticks,credit in ((0,0,0,0),(1,0,3,0),(2,0,30,0),
                                   (1,250,1,0),(1,0,2,2),(2,0,3,0),(255,0,0,0)):
        state(gameclockpath=7,gameclockseen=seen,gameclockticks=ticks,
              gameclockcredit=credit.to_bytes(2,'big'),
              **{'vmvariables':bytes(10)+bytes([delay])})
        def tick(r):
            assert r['x']==0
            put('gameclockticks',(byte('gameclockticks')+5)&255)
        r,sleeps,statuses,paths=execute('GameClockGate',on_sleep=None if not delay else tick)
        assert not r['cc']&1 and not statuses and not paths
        threshold=delay*3
        if not delay:assert sleeps==[1]
        else:
            initial=((ticks-seen)&255)+credit
            waits=max(0,(threshold-initial+4)//5)
            assert sleeps==[0]*waits
            assert int.from_bytes(d.read(private+syms['gameclockcredit'],2),'big')==min(initial+5*waits-threshold,threshold)
        count+=1
    for capabilities,error,registration in ((0,0,0),(1,0,0),(3,0,0),(7,syms['E$PNNF'],0),
                                              (7,0,syms['E$DevOvf']),(7,0,0)):
        state(gameclockpath=255)
        r,sleeps,statuses,paths=execute('GameClockOpen',capabilities=capabilities,
                                     open_error=error,register_error=registration)
        assert not r['cc']&1 and not r['b'] and not sleeps
        active=capabilities==7 and not error and not registration
        assert byte('gameclockpath')==(7 if active else 255)
        assert paths==({7} if active else set())
        if active:
            assert statuses==[(syms['SS.SOLIRQ'],0,syms['S$Wake'])]
            r,sleeps,statuses,paths=execute('GameClockClose')
            assert not r['cc']&1 and not r['b'] and byte('gameclockpath')==255
            assert statuses==[(syms['SS.SOLIRQ'],0,0)] and not paths
        count+=1
    state(gameclockpath=7,gameclockticks=150,gameclockseen=30,
          gameclockcredit=b'\0\x09',paused=1,mapped=1,mapbase=b'\x80\0')
    def resume(r):
        assert r['x']==2
        put('paused',0);put('gameclockreset',1)
    r,sleeps,statuses,paths=execute('foreground',on_sleep=resume)
    assert not r['cc']&1 and not r['b'] and (r['x'],r['y'],r['u'])==(0x1234,0x2345,private)
    assert sleeps==[2] and [item[:2] for item in statuses]==[(syms['SS.SOLMUTE'],1),(syms['SS.SOLMUTE'],0)]
    assert byte('gameclockmuted')==0 and byte('gameclockseen')==150 and byte('mapped')==0
    assert d.read(private+syms['gameclockcredit'],2)==b'\0\0'
    count+=1
    state(gameclockpath=7,paused=1,mapped=1,mapbase=b'\x80\0')
    r,sleeps,statuses,_=execute('foreground',unmap_error=207)
    assert r['cc']&1 and r['b']==207 and not sleeps and not statuses and byte('mapped')==1
    assert (r['x'],r['y'],r['u'])==(0x1234,0x2345,private)
    count+=1
    state(gameclockpath=7,gameclockreset=1,gameclockticks=150,gameclockseen=30,
          gameclockcredit=b'\0\x09',gameclocklast=12,
          **{'vmvariables':bytes(10)+b'\x02'})
    def reset_tick(r):put('gameclockticks',(byte('gameclockticks')+5)&255)
    r,sleeps,statuses,paths=execute('GameClockGate',on_sleep=reset_tick)
    assert not r['cc']&1 and sleeps==[0,0] and not statuses and not paths
    assert byte('gameclockreset')==0 and byte('gameclocklast')==30
    assert d.read(private+syms['gameclockcredit'],2)==b'\0\x04'
    assert d.read(private+syms['vmvariables']+11,4)==b'\0'*4
    count+=1
    state(gameclockpath=7,**{'vmvariables':bytes(10)+b'\x02'})
    def abort(r):put('aborted',1)
    r,sleeps,_,_=execute('GameClockGate',on_sleep=abort)
    assert r['cc']&1 and r['b']==syms['E$PrcAbt'] and sleeps==[0]
    count+=1
    state(gameclockpath=7,**{'vmvariables':bytes(10)+b'\x01'})
    r,sleeps,_,_=execute('GameClockGate',get_error=syms['E$BMode'] if 'E$BMode' in syms else 207)
    assert r['cc']&1 and not sleeps
    count+=1
    # Unrelated user signals must not alter the public driver counter snapshot.
    # Execute RTI with an interrupted DP/U unrelated to game storage.
    for ticks in (0,254,255):
        state(gameclockpath=7,gameclockticks=ticks)
        frame=b'\xd0\x11\x22\x33\x12\x34\x23\x45\x34\x56'+finish.to_bytes(2,'big')
        d.write(stack,frame+b'STACK')
        d.regs(pc=base+syms['intercept'],s=stack,u=private,b=0x83,dp=0x44,cc=0x50)
        d.call('c');r=d.regs()
        assert r['pc']==finish and r['s']==stack+12 and r['u']==0x3456 and r['dp']==0x33
        assert byte('gameclockticks')==ticks and d.read(stack+12,5)==b'STACK'
        count+=1
    for address in calls:d.breakpoint(address,False)
    assert d.read(base,len(code))==code
    print(f'PASS: {count} actual frame-clock cases; safe capability fallback, full-delay fallback, elapsed credit/wrap/cap, tick waits/yield, owned cleanup, muted foreground restoration, abort and RTI guards')


def check_cycle_flags(d, coco, cs, native, ns):
    calls=0
    for owner,code,syms in [('CoCo',coco,cs),('native',native,ns)]:
        private=0x1000
        flagbase=0x01ae if owner=='CoCo' else private+syms['vmflags']
        length=32 if owner=='CoCo' else 256
        for base in (0x8000,0x9000):
            d.write(base,code)
            for phase,flags in [('Input',(2,4)),('Room',(5,6))]:
                entry=base+syms[('ClearCycleFlags' if phase=='Input' else 'CycleRoomReset')
                                if owner=='CoCo' else 'GameCycle'+phase+'Reset']
                stop=base+syms['Cycle'+phase+'ResetDone']
                d.breakpoint(stop)
                for value in range(256):
                    before=bytearray([value]*length);wanted=bytearray(before)
                    for flag in flags:
                        if owner=='CoCo':wanted[flag>>3]&=255-(128>>(flag&7))
                        else:wanted[flag]=0
                    d.write(flagbase-1,b'G'+before+b'H')
                    d.write(0x7ef0,b'STACK')
                    u=0x7000 if owner=='CoCo' else private
                    d.regs(pc=entry,s=0x7ef0,u=u,x=0x3456,y=0x7654,b=0x93,dp=0,cc=0x50)
                    d.call('c');result=d.regs()
                    assert result['pc']==stop,(owner,phase,value,result)
                    assert d.read(flagbase-1,length+2)==b'G'+wanted+b'H',(owner,phase,value)
                    assert d.read(0x7ef0,5)==b'STACK'
                    for reg,expected in [('s',0x7ef0),('u',u),('x',0x3456),('y',0x7654),('b',0x93)]:
                        assert result[reg]==expected,(owner,phase,reg,result)
                    calls+=1
                d.breakpoint(stop,False)
            assert d.read(base,len(code))==code
    print(f'PASS: {calls} actual CoCo/native cycle-flag boundaries; every packed-byte/private-byte value, input and room/restart flags, unrelated flags, guards/registers/stack, two code addresses and immutable code',flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--gate-only',action='store_true')
    ap.add_argument('--cycle-only',action='store_true')
    args=ap.parse_args()
    with tempfile.TemporaryDirectory(prefix='sierra-clock-') as name:
        tmp = Path(name)
        coco, cs = compile_module(ROOT/'objs/sierra.asm', tmp/'sierra')
        native, ns = compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame', defines=('WILDBITS=1',),listing=True)
        mainline, ms = compile_module(ROOT/'objs/mnln.asm',tmp/'mnln') if not args.gate_only else (None,None)
        vectors = []
        for field in range(4):
            for value in range(256):
                clock = [59, 59, 23, 7]
                clock[field] = value
                vectors.append((bytes(clock), value in EDGES))
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=900)
        calls = 0
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            d.breakpoint(0x7e00)
            if args.gate_only:
                check_frame_gate(d,native,ns,tmp/'wbgame.list')
                return
            check_cycle_flags(d,mainline,ms,native,ns)
            if args.cycle_only:return
            for owner, code, syms, bases in [('CoCo', coco, cs, (0x8000, 0x9000)),
                                            ('native', native, ns, (0x9000, 0xa000))]:
                private = 0x1000
                clockaddr = private + (syms['TimeOfDay'] if owner == 'CoCo' else syms['vmvariables']+11)
                for base in bases:
                    d.write(base, code)
                    d.write(private, b'\x91'*syms['size'] + b'GUARD')
                    if owner == 'native':
                        d.write(private+syms['resourcebase'], private.to_bytes(2, 'big'))
                        kernel = base+syms['GameClockTimeCall']
                        d.breakpoint(kernel)
                    for clock, full_guard in vectors:
                        d.write(clockaddr-1, b'G'+clock+b'H')
                        if owner == 'CoCo':
                            timeraddr = private+syms['GameTimerB3']
                            # Carry all the way through the 32-bit timer.
                            d.write(timeraddr, b'\xff'*4)
                            d.write(private+syms['GamePausedFlag'], b'\0')
                            d.write(private+syms['TickAccum'], b'\0\x13')
                            d.write(private+syms['TickCountHi'], b'\x12\xff')
                        else:
                            d.write(private+syms['gameclocklast'], b'\x0c')
                            d.write(private+syms['gameclockreset'], b'\0')
                            d.write(private+syms['gameclockdelta'], b'\0')
                        before = d.read(private, syms['size']) if full_guard else None
                        d.write(0x7ef0, b'\x7e\x00STACK')
                        entry = base+syms['SigHandlerCore' if owner == 'CoCo' else 'GameReadClock']
                        d.regs(pc=entry, s=0x7ef0, u=private, dp=private >> 8, cc=0x50)
                        d.call('c'); regs = d.regs()
                        if owner == 'native':
                            assert regs['pc'] == kernel and regs['x'] == private+syms['gametime']
                            timebuf = bytes([26, 10, 5, 10, 11, 13])
                            d.write(regs['x'], timebuf)
                            d.regs(pc=kernel+3, cc=regs['cc'] & ~1)
                            d.call('c'); regs = d.regs()
                            assert not regs['cc'] & 1 and regs['b'] == 0
                            assert d.read(private+syms['gameclocklast'], 1) == b'\x0d'
                            assert d.read(private+syms['gameclockdelta'], 1) == b'\0'
                            assert d.read(private+syms['gameclockreset'], 1) == b'\0'
                        else:
                            assert d.read(timeraddr, 4) == b'\0'*4
                            assert d.read(private+syms['TickCountHi'], 2) == b'\x13\0'
                            assert d.read(private+syms['TickAccum'], 2) == b'\0\0'
                        wanted = advance(clock)
                        assert d.read(clockaddr-1, 6) == b'G'+wanted+b'H', (owner, clock, wanted)
                        assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2 and regs['u'] == private
                        assert d.read(0x7ef2, 5) == b'STACK'
                        assert d.read(private+syms['size'], 5) == b'GUARD'
                        if full_guard:
                            expected = bytearray(before)
                            offset = clockaddr-private
                            expected[offset:offset+4] = wanted
                            if owner == 'CoCo':
                                expected[syms['GameTimerB3']:syms['GameTimerB3']+4] = b'\0'*4
                                expected[syms['TickCountHi']:syms['TickCountHi']+2] = b'\x13\0'
                                expected[syms['TickAccum']:syms['TickAccum']+2] = b'\0\0'
                            else:
                                expected[syms['gametime']:syms['gametime']+6] = timebuf
                                expected[syms['gameclocklast']] = 13
                            assert d.read(private, syms['size']) == expected, (owner, clock)
                        calls += 1
                    if owner == 'CoCo':
                        for paused, accum in [(1, 19), (0, 0), (0, 18)]:
                            clock = bytes([59, 59, 23, 255])
                            d.write(clockaddr, clock)
                            d.write(private+syms['GamePausedFlag'], bytes([paused]))
                            d.write(private+syms['TickAccum'], accum.to_bytes(2, 'big'))
                            d.write(timeraddr, b'\0'*4)
                            d.write(private+syms['TickCountHi'], b'\0\x01')
                            d.write(0x7ef0, b'\x7e\x00STACK')
                            d.regs(pc=base+syms['SigHandlerCore'], s=0x7ef0, u=private, dp=private >> 8, cc=0x50)
                            d.call('c'); regs = d.regs()
                            assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                            assert d.read(clockaddr, 4) == clock
                            assert d.read(timeraddr, 4) == b'\0\0\0\x01'
                            assert d.read(private+syms['TickCountHi'], 2) == (1 if paused else 2).to_bytes(2, 'big')
                            assert d.read(private+syms['TickAccum'], 2) == (accum if paused else accum+1).to_bytes(2, 'big')
                            calls += 1
                    else:
                        # Minute wrap, multi-second delta, initial sample, modal reset,
                        # unchanged second, invalid OS second, and F$Time failure.
                        for last, now, reset, error in [(59,0,0,0), (58,1,0,0), (10,13,0,0),
                                                       (255,40,0,0), (10,40,1,0), (12,12,0,0),
                                                       (12,60,0,0), (12,13,0,syms['E$NotRdy'])]:
                            clock = bytes([59, 59, 23, 255])
                            d.write(clockaddr, clock)
                            d.write(private+syms['gameclocklast'], bytes([last]))
                            d.write(private+syms['gameclockreset'], bytes([reset]))
                            d.write(private+syms['gameclockdelta'], b'\0')
                            d.write(0x7ef0, b'\x7e\x00STACK')
                            d.regs(pc=base+syms['GameReadClock'], s=0x7ef0, u=private, dp=private >> 8, cc=0x50)
                            d.call('c'); regs = d.regs()
                            assert regs['pc'] == kernel
                            if not error: d.write(regs['x'], bytes([26,10,5,10,11,now]))
                            d.regs(pc=kernel+3, b=error, cc=(regs['cc'] & ~1) | bool(error))
                            d.call('c'); regs = d.regs()
                            rejected = bool(error or now >= 60)
                            ticks = 0 if rejected or reset or last == 255 else (now-last) % 60
                            assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                            assert bool(regs['cc'] & 1) == rejected
                            assert regs['b'] == (error or syms['E$BMode'] if rejected else 0)
                            assert d.read(clockaddr, 4) == advance(clock, ticks)
                            assert d.read(private+syms['gameclocklast'], 1) == bytes([last if rejected else now])
                            assert d.read(private+syms['gameclockreset'], 1) == bytes([reset if rejected else 0])
                            assert d.read(0x7ef2, 5) == b'STACK'
                            calls += 1
                        d.breakpoint(kernel, False)
                    assert d.read(base, len(code)) == code
            check_frame_gate(d,native,ns,tmp/'wbgame.list')
            print(f'PASS: {calls} real CoCo/native clock calls; every byte in all four fields, sec/min/hour/day rollover and byte wrapping, paused/subsecond CoCo timer and 32-bit carry, native OS time/delta/reset/error policy, two code bases, full-state edge checks, guards/stack and immutable code')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
