#!/usr/bin/env python3
"""Verify priority-plane diagnostic display, dismissal and scene restoration."""
from pathlib import Path
import subprocess
import tempfile
from check_wbplay import fixture
from check_logic_executor import compile_module
from check_instances import symbols

ROOT=Path(__file__).resolve().parents[1]
from check_wbres import exercise, idle_rom, start_cpu


def compare_conversion(d,tmp):
    code,cs=compile_module(ROOT/'objs/shdw.asm',tmp/'shdw')
    original=bytes(range(256))*105
    start=cs['gfx_picbuff']
    d.write(0xe000,code); d.write(start,original)
    d.write(0x1df0,b'\x1f\0STACK'); d.breakpoint(0x1f00)
    d.regs(pc=0xe000+cs['PicBufUpdateRemap'],s=0x1df0,dp=0,cc=0x50)
    d.call('c');regs=d.regs()
    assert regs['pc']==0x1f00 and regs['s']==0x1df2
    swapped=d.read(start,len(original))
    assert swapped==bytes((n>>4)|((n&15)<<4) for n in original)
    assert d.read(0xe000,len(code))==code
    d.breakpoint(0x1f00,False)
    code=(ROOT/'objs/wbgame').read_bytes();gs=symbols(ROOT/'objs/wbgame.map')
    d.write(0,bytes(gs['size']));d.write(0xa000,code);d.breakpoint(0x7e00)
    for mode in (0,1):
        for offset in (0,160):
            source=original[offset:offset+160]
            reference=(swapped if mode else original)[offset:offset+160]
            wanted=bytes(v for n in reference for v in ((n&15)+1,)*2)
            d.write(0x8000,b'G'+source+b'H');d.write(0x8200,b'I'+bytes(320)+b'J')
            d.write(gs['gamepresentwidth'],b'\xa0');d.write(gs['gamepriorityview'],bytes([mode]))
            private=d.read(0,gs['size'])
            d.write(0x5ff0,b'\x7e\0STACK')
            d.regs(pc=0xa000+gs['ConvertRow'],s=0x5ff0,u=0,x=0x8001,y=0x8201,dp=0,cc=0x50)
            d.call('c');regs=d.regs()
            assert (regs['pc'],regs['s'],regs['x'],regs['y'])==(0x7e00,0x5ff2,0x80a1,0x8341)
            assert d.read(0x8000,162)==b'G'+source+b'H'
            assert d.read(0x8200,322)==b'I'+wanted+b'J'
            assert d.read(0,gs['size'])==private
            assert d.read(0x5ff2,5)==b'STACK'
    assert d.read(0xa000,len(code))==code
    d.breakpoint(0x7e00,False)
    print('PASS: native color/priority conversion matches actual CoCo nibble swap for all 256 combined bytes, with input/state/stack/code guards')


def check_input_drain(d):
    code=(ROOT/'objs/wbgame').read_bytes();gs=symbols(ROOT/'objs/wbgame.map');base=0xa000
    begin=gs['GamePriorityPrepare'];end=gs['GamePriorityKey']
    sites={}
    for service in ('I$GetStt','I$Read'):
        needle=bytes([0x10,0x3f,gs[service]])
        offsets=[i for i in range(begin,end) if code[i:i+3]==needle]
        assert len(offsets)==1,(service,offsets)
        sites[base+offsets[0]]=service
    d.write(base,code);d.breakpoint(0x7e00)
    for addr in sites:d.breakpoint(addr)
    scenarios=[(n,None) for n in (0,1,7,8,255,256,257)]
    scenarios += [(1,(service,error)) for service in ('I$GetStt','I$Read')
                  for error in (gs['E$DevBsy'],gs['E$BMode'])]
    for length,failure in scenarios:
        queue=bytearray((i&255) for i in range(length));reads=0
        d.write(0,bytes([0xa5])*gs['size'])
        for field in ('assetmapped','picturemapped'):d.write(gs[field],b'\0')
        private=d.read(0,gs['size'])
        d.write(0x5fe0,b'G'*16+b'\x7e\0STACK')
        d.regs(pc=base+begin,s=0x5ff0,u=0,dp=0,cc=0x50)
        for _ in range(600):
            d.call('c');r=d.regs()
            if r['pc']==0x7e00:break
            service=sites[r['pc']];updates={'pc':r['pc']+3,'cc':r['cc']&~1}
            if failure and service==failure[0]:updates.update(b=failure[1],cc=r['cc']|1)
            elif service=='I$GetStt':
                if not queue:updates.update(b=gs['E$NotRdy'],cc=r['cc']|1)
            else:
                assert queue and r['x']==0x5fef and r['y']==1
                d.write(r['x'],bytes([queue.pop(0)]));reads+=1
            d.regs(**updates)
        else:raise AssertionError('input drain did not terminate')
        error=failure[1] if failure else gs['E$BMode'] if length>=256 else 0
        assert r['s']==0x5ff2 and r['u']==0
        assert bool(r['cc']&1)==bool(error),(length,failure,r)
        assert r['b']==error,(length,failure,r)
        assert reads==(0 if failure else min(length,256))
        assert d.read(0,gs['size'])==private
        assert d.read(0x5fe0,14)==b'G'*14 and d.read(0x5ff2,5)==b'STACK'
        assert d.read(base,len(code))==code
    for addr in [*sites,0x7e00]:d.breakpoint(addr,False)
    print('PASS: bounded fresh-input drain, empty/small/255/256/257-byte queues, readiness/read errors including high-valued errors, full private-state/stack/code guards')


def compare_reference_control(d,tmp):
    code,cs=compile_module(ROOT/'objs/mnln.asm',tmp/'mnln');base=0x8000
    hooks={base+cs[n]:n for n in ('gfx_picbuff_update','events_clear','GetKeyEvent')}
    d.write(base,code)
    for addr in [*hooks,0x7e00]:d.breakpoint(addr)
    for last in (13,27):
        queue=[0,255,ord('x'),last];events=[]
        d.write(0,bytes([0xa5])*4096);d.write(cs['GfxPicBufRotate'],b'\0')
        private=d.read(0,4096)
        d.write(0x5ff0,b'\x7e\0STACK')
        d.regs(pc=base+cs['CmdSaveGame'],s=0x5ff0,dp=0,cc=0x50)
        for _ in range(12):
            d.call('c');r=d.regs()
            if r['pc']==0x7e00:break
            name=hooks[r['pc']];events.append(name)
            assert d.read(cs['GfxPicBufRotate'],1)==b'\1'
            updates={'pc':int.from_bytes(d.read(r['s'],2),'big'),'s':r['s']+2}
            if name=='GetKeyEvent':
                key=queue.pop(0)
                updates.update(a=key,cc=(r['cc']&~0x0f)|(4 if not key else 0)|(8 if key&128 else 0))
            d.regs(**updates)
        else:raise AssertionError('CoCo priority diagnostic did not return')
        assert not queue
        assert events==['gfx_picbuff_update','events_clear',*['GetKeyEvent']*4,'gfx_picbuff_update']
        assert r['s']==0x5ff2 and d.read(0x5ff2,5)==b'STACK'
        assert d.read(0,4096)==private
        assert d.read(base,len(code))==code
    for addr in [*hooks,0x7e00]:d.breakpoint(addr,False)
    print('PASS: actual CoCo command swaps/blits twice, clears pending events once, ignores null/non-key/ordinary input, accepts Enter/Escape and preserves private state/stack/code')


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-priority-view-') as name:
        d, proc = start_cpu(idle_rom(Path(name)/'idle.rom'), timeout=900)
        try:
            d.write(0xffdf,b'\0'); d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\1'); d.write(0xffa8,bytes(range(8)))
            compare_reference_control(d,Path(name))
            compare_conversion(d,Path(name))
            check_input_drain(d)
            code=bytes([3,21,9,12,15,3,0,1,24,0,25,0,26,29,29,3,220,42,134,1,0])
            picture=b'\xf0\x03\xf2\x08\xf8\0\0\xff'
            def pages(first,count):
                data=bytearray()
                try:
                    for page in range(count):
                        d.write(0xffac,bytes([first+page]))
                        data.extend(d.read(0x8000,8192))
                finally:d.write(0xffac,b'\4')
                return bytes(data)
            logical={'vmvariables':256,'vmflags':256,'vmobjects':2752,
                     'vmstrings':480,'textcharacters':2000,'menutitles':992}
            gs=symbols(ROOT/'objs/wbgame.map')
            for last in (13,27,5):
                shown=[];before={}
                def prepare(d,regs,syms):
                    for field,length in logical.items():before[field]=d.read(syms[field],length)
                    first=int.from_bytes(d.read(syms['picturefirst'],2),'big')
                    before['picture']=pages(first,4)
                def observe(d,regs,syms):
                    assert d.read(syms['gamepriorityview'],1)==b'\1'
                    assert d.read(syms['parsercharacter'],1)==b'x', 'stale input dismissed a new priority display'
                    first=int.from_bytes(d.read(syms['firstblock'],2),'big')
                    data=pages(first,10)
                    assert data[8*320:176*320]==bytes([9])*(168*320), 'priority plane was not displayed'
                    shown.append(True)
                def restored(d,regs,syms):
                    assert d.read(syms['gamepriorityview'],1)==b'\0'
                    assert d.read(syms['dialoginputmode'],1)==b'\0'
                    for field,length in logical.items():
                        wanted=bytearray(before[field])
                        if field=='vmvariables':wanted[220]=42
                        assert d.read(syms[field],length)==wanted,('changed logical state',field)
                    first=int.from_bytes(d.read(syms['picturefirst'],2),'big')
                    assert pages(first,4)==before['picture'],'combined color/priority buffer changed'
                error,frame,state=exercise(d,fixture(code,picture),module='wbgame',
                    base=0xa000,database=0,window=0x8000,blocks=None,multiple=True,
                    firstblock=0x10,capture=True,frame_capture=True,keyboard=b'\r',
                    keyboard_by_cycle={1:(b'x'+bytes([last]),0),2:(b'x'+bytes([last]),0)},
                    breakpoint_hooks={'GamePriorityPrepare':prepare,'GamePriorityKey':observe,
                                      'GameQuitCommand':restored})
                assert not error, ('priority view command',last,error)
                assert shown, 'priority display checkpoint was not reached'
                assert state['vmvariables'][220]==42, 'following command was not executed'
                assert frame[8*320:176*320]==bytes([4])*(168*320), 'color scene was not restored'
            for stage in ('show','restore'):
                seen=False;failed=False
                def fail_map(d,regs,syms):
                    nonlocal seen,failed
                    priority=d.read(syms['gamepriorityview'],1)==b'\1'
                    seen|=priority
                    match=priority if stage=='show' else seen and not priority
                    if match and not failed:failed=True;return True
                    return False
                error,frame,state=exercise(d,fixture(code,picture),module='wbgame',
                    base=0xa000,database=0,window=0x8000,blocks=None,multiple=True,
                    firstblock=0x10,capture=True,frame_capture=True,
                    keyboard_by_cycle={1:(b'\r',0)},map_failure=fail_map)
                assert failed and error==gs['E$MemFul'],('presentation failure',stage,error)
                assert d.read(gs['gamepriorityview'],1)==b'\0'
                assert d.read(gs['dialoginputmode'],1)==b'\0'
                assert state['vmvariables'][220]==0, 'failed diagnostic continued execution'
            failed=False
            def cached_unmap_fail(d,regs,syms):
                nonlocal failed
                match=(d.read(syms['vmopcode'],1)==bytes([29]) and
                       int.from_bytes(d.read(syms['showentry'],2),'big')!=0 and
                       d.read(syms['gamepriorityview'],1)==b'\0')
                if match and not failed:failed=True;return True
                return False
            error,_,state=exercise(d,fixture(code,picture),module='wbgame',
                base=0xa000,database=0,window=0x8000,blocks=None,multiple=True,
                firstblock=0x10,capture=True,keyboard_by_cycle={1:(b'\r',0)},
                unmap_error=cached_unmap_fail)
            assert failed and error==gs['E$MemFul'] and state['vmvariables'][220]==0
            assert d.read(gs['gamepriorityview'],1)==b'\0'
            empty=fixture(bytes([29,3,220,42,134,1,0]))
            empty_shown=[]
            def empty_observe(d,regs,syms):
                first=int.from_bytes(d.read(syms['firstblock'],2),'big')
                data=pages(first,10)
                assert data[8*320:176*320]==bytes([5])*(168*320)
                empty_shown.append(True)
            error,frame,state=exercise(d,empty,module='wbgame',base=0xa000,
                database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,
                capture=True,frame_capture=True,keyboard_by_cycle={1:(b'\r',0)},
                breakpoint_hooks={'GamePriorityKey':empty_observe})
            assert not error and empty_shown and state['vmvariables'][220]==42
            assert frame[8*320:176*320]==bytes([1])*(168*320)
            failed=False
            def empty_fail(d,regs,syms):
                nonlocal failed
                if not failed and d.read(syms['vmopcode'],1)==bytes([29]):
                    failed=True;return True
                return False
            error,_,state=exercise(d,empty,module='wbgame',base=0xa000,
                database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,
                capture=True,map_failure=empty_fail)
            assert failed and error==gs['E$MemFul'] and state['vmvariables'][220]==0
            assert d.read(gs['gamepriorityview'],1)==b'\0'
            print('PASS: priority diagnostic before the first picture, safe default canvas, blank-creation map failure and cleanup')
            print('PASS: visible priority pixels, repeated cached calls, fresh Enter/Escape dismissal, ignored ordinary keys, color restoration, unchanged combined buffer/gameplay/text/menu state, show/restore/cached-unmap failures and ownership cleanup')
        finally:
            d.s.close();proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)


if __name__=='__main__':main()
