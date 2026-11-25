#!/usr/bin/env python3
"""Execute native AGI picture commands through the integrated game owner."""
from pathlib import Path
import argparse
import subprocess
import tempfile
import re
from check_wbres import exercise, idle_rom, start_cpu
from check_instances import symbols
from check_wbplay import queued_menu_script
ROOT = Path(__file__).resolve().parents[1]
from export_picture import resource, render


def check_object_status_commands(d):
    """Exercise actual scripts and modal lifetime, not just the formatter entry."""
    for obj in (0,63,64,255):
     body=bytes([3,255,obj,12,15,133,255,134,1,0]);logic=len(body).to_bytes(2,'little')+body
     files={'/game/logDir':b'\xff'*3+bytes(3),'/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic}
     error,out,state=exercise(d,files,module='wbgame',base=0xa000,database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,module_root=ROOT/'objs',os_call_limit=20000)
     print('OBJECT',obj,'ERROR',error,'TEXT',state['messagebuffer'].split(b'\0')[0],flush=True)
     assert error==(0 if obj<64 else 187),(obj,error)
     if obj<64:assert state['messagebuffer'].startswith(f'Object {obj}:\n'.encode()) and state['vmflags'][15]==0
    for label,setup,keys,future,wanted_sleeps in [
        ('cached repeat',bytes([12,15,133,255]),b'old\r',{1:b'x',2:b'\r'},2),
      ('fresh Enter',b'',b'old\r',{1:b'x',2:b'\r'},2),
        ('fresh physical Escape',b'',b'old\r',{1:b'x',2:b'\x05'},2),
        ('fresh AGI Escape',b'',b'old\r',{1:b'x',2:b'\x1b'},2),
        ('timed ordinary key rejected',bytes([3,21,1]),b'x\r',None,0),
        ('timed expiry',bytes([3,21,1]),b'',None,30)]:
     body=setup+bytes([133,255,134,1,0]);logic=len(body).to_bytes(2,'little')+body
     files={'/game/logDir':b'\xff'*3+bytes(3),'/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic}
     error,out,state=exercise(d,files,module='wbgame',base=0xa000,database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,module_root=ROOT/'objs',os_call_limit=20000,keyboard=keys,keyboard_by_sleep=future)
     print(label,error,state['sleeps'],flush=True)
     assert error==0 and state['sleeps']==wanted_sleeps and state['vmvariables'][21]==0,(label,error,state['sleeps'])
    directory=b'/'+b'a'*126
    volume=bytearray();entries=[b'\xff'*3]
    for number in range(1,18):
        body=bytes([22,number+1,0]) if number<17 else bytes([3,255,63,12,15,133,255,134,1,0])
        logic=len(body).to_bytes(2,'little')+body
        entries.append(len(volume).to_bytes(3,'big'))
        volume+=b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
    files={directory.decode()+'/logDir':b''.join(entries),directory.decode()+'/vol.0':bytes(volume)}
    error,out,state=exercise(d,files,arguments=directory+b' 1\r',module='wbgame',base=0xa000,
        database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
        module_root=ROOT/'objs',os_call_limit=30000)
    assert error==0 and state['messagebuffer'].startswith(b'Object 63:\n'),(error,out)
    assert state['gamefont']==(ROOT/'objs/sierrafont').read_bytes(),'deep diagnostic damaged private font'
    print('PASS: object status at 16 nested calls and a 127-byte directory, private font intact and owned cleanup')
    print('PASS: real loaded object-status dispatch, held text, variable255, object0/63, invalid64/255 cleanup')


def check_memory_info_commands(d):
    """Read real module/cache extents through loaded zero-operand commands."""
    root=ROOT/'objs'
    for label,setup,keys,future,wanted_sleeps,bitmap in [
            ('held',bytes([12,15]),b'',None,0,0),
            ('cached repeat',bytes([12,15,135,12,15]),b'',None,0,10),
            ('fresh Enter',b'',b'old\r',{1:b'x',2:b'\r'},2,0),
            ('fresh physical Escape',b'',b'old\r',{1:b'x',2:b'\x05'},2,0),
            ('timed ordinary key rejected',bytes([3,21,1]),b'x\r',None,0,0),
            ('timed expiry',bytes([3,21,1]),b'',None,30,0)]:
        body=setup+bytes([135,134,1,0]);logic=len(body).to_bytes(2,'little')+body
        files={'/game/logDir':b'\xff'*3+bytes(3),
               '/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic}
        error,out,state=exercise(d,files,module='wbgame',base=0xa000,database=0,window=0x8000,
            blocks=None,multiple=True,firstblock=0x10,capture=True,keyboard=keys,
            keyboard_by_sleep=future,module_root=root,os_call_limit=20000)
        expected=(f'room: 0\ncode bytes: {(root/"wbgame").stat().st_size}\n'
                  f'private bytes: {symbols(root/"wbgame.map")["size"]}\nUI bytes: {(root/"sierraui").stat().st_size}\n'
                  f'owned 8K pages:\ncache: 1  picture: 4\nbackground: 0  bitmap: {bitmap}\nmax logic bytes: {len(logic)}').encode()
        assert error==0 and state['messagebuffer'].split(b'\0')[0]==expected,(label,error,state['messagebuffer'],expected)
        assert state['sleeps']==wanted_sleeps and state['vmvariables'][21]==0,(label,state['sleeps'])
        assert state['vmflags'][15]==0 and state['gamefont']==(root/'sierrafont').read_bytes()
        print('PASS: loaded memory info:',label,flush=True)
    directory=b'/'+b'a'*126;volume=bytearray();entries=[b'\xff'*3]
    for number in range(1,18):
        body=bytes([22,number+1,0]) if number<17 else bytes([12,15,135,134,1,0])
        logic=len(body).to_bytes(2,'little')+body
        entries.append(len(volume).to_bytes(3,'big'))
        volume+=b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
    files={directory.decode()+'/logDir':b''.join(entries),directory.decode()+'/vol.0':bytes(volume)}
    error,out,state=exercise(d,files,arguments=directory+b' 1\r',module='wbgame',base=0xa000,
        database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
        module_root=root,os_call_limit=30000)
    assert error==0 and b'cache: 17  picture: 4' in state['messagebuffer'],(error,out,state['messagebuffer'])
    assert b'max logic bytes: 8\0' in state['messagebuffer']
    assert state['gamefont']==(root/'sierrafont').read_bytes()
    print('PASS: memory info at 16 nested calls and a 127-byte directory; cache accounting, private font and cleanup')


def check_state_transfers(d):
    """File counts must be checked independently of the service's Z flag."""
    root=ROOT/'objs'; syms=symbols(root/'sierrastate.map'); base=0x9000
    d.write(base,(root/'sierrastate').read_bytes())
    labels=('StateTransferBad','StateTransferDone','StateReadMore')
    for label in labels: d.breakpoint(base+syms[label])
    try:
        for zero_flag in (0,4):
            for actual,wanted in ((0,'StateTransferBad'),(8,'StateReadMore'),
                                  (16,'StateTransferDone'),(17,'StateTransferBad')):
                d.write(0x7ef0,b'\x20\x00\x00\x10')
                d.write(base+syms['StateCreated'],b'\0')
                d.regs(pc=base+syms['StateTransferCount'],s=0x7ef0,
                       y=actual,cc=0x50|zero_flag)
                d.call('c'); r=d.regs()
                assert r['pc']==base+syms[wanted], (actual,zero_flag,wanted,r)
                if actual==8:
                    assert d.read(0x7ef0,4)==b'\x20\x08\x00\x08'
    finally:
        for label in labels: d.breakpoint(base+syms[label],False)
    print('PASS: cold snapshot transfers reject zero/oversized counts and advance partial reads regardless of the incoming zero flag')


def check_provider_loaders(d):
    """Exercise both real directory loaders, including their distinct error stacks."""
    root=ROOT/'objs';gs=symbols(root/'wbgame.map');code=(root/'wbgame').read_bytes()
    offsets={int(m[1],16):int(m[2],16) for m in re.finditer(
        r'^([0-9A-F]{4}) 103F([0-9A-F]{2}).*os9',(root/'wbgame.list').read_text(),re.M)}
    common_cases=('valid','mapped valid','unmap failure','load failure','bad ABI','short header',
                  'large module','small entry','overflow entry')
    count=0
    for base in (0x9000,0xa000):
        d.write(base,code);sites={base+offset:number for offset,number in offsets.items()}
        for address in [*sites,0x7e00]:d.breakpoint(address)
        try:
            for role,entry_label in (('sierrastate','StateLoadModule'),('sierraui','UiLoadModule')):
                original=(root/role).read_bytes();entry=int.from_bytes(original[9:11],'big')
                # Keep the largest malformed provider (sierraui) below the
                # synthetic caller stack at $7FE0-$7FF7.
                module_base=0x6000 if base==0x9000 else 0x8000
                cases=common_cases+(('short prefix','large prefix','prefix past module','wrong state role') if role=='sierrastate' else ('reserved UI word',))
                for case in cases:
                    image=bytearray((root/'sierraui').read_bytes() if case=='wrong state role' else original)
                    image_entry=int.from_bytes(image[9:11],'big')
                    edits={'bad ABI':(entry+2,0),'short header':(2,entry+38),
                           'large module':(2,8193),'small entry':(9,12),'overflow entry':(9,65535),
                           'short prefix':(entry+18,entry+39),'large prefix':(entry+18,4097),
                           'prefix past module':(2,int.from_bytes(image[entry+18:entry+20],'big')-1),
                           'reserved UI word':(entry+18,4097)}
                    if case in edits:
                        at,value=edits[case];image[at:at+2]=value.to_bytes(2,'big')
                    d.write(0,bytes(gs['size'])+b'PRIVATE')
                    mapped=case in ('mapped valid','unmap failure')
                    d.write(gs['assetmapped'],bytes([mapped]))
                    d.write(gs['assetmapbase'],b'\x80\0')
                    d.write(0x7fe0,b'L'*16+b'\x7e\0STACK')
                    d.regs(pc=base+gs[entry_label],s=0x7ff0,u=0,x=0x5555,y=0x4444,dp=0,cc=0x50)
                    loaded=0;loads=0;unlinks=0;unmaps=0
                    for _ in range(8):
                        d.call('c');r=d.regs()
                        if r['pc']==0x7e00:break
                        service=sites[r['pc']];updates={'pc':r['pc']+3,'cc':r['cc']&~1}
                        if service==gs['F$ClrBlk']:
                            assert mapped and r['u']==0x8000 and r['b']==1
                            unmaps+=1
                            updates.update(x=0xdead,y=0xbeef,u=0x8000)
                            if case=='unmap failure':updates.update(b=gs['E$MemFul'],cc=r['cc']|1)
                        elif service==gs['F$Load']:
                            assert d.read(r['x'],16).split(b'\r')[0].decode()==role,'filename lost across unmap'
                            loads+=1
                            if case=='load failure':updates.update(b=gs['E$PNNF'],cc=r['cc']|1)
                            else:
                                d.write(module_base,image);loaded+=1
                                updates.update(u=module_base,y=(module_base+int.from_bytes(image[9:11],'big'))&65535)
                        elif service==gs['F$UnLink']:
                            assert loaded==1 and r['u']==module_base
                            assert d.read(module_base,len(image))==image
                            loaded-=1;unlinks+=1
                            updates.update(x=0xdead,y=0xbeef,u=0x1234)
                        else:raise AssertionError(('unexpected loader service',role,case,service))
                        d.regs(**updates)
                    else:raise AssertionError(('loader did not return',role,case))
                    error=0 if case in ('valid','mapped valid','reserved UI word') else gs['E$MemFul'] if case=='unmap failure' else gs['E$PNNF'] if case=='load failure' else gs['E$BMode']
                    assert r['s']==0x7ff2 and bool(r['cc']&1)==bool(error) and r['b']==error,(role,case,r)
                    assert unmaps==int(mapped) and loads==int(case!='unmap failure')
                    assert d.read(0x7fe0,8)==b'L'*8 and d.read(0x7ff2,5)==b'STACK'
                    assert d.read(gs['size'],7)==b'PRIVATE'
                    if not error:
                        assert r['u']==module_base and r['x']==module_base+entry+10
                        assert r['y']==int.from_bytes(image[entry+18:entry+20],'big')
                        assert loaded==1 and unlinks==0 # the caller owns the successful reference
                    else:
                        assert r['u']==0 and loaded==0
                    assert unlinks==int(bool(error) and case not in ('unmap failure','load failure'))
                    assert d.read(base,len(code))==code
                    count+=1
        finally:
            for address in [*sites,0x7e00]:d.breakpoint(address,False)
    state=(root/'sierrastate').read_bytes();state_entry=int.from_bytes(state[9:11],'big')
    directory=[int.from_bytes(state[state_entry+10+n:state_entry+12+n],'big') for n in range(0,26,2)]
    assert all(value==0 for n,value in enumerate(directory) if n!=4), 'persistence module exported a UI entry'
    ui=(root/'sierraui').read_bytes();ui_entry=int.from_bytes(ui[9:11],'big')
    assert int.from_bytes(ui[ui_entry+18:ui_entry+20],'big')==0, 'UI advertised copied code'
    d.write(0,bytes(gs['size']));copy=0x8000;d.write(copy,ui)
    private=d.read(0,gs['size']);d.breakpoint(0x7e00)
    try:
        for operation in (0,1,2,255):
            d.write(0x7ee0,b'L'*16+b'\x7e\0STACK')
            d.regs(pc=copy+ui_entry,s=0x7ef0,a=operation,u=0,x=0x5555,y=0x4444,dp=0,cc=0x50)
            d.call('c');r=d.regs()
            assert (r['pc'],r['s'],r['u'],r['b'])==(0x7e00,0x7ef2,0,gs['E$BMode']) and r['cc']&1
            assert d.read(0,gs['size'])==private
            assert d.read(0x7ee0,16)==b'L'*16 and d.read(0x7ef2,5)==b'STACK'
    finally:d.breakpoint(0x7e00,False)
    from check_wbplay import fixture as logic_fixture
    files=logic_fixture(bytes([154,0,0,24,39,0,134,1,0]));files['sierraui']=state
    error,_,_=exercise(d,files,module='wbgame',base=0xa000,database=0,
        window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True)
    assert error==gs['E$BMode'],'persistence image accepted as UI code'
    print('PASS: wrong provider roles fail safely: state loader rejects a UI image; UI entry rejects persistence operations; state directory cannot execute UI callbacks; unchanged private state and ownership cleanup')
    print(f'PASS: {count} actual UI/state loader cases at two code/provider addresses; saved filename across unmap clobbers, ABI/header/prefix bounds, load/unmap failures, exact reference ownership, original U, balanced error stacks and immutable code')


def check_native_trace(d):
    """Run trace.info/on through real loaded logic and verify event/exit cleanup."""
    cases=[(0,1,8,picturetop) for picturetop in range(5)]
    cases.extend(((255,255,255,0),(0,0,0,0)))
    for logic_no,line,rows,picturetop in cases:
        body=bytes([111,picturetop,23,0,12,10,150,logic_no,line,rows,
                    149,3,10,42,134,1,0])
        logic=len(body).to_bytes(2,'little')+body
        files={'/game/logDir':b'\0\0\0'+bytes(3),
               '/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic}
        presentation=[]
        def capture_overlay(cpu,regs,syms):
            if cpu.read(syms['traceowned'],1)==b'\x01':
                presentation.append(cpu.read(syms['textcharacters'],2000))
            return False
        error,_,state=exercise(d,files,module='wbgame',base=0xa000,database=0,
            window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
            module_root=ROOT/'objs',keyboard_by_sleep={1:b'  '},
            cycle_limit=40,os_call_limit=30000,
            breakpoint_hooks={'GameTextPresent':capture_overlay})
        assert error==0, ('trace fixture failed',logic_no,line,rows,error)
        assert len(presentation)==1, ('native trace event was not presented',len(presentation))
        rows_text=[presentation[0][i:i+40] for i in range(0,1000,40)]
        visible=b'\n'.join(rows_text)
        assert b'1: 3(10,42)' in visible, visible
        assert state['vmvariables'][10]==42, 'execution did not resume after a trace step'
        assert state['traceowned']==b'\0', 'trace page survived process exit'
        assert state['traceconfiglogic']==bytes([logic_no])
        assert state['traceconfigline']==bytes([line])
        assert state['traceconfigrows']==bytes([max(2,rows)])
        expected_top=min((state['vmpicturetop'][0]+1+line)&255,23)
        expected_rows=min(max(2,rows),25-expected_top)
        assert state['tracetop']==bytes([expected_top]),(line,rows,state['tracetop'],expected_top)
        assert state['tracelines']==bytes([expected_rows]),(line,rows,state['tracelines'],expected_rows)
        assert expected_top+expected_rows<=25
    print('PASS: loaded config.screen/trace.info/on variants display and step a real command, match tested CoCo trace rows for all five legal picture tops, clamp low/high geometry, resume execution and release the trace page')


def check_reused_private_state(d):
    """A newly allocated process may inherit nonzero restore staging bytes."""
    game=ROOT/'kingsquest1'
    files={'/game/'+p.name:p.read_bytes() for p in game.iterdir()
           if p.name.startswith('vol.') or p.name in
           ('logDir','picDir','viewDir','sndDir','object','words.tok')}
    for fill,long_path in ((0xa5,False),(0xff,True)):
        directory='/'+('x'*126) if long_path else '/game'
        inputs={directory+name[5:]:data for name,data in files.items()}
        def poison(cpu,r,syms):
            # Preserve loaded parameters/stack and the font/audio tail. This
            # models recycled private controls, not a changed OS service.
            cpu.write(r['u'],bytes([fill])*syms['gamefont'])
        error,output,state=exercise(d,inputs,arguments=(directory+' 0\r').encode(),
            module='wbgame',base=0xa000,database=0,window=0x8000,blocks=None,
            multiple=True,firstblock=0x10,capture=True,cycle_limit=10,
            keyboard_by_cycle={2:(b' \r',0)},breakpoint_hooks={'start':poison},
            os_call_limit=100000)
        assert error==228 and state['cycles']==10,(fill,long_path,error,state['cycles'])
        assert state['vmvariables'][0]==1
        assert state['vminputenabled']==b'\1'
        assert state['gamefont']==(ROOT/'objs/sierrafont').read_bytes()
    print('PASS: original KQ1 starts in recycled nonzero private memory, preserves short/126-byte paths and font, enables input and cleans up on planned interrupt')


def check_state_cache_bounds(d, helper_root=None):
    """Restoring code bounds must not write beyond a 12-byte cache entry."""
    root=Path(helper_root) if helper_root is not None else ROOT/'objs'
    hs=symbols(root/'sierrastate.map');gs=symbols(ROOT/'objs/wbgame.map')
    base=0x9000;code=(root/'sierrastate').read_bytes();d.write(base,code)
    labels=('StateCallWarm','StateMapSpan','StateUnmap','StateNextRecipe')
    for label in labels:d.breakpoint(base+hs[label])
    try:
        for private in (0,0x1000):
            for index in (0,1):
                slot=private+gs['vmcache']+12*index
                record=bytes.fromhex('000100300100002000200002')
                neighbor=b'NEXT-SLOT-ID!'
                d.write(slot,record+neighbor)
                cache=base+hs['StateCache'];recipe=cache+5*index
                d.write(cache,bytes(160));d.write(recipe,bytes([1,index,0,2,0]))
                for field,value in (('StateBase',private),('StateRecipe',recipe)):
                    d.write(base+hs[field],value.to_bytes(2,'big'))
                if 'StateRootCodeEnd' in hs:
                    d.write(base+hs['StateRootCodeEnd'],b'\x12\x34')
                d.write(0x8000,b'\x0a\0'+bytes(30))
                d.write(0x7ef0,b'\x7e\0STACK')
                d.regs(pc=base+hs['StateLoadRecipe'],s=0x7ef0,u=private,dp=private>>8,cc=0x50)
                for _ in range(8):
                    d.call('c');r=d.regs()
                    if r['pc']==base+hs['StateNextRecipe']:break
                    assert r['pc'] in {base+hs[n] for n in labels},r
                    ret=int.from_bytes(d.read(r['s'],2),'big')
                    if r['pc']==base+hs['StateCallWarm']:
                        assert d.read(ret,1)==b'\x0a'
                        d.regs(pc=ret+1,s=r['s']+2,x=slot,cc=r['cc']&~1)
                    else:
                        d.regs(pc=ret,s=r['s']+2,u=0x8000,cc=r['cc']&~1)
                else:raise AssertionError('recipe reconstruction did not finish')
                assert d.read(slot,12)==record,'cache record changed outside its scan field'
                assert d.read(slot+12,len(neighbor))==neighbor,'logic code-end overwrote the adjacent cache slot'
                assert d.read(0x7ef0,7)==b'\x7e\0STACK'
                assert 'StateRootCodeEnd' in hs
                expected=b'\0\x0c' if index==0 else b'\x12\x34'
                assert d.read(base+hs['StateRootCodeEnd'],2)==expected
    finally:
        for label in labels:d.breakpoint(base+hs[label],False)
    print('PASS: root/non-root restore code bounds preserve adjacent 12-byte cache entries at two private bases')


def check_state_validation(d):
    root=ROOT/'objs'; syms=symbols(root/'sierrastate.map'); base=0x9000
    d.write(base,(root/'sierrastate').read_bytes())
    import re
    calls={base+int(m[1],16):int(m[2],16) for m in re.finditer(
        r'^([0-9A-F]{4}) 103F([0-9A-F]{2}).*os9',
        (root/'sierrastate.list').read_text(),re.M)}
    for address in calls: d.breakpoint(address)
    d.breakpoint(0x5000)
    clean=bytearray(syms['StateCoreBytes']+160)
    clean[syms['StateCoreBytes']:syms['StateCoreBytes']+5]=b'\x01\0\0\x02\0'
    cases=[('valid',None,b''),
        ('key count','SavedKeyCount',bytes([51])),
        ('menu count','SavedMenuControl',bytes([9])),
        ('foreground','SavedScreen',bytes([0,16])),
        ('input row','SavedScreen',bytes([0,0,0,0,25])),
        ('inventory count','SavedInventoryControl',b'\x01\0\0\x01\x01'),
        ('odd replay length','SavedReplay',b'\0\0\x01'),
        ('glyph','SavedText',bytes([128])),
        ('resource kind','StateCoreBytes',bytes([5])),
        ('cache reserved','StateCoreBytes',b'\x01\0\0\x02\x01'),
        ('empty cache payload','StateCoreBytes',b'\0\x01'),
        ('root ID','StateCoreBytes',b'\x01\x01\0\x02\0')]
    try:
        for label,field,value in cases:
            stage=clean[:]
            if field is not None: stage[syms[field]:syms[field]+len(value)]=value
            d.write(0x6000,stage)
            d.write(base+syms['StateFirst'],b'\0\x30')
            d.write(base+syms['StateHeader'],bytes(18))
            d.write(base+syms['StateMapped'],b'\0')
            d.write(0x5100,b'\x50\0')
            d.regs(pc=base+syms['StateValidate'],s=0x5100,dp=0x10,u=0x1000,cc=0x50)
            mapped=False; maps=unmaps=0
            for count in range(4):
                d.call('c'); r=d.regs()
                if r['pc']==0x5000: break
                service=calls[r['pc']]
                if service==syms['F$MapBlk']:
                    assert not mapped and r['b']==1
                    mapped=True; maps+=1; d.regs(u=0x6000,cc=r['cc']&~1,pc=r['pc']+3)
                elif service==syms['F$ClrBlk']:
                    assert mapped and r['u']==0x6000 and r['b']==1
                    mapped=False; unmaps+=1; d.regs(cc=r['cc']&~1,pc=r['pc']+3)
                else: raise AssertionError((label,service,r))
            assert r['pc']==0x5000 and maps==unmaps==1 and not mapped,(label,r)
            assert bool(r['cc']&1)==(field is not None),(label,r)
            if field is not None: assert r['b']==syms['E$BMode'],(label,r)
            assert d.read(0x6000,len(stage))==stage,label
    finally:
        for address in calls: d.breakpoint(address,False)
        d.breakpoint(0x5000,False)
    print('PASS: cold snapshot validation rejects malformed counts, colors, rows, glyphs and resource recipes without changing staged bytes or leaking its mapping')


def check_bounded_said(d):
    """Long predicates must consume their tail without retaining unreachable IDs."""
    cases=[([],0,True),([123]*20,20,True),([123]*20+[1],20,False),
           ([123]*20+[9999],20,True),([9999]+[123]*126,20,True),
           ([123]*20+[9999]+[123]*106,20,True),([123]*127,20,False)]
    replay=None
    for words,parsed,expected in cases:
        script=bytes([12,2,255,14,len(words)])
        script+=b''.join(word.to_bytes(2,'little') for word in words)
        script+=bytes([255,2,0,12,200,134,1,0])
        payload=len(script).to_bytes(2,'little')+script
        files={'/game/logDir':bytes(3),'/game/vol.0':b'\x12\x34\0'+len(payload).to_bytes(2,'little')*2+payload}
        def parsed_words(cpu,regs,syms):
            cpu.write(0x0000+syms['parsercount'],bytes([parsed]))
            cpu.write(0x0000+syms['parserids'],b'\0\x7b'*parsed)
        error,output,state=exercise(d,files,arguments=b'/game 0\r',module='wbgame',
            base=0xa000,database=0x0000,window=0x8000,blocks=None,multiple=True,
            firstblock=0x10,capture=True,breakpoint_hooks={'ParserSaid':parsed_words})
        assert not error and not output,(len(words),error,output)
        assert bool(state['vmflags'][200])==expected,(len(words),parsed,expected)
        if replay is None:replay=state['replaybuffer']
        assert state['replaybuffer']==replay,'said operands overwrote the next private buffer'
    script=bytes([255,14,127])+b'\x7b\0'*21+bytes([255,0,0,134,1,0])
    payload=len(script).to_bytes(2,'little')+script
    files={'/game/logDir':bytes(3),'/game/vol.0':b'\x12\x34\0'+len(payload).to_bytes(2,'little')*2+payload}
    error,output=exercise(d,files,arguments=b'/game 0\r',module='wbgame',base=0xa000,
        database=0x0000,window=0x8000,blocks=None,multiple=True,firstblock=0x10)
    assert error and not output,'truncated discarded predicate tail was accepted'
    print('PASS: bounded said storage preserves 20 words plus a following wildcard, accepts complete 127-word predicates, rejects truncated tails and preserves the next private buffer')

def check_compatibility_noops(d):
    """CoCo's explicit zero-operand no-ops must not abort native scripts."""
    script=bytes([3,240,73,12,221,127,163,164,173,176,178,181,4,241,240,134,1,0])
    logic=len(script).to_bytes(2,'little')+script
    files={'/game/logDir':b'\xff'*3+bytes(3),
           '/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic}
    error,output,state=exercise(d,files,module='wbgame',base=0xa000,
        database=0x0000,window=0x8000,blocks=None,multiple=True,
        firstblock=0x10,capture=True)
    assert not error and not output,(error,output)
    assert state['vmvariables'][240:242]==bytes([73,73])
    assert state['vmflags'][221]==1
    print('PASS: CoCo-compatible zero-operand no-ops continue native scripts and preserve variables/flags')


def check_positioned_messages(d):
    """Check positions and wraps against literal AGI row/column/width inputs."""
    key=b'Avis Durgan'
    cases=[
        ('literal',151,3,7,12,b'alpha beta gamma delta',[(3,7,b'alpha beta '),(4,7,b'gamma delta')]),
        ('variable message',152,3,7,12,b'alpha beta gamma delta',[(3,7,b'alpha beta '),(4,7,b'gamma delta')]),
        ('newline',151,4,9,7,b'one\ntwo',[(4,9,b'one'),(5,9,b'two')]),
        ('long word',151,2,6,4,b'ABCDEFGHIJK',[(2,6,b'ABCD'),(3,6,b'EFGH'),(4,6,b'IJK')]),
        ('default width',151,3,2,0,b'abcdefghijklmnopqrstuvwxy ABCDEFG',[(3,2,b'abcdefghijklmnopqrstuvwxy '),(4,2,b'ABCDEFG')]),
        ('right clip',151,4,38,20,b'ABCD',[(4,38,b'AB'),(5,38,b'CD')]),
        ('overflowing width',151,4,38,255,b'ABCD',[(4,38,b'AB'),(5,38,b'CD')]),
        ('bottom clip',151,24,38,20,b'ABCD',[(24,38,b'AB')]),
        ('bad text entry',151,2,2,10,b'bad',None),
        ('oversized text entry',151,2,2,10,b'bad',None),
        ('CRC text entry',151,2,2,10,b'bad',None),
        ('missing helper',151,2,2,10,b'bad',None),
        ('bad row',151,25,2,10,b'bad',None),
        ('bad column',151,2,40,10,b'bad',None),
        ('default after positioned',151,3,7,12,b'alpha beta gamma delta',[(10,10,b'alpha beta gamma '),(11,10,b'delta')]),
    ]
    for label,opcode,row,column,width,message,expected in cases:
        print('Checking positioned message:',label,flush=True)
        before=bytes([3,6,1])
        body=bytes([opcode,6 if opcode==152 else 1,row,column,width])
        if label=='default after positioned':
            before+=bytes([12,15]);body+=bytes([101,1])
        script=before+body+bytes([134,1,0])
        plaintext=message+b'\0'
        encrypted=bytes(value^key[i%len(key)] for i,value in enumerate(plaintext))
        logic=len(script).to_bytes(2,'little')+script
        logic+=bytes([1])+(4+len(plaintext)).to_bytes(2,'little')+bytes([4,0])+encrypted
        files={'/game/logDir':b'\xff'*3+bytes(3),
               '/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic}
        if label in ('bad text entry','oversized text entry','CRC text entry'):
            # Mock F$Load has already accepted the module; exercise our own
            # executable-entry bounds independently of the kernel CRC check.
            helper=bytearray((ROOT/'objs/sierraui').read_bytes())
            entry=int.from_bytes(helper[9:11],'big')
            offset=0 if label=='bad text entry' else len(helper)-(1 if label=='CRC text entry' else 0)
            helper[entry+14:entry+16]=offset.to_bytes(2,'big')
            files['sierraui']=bytes(helper)
        elif label=='missing helper':files['sierraui']=None
        captured=[]
        def capture(debug,registers,syms):
            captured.append(debug.read(0x0000+syms['textcharacters'],2000))
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,
            database=0x0000,window=0x8000,blocks=None,multiple=True,
            firstblock=0x10,capture=True,keyboard=b'\r',
            breakpoint_hooks={'GamePrintWait':capture},os_call_limit=20000)
        if expected is None:
            wanted_error=216 if label=='missing helper' else 203
            assert error==wanted_error and not captured,(label,error,captured)
        else:
            assert not error and len(captured)==1,(label,error,len(captured))
            wanted=bytearray(1000)
            if label=='default after positioned':
                for popup_row in range(9,16):
                    wanted[popup_row*40+9:popup_row*40+30]=b' '*21
            for r,c,text in expected:wanted[r*40+c:r*40+c+len(text)]=text
            assert captured[0][:1000]==wanted,(label,[(i,a,b) for i,(a,b) in enumerate(zip(captured[0],wanted)) if a!=b][:12])
            for r,c,text in expected:
                # Cell colors store foreground/background in high/low nibbles.
                assert captured[0][1000+r*40+c:1000+r*40+c+len(text)]==bytes([0xF0])*len(text),(label,'message colors')
    print('PASS: native print.at/print.at.v positions, word/newline/hard wrapping, default width, clipped edges, safe invalid coordinates and normal-print reset')


def check_text_screen_key_wait(d):
    """King's text-screen loop clears v19 before waiting for a fresh key."""
    script=bytes([106,103,8,2,1,3,19,0])+bytes.fromhex('ff fd 0d ff 03 00 fe f7 ff')+bytes([107,134,1,0])
    message=b'When you speak to King Edward,\0';key=b'Avis Durgan'
    encrypted=bytes(value^key[i%len(key)] for i,value in enumerate(message))
    logic=len(script).to_bytes(2,'little')+script+bytes([1])+(4+len(message)).to_bytes(2,'little')+bytes([4,0])+encrypted
    seen={}
    def submitting_key(cpu,r,syms):
        cpu.write(syms['vmhavekey'],b'\x01')
        cpu.write(syms['vmvariables']+19,b'\r')
        cpu.write(syms['parserline'],b'abc\0');cpu.write(syms['parserlength'],b'\x03')
    def text_visible(cpu,r,syms):
        seen['line']=cpu.read(syms['textcharacters']+2*40+4,len(message)-1)
        seen['panel']=(cpu.read(syms['textcharacters']+40+3,1),
                       cpu.read(syms['textcolors']+1000+40+3,1),
                       cpu.read(syms['textcharacters']+3,1),
                       cpu.read(syms['textcolors']+1000+3,1))
    def resumed(cpu,r,syms):
        seen['graphics']=cpu.read(syms['vmgraphics'],1)
        seen['parser']=cpu.read(syms['parserline'],4)
    files={'/game/logDir':bytes(3),'/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic}
    error,output,state=exercise(d,files,
        arguments=b'/game 0\r',module='wbgame',base=0xa000,database=0,window=0x8000,blocks=None,
        multiple=True,firstblock=0x10,capture=True,keyboard_by_cycle={5:(b'p',0)},
        breakpoint_hooks={'GameTextScreen':submitting_key,'InputHaveKeyTest':text_visible,'GameQuitCommand':resumed})
    assert not error,(error,state['cycles'])
    assert seen['line']==message[:-1],seen
    assert seen['panel']==(b' ',b'\x0f',b' ',b'\0'),seen['panel']
    assert state['cycles']==5,('stale submitting key dismissed the king text screen',state['cycles'])
    assert state['vmvariables'][19]==ord('p') and seen['graphics']==b'\x01'
    assert seen['parser']==b'abc\0','dialog key changed the command line'
    helper=bytearray((ROOT/'objs/sierraui').read_bytes());entry=int.from_bytes(helper[9:11],'big')
    helper[entry+16:entry+18]=bytes(2)
    error,output,state=exercise(d,{**files,'sierraui':bytes(helper)},
        arguments=b'/game 0\r',module='wbgame',base=0xa000,database=0,window=0x8000,blocks=None,
        multiple=True,firstblock=0x10,capture=True)
    assert error==203,'invalid have.key wait entry did not unwind safely'
    # A pending key satisfies have.key without another read, and is boolean
    # true rather than its raw ASCII value (NOT must therefore be false).
    script=bytes([3,19,112,255,253,13,255,3,0,3,200,1,134,1,0])
    logic=len(script).to_bytes(2,'little')+script
    error,output,state=exercise(d,{'/game/logDir':bytes(3),'/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic},
        arguments=b'/game 0\r',module='wbgame',base=0xa000,database=0,window=0x8000,blocks=None,
        multiple=True,firstblock=0x10,capture=True)
    assert not error and state['cycles']==0 and state['vmvariables'][19]==112
    assert state['vmvariables'][200]==0,'have.key did not return normalized boolean true'
    print('PASS: text-screen have.key honors cleared v19, waits for fresh input and resumes graphics without resubmitting parser text')


def check_original_help(d):
    """Run original KQ1 logic 92, including its inline fresh-key wait."""
    game=ROOT/'kingsquest1'
    files={'/game/'+path.name:path.read_bytes() for path in game.iterdir()
           if path.is_file() and (path.name.startswith('vol.') or path.name in
                                  ('logDir','picDir','viewDir','sndDir','words.tok','object'))}
    root=bytes([22,92,134,1,0]);logic=len(root).to_bytes(2,'little')+root
    volume=files['/game/vol.0'];offset=len(volume)
    files['/game/vol.0']=volume+b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
    directory=bytearray(files['/game/logDir']);directory[:3]=offset.to_bytes(3,'big')
    files['/game/logDir']=bytes(directory);observed={}
    def visible(cpu,r,syms):
        observed['title']=cpu.read(syms['textcharacters']+2*40+12,12)
        observed['input']=cpu.read(syms['vminputenabled'],1)
    def resumed(cpu,r,syms):
        observed['graphics']=cpu.read(syms['vmgraphics'],1)
    error,output,state=exercise(d,files,arguments=b'/game 0\r',module='wbgame',
        base=0xa000,database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,
        capture=True,keyboard_by_cycle={5:(b'x',0)},
        breakpoint_hooks={'GameHaveKeyWait':visible,'GameQuitCommand':resumed})
    assert not error,(error,state['cycles'])
    assert observed=={'title':b"KING'S QUEST",'input':b'\0','graphics':b'\x01'},observed
    assert state['cycles']==5 and state['vmvariables'][19]==ord('x')
    assert state['vminputenabled']==b'\x01' and state['vmflags'][4]==1
    print('PASS: original KQ1 help logic, nested caller resume, fresh-key wait, restored input/graphics and cleanup')


def check_nested_logic_calls(d):
    """Run call/call.v at multiple levels and prove each caller resumes."""
    game=ROOT/'kingsquest1'
    files={'/game/'+path.name:path.read_bytes() for path in game.iterdir()
           if path.is_file() and (path.name.startswith('vol.') or path.name in
                                  ('logDir','picDir','viewDir','sndDir','words.tok','object'))}
    scripts=(
        # Root: preload literal logic 1 and variable logic 3, then call 1
        # and call.v through v242=2. The load order is observed at the real
        # resource-pointer service to prove later calls hit the cache.
        bytes([3,249,3,20,1,21,249,3,240,1,22,1,3,241,42,
               3,242,2,23,242,3,243,84,134,1,0]),
        # Logic 1: call.v through v245=3, then resume and assign v246.
        bytes([3,245,3,23,245,3,246,33,0]),
        bytes([3,247,22,0]),
        bytes([3,248,33,0]),
    )
    volume=bytearray(files['/game/vol.0'])
    directory=bytearray(files['/game/logDir'])
    for number,script in enumerate(scripts):
        logic=len(script).to_bytes(2,'little')+script
        offset=len(volume)
        volume.extend(b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic)
        directory[number*3:number*3+3]=offset.to_bytes(3,'big')
    files['/game/vol.0']=bytes(volume)
    files['/game/logDir']=bytes(directory)
    call_depths=[];quit_depth=[];logic_resource_loads=[]
    def entered(cpu,r,syms):
        call_depths.append(cpu.read(syms['vmdepth'],1)[0])
        return True
    def quitting(cpu,r,syms):
        quit_depth.append(cpu.read(syms['vmdepth'],1)[0])
    def logic_cache_load(cpu,r,syms):
        if cpu.read(syms['vmrequestedkind'],1)[0]==0:
            logic_resource_loads.append(cpu.read(syms['vmrequested'],1)[0])
        return True
    error,output,state=exercise(d,files,arguments=b'/game 0\r',module='wbgame',
        base=0xa000,database=0,window=0x8000,blocks=None,multiple=True,
        firstblock=0x10,capture=True,
        breakpoint_hooks={'VmCallLogic':entered,'GameQuitCommand':quitting,
                          'VmCacheLoad':logic_cache_load})
    assert error==0,(error,output)
    expected={240:1,241:42,242:2,243:84,245:3,246:33,247:22,248:33}
    actual={index:state['vmvariables'][index] for index in expected}
    assert actual==expected,('nested logic state/caller continuation',actual)
    assert call_depths==[0,1,0],('literal and variable nested call depth',call_depths)
    assert quit_depth==[0],('call frame was not unwound before caller continuation',quit_depth)
    assert logic_resource_loads==[1,3,2],('literal/variable logic preload and call cache-miss order',logic_resource_loads)
    print('PASS: original loader with literal load.logics, variable load.logics.v, literal call, nested call.v and root call.v; preloaded logic cache hits, child effects, caller continuations, depth/frame cleanup')


def check_original_death_messages(d):
    """Run original death-support logic 100 at three score thresholds."""
    game=ROOT/'kingsquest1'
    original={'/game/'+path.name:path.read_bytes() for path in game.iterdir()
              if path.is_file() and (path.name.startswith('vol.') or path.name in
                                     ('logDir','picDir','viewDir','sndDir','words.tok','object'))}
    for score,phrase in ((0,b'very sorry'),(50,b'pleased'),(100,b'delighted')):
        # Original death callers arm v97=2; logic 100 decrements it to one.
        root=bytes([3,3,score,3,97,2,22,100,134,1,0]);logic=len(root).to_bytes(2,'little')+root
        volume=original['/game/vol.0'];offset=len(volume);files=dict(original)
        files['/game/vol.0']=volume+b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
        directory=bytearray(files['/game/logDir']);directory[:3]=offset.to_bytes(3,'big')
        files['/game/logDir']=bytes(directory);observed=[];text_colors=[]
        def message(cpu,r,syms):observed.append(cpu.read(r['x'],512).split(b'\0')[0])
        def popup_color(cpu,r,syms):
            text_colors.append((cpu.read(syms['vmtextforeground'],1)[0],
                                cpu.read(syms['vmtextbackground'],1)[0]))
            return False
        error,output,state=exercise(d,files,arguments=b'/game 0\r',module='wbgame',
            base=0xa000,database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,
            capture=True,keyboard=b'\r',breakpoint_hooks={
                'GamePrintText':message,'GamePrintPositionReady':popup_color})
        assert not error,(score,error)
        assert len(observed)==1 and phrase in observed[0],(score,observed)
        assert text_colors==[(15,0)],('popup must render white text on black background',text_colors)
        assert state['vmvariables'][97]==0 and state['vmvariables'][3]==score
    print('PASS: original KQ1 death-support score branches, white-on-black popup colors, message dismissal, nested caller resume and resource cleanup')


def check_original_pickup_puzzles(d):
    """Original pickup scripts decide proximity, acquisition and repeat scoring."""
    game=ROOT/'kingsquest1'
    original={'/game/'+path.name:path.read_bytes() for path in game.iterdir()
              if path.is_file() and (path.name.startswith('vol.') or path.name in
                                     ('logDir','picDir','viewDir','sndDir','words.tok','object'))}
    puzzles=[('clover',24,'get clover',8,(50,134),(100,160),(86,87),2,b''),
             ('mirror',51,'get mirror',19,(40,115),(100,150),(100,165),8,bytes([3,75,2,12,167])),
             ('shield',77,'get shield',21,(130,128),(50,160),(188,102),8,bytes([12,186,12,187])),
             ('chest',58,'get chest',2,(75,115),(10,160),(104,169),8,bytes([3,86,4]))]
    for name,room,command,item,near,far,flags,points,preconditions in puzzles:
        cases=[('near',near,False),('far',far,False),('repeat',near,True)]
        if name in ('mirror','chest'):cases.append(('guarded',near,False))
        if name=='chest':cases.append(('third treasure',near,False))
        for label,(x,y),repeated in cases:
            setup=preconditions+(bytes([3,75 if name=='mirror' else 86,0]) if label=='guarded' else b'')
            if label=='third treasure':
                setup+=bytes([3,74,2,3,3,16,12,100,12,165,12,188,12,102,92,19,92,21])
            body=setup+bytes([3,0,room,12,5,33,0,30,0,41,0,0,37,0,x,y,114,0,1,117,0,22,room])
            if repeated:body+=bytes([13,5,117,0,22,room])
            body+=bytes([3,240,item,97,240,200])
            if label=='third treasure':body+=bytes([3,240,19,97,240,201,3,240,21,97,240,202])
            body+=bytes([134,1,0])
            text=command.encode()+b'\0';key=b'Avis Durgan'
            messages=bytes([1])+(4+len(text)).to_bytes(2,'little')+bytes([4,0])+bytes(v^key[i%11] for i,v in enumerate(text))
            logic=len(body).to_bytes(2,'little')+body+messages
            files=dict(original);volume=files['/game/vol.0'];offset=len(volume)
            files['/game/vol.0']=volume+b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
            directory=bytearray(files['/game/logDir']);directory[:3]=offset.to_bytes(3,'big')
            files['/game/logDir']=bytes(directory)
            error,output,state=exercise(d,files,arguments=b'/game 0\r',module='wbgame',base=0xa000,
                database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
                keyboard=b'\r\r',os_call_limit=100000)
            assert not error,(name,label,error)
            acquired=label in ('near','repeat','third treasure')
            assert state['vmvariables'][200]==(255 if acquired else 0),(name,label,'inventory',state['vmvariables'][200])
            expected_score=(16 if label=='third treasure' else 0)+(points if acquired else 0)
            assert state['vmvariables'][3]==expected_score,(name,label,'score',state['vmvariables'][3])
            assert all(state['vmflags'][flag]==int(acquired) for flag in flags),(name,label,'puzzle flags')
            if name!='clover':assert state['vmvariables'][74]==(2 if label=='third treasure' else 0)+int(acquired),(name,label,'quest progress')
            if label=='third treasure':assert state['vmvariables'][201:203]==b'\xff\xff','earlier treasures were lost'
    print('PASS: original clover/mirror/shield/chest pickups, real vocabulary parsing, near/far and guarded acquisition, inventory/quest flags and no repeat score')


def check_original_coronation(d):
    """Run original throne-room endgame from the three-treasure return state."""
    game=ROOT/'kingsquest1'
    files={'/game/'+path.name:path.read_bytes() for path in game.iterdir()
           if path.is_file() and (path.name.startswith('vol.') or path.name in
                                  ('logDir','picDir','viewDir','sndDir','words.tok','object'))}
    # Only the bootstrap is synthetic. The original room owns the countdown,
    # choreography, text, and endgame flag; no completion flags are injected.
    setup=bytes([3,250,1,3,0,53,3,1,54,3,74,3,3,3,24,12,5,
                 33,0,30,0,41,0,0,37,0,50,110,92,19,92,21,92,2])
    body=bytes([255,1,250,0,255])+len(setup).to_bytes(2,'little')+setup
    body+=bytes([22,53,13,5,255,7,195,255,2,0,134,1,0])
    logic=len(body).to_bytes(2,'little')+body
    volume=files['/game/vol.0'];offset=len(volume)
    files['/game/vol.0']=volume+b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
    directory=bytearray(files['/game/logDir']);directory[:3]=offset.to_bytes(3,'big')
    files['/game/logDir']=bytes(directory)
    error,output,state=exercise(d,files,arguments=b'/game 0\r',module='wbgame',base=0xa000,
        database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
        keyboard_by_cycle={cycle:(b'\r',0) for cycle in range(5,2000,5)},os_call_limit=300000)
    assert not error,('coronation',error)
    assert state['vmflags'][195]==1,'original coronation did not complete'
    assert state['vmvariables'][74]==3,'coronation lost quest progress'
    assert state['vmflags'][95]==0,'king succession sequence remained active'
    assert b'Thank you for playing' in state['messagebuffer'],'original closing credits were not shown'
    print('PASS: original three-treasure throne-room coronation choreography, messages and cleanup')


def check_original_fiddle_encounter(d):
    """Original leprechaun room reacts to a parsed fiddle command and finishes."""
    game=ROOT/'kingsquest1'
    files={'/game/'+path.name:path.read_bytes() for path in game.iterdir()
           if path.is_file() and (path.name.startswith('vol.') or path.name in
                                  ('logDir','picDir','viewDir','sndDir','words.tok','object'))}
    # The clover and fiddle are pre-owned. Flags 87/171 are the original root's
    # possession summaries, not encounter completion flags.
    setup=bytes([3,250,1,3,0,76,3,1,77,12,5,12,87,12,171,92,8,92,22,
                 33,0,30,0,41,0,0,37,0,73,150])
    body=bytes([255,1,250,0,255])+len(setup).to_bytes(2,'little')+setup
    # Initialize the room before submitting the command on the second cycle.
    parse=bytes([114,0,1,117,0])
    body+=bytes([255,1,250,2,255])+len(parse).to_bytes(2,'little')+parse
    body+=bytes([22,76,13,5,1,250,255,7,186,1,30,0,255,2,0,134,1,0])
    text=b'play fiddle\0';key=b'Avis Durgan'
    messages=bytes([1])+(4+len(text)).to_bytes(2,'little')+bytes([4,0])+bytes(v^key[i%11] for i,v in enumerate(text))
    logic=len(body).to_bytes(2,'little')+body+messages
    volume=files['/game/vol.0'];offset=len(volume)
    files['/game/vol.0']=volume+b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
    directory=bytearray(files['/game/logDir']);directory[:3]=offset.to_bytes(3,'big')
    files['/game/logDir']=bytes(directory)
    error,output,state=exercise(d,files,arguments=b'/game 0\r',module='wbgame',base=0xa000,
        database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
        keyboard_by_cycle={cycle:(b'\r',0) for cycle in range(5,2000,5)},os_call_limit=300000)
    assert not error,('fiddle encounter',error)
    assert state['vmflags'][186]==1,'leprechauns did not leave'
    assert state['vmvariables'][3]==3,'fiddle encounter score differs'
    assert state['vmflags'][21:23]==b'\0\0','fiddle choreography remained active'
    assert state['vminputenabled']==b'\1','fiddle encounter did not restore input'
    print('PASS: original parsed fiddle encounter, leprechaun departure, score, restored input and cleanup')


def check_original_dragon_encounter(d):
    """Use actual parsed water command against the original live dragon."""
    game=ROOT/'kingsquest1'
    files={'/game/'+path.name:path.read_bytes() for path in game.iterdir()
           if path.is_file() and (path.name.startswith('vol.') or path.name in
                                  ('logDir','picDir','viewDir','sndDir','words.tok','object'))}
    # Original root possession summary: flag 88 means the filled bucket.
    body=bytes([3,0,51,12,5,12,88,12,167,92,26,33,0,30,0,41,0,0,37,0,80,140,
                22,51,13,5,114,0,1,117,0,22,51,3,240,26,97,240,200,134,1,0])
    text=b'throw water\0';key=b'Avis Durgan'
    messages=bytes([1])+(4+len(text)).to_bytes(2,'little')+bytes([4,0])+bytes(v^key[i%11] for i,v in enumerate(text))
    logic=len(body).to_bytes(2,'little')+body+messages
    volume=files['/game/vol.0'];offset=len(volume)
    files['/game/vol.0']=volume+b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
    directory=bytearray(files['/game/logDir']);directory[:3]=offset.to_bytes(3,'big')
    files['/game/logDir']=bytes(directory)
    error,output,state=exercise(d,files,arguments=b'/game 0\r',module='wbgame',base=0xa000,
        database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
        keyboard=b'\r\r',os_call_limit=100000)
    assert not error,('dragon encounter',error)
    assert state['vmvariables'][75]==2,'water did not subdue the original dragon'
    assert state['vmflags'][88]==0,'filled bucket possession summary remained set'
    assert state['vmvariables'][200]==0,'water was not consumed'
    assert state['vmvariables'][3]==5,'nonlethal dragon score differs'
    print('PASS: original parsed water command, live dragon defeat, consumed water, score and cleanup')


def check_original_giant_encounter(d):
    """The original sling shot must finish its animation and kill the giant."""
    game=ROOT/'kingsquest1'
    files={'/game/'+path.name:path.read_bytes() for path in game.iterdir()
           if path.is_file() and (path.name.startswith('vol.') or path.name in
                                  ('logDir','picDir','viewDir','sndDir','words.tok','object'))}
    # Pebbles and sling are pre-owned. These possession flags are set by the
    # original acquisition scripts in rooms 34 and 62, respectively.
    setup=bytes([3,250,1,3,0,58,3,1,57,12,5,12,93,12,97,92,13,92,14,
                 33,0,30,0,41,0,0,37,0,50,120])
    body=bytes([255,1,250,0,255])+len(setup).to_bytes(2,'little')+setup
    parse=bytes([114,0,1,117,0])
    body+=bytes([255,1,250,2,255])+len(parse).to_bytes(2,'little')+parse
    finish=bytes([3,240,13,97,240,200,3,240,14,97,240,201,134,1])
    body+=bytes([22,58,13,5,1,250,255,1,86,4,255])+len(finish).to_bytes(2,'little')+finish+b'\0'
    text=b'use sling\0';key=b'Avis Durgan'
    messages=bytes([1])+(4+len(text)).to_bytes(2,'little')+bytes([4,0])+bytes(v^key[i%11] for i,v in enumerate(text))
    logic=len(body).to_bytes(2,'little')+body+messages
    volume=files['/game/vol.0'];offset=len(volume)
    files['/game/vol.0']=volume+b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
    directory=bytearray(files['/game/logDir']);directory[:3]=offset.to_bytes(3,'big')
    files['/game/logDir']=bytes(directory)
    error,output,state=exercise(d,files,arguments=b'/game 0\r',module='wbgame',base=0xa000,
        database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
        keyboard_by_cycle={cycle:(b'\r',0) for cycle in range(5,2000,5)},os_call_limit=100000)
    assert not error,('giant encounter',error)
    assert state['vmvariables'][86]==4,'original giant did not die after sling animation'
    assert state['vmflags'][93]==0,'pebble possession summary remained set'
    assert state['vmvariables'][200:202]==b'\0\xff','pebbles were not consumed or sling was lost'
    assert state['vmvariables'][3]==2,'sling encounter net score differs'
    print('PASS: original parsed sling command, completed shot animation, giant death, net score and cleanup')


def original_quest_chain_files(prerequisites=False,all_acquisitions=False,snapshot=False):
    """Carry actual puzzle results through room changes to the original ending."""
    game=ROOT/'kingsquest1'
    files={'/game/'+path.name:path.read_bytes() for path in game.iterdir()
           if path.is_file() and (path.name.startswith('vol.') or path.name in
                                  ('logDir','picDir','viewDir','sndDir','words.tok','object'))}
    if snapshot:all_acquisitions=True
    if all_acquisitions:prerequisites=True
    from check_lzw import expand
    entry=int.from_bytes(files['/game/logDir'][:3],'big')
    volume=files[f'/game/vol.{entry>>20}'];offset=entry&0xfffff
    header=volume[offset:offset+7];payload=volume[offset+7:offset+7+int.from_bytes(header[5:7],'little')]
    compressed=header[3:5]!=header[5:7]
    if compressed:payload=expand(payload)
    original_messages=payload[2+int.from_bytes(payload[:2],'little'):]
    message_base=original_messages[0]
    assert message_base+17<=255
    def when(condition,body):return b'\xff'+bytes(condition)+b'\xff'+len(body).to_bytes(2,'little')+body
    def parse(message,x=None,y=None):
        return (bytes([37,0,x,y]) if x is not None else b'')+bytes([114,0,message_base+message,117,0])
    def transfer(stage,room):return bytes([3,250,stage,3,251,0,18,room])
    setup=bytes([3,250,1,3,251,0,3,0,76,3,1,77,3,7,158,12,5,12,87,12,171,
                 12,88,12,167,12,93,12,97,92,8,92,22,92,26,92,13,92,14,
                 33,0,30,0,41,0,0,37,0,73,150,112])
    if prerequisites:
        setup=bytes([3,250,6,3,251,0,3,0,24,3,1,23,3,7,158,12,5,12,171,
                     12,88,92,22,92,26,33,0,30,0,41,0,0,37,0,50,134,112])
    if all_acquisitions:
        setup=bytes([3,250,9,3,251,0,3,0,3,3,1,0,3,7,158,12,5,
                     33,0,30,0,41,0,0,37,0,122,120,112])
    if snapshot:
        setup+=bytes([143,5])  # Original root normally sets its game ID in room 0.
    body=when([1,250,0],setup)
    first=[253,7,5,1,251,0]
    if all_acquisitions:
        stage=when(first,parse(10,122,120)+bytes([3,251,1]))
        stage+=when([1,251,2],parse(11,122,120)+bytes([3,251,3]))+bytes([22,105])
        stage+=when([7,62,1,251,1],bytes([3,251,2]))
        stage+=when([7,67],transfer(10,12))
        body+=when([1,250,9],stage)
        stage=when(first,parse(12,40,130)+bytes([3,251,1]))+bytes([22,105])
        stage+=when([7,81],transfer(6,24))
        body+=when([1,250,10],stage)
        stage=when(first,parse(14,126,138)+bytes([3,251,1]))
        stage+=when([1,251,2],parse(15)+bytes([3,251,3]))+bytes([22,105])
        stage+=when([7,89,1,251,1],bytes([3,251,2]))
        stage+=when([7,89,1,89,1],transfer(12,79))
        body+=when([1,250,11],stage)
        stage=when(first,parse(16)+bytes([3,251,1]))
        stage+=when([1,251,2],parse(17,130,150)+bytes([3,251,3]))+bytes([22,105])
        stage+=when([7,185,1,251,1],bytes([3,251,2]))
        stage+=when([7,171],transfer(1,76))
        body+=when([1,250,12],stage)
    if prerequisites:
        for stage_number,room,message,x,y,flag,next_stage,next_room in (
                (6,24,7,50,134,86,7,34),
                (7,34,8,80,100,93,8,62),
                (8,62,9,130,110,97,1,76)):
            stage=when(first,parse(message,x,y)+bytes([3,251,1]))
            if all_acquisitions and stage_number==7:
                stage+=when([1,251,2],parse(13,130,100)+bytes([3,251,3]))
            stage+=bytes([22,105])
            if all_acquisitions and stage_number==7:
                stage+=when([7,93,1,251,1],bytes([3,251,2]))
                stage+=when([7,flag,7,88],transfer(next_stage,next_room))
            elif all_acquisitions and stage_number==8:
                stage+=when([7,flag],transfer(11,31))
            else:stage+=when([7,flag],transfer(next_stage,next_room))
            body+=when([1,250,stage_number],stage)
    stage=when(first,parse(1)+bytes([3,251,1]))+bytes([22,105])
    stage+=when([7,186,1,30,0],transfer(2,77))
    body+=when([1,250,1],stage)
    stage=when(first+[7,187],parse(3,130,128)+bytes([3,251,1]))+bytes([22,105])
    if snapshot:
        # Save phase 1, then corrupt earned progress. A successful deferred
        # restore returns to phase 1; a failed restore remains in phase 2.
        stage+=when([7,188],bytes([3,250,13,3,251,0]))
    else:stage+=when([7,188],transfer(3,51))
    body+=when([1,250,2],stage)
    if snapshot:
        checkpoint=bytes([142,255,30,143,3,251,1,125,3,3,200,3,74,0,13,188,93,21,3,251,2,126])
        body+=when([1,250,13],when([1,251,0],checkpoint)+when([1,251,1],transfer(3,51)))
    stage=when(first,parse(2,80,140)+bytes([3,251,1]))
    stage+=when([1,251,2],parse(4,40,115)+bytes([3,251,3]))+bytes([22,105])
    stage+=when([1,75,2,1,251,1],bytes([3,251,2]))
    stage+=when([7,100],transfer(4,58))
    body+=when([1,250,3],stage)
    stage=when(first,parse(5,50,120)+bytes([3,251,1]))
    stage+=when([1,251,2],bytes([39,2,241,242,38,0,241,242])+parse(6)+bytes([3,251,3]))+bytes([22,105])
    stage+=when([1,86,4,1,251,1],bytes([3,251,2]))
    stage+=when([7,104],transfer(5,53))
    body+=when([1,250,4],stage)
    finish=b''.join(bytes([3,240,item,97,240,variable]) for item,variable in
                    ((19,200),(21,201),(2,202),(13,203),(14,204),(22,205),(26,206),(8,207),(11,208),(1,209),(9,210)))
    if snapshot:
        # Save the completed ending state to a second file before quitting.
        # This lets the real-driver MAME test inspect private VM state after
        # the root process has released its workspace.
        finish+=bytes([3,250,14,125,3,250,15,134,1])
    else:
        finish+=bytes([134,1])
    body+=when([1,250,5],bytes([22,105])+when([7,195],finish))+b'\0'
    strings=b''.join(command+b'\0' for command in
                     (b'play fiddle',b'throw water',b'get shield',b'get mirror',b'use sling',b'get chest',
                      b'get clover',b'get pebbles',b'get sling',b'push rock',b'get dagger',
                      b'cut rope',b'get water',b'get bowl',b'fill',b'give bowl',b'get fiddle'))
    # Keep all original global-message IDs: room scripts may reference %gN.
    old_end=int.from_bytes(original_messages[1:3],'little')+1
    old_strings=original_messages[3+2*message_base:old_end]
    key=b'Avis Durgan'
    if not compressed:old_strings=bytes(value^key[i%11] for i,value in enumerate(old_strings))
    offsets=[int.from_bytes(original_messages[3+i*2:5+i*2],'little') for i in range(message_base)]
    offsets=[value+34 if value else 0 for value in offsets]
    offset=2+2*(message_base+17)+len(old_strings)
    for text in strings.split(b'\0')[:-1]:offsets.append(offset);offset+=len(text)+1
    strings=old_strings+strings
    messages=bytes([message_base+17])+(2+2*(message_base+17)+len(strings)).to_bytes(2,'little')
    messages+=b''.join(value.to_bytes(2,'little') for value in offsets)
    messages+=bytes(value^key[i%11] for i,value in enumerate(strings))
    logic=len(body).to_bytes(2,'little')+body+messages
    volume=files['/game/vol.0'];offset=len(volume)
    files['/game/vol.0']=volume+b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
    directory=bytearray(files['/game/logDir'])
    assert len(directory)==105*3
    directory.extend(directory[:3])  # Unchanged original root is additionally reachable as logic 105.
    directory[:3]=offset.to_bytes(3,'big');files['/game/logDir']=bytes(directory)
    return files


def check_original_quest_chain(d,prerequisites=False,all_acquisitions=False):
    """Carry actual puzzle results through room changes to the original ending."""
    files=original_quest_chain_files(prerequisites,all_acquisitions)
    error,output,state=exercise(d,files,arguments=b'/game 0\r',module='wbgame',base=0xa000,
        database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
        keyboard_by_cycle={cycle:(b'\r',0) for cycle in range(5,5000,5)},cycle_limit=1500,os_call_limit=300000)
    assert not error,('quest chain',error,state['vmcurrent'],state['vmopcode'],state['vmip'].hex(),list(state['vmvariables'][250:252]),state['asseterror'],state['vmerror'],state['messagebuffer'][:80])
    assert state['vmflags'][195]==1,'combined quest did not reach original ending'
    assert state['vmvariables'][74]==3,'combined quest lost treasure progress'
    assert state['vmvariables'][200:203]==b'\xff'*3,'combined quest lost a treasure'
    assert state['vmvariables'][203:207]==b'\0\xff\xff\0','combined quest consumed/retained prerequisites incorrectly'
    assert state['vmvariables'][207]==255,'clover was lost'
    assert state['vmvariables'][208:210]==(b'\xff\xff' if all_acquisitions else b'\0\0'),'bucket/dagger ownership differs'
    assert state['vmvariables'][210]==0,'given bowl remained in inventory'
    expected_score=61 if all_acquisitions else 39 if prerequisites else 34
    assert state['vmvariables'][3]==expected_score,('combined quest score',state['vmvariables'][3])
    print('PASS: original quest chain, prerequisite acquisitions='+str(prerequisites)+', all acquisitions='+str(all_acquisitions)+', real root/room changes, carried inventory, score '+str(expected_score)+' and ending/cleanup')


def check_original_rock_death(d,restart=False):
    """Let an original lethal encounter enter the original death-action loop."""
    files=original_quest_chain_files(all_acquisitions=True)
    entry=int.from_bytes(files['/game/logDir'][:3],'big')
    volume=files['/game/vol.0'];offset=entry&0xfffff
    payload=volume[offset+7:offset+7+int.from_bytes(volume[offset+5:offset+7],'little')]
    messages=payload[2+int.from_bytes(payload[:2],'little'):]
    message_base=messages[0]-17
    def when(condition,body):return b'\xff'+bytes(condition)+b'\xff'+len(body).to_bytes(2,'little')+body
    setup=bytes([3,250,1,3,0,3,3,1,0,3,7,158,12,5,
                 33,0,30,0,41,0,0,37,0,122,140,112,143,5])
    body=(when([7,6],bytes([134,1])) if restart else b'')+when([1,250,0],setup)
    body+=when([253,7,5,1,250,1],bytes([114,0,message_base+10,117,0,3,250,2]))
    body+=bytes([22,105])+when([7,197,1,97,0],bytes([128] if restart else [134,1]))+b'\0'
    logic=len(body).to_bytes(2,'little')+body+messages
    offset=len(volume);files['/game/vol.0']=volume+b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
    directory=bytearray(files['/game/logDir']);directory[:3]=offset.to_bytes(3,'big')
    files['/game/logDir']=bytes(directory);controls=[];deaths=[]
    def quitting(cpu,r,syms):controls.append(cpu.read(syms['vmplayercontrol'],1)[0])
    def restarting(cpu,r,syms):
        deaths.append((cpu.read(syms['vmflags']+63,1)[0],cpu.read(syms['vmflags']+197,1)[0],
                       cpu.read(syms['vmvariables']+97,1)[0],cpu.read(syms['vmplayercontrol'],1)[0]))
    hooks={'GameQuitCommand':quitting}
    if restart:hooks['GameRestartCommand']=restarting
    error,output,state=exercise(d,files,arguments=b'/game 0\r',module='wbgame',base=0xa000,
        database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
        keyboard_by_cycle={cycle:(b'\r',0) for cycle in range(5,2000,5)},
        cycle_limit=500,os_call_limit=100000,breakpoint_hooks=hooks)
    assert not error,('rock death',error,state['vmopcode'],state['vmvariables'][97])
    if restart:
        assert deaths==[(1,1,0,0)],('restart did not follow completed death handling',deaths)
        assert state['vmflags'][6]==1 and state['vmflags'][63]==0 and state['vmflags'][197]==0,'restart retained death state'
        assert controls==[1],'restart did not restore player control'
    else:
        assert state['vmflags'][63]==1 and state['vmflags'][197]==1,'lethal rock did not enter original death handling'
        assert controls==[0],'death handling restored player movement'
        assert b'very sorry' in state['messagebuffer'],state['messagebuffer'][:160]
    assert state['vmvariables'][97]==0 and state['vmvariables'][3]==0,'death countdown or score differs'
    print('PASS: original lethal rock encounter, death countdown/message, player-control ownership, restart='+str(restart)+' and cleanup')



def check_timed_messages(d):
    """Exercise blocking timeouts, public counter wrap and modal exclusions."""
    cases=[
        ('print',101,1,None,b'',None,30,0),
        ('print.v',102,2,None,b'',None,60,0),
        ('print.at',151,1,None,b'',None,30,0),
        ('print.at.v',152,1,None,b'',None,30,0),
        ('keyboard before timeout',101,2,None,b'',{5:(b'\r',0)},5,0),
        ('maximum timeout interrupted',101,255,None,b'\r',None,0,0),
        ('untimed keyboard',101,0,None,b'\r',None,0,0),
        ('held message',101,1,None,b'',None,0,1),
        ('pause ignores print timer',136,1,None,b'\r',None,0,1),
        ('raster counter wrap',101,1,{'start':250,'step':1},b'',None,30,0),
        ('raster coarse samples',151,2,{'start':250,'step':7},b'',None,9,0),
        ('raster maximum timeout',102,255,{'start':250,'step':17},b'',None,450,0),
        ('foreground rebase',101,1,{'start':250,'step':200},b'',None,2,0),
    ]
    key=b'Avis Durgan'
    for label,opcode,timeout,sol,keyboard,keys,wanted_cycles,wanted_timer in cases:
        print('Checking timed message:',label,flush=True)
        script=bytes([3,21,timeout,3,6,1])
        if label=='held message':script+=bytes([12,15])
        script+=bytes([opcode])
        if opcode!=136:script+=bytes([6 if opcode in (102,152) else 1])
        if opcode in (151,152):script+=bytes([3,7,12])
        script+=bytes([134,1,0])
        plaintext=b'timed test\0'
        encrypted=bytes(value^key[i%len(key)] for i,value in enumerate(plaintext))
        logic=len(script).to_bytes(2,'little')+script+bytes([1])+(4+len(plaintext)).to_bytes(2,'little')+bytes([4,0])+encrypted
        files={'/game/logDir':b'\xff'*3+bytes(3),
               '/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic}
        hooks={}
        if label=='foreground rebase':
            def resume(debug,registers,syms):
                # A foreground notification advances the visibility epoch.
                # The following 200-frame counter jump must be discarded.
                debug.write(0x0000+syms['gameclockreset'],b'\x01')
            hooks['GameModalForeground']=resume
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,
            database=0x0000,window=0x8000,blocks=None,multiple=True,
            firstblock=0x10,capture=True,keyboard=keyboard,
            keyboard_by_cycle=keys,sol=sol,breakpoint_hooks=hooks,
            os_call_limit=20000)
        assert not error and state['cycles']==wanted_cycles,(label,error,state['cycles'])
        assert state['vmvariables'][21]==wanted_timer,(label,state['vmvariables'][21])
    for offset_name in ('zero','size','CRC'):
        helper=bytearray((ROOT/'objs/sierraui').read_bytes())
        entry=int.from_bytes(helper[9:11],'big')
        offset=0 if offset_name=='zero' else len(helper)-(1 if offset_name=='CRC' else 0)
        helper[entry+16:entry+18]=offset.to_bytes(2,'big')
        files['sierraui']=bytes(helper)
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,
            database=0x0000,window=0x8000,blocks=None,multiple=True,
            firstblock=0x10,capture=True,keyboard=b'\r',os_call_limit=20000)
        assert error==203,(offset_name,error)
    print('PASS: timed blocking messages, keyboard interruption, held/pause exclusions, raster wrap/coarse/max samples, foreground rebase and invalid wait-entry cleanup')


def check_coco_show_object(d):
    """Run CoCo show.obj through its sprite MMU calls and message_box."""
    from check_logic_executor import compile_module
    with tempfile.TemporaryDirectory(prefix='sierra-coco-show-object-') as name:
        code,syms=compile_module(ROOT/'objs/mnln.asm',Path(name)/'mnln')
        node,data=0x4000,0x5000
        from check_lzw import resources
        actual_view=bytearray(next(payload for name,_,payload in resources()
                                   if name=='viewDir/4'))
        description=b'A fine treasure.\0'
        description_offset=len(actual_view)
        actual_view[3:5]=description_offset.to_bytes(2,'little')
        actual_view.extend(description)
        stop=0x7e00
        d.write(stop,b'\x39');d.breakpoint(stop)
        cases=[('literal','cmd_show_obj',bytes([4]),1,4),
               ('variable','cmd_show_obj_v',bytes([200]),1,13)]
        total=0;mmu_calls=[]
        for base in (0x8000,0x9000):
            d.write(0,bytes(0x6000));d.write(base,code)
            d.write(0x0000,bytes.fromhex('7fff'))
            for address in (0x004b,0x004d,0x004f,0x0051,0x0053,0x0055):
                d.write(address,bytes.fromhex('6000'))
            hooks={}
            for label in ('message_box','SetLogicPage'):
                address=base+syms[label]
                d.breakpoint(address)
                hooks[address]=label
            d.write(0x0701,b'\x39');d.breakpoint(0x0701)
            for label,entry,operands,count,viewnum in cases:
                d.write(base+syms['list_struct'],node.to_bytes(2,'big'))
                d.write(node,b'\0\0'+bytes([viewnum])+data.to_bytes(2,'big')+
                        len(actual_view).to_bytes(2,'big'))
                d.write(data,actual_view)
                d.write(0x0431+200,bytes([viewnum]))
                d.write(0x05b1,b'\0')
                d.write(0x3000,operands+b'GUARD')
                d.write(0x7ef0,b'\x7e\x00STACK')
                captured=[]
                d.regs(pc=base+syms[entry],s=0x7ef0,y=0x3000,dp=0,cc=0x50)
                for _ in range(32):
                    d.call('c');r=d.regs()
                    if r['pc']==stop:break
                    if r['pc']==0x0701:
                        function19=d.read(0x0019,1)[0]
                        function=function19 if function19==0x1b else d.read(0x0021,1)[0]
                        d.write(0x0019,b'\0')
                        argument=int.from_bytes(d.read(r['s']+2,2),'big')
                        if function==0x15:
                            view_node=argument
                            object_ptr=int.from_bytes(d.read(view_node+4,2),'big')
                            coords=d.read(object_ptr+3,2)
                            dimensions=d.read(view_node+8,4)
                            mmu_calls.append((entry,function,coords,dimensions))
                        elif function in (0x0c,0x1b,0x12):
                            mmu_calls.append((entry,function,b'',b''))
                        else:raise AssertionError(('unexpected show.obj MMU function',entry,function))
                        ret=int.from_bytes(d.read(r['s'],2),'big')
                        d.regs(pc=ret,s=r['s']+2)
                        continue
                    assert r['pc'] in hooks,(label,entry,r)
                    service=hooks[r['pc']]
                    ret=int.from_bytes(d.read(r['s'],2),'big')
                    update={'pc':ret,'s':r['s']+2}
                    if service=='message_box':
                        captured.append(d.read(r['u'],len(description)).split(b'\0',1)[0])
                    d.regs(**update)
                else:raise AssertionError((entry,'CoCo show.obj failed to return'))
                assert r['pc']==stop and r['s']==0x7ef2,(entry,r)
                assert r['y']==0x3000+count,(entry,r['y'])
                assert captured==[description[:-1]],(label,captured,description)
                assert d.read(0x05b1,1)==b'\1','CoCo full-screen redraw flag was not restored'
                assert d.read(0x3000+count,5)==b'GUARD' and d.read(0x7ef2,5)==b'STACK'
                loaded_code=d.read(base,len(code))
                mutable={*range(syms['list_struct'],syms['list_struct']+7),
                         *range(syms['ListLastNode'],syms['ListLastNode']+2)}
                assert all(loaded_code[i]==code[i] for i in range(len(code))
                           if i not in mutable),(entry,'CoCo module code modified',
                    [(i,loaded_code[i],code[i]) for i in range(len(code))
                     if loaded_code[i]!=code[i] and i not in mutable][:8])
                assert d.read(base+syms['list_struct'],2)==node.to_bytes(2,'big')
                assert d.read(base+syms['ListLastNode'],2)==(
                    base+syms['list_struct']).to_bytes(2,'big')
                total+=1
            for address in hooks:d.breakpoint(address,False)
            d.breakpoint(0x0701,False)
        for entry in ('cmd_show_obj','cmd_show_obj_v'):
            calls=[call for call in mmu_calls if call[0]==entry]
            sequence=[0x15,0x0c,0x1b,0x12,0x1b]
            assert [call[1] for call in calls]==sequence*2,(entry,calls)
            for sprite in (calls[0],calls[len(sequence)]):
                assert sprite[2]==bytes([69,167]) and sprite[3][:2]==bytes([22,22]),(entry,sprite)
        # Exercise the real CoCo view selectors against an expanded KQ1 view,
        # so the geometry above is not the only evidence from a synthetic cel.
        from check_lzw import resources
        actual_view=next(data for name,_,data in resources() if name=='viewDir/4')
        view_node,view_data,object_record=0x4000,0x5000,0x6000
        d.write(base+syms['list_struct'],view_node.to_bytes(2,'big'))
        d.write(view_node,b'\0\0\x04'+view_data.to_bytes(2,'big')+
                len(actual_view).to_bytes(2,'big'))
        d.write(view_data,actual_view)
        d.write(object_record,bytes(43))
        d.write(0x7ef0,b'\x7e\x00STACK')
        d.breakpoint(base+syms['SetLogicPage'])
        d.regs(pc=base+syms['SetViewForObj'],s=0x7ef0,u=object_record,b=4,dp=0,cc=0x50)
        for _ in range(32):
            d.call('c');r=d.regs()
            if r['pc']==stop:break
            assert r['pc']==base+syms['SetLogicPage'],('real CoCo view selector service',r)
            ret=int.from_bytes(d.read(r['s'],2),'big')
            d.regs(pc=ret,s=r['s']+2)
        else:raise AssertionError('real CoCo view selector did not return')
        selected=d.read(object_record,43)
        cel_pointer=int.from_bytes(selected[0x10:0x12],'big')
        cel_dimensions=selected[0x1c:0x1e]
        assert int.from_bytes(selected[6:8],'big')==view_data,(selected.hex())
        assert cel_pointer==view_data+0x1a,(hex(cel_pointer),actual_view[:32].hex())
        assert cel_dimensions==actual_view[0x1a:0x1c] and cel_dimensions!=b'\0\0',(
            cel_dimensions.hex(),actual_view[0x1a:0x1c].hex())
        assert r['s']==0x7ef2 and d.read(0x7ef2,5)==b'STACK'
        d.breakpoint(base+syms['SetLogicPage'],False)
        # Rasterize that same resource cel with CoCo's production ObjBlit,
        # then compare every emitted pixel with an independent row-run decoder.
        from check_logic_executor import compile_module
        shdw,shdw_syms=compile_module(ROOT/'objs/shdw.asm',Path(name)/'shdw')
        shdw=bytearray(shdw);shdw[shdw_syms['TwiddleMmu']]=0x39
        render_base,cel_address,object_address=0xd000,0x4000,0x3000
        d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01')
        d.write(0xffa8,bytes(range(8)));d.write(render_base,shdw)
        cel=actual_view[cel_pointer-view_data:]
        width,height,transparent=cel[:3]
        runs=cel[3:];cursor=0;decoded=[]
        for row in range(height):
            pixels=[]
            while True:
                run=runs[cursor];cursor+=1
                if run==0:break
                color=run&0xf0;length=run&0x0f
                assert length and len(pixels)+length<=width,(row,run,len(pixels))
                pixels.extend([None if color==((transparent<<4)&0xf0) else color>>4]*length)
            assert len(pixels)<=width,(row,len(pixels),width)
            pixels.extend([None]*(width-len(pixels)))
            decoded.append(pixels)
        render_x,render_y=50,70;top=render_y-height+1;background=0x4f
        for row in range(top,top+height):
            d.write(0x6040+row*160+render_x-1,bytes([background])*(width+2))
        record=bytearray(0x30);record[3]=render_x;record[4]=render_y
        record[8:10]=view_data.to_bytes(2,'big')
        record[0x10:0x12]=cel_address.to_bytes(2,'big');record[0x24]=15
        d.write(object_address,record);d.write(cel_address,cel)
        stop=0x7e00;stack=0x7ef0
        d.write(stop,b'\x39');d.breakpoint(stop)
        d.write(stack,stop.to_bytes(2,'big')+object_address.to_bytes(2,'big')+b'STACK')
        d.regs(pc=render_base+shdw_syms['ObjBlit'],s=stack,dp=0,cc=0x50)
        d.call('c');r=d.regs()
        assert r['pc']==stop and r['s']==stack+2 and d.read(stack+4,5)==b'STACK',r
        for row,pixels in enumerate(decoded):
            actual=d.read(0x6040+(top+row)*160+render_x,width)
            expected=bytes(background if pixel is None else 0xf0|pixel for pixel in pixels)
            assert actual==expected,('real KQ1 CoCo ObjBlit pixels',row,actual.hex(),expected.hex())
            assert d.read(0x6040+(top+row)*160+render_x-1,1)==bytes([background])
            assert d.read(0x6040+(top+row)*160+render_x+width,1)==bytes([background])
        d.breakpoint(stop,False)
        print(f'PASS: {total} CoCo show.obj/show.obj.v cases; real KQ1 view 4 selects cel offset $001A (21x22), and production ObjBlit matches an independent RLE pixel oracle with clipped-edge guards')


def check_object_previews(d):
    """Check item pixels during dismissal and exact restoration afterwards."""
    default=bytearray([0,0,1,0,0,7,0,1,3,0,4,3,31,0x12,0xf1,0x21,0,0x31,0x43,0,0x51,0])
    default[3:5]=len(default).to_bytes(2,'little');default+=b'A fine treasure.\0'
    def fixture(command,view=default,depth=0,audio=False,viewnum=0):
        config=b''
        if command[:1]==bytes([111]):
            config,command=command[:4],command[4:]
        start=config+bytes([3,0,1,24,0,25,0,26])
        if audio:start+=bytes([98,0,99,0,200])
        script=start+(bytes([22,2]) if depth else command)+bytes([3,240,73,134,1,0])
        logic=len(script).to_bytes(2,'little')+script
        data=bytearray();offsets=[]
        def record(payload):return b'\x12\x34\0'+len(payload).to_bytes(2,'little')*2+payload
        for payload in (logic,b'\xff',view):offsets.append(len(data));data.extend(record(payload))
        logs=[b'\xff'*3,offsets[0].to_bytes(3,'big')]
        for number in range(2,depth+2):
            logs.append(len(data).to_bytes(3,'big'))
            body=bytes([22,number+1,0]) if number<depth+1 else command+b'\0'
            data.extend(record(len(body).to_bytes(2,'little')+body))
        sound=len(data);data.extend(record(bytes([28,63,0,240,255,0,240])))
        return {'/game/vol.0':bytes(data),'/game/logDir':b''.join(logs),
                '/game/picDir':b'\xff'*3+offsets[1].to_bytes(3,'big'),
                '/game/viewDir':b'\xff'*(3*viewnum)+offsets[2].to_bytes(3,'big'),
                '/game/sndDir':sound.to_bytes(3,'big')}
    baseline=None
    configured_baselines={}
    cases=[('baseline',b'',0,False),('literal',bytes([129,0]),0,False),
           ('variable',bytes([3,200,0,162,200]),0,False),
           *((f'configured screen offset {offset}',bytes([111,offset,23,0,129,0]),0,False)
             for offset in range(5)),
           ('literal view 4',bytes([129,4]),0,False,4),
           ('variable view 13',bytes([3,200,13,162,200]),0,False,13),
           ('already cached',bytes([30,0,129,0]),0,False),
           ('held/timer flags',bytes([12,15,3,21,2,129,0]),0,False),
           ('depth 16 and long directory',bytes([129,0]),16,True),
           ('moving-object baseline',bytes([33,0,41,0,0,37,0,20,30,54,0,15,35,0,37,0,30,40,26]),0,False),
           ('moving-object preview',bytes([33,0,41,0,0,37,0,20,30,54,0,15,35,0,129,0,37,0,30,40,26]),0,False),
           ('text-screen baseline',bytes([106]),0,False),
           ('text-screen preview',bytes([106,129,0]),0,False),
           ('text-screen held/timer flags',bytes([106,12,15,3,21,2,129,0]),0,False)]
    for case in cases:
        label,command,depth,audio=case[:4]
        viewnum=case[4] if len(case)>4 else 0
        screen_offset=None
        if label.startswith('configured screen offset '):
            screen_offset=int(label.rsplit(' ',1)[1])
            print('Checking object preview baseline: screen offset',screen_offset,flush=True)
            error,configured_baselines[screen_offset],state=exercise(
                d,fixture(bytes([111,screen_offset,23,0])),arguments=b'/game 1\r',
                module='wbgame',base=0xa000,database=0,window=0x8000,blocks=None,
                multiple=True,firstblock=0x10,capture=True,frame_capture=True,
                os_call_limit=60000)
            assert not error and state['vmvariables'][240]==73,(screen_offset,error)
        print('Checking object preview:',label,flush=True)
        modal={}
        def inspect(cpu,r,syms):
            modal['text']=cpu.read(syms['textcharacters'],1000)
            block=int.from_bytes(cpu.read(syms['firstblock'],2),'big')
            old=cpu.read(0xffac,1);frame=bytearray()
            for page in range(10):
                cpu.write(0xffac,bytes([block+page]));frame.extend(cpu.read(0x8000,8192))
            cpu.write(0xffac,old);modal['frame']=bytes(frame[:76800])
        hooks={'GamePrintWait':inspect} if 'baseline' not in label else None
        if label=='already cached':
            def unexpected_discard(*args):raise AssertionError('preview discarded an existing cached view')
            hooks['VmDiscardResource']=unexpected_discard
        files=fixture(command,depth=depth,audio=audio,viewnum=viewnum);arguments=b'/game 1\r'
        if depth:
            directory=b'/'+b'x'*126
            files={directory.decode()+name[5:]:data for name,data in files.items()}
            arguments=directory+b' 1\r'
        error,frame,state=exercise(d,files,arguments=arguments,module='wbgame',base=0xa000,
            database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,
            capture=True,frame_capture=True,keyboard=b'\r',os_call_limit=60000,
            breakpoint_hooks=hooks,psg={'version':4} if audio else None,
            sol={'start':250,'step':1} if audio else None)
        assert not error,(label,error)
        assert state['vmvariables'][240]==73,(label,'caller not resumed')
        assert state['gamefont']==(ROOT/'objs/sierrafont').read_bytes(),(label,'font overwritten')
        if 'baseline' in label:baseline=frame
        else:
            expected_scene=configured_baselines[screen_offset] if screen_offset is not None else baseline
            assert frame==expected_scene,(label,'scene not restored')
            popup=bytearray(1000)
            offset=screen_offset if screen_offset is not None else 0
            for popup_row in range(9,16):
                popup[popup_row*40+9+offset:popup_row*40+30+offset]=b' '*21
            popup[10*40+10+offset:10*40+26+offset]=b'A fine treasure.'
            assert modal['text']==popup,(label,modal['text'].find(b'A fine treasure.'))
            preview_y=173+(screen_offset-1)*8 if screen_offset is not None else 173
            pixels=bytes([2,2,2,2,16,16,3,3])
            matches=[i for i in range(0,len(modal['frame'])-len(pixels)+1)
                     if modal['frame'][i:i+len(pixels)]==pixels]
            assert modal['frame'][preview_y*320+156:preview_y*320+164]==pixels,(label,'preview pixels missing',preview_y,matches[:10])
        if 'held/timer flags' in label:assert state['vmflags'][15]==1 and state['vmvariables'][21]==2
    # Use the real expanded KQ1 view resource on Wild Bits as well. Add a
    # bounded description at the resource's declared description offset; cel
    # and loop tables stay byte-for-byte as shipped in the game.
    from check_lzw import resources
    actual_view=next(data for name,_,data in resources() if name=='viewDir/4')
    description=b'A fine treasure.\0'
    description_offset=len(actual_view)
    actual_view=bytearray(actual_view)
    actual_view[3:5]=description_offset.to_bytes(2,'little')
    actual_view.extend(description)
    _,actual_baseline,baseline_state=exercise(d,
        fixture(b'',view=bytes(actual_view),viewnum=4),module='wbgame',base=0xa000,
        database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,
        capture=True,frame_capture=True,os_call_limit=60000)
    assert baseline_state['vmvariables'][240]==73,'real-view baseline script did not resume'
    print('Checking object preview: real expanded KQ1 view 4',flush=True)
    modal={}
    def inspect_real_view(cpu,r,syms):
        modal['text']=cpu.read(syms['textcharacters'],1000)
        block=int.from_bytes(cpu.read(syms['firstblock'],2),'big')
        old=cpu.read(0xffac,1);frame=bytearray()
        for page in range(10):
            cpu.write(0xffac,bytes([block+page]));frame.extend(cpu.read(0x8000,8192))
        cpu.write(0xffac,old);modal['frame']=bytes(frame[:76800])
    files=fixture(bytes([129,4]),view=bytes(actual_view),viewnum=4)
    error,frame,state=exercise(d,files,module='wbgame',base=0xa000,database=0,
        window=0x8000,blocks=None,multiple=True,firstblock=0x10,
        capture=True,frame_capture=True,keyboard=b'\r',os_call_limit=60000,
        breakpoint_hooks={'GamePrintWait':inspect_real_view})
    assert not error and state['vmvariables'][240]==73,('real KQ1 view 4',error)
    assert frame==actual_baseline,'real KQ1 view preview did not restore the original scene'
    popup=bytearray(1000)
    for popup_row in range(9,16):popup[popup_row*40+9:popup_row*40+30]=b' '*21
    popup[10*40+10:10*40+10+len(description)-1]=description[:-1]
    assert modal['text']==popup,'real KQ1 view description was not displayed'
    cel=actual_view[0x1a:];width,height,transparent=cel[:3]
    pixels=cel[3:];cursor=0;decoded=[]
    for row in range(height):
        decoded_row=[]
        while True:
            run=pixels[cursor];cursor+=1
            if run==0:break
            color=run&0xf0;length=run&0x0f
            assert length and len(decoded_row)+length<=width,(row,run)
            decoded_row.extend([None if color==((transparent<<4)&0xf0) else color>>4]*length)
        decoded_row.extend([None]*(width-len(decoded_row)))
        decoded.append(decoded_row)
    origin_x=((160-width)//2)*2;origin_y=167-height+1+8
    for row,decoded_row in enumerate(decoded):
        at=(origin_y+row)*320+origin_x
        expected_row=bytearray(actual_baseline[at:at+width*2])
        for column,color in enumerate(decoded_row):
            if color is not None:
                expected_row[column*2:column*2+2]=bytes([color+1])*2
        actual_row=modal['frame'][at:at+width*2]
        assert actual_row==expected_row,('Wild Bits KQ1 view 4 pixels differ from independent cel RLE oracle',
            row,actual_row.hex(),expected_row.hex())
    for label,view,expected_error in [('empty description',default[:3]+b'\0\0'+default[5:],0),
                       ('maximum description',default[:22]+b'X'*511+b'\0',0),
                       ('description outside slab',default[:3]+b'\xff\xff'+default[5:],203),
                       ('unterminated description',default[:-1],203),
                       ('oversized description',default[:22]+b'X'*512+b'\0',203)]:
        print('Checking object preview:',label,flush=True)
        error,output,state=exercise(d,fixture(bytes([129,0]),view),module='wbgame',base=0xa000,
            database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,
            capture=True,keyboard=b'\r',os_call_limit=60000)
        assert error==expected_error,(label,error)
    original=(ROOT/'objs/sierraui').read_bytes();entry=int.from_bytes(original[9:11],'big')
    for offset in (0,len(original),len(original)-1):
        helper=bytearray(original);helper[entry+34:entry+36]=offset.to_bytes(2,'big')
        files=fixture(bytes([129,0]));files['sierraui']=bytes(helper)
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,database=0,
            window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
            keyboard=b'\r',os_call_limit=60000)
        assert error==203,(offset,error)
    print('PASS: literal/variable synthetic and real KQ1 view 4 pixels/descriptions, exact restoration, preserved cache/print flags, deep audio/long-path safety and bounded malformed-resource cleanup')
    check_coco_show_object(d)


def check_interpreter_information(d):
    """A menu version request must dismiss, restore state and resume its caller."""
    from check_logic_executor import compile_module
    with tempfile.TemporaryDirectory(prefix='sierra-version-reference-') as name:
        coco,cs=compile_module(ROOT/'objs/mnln.asm',Path(name)/'mnln')
        stop=0x7e00
        d.write(stop,b'\x39');d.breakpoint(stop)
        for base in (0x8000,0x9000):
            d.write(0,bytes(0x6000));d.write(base,coco)
            entry=base+cs['message_box'];d.breakpoint(entry)
            d.write(0x7ef0,b'\x7e\x00STACK')
            d.regs(pc=base+cs['CmdShowAgiInfo'],s=0x7ef0,dp=0,cc=0x50)
            d.call('c');r=d.regs()
            assert r['pc']==entry,('CoCo message_box entry',r)
            version=d.read(r['u'],64).split(b'\0',1)[0]
            assert version==b'Adventure Game Interpreter\n      Version 2.072',version
            ret=int.from_bytes(d.read(r['s'],2),'big')
            d.regs(pc=ret,s=r['s']+2)
            d.call('c');r=d.regs()
            assert r['pc']==stop and r['s']==0x7ef2,r
            assert d.read(0x7ef2,5)==b'STACK'
            d.breakpoint(entry,False)
        d.breakpoint(stop,False)
    for label,prefix,depth in [('ordinary',b'',0),('held print',bytes([12,15]),0),
                              ('timed print',bytes([3,21,2]),0),
                              ('deep caller',bytes([12,15,3,21,2]),16)]:
        print('Checking interpreter information:',label,flush=True)
        data=bytearray();logs=[b'\xff'*3]
        for number in range(1,depth+2):
            logs.append(len(data).to_bytes(3,'big'))
            command=bytes([22,number+1]) if number<=depth else prefix+bytes([141])
            body=command+(bytes([3,240,73,134,1,0]) if number==1 else b'\0')
            logic=len(body).to_bytes(2,'little')+body
            data+=b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
        files={'/game/logDir':b''.join(logs),'/game/vol.0':bytes(data)}
        modal={}
        def inspect(cpu,r,syms):
            modal['text']=cpu.read(syms['textcharacters'],1000)
            assert cpu.read(syms['vmflags']+15,1)==b'\0'
            assert cpu.read(syms['vmvariables']+21,1)==b'\0'
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,
            database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,
            capture=True,keyboard=b'\r',os_call_limit=30000,
            breakpoint_hooks={'GamePrintWait':inspect})
        assert not error,(label,error)
        assert state['vmvariables'][240]==73,(label,'caller did not resume')
        for line in (b'Adventure Game',b'Interpreter',b'Version 2.072'):
            assert line in modal['text'],(label,line,modal)
        assert b'Wild Bits' not in modal['text'],(label,modal)
        assert state['vmflags'][15]==(1 if 15 in prefix else 0),(label,'print flag changed')
        assert state['vmvariables'][21]==(2 if 21 in prefix else 0),(label,'print timer changed')
    print('PASS: interpreter information, blocking dismissal, preserved flags/timer and deep caller resume')


def check_simple_save_staging(d):
    """Test loaded command/name staging; actual file I/O is checked in MAME."""
    from check_wbplay import fixture
    cases=[('default cancellation',bytes([125]),b'\5',[]),
           ('first string',bytes([114,0,2,170,0,125]),b'',[b'/alpha']),
           ('last string',bytes([114,11,2,170,11,126]),b'',[b'/alpha']),
           ('repeat then clear',bytes([114,11,2,170,11,125,114,11,3,170,11,126,
                                      114,11,4,170,11,125]),b'\5',[b'/alpha',b'/beta']),
           ('31 byte bound',bytes([114,11,5,170,11,125]),b'',[b'X'*31])]
    for label,commands,keys,wanted in cases:
        body=bytes([143,1])+commands+bytes([3,240,73,134,1,0])
        files=fixture(body,message=[b'AUTO',b'/alpha',b'/beta',b'',b'X'*39]);seen=[]
        def stage(cpu,regs,syms):
            seen.append(cpu.read(syms['parserline'],40).split(b'\0')[0])
            # Only the file transaction is substituted. Real provider loading,
            # bounds validation, private copying and name staging ran above.
            cpu.regs(pc=0xa000+syms['GameStateSuccess'])
            return True
        error,out,state=exercise(d,files,module='wbgame',base=0xa000,database=0,
            window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
            keyboard=keys,os_call_limit=30000,breakpoint_hooks={'GameStateInvoke':stage})
        assert error==0 and seen==wanted and state['vmvariables'][240]==73,(label,error,out,seen)
        assert state['gamefont']==(ROOT/'objs/sierrafont').read_bytes()
        print('PASS: automatic filename staging:',label,flush=True)
    directory=b'/'+b'a'*126;volume=bytearray();entries=[b'\xff'*3]
    final=fixture(bytes([143,1,114,11,2,170,11,125,3,240,73,134,1,0]),
                  message=[b'AUTO',b'/alpha'])['/game/vol.0']
    for number in range(1,18):
        entries.append(len(volume).to_bytes(3,'big'))
        if number==17:volume+=final
        else:
            body=bytes([22,number+1,0]);logic=len(body).to_bytes(2,'little')+body
            volume+=b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
    files={directory.decode()+'/logDir':b''.join(entries),directory.decode()+'/vol.0':bytes(volume)}
    seen=[]
    error,out,state=exercise(d,files,arguments=directory+b' 1\r',module='wbgame',base=0xa000,
        database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
        os_call_limit=30000,breakpoint_hooks={'GameStateInvoke':stage})
    assert error==0 and seen==[b'/alpha'] and state['vmvariables'][240]==73,(error,out,seen)
    assert state['gamefont']==(ROOT/'objs/sierrafont').read_bytes()
    print('PASS: automatic name/provider staging at 16 nested calls and 127-byte directory, private font intact and ownership recovered')


def check_simple_save_restart(d):
    from check_wbplay import fixture
    body=bytes([255,7,6,255,3,0,134,1,0,114,11,1,170,11,12,16,128,134,1,0])
    seen=[]
    def observe(cpu,regs,syms):seen.append(cpu.read(syms['statesimplename'],32).split(b'\0')[0])
    error,out,state=exercise(d,fixture(body,message=b'/alpha'),module='wbgame',base=0xa000,
        database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
        os_call_limit=30000,breakpoint_hooks={'GameQuitCommand':observe})
    assert error==0 and seen==[b'/alpha'] and state['vmflags'][6]==1,(error,out,seen)
    assert not any(state['vmstrings']) and state['gamefont']==(ROOT/'objs/sierrafont').read_bytes()
    print('PASS: automatic name survives actual restart while its old source string table is cleared, with balanced ownership and private-font guards')


def check_save_replacement(d):
    """Compare actual create/delete wrappers, including clobbers and errors."""
    from check_logic_executor import compile_module
    with tempfile.TemporaryDirectory(prefix='sierra-save-replace-') as name:
        coco,cs=compile_module(ROOT/'objs/mnln.asm',Path(name)/'mnln')
        native=(ROOT/'objs/sierrastate').read_bytes();ns=symbols(ROOT/'objs/sierrastate.map')
        count=0
        for owner,code,syms in [('CoCo',coco,cs),('native',native,ns)]:
            entry='CreateFile' if owner=='CoCo' else 'StateCreateFile'
            regions=[('CreateFile','OpenFile'),('DeleteFile','DeleteFileRet')] if owner=='CoCo' else [('StateCreateFile','StatePrepare')]
            sites={}
            for first,last in regions:
                for service in ('I$Delete','I$Create'):
                    needle=bytes([0x10,0x3f,syms[service]])
                    begin,end=syms[first],syms[last]
                    for offset in range(begin,end):
                        if code[offset:offset+3]==needle:sites[offset]=service
            assert sorted(sites.values())==['I$Create','I$Delete'],(owner,sites)
            for base in (0x8000,0x9000):
                d.write(base,code);d.breakpoint(0x7e00)
                for address in sites:d.breakpoint(base+address)
                if owner=='CoCo':d.breakpoint(base+cs['OsErrorHandler'])
                try:
                    for delete_error in (None,syms['E$PNNF'],syms['E$FNA'],syms['E$MemFul']):
                        for create_error in (None,syms['E$CEF'],syms['E$Write'],syms['E$Full']):
                            d.write(0x7000,b'/save\0');d.write(0x7ed0,b'G'*16);d.write(0x7ef0,b'\x7e\0STACK')
                            d.regs(pc=base+syms[entry],s=0x7ef0,x=0x7000,y=0x7777,u=0x6666,a=2,b=3,dp=0,cc=0x50)
                            seen=[]
                            for _ in range(6):
                                d.call('c');regs=d.regs()
                                if regs['pc']==0x7e00:break
                                if owner=='CoCo' and regs['pc']==base+cs['OsErrorHandler']:
                                    d.regs(pc=int.from_bytes(d.read(regs['s'],2),'big'),s=regs['s']+2)
                                    continue
                                service=sites[regs['pc']-base];seen.append(service)
                                assert regs['x']==0x7000,(owner,service,regs)
                                if service=='I$Create':assert (regs['a'],regs['b'])==(2,3),regs
                                error=delete_error if service=='I$Delete' else create_error
                                d.regs(pc=regs['pc']+3,cc=(regs['cc']|1 if error is not None else regs['cc']&~1),
                                       a=55 if service=='I$Delete' else 5,b=error or 0,x=0x4444 if service=='I$Delete' else 0x7005)
                            else:raise AssertionError((owner,'wrapper did not return'))
                            assert seen==['I$Delete','I$Create'] and regs['s']==0x7ef2
                            assert bool(regs['cc']&1)==(create_error is not None)
                            assert regs['b']==(create_error or 0) and regs['a']==5
                            assert d.read(0x7ed0,16)==b'G'*16 and d.read(0x7ef2,5)==b'STACK'
                            assert d.read(base,len(code))==code
                            count+=1
                finally:
                    for address in sites:d.breakpoint(base+address,False)
                    if owner=='CoCo':d.breakpoint(base+cs['OsErrorHandler'],False)
                    d.breakpoint(0x7e00,False)
    print(f'PASS: {count} actual CoCo/native save replacement cases; delete-before-create, missing/protected targets, register clobbers, final create/full-disk errors, exact status/stack/code guards')


def check_simple_save_reference(d):
    """Compare the actual string-index command and bounded automatic name."""
    from check_logic_executor import compile_module
    with tempfile.TemporaryDirectory(prefix='sierra-simple-reference-') as name:
        coco,cs=compile_module(ROOT/'objs/mnln.asm',Path(name)/'mnln')
        ui,ns=compile_module(ROOT/'objs/sierraui.asm',Path(name)/'sierraui')
        d.breakpoint(0x7e00);calls=0
        for base in (0x8000,0x9000):
            for owner,code,syms in [('CoCo',coco,cs),('native',ui,ns)]:
                assert base+len(code)<=0xfe00,(owner,base,len(code))
                print('Checking simple save reference:',owner,hex(base),flush=True)
                d.write(base,code)
                for index in range(12):
                    for length in (0,1,15,30,31,32,39):
                        d.write(0,bytes(ns['size']))
                        text=(bytes([65+index])*length+b'\0').ljust(40,b'.')
                        table=0x251 if owner=='CoCo' else ns['vmstrings']
                        target=base+cs['state_name_auto'] if owner=='CoCo' else ns['statesimplename']
                        d.write(table+40*index,text);d.write(target,b'~'*32)
                        d.write(0x7000,bytes([index]));d.write(ns['vmarguments'],bytes([index]))
                        d.write(0x7ef0,b'\x7e\0STACK')
                        private=d.read(0,ns['size']);image=d.read(base,len(code))
                        entry='cmd_set_simple' if owner=='CoCo' else 'AuxSimpleSaveName'
                        d.regs(pc=base+syms[entry],s=0x7ef0,y=0x7000,u=0,dp=0,cc=0x51)
                        d.call('c');regs=d.regs()
                        count=min(length,31);wanted=(text[:count]+b'\0').ljust(32,b'~')
                        assert regs['pc']==0x7e00 and regs['s']==0x7ef2
                        assert d.read(target,32)==wanted,(owner,index,length,d.read(target,32))
                        assert d.read(table+40*index,40)==text
                        assert d.read(0x7ef2,5)==b'STACK'
                        if owner=='native':
                            expected=bytearray(private);expected[target:target+32]=wanted
                            assert d.read(0,ns['size'])==expected and not(regs['cc']&1)
                            assert d.read(base,len(code))==image
                        else:
                            expected=bytearray(image);at=target-base;expected[at:at+32]=wanted
                            assert d.read(base,len(code))==expected
                            assert regs['y']==0x7001
                        calls+=1
                if owner=='native':
                    for index in (12,127,128,255):
                        d.write(0,bytes(ns['size']));d.write(ns['vmarguments'],bytes([index]))
                        d.write(ns['statesimplename'],b'keep\0'+bytes(27))
                        before=d.read(0,ns['size']);d.write(0x7ef0,b'\x7e\0STACK')
                        d.regs(pc=base+ns['AuxSimpleSaveName'],s=0x7ef0,u=0,dp=0,cc=0x50)
                        d.call('c');regs=d.regs()
                        assert regs['pc']==0x7e00 and regs['b']==ns['E$BMode'] and regs['cc']&1
                        assert d.read(0,ns['size'])==before and d.read(0x7ef2,5)==b'STACK'
                        calls+=1
        d.breakpoint(0x7e00,False)
    print(f'PASS: {calls} actual CoCo/native simple-name calls; all 12 string indices, empty/30/31/32/39-byte sources, truncation/NUL, operand/stack/source/code/private guards and invalid-index preservation')


def check_ui_command_cache(d):
    """Interleave diagnostic/visibility/restart groups through one cache."""
    body=bytes([255,7,6,255,3,0,134,1,0,12,15,135,177,0,12,15,135,
                12,16,128,3,254,99,134,1,0])
    logic=len(body).to_bytes(2,'little')+body
    files={'/game/logDir':b'\xff'*3+bytes(3),
           '/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic}
    calls=[]
    def entry(cpu,regs,syms):
        calls.append((cpu.read(syms['vmopcode'],1)[0],
                      int.from_bytes(cpu.read(syms['uicommandentry'],2),'big')))
        return True
    error,out,state=exercise(d,files,module='wbgame',base=0xa000,database=0,
        window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
        os_call_limit=30000,breakpoint_hooks={'GameUiCommand':entry})
    assert error==0 and state['vmflags'][6]==1 and state['vmvariables'][254]==0,(error,out)
    assert [opcode for opcode,_ in calls]==[135,177,135,128],calls
    assert calls[0][1]==0 and len({pointer for _,pointer in calls[1:]})==1 and calls[1][1],calls
    assert state['gamefont']==(ROOT/'objs/sierrafont').read_bytes()
    print('PASS: interleaved diagnostic/visibility/restart use one stable private UI cache; restart apply survives unwind and preserves the private font')


def check_menu_request_order_reference(d):
    """Execute the actual CoCo script and following event loop as the oracle."""
    from check_logic_executor import compile_module
    with tempfile.TemporaryDirectory(prefix='sierra-menu-order-') as name:
        code,syms=compile_module(ROOT/'objs/mnln.asm',Path(name)/'mnln')
        base=0x8000;d.write(0,bytes(0x6000));d.write(base,code)
        d.write(0x2e,base.to_bytes(2,'big'))
        d.run(base+syms['PatchCmdTable']);d.run(base+syms['FixupEvalTbl'])
        d.breakpoint(0x1d00,False)
        script=bytes([12,14,161,177,0,3,240,73,0])
        d.write(0x62,b'\x30\0');d.write(0x3000,bytes(10));d.write(0x3008,b'\x20\0')
        d.write(0x2000,script)
        page=base+syms['SetLogicPage'];d.breakpoint(page);d.breakpoint(0x7e00)
        d.write(0x7ef0,b'\x7e\0STACK')
        d.regs(pc=base+syms['ExecLogicScript'],s=0x7ef0,dp=0,cc=0x50)
        for _ in range(5):
            d.call('c');regs=d.regs()
            if regs['pc']==0x7e00:break
            assert regs['pc']==page,regs
            d.regs(pc=int.from_bytes(d.read(regs['s'],2),'big'),s=regs['s']+2)
        else:raise AssertionError('CoCo script failed to return')
        assert d.read(0x431+240,1)==b'I' and d.read(base+syms['MenuExtraFlag'],1)==b'\0'
        assert d.read(0x5ae,1)==b'\1'
        d.breakpoint(page,False);d.write(0x92,b'\1\3\1\3')
        d.write(0x7ef0,b'\x7e\0STACK')
        d.regs(pc=base+syms['EventLoop'],s=0x7ef0,dp=0,cc=0x50)
        d.call('c');regs=d.regs()
        assert regs['pc']==0x7e00 and d.read(0x5ae,1)==b'\0'
        d.breakpoint(0x7e00,False)
    print('PASS: actual CoCo executor completes following hide/assignment before the next event loop consumes its menu request')


def check_menu_visibility_reference(d):
    """Compare actual CoCo byte setters/input gates with private native controls."""
    from check_logic_executor import compile_module
    with tempfile.TemporaryDirectory(prefix='sierra-menu-reference-') as name:
        coco,cs=compile_module(ROOT/'objs/mnln.asm',Path(name)/'mnln')
        native,ns=compile_module(ROOT/'objs/sierraui.asm',Path(name)/'sierraui')
        d.breakpoint(0x7e02);d.write(0x7e00,b'\x39')
        calls=0
        for owner,code,syms,bases in [('CoCo',coco,cs,(0x8000,0x9000)),
                                     ('native',native,ns,(0x8000,0xa000))]:
            for base in bases:
                d.write(base,code)
                for value in range(256):
                    d.write(0,bytes(ns['size']));d.write(0x7000,bytes([value]))
                    d.write(ns['vmarguments'],bytes([value]))
                    before=d.read(0,ns['size']) if owner=='native' and value in (0,1,2,127,128,255) else None
                    d.write(0x7ef0,b'\x7e\x02STACK');d.write(0x7c00,b'LOWGUARD')
                    entry='cmd_show_menu' if owner=='CoCo' else 'AuxMenuVisibility'
                    d.regs(pc=base+syms[entry],s=0x7ef0,y=0x7000,u=0,dp=0,cc=0x50)
                    d.call('c');regs=d.regs()
                    assert regs['pc']==0x7e02 and regs['s']==0x7ef2
                    if owner=='CoCo':
                        assert regs['y']==0x7001 and d.read(base+syms['MenuExtraFlag'],1)==bytes([value])
                    else:
                        assert regs['u']==0 and not(regs['cc']&1) and regs['b']==0
                        assert d.read(syms['menuvisibility'],2)==bytes([value,1])
                        if before is not None:
                            after=bytearray(d.read(0,ns['size']))
                            p=syms['menuvisibility'];after[p:p+2]=before[p:p+2]
                            assert after==before,'visibility setter altered unrelated private state'
                    assert d.read(0x7c00,8)==b'LOWGUARD' and d.read(0x7ef2,5)==b'STACK'
                    calls+=1
                actual=bytearray(d.read(base,len(code)))
                if owner=='CoCo':actual[syms['MenuExtraFlag']]=code[syms['MenuExtraFlag']]
                assert actual==code,'visibility setter modified instructions'
        # Compare the actual CoCo draw-entry gate for every literal byte.
        for base in (0x8000,0x9000):
            d.write(base,coco)
            yes=base+cs['PushRowCol'];no=base+cs['MenuInputExit']
            d.breakpoint(yes);d.breakpoint(no)
            for value in range(256):
                d.write(base+cs['MenuExtraFlag'],bytes([value]))
                d.write(base+cs['state_name_auto'],b'/alpha\0')
                d.write(0x7ef0,b'\x7e\x02STACK')
                d.regs(pc=base+cs['DrawMenuBar'],s=0x7ef0,dp=0,cc=0x50)
                d.call('c');regs=d.regs()
                assert regs['pc']==(yes if value else no),(value,regs)
                calls+=1
            d.breakpoint(yes,False);d.breakpoint(no,False)
        for base in (0x8000,0xa000):
            d.write(base,native)
            for value in range(256):
                d.write(0,bytes(ns['size']))
                d.write(ns['menuvisibility'],bytes([value,1]))
                d.write(ns['vmflags']+14,b'\x01')
                d.write(ns['menuready'],b'\x01');d.write(ns['menuitems'],b'\x01')
                d.write(ns['coldapi'],b'\x72\0');d.write(0x7200,(0x7e00-0x7200).to_bytes(2,'big'))
                d.write(0x7ef0,b'\x7e\x02STACK');d.breakpoint(0x7e00)
                d.regs(pc=base+ns['AuxMenuInput'],s=0x7ef0,y=0x7200,u=0,dp=0,cc=0x50)
                d.call('c');regs=d.regs()
                assert regs['pc']==(0x7e00 if value else 0x7e02),(value,regs)
                if not value:assert regs['s']==0x7ef2 and not(regs['cc']&1)
                d.breakpoint(0x7e00,False)
                calls+=1
            assert d.read(base,len(native))==native
        # CoCo menu requests are independently gated by packed AGI flag 14.
        for base in (0x8000,0x9000):
            d.write(base,coco)
            for packed in range(256):
                d.write(0x1af,bytes([packed]));d.write(0x5ae,b'\0')
                d.write(0x7ef0,b'\x7e\x02STACK')
                d.regs(pc=base+cs['cmd_menu_input'],s=0x7ef0,dp=0,cc=0x50)
                d.call('c');regs=d.regs()
                assert regs['pc']==0x7e02 and regs['s']==0x7ef2
                assert d.read(0x5ae,1)==bytes([bool(packed&2)])
                calls+=1
        for base in (0x8000,0xa000):
            d.write(base,native)
            for enabled,known,visible in [(0,0,0),(0,1,0),(0,1,255),(1,0,0),(1,1,255)]:
                d.write(0,bytes(ns['size']))
                d.write(ns['vmflags']+14,bytes([enabled]))
                d.write(ns['menuvisibility'],bytes([visible,known]))
                d.write(ns['menuready'],b'\x01');d.write(ns['menuitems'],b'\x01')
                d.write(ns['menupending'],b'\0')
                d.write(0x7ef0,b'\x7e\x02STACK')
                d.regs(pc=base+ns['AuxMenuRequest'],s=0x7ef0,u=0,dp=0,cc=0x51)
                d.call('c');requestregs=d.regs()
                assert requestregs['pc']==0x7e02 and not(requestregs['cc']&1)
                assert d.read(ns['menupending'],1)==bytes([enabled])
                calls+=1
                d.write(ns['coldapi'],b'\x72\0');d.write(0x7200,(0x7e00-0x7200).to_bytes(2,'big'))
                d.write(0x7ef0,b'\x7e\x02STACK');d.breakpoint(0x7e00)
                d.regs(pc=base+ns['AuxMenuInput'],s=0x7ef0,y=0x7200,u=0,dp=0,cc=0x50)
                d.call('c');regs=d.regs();wanted=bool(not known or visible)
                assert regs['pc']==(0x7e00 if wanted else 0x7e02),(enabled,known,visible,regs)
                d.breakpoint(0x7e00,False);calls+=1
            assert d.read(base,len(native))==native
        # Actual restart preserves the module's visibility byte. Stub only
        # object-file I/O and unrelated linked-list item re-enabling.
        d.write(0xff92,b'\0');d.write(0xff93,b'\0')
        for base in (0x8000,0x9000):
            d.write(base,coco)
            hooks={base+cs[n]:n for n in ('LoadObjectData','EnableItemLoop')}
            for address in hooks:d.breakpoint(address)
            for value in (0,255):
                d.write(0,bytes(0x6000));d.write(0x531,b'\xff'*16)
                d.write(0x1b0,b'\x80');d.write(0x1af,b'\2')
                d.write(0x4d,b'\x30\0');d.write(0x53,b'\x31\0')
                d.write(base+cs['MenuExtraFlag'],bytes([value]))
                d.write(base+cs['state_name_auto'],b'/alpha\0')
                d.write(0x7ef0,b'\x7e\x02STACK')
                d.regs(pc=base+cs['cmd_restart_game'],s=0x7ef0,dp=0,cc=0x50)
                for _ in range(8):
                    d.call('c');regs=d.regs()
                    if regs['pc']==0x7e02:break
                    assert regs['pc'] in hooks,regs
                    d.regs(pc=int.from_bytes(d.read(regs['s'],2),'big'),s=regs['s']+2)
                else:raise AssertionError('reference restart did not return')
                assert regs['s']==0x7ef2 and d.read(base+cs['MenuExtraFlag'],1)==bytes([value])
                assert d.read(base+cs['state_name_auto'],7)==b'/alpha\0'
            for address in hooks:d.breakpoint(address,False)
        # Execute the real save/write-block control flow and inspect every
        # write span; MenuExtraFlag is not among the serialized fields.
        for base in (0x8000,0x9000):
            hooks={base+cs[n]:n for n in ('WriteFile','XorDecrypt','BuildLogicList','SaveGameWriteOk')}
            for address in hooks:d.breakpoint(address)
            for value in (0,255):
                d.write(base,coco);d.write(0,bytes(0x6000))
                for address,word in [(0x30,0x2000),(0x34,64),(0x38,0x2100),(0x3a,16),(0x5af,0x2200)]:
                    d.write(address,word.to_bytes(2,'big'))
                d.write(0x245,b'\1');d.write(base+cs['MenuExtraFlag'],bytes([value]))
                d.write(base+cs['state_name_auto'],b'/alpha\0')
                d.write(0x7d00,bytes(254));d.write(0x7c00,b'LOWGUARD')
                writes=[]
                d.regs(pc=base+cs['SaveGameWriteData'],s=0x7d00,a=3,dp=0,cc=0x50)
                for _ in range(24):
                    d.call('c');regs=d.regs();kind=hooks[regs['pc']]
                    if kind=='SaveGameWriteOk':break
                    update={'pc':int.from_bytes(d.read(regs['s'],2),'big'),'s':regs['s']+2}
                    if kind=='WriteFile':
                        writes.append((regs['x'],regs['y']))
                        update.update(a=regs['y']>>8,b=regs['y']&255,cc=regs['cc']&~1)
                    elif kind=='BuildLogicList':update['x']=16
                    d.regs(**update)
                else:raise AssertionError('reference save did not reach success')
                target=base+cs['MenuExtraFlag']
                assert len(writes)==11 and all(not(start<=target<start+length) for start,length in writes),writes
                auto_target=base+cs['state_name_auto']
                assert all(not(start<=auto_target<start+length) for start,length in writes),writes
                assert d.read(auto_target,7)==b'/alpha\0'
                assert d.read(target,1)==bytes([value]) and d.read(0x7c00,8)==b'LOWGUARD'
                current=bytearray(d.read(base,len(coco)))
                for label in ('MenuExtraFlag','SaveFileHandle'):current[cs[label]]=coco[cs[label]]
                at=cs['state_name_auto'];current[at:at+31]=coco[at:at+31]
                assert current==coco,'reference save changed instructions'
            for address in hooks:d.breakpoint(address,False)
        print('PASS: actual CoCo restart retains visibility/automatic name and actual save write spans exclude both module-private settings')
        d.breakpoint(0x7e02,False)
        print(f'PASS: {calls} actual CoCo/native menu visibility/input calls; all literal bytes, opaque zero/nonzero behavior, default visibility, independent flag14, operand/stack/private/code guards')


def check_menu_item_enable_reference(d):
    """Compare actual CoCo and native item-enable command state changes."""
    from check_logic_executor import compile_module
    with tempfile.TemporaryDirectory(prefix='sierra-menu-item-enable-') as name:
        coco,cs=compile_module(ROOT/'objs/mnln.asm',Path(name)/'mnln')
        game=ROOT/'objs'
        native=(game/'wbgame').read_bytes();ns=symbols(game/'wbgame.map')
        calls=0
        d.breakpoint(0x7e00)
        menu1,menu2=0x7000,0x7020
        item1,item2,item3=0x7100,0x7120,0x7140
        for owner,code,syms,bases in [('CoCo',coco,cs,(0x8000,0x9000)),
                                     ('Wild Bits',native,ns,(0x9000,0xa000))]:
            for base in bases:
                for sequence in (((160,10),(159,20)),((159,10),(160,20)),
                                 ((160,99),),((160,10),(159,10))):
                    d.write(base,code)
                    enabled=[1,1,1]
                    if owner=='CoCo':
                        menus=bytearray(0x40)
                        menus[0:2]=menu2.to_bytes(2,'big')
                        menus[0x20:0x22]=menu1.to_bytes(2,'big')
                        menus[0x0a]=menus[0x2a]=1
                        menus[0x0b:0x0d]=item1.to_bytes(2,'big')
                        menus[0x2b:0x2d]=item3.to_bytes(2,'big')
                        d.write(menu1-1,b'G');d.write(menu1,menus);d.write(menu2+0x20,b'H')
                        records=bytearray(0x60)
                        for address,nxt,prev,action in ((item1,item2,item2,10),
                            (item2,item1,item1,20),(item3,item3,item3,10)):
                            off=address-item1
                            records[off:off+2]=nxt.to_bytes(2,'big')
                            records[off+2:off+4]=prev.to_bytes(2,'big')
                            records[off+10]=1;records[off+11]=action
                        d.write(item1-1,b'G');d.write(item1,records);d.write(item3+0x20,b'H')
                        d.write(base+cs['MenuHead'],menu1.to_bytes(2,'big'))
                    else:
                        d.write(0,bytes(ns['size']))
                        d.write(ns['resourcebase'],b'\0\0')
                        d.write(ns['menuitems'],b'\x03')
                        entries=bytearray(18)
                        for i,(action,title) in enumerate(((10,0),(20,0),(10,1))):
                            entries[i*6+2]=action;entries[i*6+3]=title
                            entries[i*6+4]=1
                        d.write(ns['menuentries'],entries)
                    for opcode,action in sequence:
                        if owner=='CoCo':
                            operand=0x7400
                            d.write(operand-1,b'G'+bytes([action])+b'ARGS')
                            d.write(0x7ef0,b'\x7e\x00STACK')
                            entry='cmd_enable_item' if opcode==159 else 'cmd_disable_item'
                            d.regs(pc=base+syms[entry],s=0x7ef0,y=operand,dp=0,cc=0x50)
                        else:
                            d.write(ns['vmopcode'],bytes([opcode]))
                            d.write(ns['vmarguments'],bytes([action]))
                            d.write(0x7ef0,b'\x7e\x00STACK')
                            d.regs(pc=base+ns['MenuCommand'],s=0x7ef0,u=0,
                                   y=0x7400,dp=0,cc=0x50)
                        d.call('c');regs=d.regs()
                        assert regs['pc']==0x7e00 and regs['s']==0x7ef2,(owner,opcode,action,regs)
                        assert d.read(0x7ef2,5)==b'STACK'
                        if action in (10,20):
                            value=1 if opcode==159 else 0
                            for i,selected in enumerate((10,20,10)):
                                if selected==action:enabled[i]=value
                        if owner=='CoCo':
                            assert regs['y']==0x7401 and d.read(0x7401,4)==b'ARGS'
                            for i,address in enumerate((item1,item2,item3)):
                                assert d.read(address+10,1)==bytes([enabled[i]]),(owner,base,sequence,action,address,enabled,d.read(address+10,1))
                            actual=[d.read(address+10,1)[0] for address in (item1,item2,item3)]
                        else:
                            assert not(regs['cc']&1) and regs['b']==0
                            actual=[d.read(ns['menuentries']+i*6+4,1)[0] for i in range(3)]
                        assert actual==enabled,(owner,base,sequence,action,actual,enabled)
                        calls+=1
                    if owner=='CoCo':
                        image=bytearray(d.read(base,len(code)))
                        image[syms['MenuHead']:syms['MenuHead']+2]=code[syms['MenuHead']:syms['MenuHead']+2]
                        assert image==code,'CoCo menu-item command modified code'
                    else:assert d.read(base,len(code))==code
        d.breakpoint(0x7e00,False)
        print(f'PASS: {calls} actual CoCo/Wild Bits enable.item/disable.item calls at two code bases; duplicate actions, absent action, ordered toggles, operand/stack/record guards and immutable code')


def check_menu_build_reference(d):
    """Normalize actual CoCo menu lists against the loaded Wild Bits tables."""
    from check_logic_executor import compile_module
    from check_wbplay import fixture as menu_fixture
    with tempfile.TemporaryDirectory(prefix='sierra-menu-build-') as name:
        coco,cs=compile_module(ROOT/'objs/mnln.asm',Path(name)/'mnln')
        messages=(b'File',b'Look',b'Open',b'Action',b'Talk')
        message_pointers={index+1:0x6000+index*0x10
                          for index in range(len(messages))}
        expected=[('File', [('Look',21,1),('Open',22,1)]),
                  ('Action',[('Talk',23,1)])]
        d.breakpoint(0x7e00)
        coco_results=[]
        for base in (0x8000,0x9000):
            d.write(base,coco)
            for index,message in enumerate(messages):
                d.write(message_pointers[index+1],message+b'\0')
            d.write(0x0062,b'\x65\x00');d.write(0x6504,b'\x12\x34')
            d.write(0x0055,b'\x70\x00')
            next_block=[0x7000]
            def get_message(cpu,registers,syms):
                pointer=message_pointers[registers['b']]
                ret=int.from_bytes(cpu.read(registers['s'],2),'big')
                cpu.regs(pc=ret,s=registers['s']+2,u=pointer)
            def allocate(cpu,registers,syms):
                size=(registers['a']<<8)|registers['b']
                pointer=next_block[0];next_block[0]+=size
                cpu.write(pointer,bytes(size))
                cpu.write(0x0055,next_block[0].to_bytes(2,'big'))
                ret=int.from_bytes(cpu.read(registers['s'],2),'big')
                cpu.regs(pc=ret,s=registers['s']+2,u=pointer)
            for label in ('GetMsgPtr','AllocDataBlock'):
                d.breakpoint(base+cs[label])
            def invoke(entry,operands=b''):
                operand=0x7400
                d.write(operand,operands)
                d.write(0x7ef0,b'\x7e\0STACK')
                d.regs(pc=base+cs[entry],s=0x7ef0,y=operand,dp=0,cc=0x50)
                for _ in range(12):
                    d.call('c');regs=d.regs()
                    if regs['pc']==0x7e00:break
                    if regs['pc']==base+cs['GetMsgPtr']:
                        get_message(d,regs,cs)
                    elif regs['pc']==base+cs['AllocDataBlock']:
                        allocate(d,regs,cs)
                    else:raise AssertionError(('unexpected CoCo menu-build target',entry,regs))
                else:raise AssertionError(('CoCo menu build did not return',entry))
                assert regs['s']==0x7ef2 and d.read(0x7ef2,5)==b'STACK',(entry,regs)
                assert regs['y']==operand+len(operands),(entry,regs['y'],len(operands))
            invoke('cmd_set_menu',b'\x01')
            invoke('cmd_set_menu_item',b'\x02\x15')
            invoke('cmd_set_menu_item',b'\x03\x16')
            invoke('cmd_set_menu',b'\x04')
            invoke('cmd_set_menu_item',b'\x05\x17')
            invoke('cmd_submit_menu')
            assert d.read(base+cs['MenuSubmitted'],1)==b'\x01'
            assert int.from_bytes(d.read(0x0053,2),'big')==next_block[0]
            menus=[];menu=int.from_bytes(d.read(base+cs['MenuHead'],2),'big')
            for _ in range(2):
                title_node=d.read(menu,16)
                title_ptr=int.from_bytes(title_node[4:6],'big')
                title=bytes(d.read(title_ptr,32)).split(b'\0',1)[0].decode()
                count=title_node[15]
                item=int.from_bytes(title_node[11:13],'big')
                items=[]
                for _ in range(count):
                    item_node=d.read(item,12)
                    label_ptr=int.from_bytes(item_node[4:6],'big')
                    label=bytes(d.read(label_ptr,32)).split(b'\0',1)[0].decode()
                    items.append((label,item_node[11],item_node[10]))
                    item=int.from_bytes(item_node[:2],'big')
                menus.append((title,items))
                menu=int.from_bytes(title_node[:2],'big')
            assert menus==expected,(base,menus,expected)
            assert int.from_bytes(d.read(base+cs['MenuCurrent'],2),'big')==int.from_bytes(d.read(base+cs['MenuHead'],2),'big')
            assert int.from_bytes(d.read(base+cs['MenuItemCurrent'],2),'big')==int.from_bytes(d.read(int.from_bytes(d.read(base+cs['MenuHead'],2),'big')+11,2),'big')
            coco_results.append(menus)
            for label in ('GetMsgPtr','AllocDataBlock'):d.breakpoint(base+cs[label],False)
        assert coco_results[0]==coco_results[1]
        # Run CoCo's actual menu event loop with only drawing, event wait and
        # event publication substituted. A right-arrow event followed by
        # Enter must select the tail item in the next nonempty title group.
        menu1,menu2=0x7000,0x7010
        item1,item2,item3=0x7020,0x7030,0x7040
        def menu_record(address,next_address,previous,title,item_head,item_tail,item_count):
            record=bytearray(16)
            record[:2]=next_address.to_bytes(2,'big')
            record[2:4]=previous.to_bytes(2,'big')
            record[4:6]=message_pointers[title].to_bytes(2,'big')
            record[10]=1
            record[11:13]=item_head.to_bytes(2,'big')
            record[13:15]=item_tail.to_bytes(2,'big')
            record[15]=item_count
            d.write(address,record)
        def item_record(address,next_address,previous,label,action):
            record=bytearray(12)
            record[:2]=next_address.to_bytes(2,'big')
            record[2:4]=previous.to_bytes(2,'big')
            record[4:6]=message_pointers[label].to_bytes(2,'big')
            record[10]=1;record[11]=action
            d.write(address,record)
        menu_record(menu1,menu2,menu2,1,item1,item2,2)
        menu_record(menu2,menu1,menu1,4,item3,item3,1)
        item_record(item1,item2,item2,2,21)
        item_record(item2,item1,item1,3,22)
        item_record(item3,item3,item3,5,23)
        draw_stubs=('PushRowCol','PushTextColor','ClearTextLine',
                    'DrawMenuItemNormal','DrawMenuItemHighlight','DrawMenuItem','WaitForEvent',
                    'EventPush','EraseMenuItem','PopTextColor','PopRowCol',
                    'StatusLineWrite')
        for base,navigation_events,initial_item,expected_menu,expected_item,expected_action in (
                (0x8000,(b'\x02\x01',),item1,menu1,item2,22),
                (0x9000,(b'\x02\x03',),item1,menu2,item3,23),
                (0x8000,(b'\x02\x02',),item2,menu1,item1,21),
                (0x8000,(b'\x01\x1b',),item1,menu1,item1,None)):
            d.write(base,coco)
            d.write(base+cs['MenuHead'],menu1.to_bytes(2,'big'))
            d.write(base+cs['MenuCurrent'],menu1.to_bytes(2,'big'))
            d.write(base+cs['MenuItemCurrent'],initial_item.to_bytes(2,'big'))
            d.write(base+cs['MenuExtraFlag'],b'\x01')
            d.write(0x0246,b'\0')
            event_queue=[*navigation_events]
            if expected_action is not None:event_queue.append(b'\x01\x0d')
            event_index=[0];published=[]
            def rts(cpu,registers,ss):
                ret=int.from_bytes(cpu.read(registers['s'],2),'big')
                cpu.regs(pc=ret,s=registers['s']+2)
            def wait_event(cpu,registers,ss):
                assert event_index[0]<len(event_queue),event_index
                ptr=0x7500+2*event_index[0]
                cpu.write(ptr,event_queue[event_index[0]])
                event_index[0]+=1
                ret=int.from_bytes(cpu.read(registers['s'],2),'big')
                cpu.regs(pc=ret,s=registers['s']+2,x=ptr)
            def push_event(cpu,registers,ss):
                published.append((registers['a'],registers['b']))
                rts(cpu,registers,ss)
            callbacks={base+cs[label]:(wait_event if label=='WaitForEvent'
                         else push_event if label=='EventPush' else rts)
                       for label in draw_stubs}
            d.write(0x7ef0,b'\x7e\0STACK')
            d.regs(pc=base+cs['DrawMenuBar'],s=0x7ef0,dp=0,cc=0x50)
            for address in callbacks:d.breakpoint(address)
            try:
                for _ in range(100):
                    d.call('c');regs=d.regs()
                    if regs['pc']==0x7e00:break
                    callback=callbacks.get(regs['pc'])
                    assert callback is not None,('unexpected CoCo menu event target',regs)
                    callback(d,regs,cs)
                else:raise AssertionError('CoCo menu event loop did not exit')
                expected_events=[] if expected_action is None else [(expected_action,3)]
                assert event_index==[len(event_queue)] and published==expected_events,(base,event_index,published)
                assert int.from_bytes(d.read(base+cs['MenuCurrent'],2),'big')==expected_menu
                assert int.from_bytes(d.read(base+cs['MenuItemCurrent'],2),'big')==expected_item
                assert regs['s']==0x7ef2 and d.read(0x7ef2,5)==b'STACK'
            finally:
                for address in callbacks:d.breakpoint(address,False)
        # Run the real VM through the same five commands and inspect its
        # process-owned menu tables at the actual input boundary.
        request=(bytes([12,14,156,1,157,2,21,157,3,22,156,4,
                        157,5,23,158,161]))
        script=queued_menu_script(request,bytes([3,240,73,134,1,0]))
        files=menu_fixture(script,message=list(messages))
        native_snapshots=[]
        def capture_native_menu(cpu,registers,syms):
            titles=cpu.read(syms['menutitles'],8*4)
            items=cpu.read(syms['menuentries'],32*6)
            text=cpu.read(syms['menutext'],768)
            count=cpu.read(syms['menucount'],1)[0]
            item_count=cpu.read(syms['menuitems'],1)[0]
            normalized=[]
            for title_index in range(count):
                off=title_index*4
                title_offset=int.from_bytes(titles[off:off+2],'big')
                start=titles[off+2];length=titles[off+3]
                title=text[title_offset:].split(b'\0',1)[0].decode()
                group=[]
                for item_index in range(start,start+length):
                    item_offset=item_index*6
                    label_offset=int.from_bytes(items[item_offset:item_offset+2],'big')
                    label=text[label_offset:].split(b'\0',1)[0].decode()
                    group.append((label,items[item_offset+2],items[item_offset+4]))
                normalized.append((title,group))
            native_snapshots.append((normalized,count,item_count,
                cpu.read(syms['menuready'],1)[0],cpu.read(syms['menutextused'],2)))
            return True
        native_cases=[]
        ui_symbols=symbols(ROOT/'objs/sierraui.map')
        ui_right_found=(0x6000+ui_symbols['GameMenuRightFound'],
                        0x8000+ui_symbols['GameMenuRightFound'])
        ui_right_found=(0x6000+ui_symbols['GameMenuRightFound'],
                        0x8000+ui_symbols['GameMenuRightFound'])
        for keys,selected_action,hook_keys in (
                (b'\r',21,{}),(b'\x08\r',22,{}),(b'\t\r',23,{}),
                (b'\x0c\r',22,{}),(b'\x0a\r',21,{}),
                (b'\t',23,{address:{1:b'\x08\r'} for address in ui_right_found})):
            native_snapshots.clear()
            hooks={'GameMenuInput':capture_native_menu}
            error,output,state=exercise(d,files,module='wbgame',module_root=ROOT/'objs',
                base=0xa000,database=0,window=0x8000,blocks=None,multiple=True,
                firstblock=0x10,capture=True,keyboard=keys,os_call_limit=30000,
                keyboard_by_hook=hook_keys,
                breakpoint_hooks=hooks)
            assert error==0 and state['vmvariables'][240]==73,(keys,error,output)
            assert native_snapshots==[(expected,2,3,1,b'\x00\x1b')],native_snapshots
            assert state['vmcontrollers'][selected_action//8] & (1<<(selected_action%8)),(
                keys,selected_action,state['vmcontrollers'])
            native_cases.append((keys,selected_action))
        d.breakpoint(0x7e00,False)
        print('PASS: CoCo menu loop Up/Down, Right and Escape; loaded Wild Bits Enter, cancel, Up/Down/Left/Right and one-item left wrap',native_cases)


def check_menu_visibility_commands(d):
    """Exercise menu input gates through actual loaded AGI commands."""
    def record(code,messages=False):
        logic=len(code).to_bytes(2,'little')+code
        if messages:
            text=b'Title\0Item\0';key=b'Avis Durgan'
            logic+=bytes([2,17,0,6,0,12,0])+bytes(c^key[i%11] for i,c in enumerate(text))
        return b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
    build=bytes([156,1,157,2,255,158])
    cases=[('default visible',bytes([12,14])+build+bytes([161]),b'\r',True,b'\0\0'),
           ('hidden before build',bytes([12,14,177,0])+build+bytes([161]),b'',False,b'\0\1'),
           ('hidden after build',bytes([12,14])+build+bytes([177,0,161]),b'',False,b'\0\1'),
           ('noncanonical visible',bytes([12,14])+build+bytes([177,2,161]),b'\r',True,b'\2\1'),
           ('high byte visible',bytes([12,14])+build+bytes([177,255,161]),b'\r',True,b'\xff\1'),
           ('hide then show',bytes([12,14])+build+bytes([177,0,161,177,255,161]),b'\r',True,b'\xff\1'),
           ('request then hide',bytes([12,14])+build+bytes([161,177,0]),b'',False,b'\0\1'),
           ('hidden request then show',bytes([12,14])+build+bytes([177,0,161,177,255]),b'\r',True,b'\xff\1'),
           ('request then revoke permission',bytes([12,14])+build+bytes([161,13,14]),b'\r',True,b'\0\0'),
           ('duplicate request',bytes([12,14])+build+bytes([161,161]),b'\r',True,b'\0\0'),
           ('flag14 disabled',build+bytes([13,14,177,255,161]),b'',False,b'\xff\1'),
           ('flag14 disabled unsubmitted',bytes([13,14,161]),b'',False,b'\0\0'),
           ('physical Escape',bytes([12,14])+build+bytes([161]),b'\5',False,b'\0\0')]
    for label,body,keys,selected,visibility in cases:
        body=queued_menu_script(body+bytes([3,240,73]),bytes([134,1,0]));files={'/game/logDir':b'\xff'*3+bytes(3),'/game/vol.0':record(body,True)}
        seen=[];requests=[]
        def observe(cpu,regs,syms):seen.append(cpu.read(syms['menuvisibility'],2))
        def event(cpu,regs,syms):
            requests.append((cpu.read(syms['vmvariables']+240,1),cpu.read(syms['menuvisibility'],2)))
            return True
        error,out,state=exercise(d,files,module='wbgame',base=0xa000,database=0,window=0x8000,
            blocks=None,multiple=True,firstblock=0x10,capture=True,keyboard=keys,os_call_limit=30000,
            breakpoint_hooks={'GameQuitCommand':observe,'GameMenuInput':event})
        expected=bytearray(32)
        if selected:expected[31]=128
        assert error==0 and state['vmvariables'][240]==73,(label,error,out)
        assert state['vmcontrollers']==expected,(label,state['vmcontrollers'])
        assert seen==[visibility],(label,seen,visibility)
        expected_requests=[] if label.startswith('flag14 disabled') else [(b'I',visibility)]
        assert requests==expected_requests,(label,'request consumed before script completion',requests,expected_requests)
        assert state['gamefont']==(ROOT/'objs/sierrafont').read_bytes()
        print('PASS: menu visibility:',label,flush=True)
    # The room changes resource ownership, not the module-lifetime visibility.
    def when(test,code):return bytes([255,*test,255])+len(code).to_bytes(2,'little')+code
    root=when([1,0,0],bytes([3,0,1]))+bytes([23,0,0])
    first=bytes([12,14,177,0])+build+bytes([18,2,0])
    second=queued_menu_script(bytes([12,14,161,3,240,73]),bytes([134,1,0]))
    volume=bytearray();entries=[]
    for code,messages in [(root,False),(first,True),(second,False)]:
        entries.append(len(volume).to_bytes(3,'big'));volume+=record(code,messages)
    seen=[]
    error,out,state=exercise(d,{'/game/logDir':b''.join(entries),'/game/vol.0':bytes(volume)},
        arguments=b'/game 0\r',module='wbgame',base=0xa000,database=0,window=0x8000,
        blocks=None,multiple=True,firstblock=0x10,capture=True,os_call_limit=30000,
        breakpoint_hooks={'GameQuitCommand':lambda cpu,regs,syms:seen.append(cpu.read(syms['menuvisibility'],2))})
    assert error==0 and state['vmvariables'][240]==73 and seen==[b'\0\1'],(error,out,seen)
    assert not any(state['vmcontrollers']) and state['gamefont']==(ROOT/'objs/sierrafont').read_bytes()
    print('PASS: hidden menu survives room/resource transition without taking input or changing the private font')
    directory=b'/'+b'a'*126;volume=bytearray();entries=[b'\xff'*3]
    for number in range(1,18):
        body=bytes([22,number+1,0]) if number<17 else queued_menu_script(bytes([12,14,177,0,177,255])+build+bytes([161,3,240,73]),bytes([134,1,0]))
        entries.append(len(volume).to_bytes(3,'big'));volume+=record(body,number==17)
    files={directory.decode()+'/logDir':b''.join(entries),directory.decode()+'/vol.0':bytes(volume)}
    error,out,state=exercise(d,files,arguments=directory+b' 1\r',module='wbgame',base=0xa000,
        database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
        keyboard=b'\r',os_call_limit=30000)
    assert error==0 and state['vmvariables'][240]==73 and state['vmcontrollers'][31]==128,(error,out)
    assert state['gamefont']==(ROOT/'objs/sierrafont').read_bytes(),'deep menu damaged the private font'
    print('PASS: menu visibility/selection at 16 nested calls and a 127-byte directory, private font intact and owned cleanup')


def check_menu_render_overlay(d):
    """Capture the first submitted-menu frame before platform cleanup runs."""
    command=bytes([156,1,157,2,255,158,161])
    script=queued_menu_script(bytes([12,14])+command+bytes([3,240,73]),bytes([134,1,0]))
    plain=b'Title\0Item\0';key=b'Avis Durgan'
    messages=bytes([2,17,0,6,0,12,0])+bytes(v^key[i%11] for i,v in enumerate(plain))
    logic=len(script).to_bytes(2,'little')+script+messages
    volume=b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
    picture=len(volume);volume+=b'\x12\x34\0\x01\0\x01\0\xff'
    files={'/game/logDir':b'\xff'*3+bytes(3),'/game/vol.0':volume,
           '/game/picDir':b'\xff'*3+picture.to_bytes(3,'big')}
    ui_symbols=symbols(ROOT/'objs/sierraui.map')
    addresses=tuple(base+ui_symbols['GameMenuPresent'] for base in (0x6000,0x8000))
    captured=[]
    class MenuFrameReached(Exception):
        pass
    def capture(cpu,regs,syms):
        captured.append((cpu.read(syms['textcharacters'],1000),
                         cpu.read(syms['textcolors'],1000),
                         cpu.read(syms['resourcecommands'],2000)))
        raise MenuFrameReached
    try:
        exercise(d,files,module='wbgame',base=0xa000,database=0,window=0x8000,
            blocks=None,multiple=True,firstblock=0x10,capture=True,keyboard=b'\r',
            os_call_limit=30000,breakpoint_hooks={address:capture for address in addresses})
    except MenuFrameReached:
        pass
    assert len(captured)==1,len(captured)
    chars,colors,saved=captured[0]
    assert chars[1*40+2:1*40+11]==b'Game menu'
    assert chars[3*40+2:3*40+13]==b'Title: Item'
    assert colors[1*40+2:1*40+38]==bytes([0x0F])*36
    assert colors[3*40+2:3*40+38]==bytes([0xF0])*36
    for index,(character,color) in enumerate(zip(chars,colors)):
        row,column=divmod(index,40)
        if not ((row in (1,3) and 2<=column<38) or (row==24 and 1<=column<39)):
            assert character==saved[index] and color==saved[1000+index],(row,column)
    print('PASS: submitted menu draws a bounded title/item overlay and preserves every outside text/color cell')


def check_cold_menus(d):
    """Cold navigation must retain labels, selection policy and ownership."""
    def fixture(command,picture=True):
        script=queued_menu_script(bytes([12,14])+(bytes([3,0,1,24,0,25,0,26]) if picture else b'')+command+bytes([3,240,73]),bytes([134,1,0]))
        plain=b'Title\0Item\0';key=b'Avis Durgan'
        messages=bytes([2,17,0,6,0,12,0])+bytes(v^key[i%11] for i,v in enumerate(plain))
        logic=len(script).to_bytes(2,'little')+script+messages
        volume=b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
        picture=len(volume);volume+=b'\x12\x34\0\x01\0\x01\0\xff'
        return {'/game/logDir':b'\xff'*3+bytes(3),'/game/vol.0':volume,
                '/game/picDir':b'\xff'*3+picture.to_bytes(3,'big')}
    cases=[('before picture',bytes([156,1,157,2,255,158,161]),b'\r',255,0),
           ('select',bytes([156,1,157,2,255,158,161]),b'\r',255,0),
           ('cancel',bytes([156,1,157,2,255,158,161]),b'\x1b',None,0),
           ('disabled then next',bytes([156,1,157,2,1,157,2,255,160,1,158,161]),b'\r\x0c\r',255,0),
           ('disabled then enabled',bytes([156,1,157,2,1,157,2,2,160,1,159,1,158,161]),b'\r',1,0),
           ('paged',bytes([156,1])+b''.join(bytes([157,2,n]) for n in range(32))+bytes([158,161]),b'\n'*22+b'\r',0,0),
           ('unsubmitted',bytes([161]),b'\r',None,203)]
    menu_frames=[]
    ui_symbols=symbols(ROOT/'objs/sierraui.map')
    ui_present=tuple(0x6000+ui_symbols['GameMenuPresent']+delta
                     for delta in (0,0x2000))
    def capture_menu(cpu,regs,syms):
        menu_frames.append((cpu.read(syms['textcharacters'],1000),
                            cpu.read(syms['textcolors'],1000),
                            cpu.read(syms['resourcecommands'],2000)))
        return True
    for label,command,keyboard,controller,expected in cases:
        print('Checking cold menu:',label,flush=True)
        hooks={address:capture_menu for address in ui_present} if label=='select' else None
        error,output,state=exercise(d,fixture(command,picture=label!='before picture'),module='wbgame',base=0xa000,
            database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,
            capture=True,keyboard=keyboard,os_call_limit=60000,
            breakpoint_hooks=hooks)
        assert error==expected,(label,error)
        if not error:
            assert state['vmvariables'][240]==73,(label,'caller did not resume')
            wanted=bytearray(32)
            if controller is not None:wanted[controller//8]=1<<(controller%8)
            assert state['vmcontrollers']==wanted,(label,state['vmcontrollers'],wanted)
        assert state['gamefont']==(ROOT/'objs/sierrafont').read_bytes(),(label,'font overwritten')
    assert len(menu_frames)==1,len(menu_frames)
    chars,colors,saved=menu_frames[0]
    assert chars[1*40+2:1*40+11]==b'Game menu',chars[1*40+2:1*40+11]
    assert chars[3*40+2:3*40+13]==b'Title: Item',chars[3*40+2:3*40+13]
    assert colors[1*40+2:1*40+38]==bytes([0x0F])*36
    assert colors[3*40+2:3*40+38]==bytes([0xF0])*36
    for index,(character,color) in enumerate(zip(chars,colors)):
        row,column=divmod(index,40)
        if not ((row in (1,3) and 2<=column<38) or (row==24 and 1<=column<39)):
            assert character==saved[index] and color==saved[1000+index],(
                'menu changed a cell outside its popup',row,column)
    print('PASS: submitted menu is a bounded text overlay; title/item colors and all outside cells are preserved')
    # CoCo locks construction after submit.menu. The actual loaded native
    # command path must consume later title/item opcodes without adding them.
    observed=[]
    def capture_submitted_menu(cpu,regs,syms):
        observed.append((cpu.read(syms['menucount'],1)[0],
                         cpu.read(syms['menuitems'],1)[0],
                         cpu.read(syms['menuready'],1)[0]))
        return False
    late_build=bytes([156,1,157,2,1,158,156,1,157,2,2,158,161])
    files=fixture(late_build,picture=False)
    error,out,state=exercise(d,files,module='wbgame',base=0xa000,database=0,
        window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
        keyboard=b'\r',os_call_limit=60000,
        breakpoint_hooks={'GameMenuInput':capture_submitted_menu})
    assert error==0 and state['vmvariables'][240]==73,(error,state['vmvariables'][240])
    assert observed==[(1,1,1)],observed
    print('PASS: loaded native menu ignores set.menu/set.menu.item after submit.menu')
    original=(ROOT/'objs/sierraui').read_bytes();entry=int.from_bytes(original[9:11],'big')
    for offset in (0,len(original),len(original)-1):
        files=fixture(bytes([156,1,157,2,1,158,161]));helper=bytearray(original)
        helper[entry+30:entry+32]=offset.to_bytes(2,'big');files['sierraui']=bytes(helper)
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,database=0,
            window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,keyboard=b'\r',os_call_limit=30000)
        assert error==203,(offset,error)
    print('PASS: cold menu selection, cancel, disabled items, paging, invalid entry and ownership cleanup')


def check_room_controls(d):
    """Door scripts stop ego; entering the next room must release that control."""
    for label,stop,variable,retake in (
            ('stopped ego',bytes([77,0]),False,False),
            ('program control',bytes([131]),False,False),
            ('variable room',bytes([77,0]),True,False),
            ('destination owns control',bytes([77,0]),False,True)):
        print('Checking room controls:',label,flush=True)
        transition=stop+bytes([90,10,90,30,110])
        transition+=bytes([3,250,1,19,250]) if variable else bytes([18,1])
        root=bytes([255,1,0,0,255])+len(transition).to_bytes(2,'little')+transition+bytes([23,0,0])
        # Await a second normal cycle: bound arrows may legitimately clear v19.
        room=(bytes([131]) if retake else b'')+bytes([1,249,255,1,249,2,255,6,0,4,200,6,134,1,0,0])
        volume=bytearray();entries=[]
        for body in (root,room):
            entries.append(len(volume).to_bytes(3,'big'))
            logic=len(body).to_bytes(2,'little')+body
            volume+=b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
        observed={}
        def inspect(cpu,r,syms):
            observed['control']=cpu.read(syms['vmplayercontrol'],1)[0]
            observed['block']=cpu.read(syms['gameblockenabled'],1)[0]
        error,output,state=exercise(d,{'/game/logDir':b''.join(entries),'/game/vol.0':bytes(volume)},
            arguments=b'/game 0\r',module='wbgame',base=0xa000,database=0,
            window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
            keyboard_by_cycle={1:(b'\x09',0x40)},os_call_limit=20000,
            breakpoint_hooks={'GameReadKey':inspect})
        assert not error,(label,error)
        assert state['vmvariables'][0:2]==bytes([1,0]),(label,'room variables')
        assert observed=={'control':0 if retake else 1,'block':0},(label,observed)
        assert state['vmvariables'][200]==(0 if retake else 3),(label,'arrow did not update ego direction')
    print('PASS: new.room/new.room.v restore player control, release the old block and permit destination program control')


def check_room_input_sound(d):
    """A pending line and active sound must not survive into destination logic."""
    for variable in (False,True):
        transition=bytes([12,9,98,0,99,0,200])
        transition+=bytes([3,250,1,19,250]) if variable else bytes([18,1])
        root=bytes([255,1,0,0,255])+len(transition).to_bytes(2,'little')+transition+bytes([23,0,0])
        room=bytes([255,7,200,255,3,0,3,201,1,255,253,1,19,0,255,2,0,134,1,0])
        volume=bytearray();entries=[]
        def record(payload):return b'\x12\x34\0'+len(payload).to_bytes(2,'little')*2+payload
        for body in (root,room):
            entries.append(len(volume).to_bytes(3,'big'))
            volume+=record(len(body).to_bytes(2,'little')+body)
        sound=len(volume);volume+=record(bytes([28,63,0,240,255,0,240]))
        observed={}
        def pending_line(cpu,r,syms):
            assert cpu.read(syms['soundpath'],1)!=b'\0','fixture sound never started'
            cpu.write(syms['parserlength'],b'\x03');cpu.write(syms['parserline'],b'abc\0')
            cpu.write(syms['vmstrings'],b'> \0')
            row=cpu.read(syms['vminputrow'],1)[0]*40
            cpu.write(syms['textcharacters']+row,b'> abc_'+b' '*34)
        def destination(cpu,r,syms):
            observed['length']=cpu.read(syms['parserlength'],1)[0]
            observed['line']=cpu.read(syms['parserline'],1)[0]
            observed['sound']=cpu.read(syms['soundpath'],1)[0]
            row=cpu.read(syms['vminputrow'],1)[0]*40
            observed['prompt']=cpu.read(syms['textcharacters']+row,3)
        def fresh_key(cpu,r,syms):
            observed['new']=cpu.read(syms['parserline'],2)
        error,output,state=exercise(d,{'/game/logDir':b''.join(entries),'/game/vol.0':bytes(volume),
            '/game/sndDir':sound.to_bytes(3,'big')},arguments=b'/game 0\r',module='wbgame',
            base=0xa000,database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,
            capture=True,keyboard_by_cycle={1:(b'd',0)},psg={'version':4},os_call_limit=30000,
            breakpoint_hooks={'ApplyRoomChange':pending_line,'GameReadKey':destination,'GameQuitCommand':fresh_key})
        assert not error,(variable,error)
        assert observed=={'length':0,'line':0,'sound':0,'prompt':b'> _','new':b'd\0'},(variable,observed)
        assert state['vmvariables'][201]==1,'sound completion was not visible to destination logic'
    print('PASS: direct/variable room changes cancel pending parser text, stop owned sound and publish completion before destination logic')


def check_joystick_input(d):
    """Driver axes/buttons, ownership and unavailable-service keyboard fallback."""
    axes=[(x,y,0) for y in (0,128,255) for x in (0,128,255)]
    cases=[('nine directions',b'',axes,[8,1,2,7,0,3,6,5,4],None),
           ('release preserves another direction',b'',[(255,128,0),(128,128,0)],[7,7],None),
           ('program control',bytes([131,3,6,3]),[(0,128,0)],[3],None),
           ('toggle off',bytes([3,6,3,139]),[(255,128,0)],[3],None),
           ('unavailable service',b'',[(128,128,0)],[0],{'fail_at':1}),
           ('poll service fails',b'',[(255,128,0),(128,128,0)],[3,0],{'fail_at':3}),
           ('restore primes held button',bytes([121,13,0,200]),
            [(128,128,b) for b in (1,1,0,1)],[0]*4,None),
           ('button edges',bytes([121,13,0,200,121,27,0,201]),
            [(128,128,b) for b in (1,1,0,2,2,0)],[0]*6,None)]
    for label,prefix,samples,wanted,options in cases:
        print('Checking joystick:',label,flush=True)
        capture=bytes([9,251,6,1,251,11,252,0,
                       255,12,200,255,3,0,11,252,1,
                       255,12,201,255,3,0,11,252,2,
                       1,252,1,250,255,1,250,len(wanted),255,2,0,134,1,0])
        setup=bytes([3,251,200,3,252,220])+prefix+bytes([139,12,20,0])
        script=bytes([255,7,20,255])+len(capture).to_bytes(2,'little')+capture+setup
        logic=len(script).to_bytes(2,'little')+script
        files={'/game/logDir':b'\xff'*3+bytes(3),'/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic}
        def replace_direction(cpu,r,syms):
            assert cpu.read(syms['vmvariables']+6,1)==b'\x03'
            cpu.write(syms['vmvariables']+6,b'\x07')
        def prime_buttons(cpu,r,syms):
            cpu.write(syms['joysticklast'],b'\0')
            cpu.write(syms['joystickbuttons'],b'\0')
            cpu.write(syms['joystickpressed'],b'\xff')
        hooks=({'GameUpdateObjects':replace_direction} if label=='release preserves another direction'
               else {'GamePollJoystick':prime_buttons} if label=='restore primes held button' else None)
        device={'samples':[(128,128,0)]+samples,**(options or {})}
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,database=0,
            window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
            keyboard=b'\r' if options and options.get('fail_at')==1 else b'',
            os_call_limit=30000,joystick=device,breakpoint_hooks=hooks)
        assert not error,(label,error)
        seen=list(state['vmvariables'][200:200+len(wanted)])
        assert seen==wanted,(label,seen,wanted)
        if label=='restore primes held button':
            assert state['vmvariables'][220:224]==bytes([0,0,0,1]),(label,state['vmvariables'][220:224])
        if label=='button edges':
            assert state['vmvariables'][220:226]==bytes([1,0,0,2,0,0]),(label,state['vmvariables'][220:226])
        if label in ('toggle off','unavailable service','poll service fails'):
            assert state['joystickenabled']==b'\0',(label,state)
        assert state['gamefont']==(ROOT/'objs/sierrafont').read_bytes(),(label,'font overwritten')
    print('PASS: all nine joystick directions, release ownership, program control, toggle, unavailable/error fallback and edge-only Enter/Escape controllers')


def check_joystick_instances(d):
    """Two physical private maps execute one immutable resident joystick body."""
    root=ROOT/'objs';syms=symbols(root/'wbgame.map');base=0xa000
    code=(root/'wbgame').read_bytes();d.write(base,code)
    calls=[base+int(m[1],16) for m in re.finditer(
        r'^([0-9A-F]{4}) 103F8D.*os9.*I\$GetStt',(root/'wbgame.list').read_text(),re.M)
        if syms['GamePollJoystick']<=int(m[1],16)<syms['GameJoystickDisable']]
    assert len(calls)==1,calls
    stop=base+syms['GameJoystickReturn'];saved=d.read(0xffa8,3)
    expected={};banks={0:bytes([0x20,0x21,0x22]),1:bytes([0x23,0x24,0x25])}
    def select(owner):d.write(0xffa8,banks[owner])
    try:
        d.breakpoint(calls[0]);d.breakpoint(stop)
        for owner in banks:
            select(owner);state=bytearray(syms['size'])
            state[syms['vmplayercontrol']]=1;state[syms['joystickenabled']]=1
            state[syms['vmvariables']+250]=40+owner
            state[syms['gamefont']:syms['gamefont']+1024]=(root/'sierrafont').read_bytes()
            if owner:
                state[syms['joysticklast']]=3;state[syms['vmvariables']+6]=3
            d.write(0,state);expected[owner]=state
        for owner,axes,direction in [(0,(255,128),3),(1,(128,128),0),(0,(128,128),0)]:
            select(owner);d.regs(pc=base+syms['GamePollJoystick'],s=0x5ff0,u=0,dp=0,cc=0x50)
            d.call('c');r=d.regs();assert r['pc']==calls[0] and r['a']==0 and r['x']==0,r
            d.regs(pc=r['pc']+3,x=axes[0],y=axes[1],a=0,cc=r['cc']&~1)
            d.call('c');r=d.regs();assert r['pc']==stop and r['s']==0x5ff0,r
            expected[owner][syms['vmvariables']+6]=direction
            expected[owner][syms['joysticklast']]=direction
            for other in banks:
                select(other)
                assert d.read(0,syms['size'])==expected[other],(owner,other,'private context changed')
            assert d.read(base,len(code))==code,'joystick modified shared code'
    finally:
        d.breakpoint(calls[0],False);d.breakpoint(stop,False);d.write(0xffa8,saved)
    print('PASS: joystick direction ownership is independent across two physical private maps; shared code, fonts and stack remain intact')


def check_monitor_profiles(d):
    """The legacy video command changes owned colors, never picture indices."""
    root=ROOT/'objs';syms=symbols(root/'wbgame.map');code=(root/'wbgame').read_bytes()
    standard=code[syms['palette']:syms['palette']+68]
    source=(root/'platform/coco-graphics.asm').read_text().split('PaletteData',1)[1].split('PLATFORM_COCO_GAME_PALETTE_SET',1)[0]
    codes=[int(value,16) for value in re.findall(r'fcb\s+\$([0-9A-F]{2})',source)]
    assert len(codes)==32,codes
    rgb=bytearray(4)
    for color in codes[16:]:
        red=(((color>>4)&2)|((color>>2)&1))*85
        green=(((color>>3)&2)|((color>>1)&1))*85
        blue=(((color>>2)&2)|(color&1))*85
        rgb+=bytes([blue,green,red,255])
    assert code[syms['CoCoRGBPalette']:syms['CoCoRGBPalette']+68]==rgb
    baseline=None
    for label,command,before,palette_failure,wanted,error_expected in [
        ('baseline',b'',False,0,[standard],0),
        ('CoCo RGB',bytes([140]),False,0,[standard,bytes(rgb)],0),
        ('back to AGI',bytes([140,140]),False,0,[standard,bytes(rgb),standard],0),
        ('before screen',bytes([140]),True,0,[bytes(rgb)],0),
        ('palette error',bytes([140]),False,2,[standard,bytes(rgb)],203)]:
        print('Checking monitor profile:',label,flush=True)
        start=bytes([3,0,1,24,0,25,0,26])
        script=(command+start if before else start+command)+bytes([3,240,73,134,1,0])
        logic=len(script).to_bytes(2,'little')+script
        volume=b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
        picture=len(volume);volume+=b'\x12\x34\0\x01\0\x01\0\xff'
        files={'/game/logDir':b'\xff'*3+bytes(3),'/game/vol.0':volume,
               '/game/picDir':b'\xff'*3+picture.to_bytes(3,'big')}
        error,frame,state=exercise(d,files,module='wbgame',base=0xa000,database=0,
            window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
            frame_capture=True,palette_error=palette_failure,os_call_limit=30000)
        assert error==error_expected,(label,error)
        assert state['palettes']==wanted,(label,state['palettes'],wanted)
        assert state['monitorprofile']==bytes([label in ('CoCo RGB','before screen','palette error')]),(label,state['monitorprofile'])
        if label=='baseline':baseline=frame
        else:assert frame==baseline,(label,'picture indices changed')
        if not error:assert state['vmvariables'][240]==73,(label,'caller did not resume')
        assert state['gamefont']==(root/'sierrafont').read_bytes(),(label,'font overwritten')
    print('PASS: exact CoCo RGB conversion, owned palette writes, toggle back, early selection, unchanged picture indices and driver-error cleanup')


def check_monitor_instances(d):
    """The shared cold configuration body keeps each palette preference private."""
    root=ROOT/'objs';syms=symbols(root/'wbgame.map');hs=symbols(root/'sierraui.map')
    base=0xa000;helperbase=0x6000;code=(root/'wbgame').read_bytes();helper=(root/'sierraui').read_bytes()
    d.write(base,code);d.write(helperbase,helper)
    saved=d.read(0xffa8,3);banks={0:bytes([0x20,0x21,0x22]),1:bytes([0x23,0x24,0x25])};expected={}
    stop=helperbase+hs['ScreenReturn'];callback=base+syms['ScreenCallbacks']
    def select(owner):d.write(0xffa8,banks[owner])
    try:
        d.breakpoint(stop)
        for owner in banks:
            select(owner);state=bytearray(syms['size']);state[syms['vmopcode']]=140
            state[syms['monitorprofile']]=owner;state[syms['vmvariables']+250]=40+owner
            state[syms['gamefont']:syms['gamefont']+1024]=(root/'sierrafont').read_bytes()
            d.write(0,state);expected[owner]=state
        for owner in (0,1,0):
            select(owner);d.regs(pc=helperbase+hs['AuxScreenCommand'],s=0x5ff0,u=0,y=callback,dp=0,cc=0x50)
            d.call('c');r=d.regs()
            assert r['pc']==stop and r['s']==0x5ff0 and r['b']==0 and not r['cc']&1,r
            expected[owner][syms['monitorprofile']]^=1
            expected[owner][syms['coldapi']:syms['coldapi']+2]=callback.to_bytes(2,'big')
            for other in banks:
                select(other);assert d.read(0,syms['size'])==expected[other],(owner,other)
            assert d.read(base,len(code))==code and d.read(helperbase,len(helper))==helper,'shared code changed'
    finally:
        d.breakpoint(stop,False);d.write(0xffa8,saved)
    print('PASS: independent palette preferences in two physical private maps, intact fonts/stack and immutable main/helper code')


def check_screen_backend(d):
    """Exercise every cold configuration branch and invalid entry cleanup."""
    key=b'Avis Durgan'
    cases=[('cursor',bytes([108,1]),0,{'vmcursor':ord('!')}),
           ('colors',bytes([109,2,3]),0,{'vmtextforeground':2,'vmtextbackground':3}),
           ('configure',bytes([111,4,22,24]),0,{'vmpicturetop':4,'vminputrow':22,'vmstatusrow':24,'vmstatusenabled':32}),
           ('status on',bytes([112]),0,{'vmstatusenabled':1}),
           ('status off',bytes([112,113]),0,{'vmstatusenabled':0}),
           ('input off',bytes([119]),0,{'vminputenabled':0}),
           ('input on',bytes([119,120]),0,{'vminputenabled':1}),
           ('bad colors',bytes([109,16,0]),187,{}),
           ('bad picture row',bytes([111,5,23,0]),187,{}),
           ('bad input row',bytes([111,1,25,0]),187,{}),
           ('bad status row',bytes([111,1,23,25]),187,{}),
           ('bad cursor message',bytes([108,2]),203,{})]
    original=(ROOT/'objs/sierraui').read_bytes();entry=int.from_bytes(original[9:11],'big')
    for label,command,error_expected,expected in cases:
        print('Checking screen backend:',label,flush=True)
        script=command+bytes([134,1,0])
        logic=len(script).to_bytes(2,'little')+script+bytes([1,6,0,4,0])+bytes([ord('!')^key[0],key[1]])
        files={'/game/logDir':b'\xff'*3+bytes(3),'/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic}
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,os_call_limit=20000)
        assert error==error_expected,(label,error)
        for name,value in expected.items():assert state[name]==bytes([value]),(label,name,state[name])
    for offset in (0,len(original),len(original)-1):
        helper=bytearray(original);helper[entry+24:entry+26]=offset.to_bytes(2,'big')
        files['sierraui']=bytes(helper)
        script=bytes([112,134,1,0]);logic=len(script).to_bytes(2,'little')+script
        files['/game/vol.0']=b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,os_call_limit=20000)
        assert error==203,(offset,error)
    print('PASS: immutable screen configuration, cursor message callback, bounds and invalid-entry cleanup')


def check_cycle_input_error(d):
    """A status/input refresh failure must reach the interpreter's cleanup."""
    setup=bytes([3,240,0,24,240,25,240,26])
    body=b'\xff'+bytes([1,250,0])+b'\xff'+len(setup).to_bytes(2,'little')+setup
    body+=bytes([1,250,255,1,250,3,255,2,0,134,1,0])
    logic=len(body).to_bytes(2,'little')+body
    def record(payload):return b'\x12\x34\0'+len(payload).to_bytes(2,'little')*2+payload
    volume=record(logic);offset=len(volume);volume+=record(b'\xff')
    files={'/game/logDir':b'\xff'*3+bytes(3),'/game/picDir':offset.to_bytes(3,'big'),'/game/vol.0':volume}
    injected=[]
    def fail_refresh(cpu,r,syms):
        injected.append(True)
        cpu.regs(pc=int.from_bytes(cpu.read(r['s'],2),'big'),s=r['s']+2,b=187,cc=r['cc']|1)
    error,output,state=exercise(d,files,module='wbgame',base=0xa000,database=0,
        window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
        breakpoint_hooks={'ParserDrawInput':fail_refresh})
    assert injected==[True] and error==187,('input refresh error was masked',injected,error)
    print('PASS: cycle status/input refresh errors propagate with complete cleanup')



def check_status_line(d):
    """Check actual status cells and every output pixel against the font."""
    font=(ROOT/'objs/sierrafont').read_bytes()
    cases=[(score,255,True,0,False,False,b'') for score in (0,9,10,99,100,255)]
    cases += [(24,158,False,24,False,False,b''),(24,158,True,0,True,False,b''),
              (24,158,True,0,False,True,b''),
              (24,158,True,0,False,True,b'0:03:07'),
              (24,158,True,24,False,True,b'0:03:07'),
              (24,158,True,0,True,False,b'0:03:07')]
    for score,maximum,sound,row,off,updated,custom in cases:
        print('Checking status line:',score,maximum,sound,row,off,updated,flush=True)
        setup=bytes([3,240,0,24,240,25,240,26,3,3,score,3,7,maximum,
                     12 if sound else 13,9,111,1,23,row,112])
        if custom:
            setup+=bytes([3,117,0,3,116,3,3,115,7,103,row,20,1])
        if updated:
            body=bytes([255,1,250,0,255])+len(setup).to_bytes(2,'little')+setup
            change=bytes([3,3,7,13,9])
            body+=bytes([1,250,255,1,250,2,255])+len(change).to_bytes(2,'little')+change
            body+=bytes([255,1,250,3,255,2,0,134,1,0])
            score,sound=7,False
        else:body=setup+(bytes([113]) if off else b'')+bytes([134,1,0])
        logic=len(body).to_bytes(2,'little')+body
        if custom:
            text=b'%v117:%v116|2:%v115|2\0';key=b'Avis Durgan'
            logic+=bytes([1])+(len(text)+4).to_bytes(2,'little')+bytes([4,0])+bytes(v^key[i%11] for i,v in enumerate(text))
        def record(payload):return b'\x12\x34\0'+len(payload).to_bytes(2,'little')*2+payload
        volume=record(logic);offset=len(volume);volume+=record(b'\xff')
        files={'/game/logDir':b'\xff'*3+bytes(3),'/game/picDir':offset.to_bytes(3,'big'),'/game/vol.0':volume}
        cells=[]
        def capture(cpu,registers,syms):
            cells.append(cpu.read(syms['textcharacters']+row*40,40))
        error,frame,state=exercise(d,files,module='wbgame',base=0xa000,database=0,
            window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
            frame_capture=True,psg={'version':4},breakpoint_hooks={'GameQuitCommand':capture})
        assert not error,('status line',error)
        expected=bytearray(b' '*40)
        if not off:
            label=f'Score:{score} of {maximum}'.encode();expected[1:1+len(label)]=label
            if custom:expected[20:20+len(custom)]=custom
            label=b'Sound: '+(b'on' if sound else b'off');expected[30:30+len(label)]=label
        assert cells==[bytes(expected)],('status cells',cells,expected)
        for y in range(8):
            wanted=bytes(1 if off or font[character*8+y]&(0x80>>bit) else 16
                         for character in expected for bit in range(8))
            start=(row*8+y)*320
            assert frame[start:start+320]==wanted,('status pixels',row,y)
    print('PASS: score/sound status pixels, decimal boundaries, selected row, disable, live cycle updates and script-owned clock text')


def check_cold_prefix_bounds(d):
    """Validate the immutable UI directory and linked-code entry bounds."""
    original=(ROOT/'objs/sierraui').read_bytes()
    entry=int.from_bytes(original[9:11],'big')
    script=bytes([154,0,0,24,39,0,134,1,0])
    logic=len(script).to_bytes(2,'little')+script
    cases=[('valid',None,None),
           ('old screen ABI',entry+2,2),
           ('incomplete current metadata',2,entry+38),
           ('entry outside module',9,len(original)),
           ('oversized module',2,8193),
           ('zero rectangle entry',entry+20,0),
           ('oversized rectangle entry',entry+20,len(original)),
           ('CRC rectangle entry',entry+20,len(original)-1)]
    for label,offset,value in cases:
        print('Checking UI directory:',label,flush=True)
        helper=bytearray(original)
        if offset is not None:helper[offset:offset+2]=value.to_bytes(2,'big')
        files={'sierraui':bytes(helper),'/game/logDir':b'\xff'*3+bytes(3),
               '/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic}
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,
            database=0x0000,window=0x8000,blocks=None,multiple=True,
            firstblock=0x10,capture=True,os_call_limit=20000)
        assert error==(0 if offset is None else 203),(label,error)
    print('PASS: immutable UI directory, one-window module bounds and cold rectangle entry validation/cleanup')


def restart_fixture(automatic=False,depth=0):
    key=b'Avis Durgan';message=b'old state\0'
    encrypted=bytes(value^key[i%len(key)] for i,value in enumerate(message))
    # A fresh root must receive flag 6 and quit without executing old callers.
    body=bytes([255,7,6,255,3,0,134,1,0,3,40,99,12,20,114,0,1,
                121,0,65,77,98,0,99,0,200])
    if automatic:body+=bytes([12,16])
    body+=bytes([22,2,3,41,77,134,1,0])
    root=len(body).to_bytes(2,'little')+body+bytes([1])+(4+len(message)).to_bytes(2,'little')+bytes([4,0])+encrypted
    def record(payload):return b'\x12\x34\0'+len(payload).to_bytes(2,'little')*2+payload
    volume=record(root);entries=[b'\xff'*3,bytes(3)]
    for number in range(2,depth+3):
        entries.append(len(volume).to_bytes(3,'big'))
        script=bytes([22,number+1,0]) if number<depth+2 else bytes([128,3,42,88,0])
        volume+=record(len(script).to_bytes(2,'little')+script)
    sound_offset=len(volume);volume+=record(bytes([28,63,0,240,255,0,240]))
    return {'/game/logDir':b''.join(entries),'/game/sndDir':sound_offset.to_bytes(3,'big'),'/game/vol.0':volume}


def check_coco_restart_cancel(d,coco,cs):
    """The real CoCo restart prompt's cancel branch must not reset a game."""
    stop,stack=0x7e00,0x7ef0
    prompt=b'Press ENTER to start a new\ngame.\n\nPress CTRL-BREAK to continue\nwith this game.'
    forbidden=('ResetHeap','LoadObjectData','VolumesClose','EnableItemLoop')
    calls=0
    for base in (0x8000,0x9000):
        d.write(base,coco)
        d.write(0,bytes(0x6000))
        d.write(0x1ae,b'\xa5');d.write(0x1af,b'\xc3');d.write(0x1b0,b'\0')
        d.write(0x05b9,b'\0');d.write(0x01ad,b'\0')
        d.write(0x0531,b'\xff'*16)
        d.write(base+cs['MenuExtraFlag'],b'\xa5')
        d.write(base+cs['state_name_auto'],b'/alpha\0')
        original_flags=d.read(0x1ae,3)
        original_name=d.read(base+cs['state_name_auto'],7)
        original_menu=d.read(base+cs['MenuExtraFlag'],1)
        original_code=d.read(base,len(coco))
        d.write(stack,stop.to_bytes(2,'big')+b'STACK')
        d.breakpoint(stop)
        d.breakpoint(base+cs['message_box'])
        for name in forbidden:d.breakpoint(base+cs[name])
        d.regs(pc=base+cs['cmd_restart_game'],s=stack,dp=0,cc=0x50)
        try:
            d.call('c');regs=d.regs()
            assert regs['pc']==base+cs['message_box'],('restart did not ask for confirmation',regs)
            assert d.read(regs['u'],len(prompt)+1)==prompt+b'\0'
            # Stub the displayed prompt's negative result. Return through the
            # real caller, preserving the 6809 call stack exactly.
            ret=int.from_bytes(d.read(regs['s'],2),'big')
            d.regs(pc=ret,s=regs['s']+2,a=0,cc=(regs['cc']|0x04)&~0x0a)
            d.call('c');regs=d.regs()
            assert regs['pc']==stop and regs['s']==stack+2,('restart cancel did not return',regs)
            assert regs['a']==0 and regs['cc']&0x04,('cancel result was not preserved',regs)
            assert d.read(stack+2,5)==b'STACK'
            assert d.read(0x1ae,3)==original_flags
            assert d.read(base+cs['MenuExtraFlag'],1)==original_menu
            assert d.read(base+cs['state_name_auto'],7)==original_name
            assert d.read(base,len(coco))==original_code
            assert d.read(0x0531,16)==b'\xff'*16
            calls+=1
        finally:
            d.breakpoint(stop,False)
            d.breakpoint(base+cs['message_box'],False)
            for name in forbidden:d.breakpoint(base+cs[name],False)
    # Exercise the affirmative branch too. Keep the restart policy and state
    # changes in CoCo code, while replacing only the external reset/load
    # routines with counted RTS stubs.
    base=0x8000
    services=('cmd_cancel_line','ResetHeap','LoadObjectData','VolumesClose',
              'EnableItemLoop','InputCursorBlink')
    image=bytearray(coco)
    for index,name in enumerate(services):
        counter=0x7000+index
        image[cs[name]:cs[name]+6]=bytes((0x7c,counter>>8,counter&255,
                                          0x1c,0xfe,0x39))
    d.write(base,image)
    d.write(0,bytes(0x6000))
    d.write(0x1ae,b'\xa5');d.write(0x1af,b'\xc3');d.write(0x1b0,b'\0')
    d.write(0x05b9,b'\0');d.write(0x01ad,b'\0');d.write(0x006a,b'\0')
    d.write(0x0531,b'\xff'*16)
    d.write(base+cs['MenuExtraFlag'],b'\xa5')
    d.write(base+cs['state_name_auto'],b'/alpha\0')
    d.write(0x7000,bytes(len(services)))
    d.write(stack,stop.to_bytes(2,'big')+b'STACK')
    d.breakpoint(stop);d.breakpoint(base+cs['message_box'])
    try:
        d.regs(pc=base+cs['cmd_restart_game'],s=stack,dp=0,cc=0x50)
        d.call('c');regs=d.regs()
        assert regs['pc']==base+cs['message_box'],('restart did not ask for confirmation',regs)
        assert d.read(regs['u'],len(prompt)+1)==prompt+b'\0'
        ret=int.from_bytes(d.read(regs['s'],2),'big')
        d.regs(pc=ret,s=regs['s']+2,a=1,cc=regs['cc']&~0x04)
        d.call('c');regs=d.regs()
        assert regs['pc']==stop and regs['s']==stack+2,('confirmed restart did not return',regs)
        assert d.read(0x7000,len(services))==bytes((1,))*len(services)
        assert d.read(0x01ae,1)==b'\xa7'
        assert d.read(0x01af,1)==b'\xc3'
        assert d.read(0x0248,4)==bytes(4)
        assert d.read(stack+2,5)==b'STACK'
        assert d.read(base+cs['MenuExtraFlag'],1)==b'\xa5'
        assert d.read(base+cs['state_name_auto'],7)==b'/alpha\0'
    finally:
        d.breakpoint(stop,False);d.breakpoint(base+cs['message_box'],False)
    # The actual automatic-restart flag bypasses the prompt but follows the
    # same synchronous reset path. Keep every reset service instrumented.
    base=0x9000
    d.write(base,image)
    d.write(0,bytes(0x6000))
    d.write(0x01ae,b'\xa5');d.write(0x01af,b'\xc3');d.write(0x01b0,b'\x80')
    d.write(0x05b9,b'\0');d.write(0x01ad,b'\0');d.write(0x006a,b'\0')
    d.write(0x0531,b'\xff'*16)
    d.write(base+cs['MenuExtraFlag'],b'\xa5')
    d.write(base+cs['state_name_auto'],b'/alpha\0')
    d.write(0x7000,bytes(len(services)))
    d.write(0x0248,b'\x12\x34\x56\x78')
    d.write(stack,stop.to_bytes(2,'big')+b'STACK')
    d.breakpoint(stop);d.breakpoint(base+cs['message_box'])
    try:
        d.regs(pc=base+cs['cmd_restart_game'],s=stack,dp=0,cc=0x50)
        d.call('c');regs=d.regs()
        assert regs['pc']==stop and regs['s']==stack+2,('automatic restart did not bypass prompt/return',regs)
        assert regs['y']==0,('automatic restart did not reset script IP',regs)
        assert d.read(0x7000,len(services))==bytes((1,))*len(services)
        assert d.read(0x01ae,3)==b'\xa7\xc3\x80'
        assert d.read(0x0248,4)==bytes(4)
        assert d.read(stack+2,5)==b'STACK'
        assert d.read(base+cs['MenuExtraFlag'],1)==b'\xa5'
        assert d.read(base+cs['state_name_auto'],7)==b'/alpha\0'
    finally:
        d.breakpoint(stop,False);d.breakpoint(base+cs['message_box'],False)
    print(f'PASS: {calls} actual CoCo cmd_restart_game cancellations at two code bases plus confirmed/manual and automatic reset paths; prompt policy, reset dispatch, flags, handles, module fields, root IP and stack guards verified')


def check_nested_coco_restart(d,coco,cs):
    """Run restart from a real child logic through the CoCo executor."""
    base,stop,stack=0x8000,0x7e00,0x7ef0
    services=('cmd_cancel_line','ResetHeap','LoadObjectData','VolumesClose',
              'EnableItemLoop','InputCursorBlink')
    image=bytearray(coco)
    for index,name in enumerate(services):
        counter=0x7000+index
        image[cs[name]:cs[name]+6]=bytes((0x7c,counter>>8,counter&255,
                                          0x1c,0xfe,0x39))
    d.write(base,image)
    d.write(0,bytes(0x6000))
    d.write(0x002e,base.to_bytes(2,'big'))
    d.run(base+cs['PatchCmdTable']);d.run(base+cs['FixupEvalTbl'])
    d.write(0x01ae,b'\xa5');d.write(0x01af,b'\xc3');d.write(0x01b0,b'\0')
    d.write(0x05b9,b'\0');d.write(0x01ad,b'\0');d.write(0x006a,b'\0')
    d.write(0x0531,b'\xff'*16);d.write(0x7000,bytes(len(services)))
    root,child,root_code,child_code=0x3000,0x3100,0x4000,0x4100
    table=base+cs['LogicTableData']
    d.write(table,root.to_bytes(2,'big'))
    d.write(root,(child.to_bytes(2,'big')+b'\0\0\0\0'+
                  root_code.to_bytes(2,'big')*2+bytes(2)))
    d.write(child,(bytes(2)+b'\x01\0\0\0'+
                   child_code.to_bytes(2,'big')*2+bytes(2)))
    d.write(0x0062,root.to_bytes(2,'big'))
    # Root calls logic 1, then would write v250. Restart must zero Y in the
    # child and propagate that return through both ExecLogic frames.
    d.write(root_code,bytes([22,1,3,250,77,0])+b'GUARD')
    d.write(child_code,bytes([128,0])+b'GUARD')
    d.write(stack,stop.to_bytes(2,'big')+b'STACK')
    d.breakpoint(stop);d.breakpoint(base+cs['SetLogicPage'])
    d.breakpoint(base+cs['message_box'])
    prompted=False
    prompt=b'Press ENTER to start a new\ngame.\n\nPress CTRL-BREAK to continue\nwith this game.'
    try:
        d.regs(pc=base+cs['ExecLogicScript'],s=stack,y=0,dp=0,cc=0x50)
        for _ in range(64):
            d.call('c');regs=d.regs()
            if regs['pc']==stop:break
            if regs['pc']==base+cs['SetLogicPage']:
                ret=int.from_bytes(d.read(regs['s'],2),'big')
                d.regs(pc=ret,s=regs['s']+2)
                continue
            if regs['pc']==base+cs['message_box']:
                assert not prompted,'nested restart displayed the prompt twice'
                assert d.read(regs['u'],len(prompt)+1)==prompt+b'\0'
                prompted=True
                ret=int.from_bytes(d.read(regs['s'],2),'big')
                d.regs(pc=ret,s=regs['s']+2,a=1,cc=regs['cc']&~0x04)
                continue
            raise AssertionError(('unexpected nested restart stop',regs))
        else:raise AssertionError('nested CoCo restart did not unwind')
        assert prompted,'nested CoCo restart skipped its manual prompt'
        assert regs['s']==stack+2 and regs['y']==0,regs
        assert d.read(0x7000,len(services))==bytes((1,))*len(services)
        assert d.read(0x01ae,1)==b'\xa7' and d.read(0x01af,1)==b'\xc3'
        assert d.read(0x0248,4)==bytes(4)
        assert d.read(0x0431+250,1)==b'\0','nested caller resumed after restart'
        assert d.read(0x0062,2)==root.to_bytes(2,'big')
        assert d.read(stack+2,5)==b'STACK'
        assert d.read(root_code+6,5)==b'GUARD' and d.read(child_code+2,5)==b'GUARD'
    finally:
        d.breakpoint(stop,False);d.breakpoint(base+cs['SetLogicPage'],False)
        d.breakpoint(base+cs['message_box'],False)
    print('PASS: actual CoCo root->call logic 1->restart.game execution; affirmative prompt unwinds nested logic frames, suppresses caller continuation, runs reset services once and preserves stack/code guards')


def check_restarts(d):
    cases=[('confirmation',False,b'\r',0,False),
           ('cancellation',False,b'x',0,False),
           ('escape cancellation',False,b'\x1b',0,False),
           ('automatic at depth 16',True,b'',15,False),
           ('manual at depth 16',False,b'\r',15,False),
           ('long path at depth 16',False,b'\r',15,True)]
    # The restart implementation and its prompt live in the cold sierraui module.
    image=(ROOT/'objs/sierraui').read_bytes()
    assert b'ENTER restarts; ESC cancels.\0' in image, 'restart prompt is missing from the production sierraui image'
    for label,automatic,key,depth,long_path in cases:
        print('Checking restart:',label,flush=True)
        prompt_seen=[]
        dialog_seen=[]
        def observe_prompt(cpu,regs,syms):
            prompt_seen.append(cpu.read(regs['x'],64).split(b'\0',1)[0])
            return False
        def observe_dialog(cpu,regs,syms):
            cells=cpu.read(regs['u']+syms['textcharacters'],1000)
            dialog_seen.append([(row,cells[row*40:(row+1)*40].strip(b'\0 '))
                                for row in range(10,17)
                                if cells[row*40:(row+1)*40].strip(b'\0 ')])
            return False
        files=restart_fixture(automatic,depth);arguments=b'/game 1\r'
        if long_path:
            directory=b'/'+b'x'*126
            files={directory.decode()+name[5:]:data for name,data in files.items()}
            arguments=directory+b' 1\r'
        error,output,state=exercise(d,files,arguments=arguments,module='wbgame',
            base=0xa000,database=0x0000,window=0x8000,blocks=None,multiple=True,
            firstblock=0x10,capture=True,keyboard=key,psg={'version':4},
            sol={'start':250,'step':1},os_call_limit=20000,
            keyboard_by_sleep=({1:b'\x05'} if key==b'x' else None),
            cold_hooks=({'sierraui':{'AuxRestartCall':observe_prompt,
                                'AuxPrintWait':observe_dialog}}
                        if not automatic else None))
        assert not error,(label,error,output)
        assert state['gamefont']==(ROOT/'objs/sierrafont').read_bytes(),(label,'font changed')
        assert state['dialoginputmode']==b'\0',(label,'restart leaked modal input mode')
        if not automatic:
            assert prompt_seen==[b'ENTER restarts; ESC cancels.'],(label,prompt_seen)
            assert dialog_seen and dialog_seen[0],(label,dialog_seen)
            rendered=b''.join(line.replace(b' ',b'')
                              for _,line in dialog_seen[0])
            assert rendered==b'ENTERrestarts;ESCcancels.',(label,dialog_seen)
        if key in (b'x',b'\x1b'):
            assert state['vmflags'][6]==0 and state['vmflags'][20]==1
            assert state['vmvariables'][40:43]==bytes([99,77,88])
            assert state['vmkeycount']==b'\x01' and state['vmstrings'].startswith(b'old state\0')
        else:
            assert state['vmflags'][6]==1 and state['vmflags'][20]==0
            assert state['vmvariables'][40:43]==bytes(3),(label,'old caller continued')
            assert state['vmkeycount']==b'\0' and not any(state['vmkeys'])
            assert not any(state['vmstrings']) and state['vmobjects'][3:5]==bytes(2)
        assert state['audio_packets'],(label,'active sound was not exercised')
    for name in ('zero','size','CRC'):
        helper=bytearray((ROOT/'objs/sierraui').read_bytes());entry=int.from_bytes(helper[9:11],'big')
        offset=0 if name=='zero' else len(helper)-(1 if name=='CRC' else 0)
        helper[entry+34:entry+36]=offset.to_bytes(2,'big')
        files=restart_fixture();files['sierraui']=bytes(helper)
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,
            database=0x0000,window=0x8000,blocks=None,multiple=True,
            firstblock=0x10,capture=True,keyboard=b'\r',os_call_limit=20000)
        assert error==203,(name,error)
    print('PASS: restart prompt text-plane capture, Enter/Escape filtering, ordinary-key rejection, confirmation/cancellation/automatic mode, 16-call unwind, long-path protection, logical reset, active sound/clock cleanup and invalid entries')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--object-previews-only',action='store_true',
                        help='run the focused object preview and CoCo reference checks')
    parser.add_argument('--menu-only',action='store_true',
                        help='run focused submitted-menu construction, rendering and cleanup checks')
    parser.add_argument('--menu-render-only',action='store_true',
                        help='capture the submitted menu overlay before cleanup checks')
    args=parser.parse_args()
    game = ROOT / 'kingsquest1'
    commands, volume, offset = resource(game, 1)
    expected = render(game, commands, 'lwasm.orig', ROOT.parent.parent / 'nitros9/defs')
    script = bytes([3,0,1,24,0,25,0,26,134,1,0])
    logic = len(script).to_bytes(2,'little') + script
    assert volume != 0, 'test logic occupies volume zero'
    files = {
        '/game/logDir': bytes.fromhex('ffffff000000'),
        '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2, 'little') * 2 + logic,
        '/game/picDir': (game / 'picDir').read_bytes(),
        f'/game/vol.{volume}': (game / f'vol.{volume}').read_bytes(),
    }
    with tempfile.TemporaryDirectory(prefix='sierra-game-') as temp:
        d, emulator = start_cpu(idle_rom(Path(temp) / 'idle.rom'), timeout=14400)
        try:
            d.write(0xffdf, b'\0')
            d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01')
            d.write(0xffa8, bytes(range(8)))
            if args.object_previews_only:
                check_object_previews(d)
                return
            if args.menu_render_only:
                check_menu_render_overlay(d)
                return
            if args.menu_only:
                check_menu_build_reference(d)
                check_menu_visibility_commands(d)
                check_cold_menus(d)
                return
            check_native_trace(d)
            check_reused_private_state(d)
            check_compatibility_noops(d)
            check_object_status_commands(d)
            check_memory_info_commands(d)
            check_positioned_messages(d)
            check_text_screen_key_wait(d)
            check_original_help(d)
            check_nested_logic_calls(d)
            check_original_death_messages(d)
            check_original_pickup_puzzles(d)
            check_original_coronation(d)
            check_original_fiddle_encounter(d)
            check_original_dragon_encounter(d)
            check_original_giant_encounter(d)
            check_original_quest_chain(d)
            check_original_quest_chain(d,prerequisites=True)
            check_original_quest_chain(d,all_acquisitions=True)
            check_original_rock_death(d)
            check_original_rock_death(d,restart=True)
            check_timed_messages(d)
            check_object_previews(d)
            check_interpreter_information(d)
            check_menu_request_order_reference(d)
            check_menu_visibility_reference(d)
            check_menu_item_enable_reference(d)
            check_menu_build_reference(d)
            check_menu_visibility_commands(d)
            check_cold_menus(d)
            check_room_controls(d)
            check_room_input_sound(d)
            check_joystick_input(d)
            check_joystick_instances(d)
            check_monitor_profiles(d)
            check_monitor_instances(d)
            check_screen_backend(d)
            check_status_line(d)
            check_cycle_input_error(d)
            check_cold_prefix_bounds(d)
            check_restarts(d)
            check_bounded_said(d)
            check_state_cache_bounds(d)
            check_state_transfers(d)
            check_state_validation(d)
            check_provider_loaders(d)
            check_ui_command_cache(d)
            check_simple_save_reference(d)
            check_simple_save_staging(d)
            check_simple_save_restart(d)
            check_save_replacement(d)
            from check_logic_executor import compile_module
            coco,cs=compile_module(ROOT/'objs/mnln.asm',Path(temp)/'mnln')
            check_coco_restart_cancel(d,coco,cs)
            check_nested_coco_restart(d,coco,cs)
            error, frame = exercise(d, files, module='wbgame', base=0xa000,
                database=0x0000, window=0x8000, blocks=None, multiple=True,
                firstblock=0x10, frame_capture=True)
            assert not error, error
            failed, unused = exercise(d, files, module='wbgame', base=0xa000,
                database=0x0000, window=0x8000, blocks=None, multiple=True,
                firstblock=0x10, bitmap_error=True)
            assert failed == 32 and not unused, 'bitmap allocation refusal did not clean up'
            expected_frame = bytearray([1]) * 76800
            for y in range(168):
                row = bytes(value for pixel in expected[y*160:(y+1)*160]
                            for value in [(pixel & 15) + 1] * 2)
                expected_frame[(y+8)*320:(y+9)*320] = row
            assert frame == expected_frame, 'integrated AGI picture commands differ from CoCo pixels'
            # Replay overflow must stop before starting another destructive draw.
            for limit in (1,2):
                body = bytes([142,limit,3,0,1,24,0,25,0,25,0,134,1,0])
                logic = len(body).to_bytes(2,'little') + body
                overflow_files = {**files,
                    '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2,'little')*2 + logic}
                error, output, state = exercise(d,overflow_files,module='wbgame',
                    base=0xa000,database=0x0000,window=0x8000,blocks=None,
                    multiple=True,firstblock=0x10,capture=True)
                assert error == 207, ('draw replay overflow',limit,error)
                replay = bytes([2,1,4,1])[:limit*2]
                assert int.from_bytes(state['replayused'],'big') == len(replay)
                assert state['replaybuffer'][:len(replay)] == replay
            # A small view makes transparency, clipping, mirroring, depth and
            # erase behavior observable independently of game scripts.
            normal_rows = [[1, 1, None, 2], [3, 4, 4, 4], [5, None, None, None]]
            for mirrored, xpos, ypos, priority, erase, transparent_only, other_object, reselect in [
                    (False, 20, 30, 15, False, False, False, False),
                    (True, 159, 1, 15, False, False, False, False),
                    (False, 20, 30, 3, False, False, False, False),
                    (False, 20, 30, 15, True, False, False, False),
                    (False, 20, 30, 15, False, True, False, False),
                    (False, 20, 30, 3, False, False, True, False),
                    (False, 159, 1, 15, False, False, False, True),
                    (False, 159, 1, 15, False, False, False, 'loop')]:
                rows = [[None]*4 for _ in range(3)] if transparent_only else normal_rows
                script = bytes([3,0,1,24,0,25,0,33,0,41,0,0,
                    37,0,xpos,ypos] +
                    ([63,48] if reselect else []) +
                    ([43 if reselect == 'loop' else 47,0,0] if reselect else []) +
                    [54,0,priority,35,0] +
                    ([36,0] if erase else []) +
                    ([33,1,41,1,0,37,1,40,30,54,1,15,35,1] if other_object else []) + [26,134,1,0])
                logic = len(script).to_bytes(2, 'little') + script
                picture = b'\xff'
                view = bytes([0,0,2,0,0,9,0,9,0,1,3,0,4,3,
                    0x9f if mirrored else 0x1f] +
                    ([0xf4,0]*3 if transparent_only else [0x12,0xf1,0x21,0,0x31,0x43,0,0x51,0]))
                resources = bytearray()
                offsets = []
                for payload in (logic, picture, view):
                    offsets.append(len(resources))
                    resources.extend(b'\x12\x34\0' + len(payload).to_bytes(2, 'little') * 2 + payload)
                files = {'/game/vol.0': bytes(resources),
                    '/game/logDir': b'\xff' * 3 + offsets[0].to_bytes(3, 'big'),
                    '/game/picDir': b'\xff' * 3 + offsets[1].to_bytes(3, 'big'),
                    '/game/viewDir': offsets[2].to_bytes(3, 'big')}
                error, frame, state = exercise(d, files, module='wbgame', base=0xa000,
                    database=0x0000, window=0x8000, blocks=None, multiple=True,
                    firstblock=0x10, frame_capture=True, capture=True)
                assert not error, (error, mirrored, xpos, ypos, priority, erase)
                if reselect:
                    assert state['vmobjects'][3:5] == bytes((156,49)), state['vmobjects'][:43]
                    xpos, ypos = 156, 49
                assert state['vmflags'][1] == int(priority < 4 or transparent_only), 'ego hidden flag did not match cel pixel visibility'
                expected_frame = bytearray([1]) * 76800
                expected_frame[8*320:176*320] = bytes([16]) * (168*320)
                if priority >= 4 and not erase:
                    for rownum, row in enumerate(rows):
                        y = ypos - len(rows) + 1 + rownum
                        for col, color in enumerate(reversed(row) if mirrored else row):
                            x = xpos + col
                            if color is not None and 0 <= x < 160 and 0 <= y < 168:
                                address = (y+8)*320 + x*2
                                expected_frame[address:address+2] = bytes([color+1]) * 2
                if other_object:
                    for rownum,row in enumerate(normal_rows):
                        for column,color in enumerate(row):
                            if color is not None:
                                start=(28+rownum+8)*320+(40+column)*2
                                expected_frame[start:start+2]=bytes([color+1])*2
                assert frame == expected_frame, (mirrored, xpos, ypos, priority, erase,
                    next((i for i, (a,b) in enumerate(zip(frame, expected_frame)) if a != b), None))
            # Overlay changes selected visual/priority pixels without clearing
            # the scene or baking animated sprites into the static background.
            for mode in ('blank','drawn','moved','erased','malformed'):
                body = bytearray([142,32])
                if mode != 'blank':
                    body.extend([3,0,1,24,0,25,0,33,0,41,0,0,
                                 37,0,20,30,54,0,14,35,0,26])
                body.extend([3,0,2,24,0,28,0])
                if mode not in ('blank','malformed'):
                    body.extend([60,0])
                if mode == 'moved':
                    body.extend([37,0,40,30,60,0])
                if mode == 'erased':
                    body.extend([36,0])
                body.extend([26,134,1,0])
                logic = len(body).to_bytes(2,'little') + body
                overlay = (bytes([240]) if mode == 'malformed' else
                           bytes([240,3,242,15,246,23,28,23,30,255]))
                view = bytes([0,0,2,0,0,9,0,9,0,1,3,0,4,3,31,
                              18,241,33,0,49,67,0,81,0])
                resources = bytearray(); offsets = []
                for payload in (logic,b'\xff',overlay,view):
                    offsets.append(len(resources))
                    resources.extend(b'\x12\x34\0'+len(payload).to_bytes(2,'little')*2+payload)
                files = {'/game/vol.0':bytes(resources),
                    '/game/logDir':b'\xff'*3+offsets[0].to_bytes(3,'big'),
                    '/game/picDir':b'\xff'*3+offsets[1].to_bytes(3,'big')+offsets[2].to_bytes(3,'big'),
                    '/game/viewDir':offsets[3].to_bytes(3,'big')}
                error,frame,state = exercise(d,files,module='wbgame',base=0xa000,
                    database=0x0000,window=0x8000,blocks=None,multiple=True,
                    firstblock=0x10,frame_capture=True,capture=True)
                assert error == (203 if mode == 'malformed' else 0), ('overlay error',mode,error)
                if mode == 'malformed':
                    continue
                wanted = bytearray([1])*76800
                wanted[8*320:176*320] = bytes([16])*(168*320)
                for row in range(28,31):
                    start=(row+8)*320+23*2
                    wanted[start:start+2]=bytes([4,4])
                if mode in ('drawn','moved'):
                    xpos=40 if mode == 'moved' else 20
                    for rownum,row in enumerate(normal_rows):
                        for col,color in enumerate(row):
                            x=xpos+col
                            if color is not None and x != 23:
                                start=(28+rownum+8)*320+x*2
                                wanted[start:start+2]=bytes([color+1])*2
                assert frame == wanted, ('overlay pixels/priority/background',mode,
                    next((i for i,(a,b) in enumerate(zip(frame,wanted)) if a!=b),None))
                replay = (b'' if mode == 'blank' else bytes([2,1,4,1,1,0])) + bytes([2,2,8,2])
                assert int.from_bytes(state['replayused'],'big') == len(replay)
                assert state['replaybuffer'][:len(replay)] == replay
            # Repeated cycles must move the ego and stop precisely at a target.
            # An end-of-loop animation must set its completion flag as well.
            for mode in ('normal', 'move', 'animation', 'arrow', 'arrowtoggle', 'programarrow', 'backspace', 'wall', 'land', 'water', 'block', 'ignoreblock', 'unblock', 'wander'):
                setup = bytes([3,0,1,24,0,25,0,33,0,41,0,0,
                    37,0,20,60,70,0,35,0,26])
                if mode in ('normal', 'wall', 'land', 'water', 'block', 'ignoreblock', 'unblock'):
                    setup += bytes([3,6,3])
                    if mode in ('block', 'ignoreblock', 'unblock'):
                        setup += bytes([90,20,50,30,70])
                        if mode == 'ignoreblock':
                            setup += bytes([88,0])
                        elif mode == 'unblock':
                            setup += bytes([91])
                    if mode == 'land':
                        setup += bytes([65,0])
                    elif mode == 'water':
                        setup += bytes([64,0])
                    stop = bytes([255,1,250,3,255,2,0,134,1])
                elif mode in ('arrow', 'arrowtoggle', 'programarrow', 'backspace'):
                    setup += bytes([131,121,9,0,200] if mode == 'programarrow' else [132])
                    stop = bytes([255,1,250,4,255,2,0,134,1])
                elif mode == 'wander':
                    setup += bytes([84,0])
                    stop = bytes([255,1,250,3,255,2,0,134,1])
                elif mode == 'move':
                    setup += bytes([81,0,23,60,2,200])
                    stop = bytes([255,7,200,255,2,0,134,1])
                else:
                    setup += bytes([73,0,200])
                    stop = bytes([255,7,200,255,2,0,134,1])
                script = bytes([255,7,11,255]) + len(setup).to_bytes(2,'little') + setup
                script += bytes([255,12,200,255,2,0,12,219])
                for test, flag in ((11,210),(16,211),(17,212),(18,213)):
                    script += bytes([255,test,0,0,0,159,167,255,2,0,12,flag])
                script += bytes([255,7,180,11,0,0,0,159,167,255,2,0,12,214])
                script += bytes([69,0,0,248,69,0,1,249,1,250]) + stop + bytes([255,1,250,8,255,2,0,134,1,0])
                logic = len(script).to_bytes(2,'little') + script
                # Two 1x1 cels: red followed by green.
                view = bytes([0,0,1,0,0,7,0,2,5,0,10,0,
                    1,1,15,0x11,0,1,1,15,0x21,0])
                resources = bytearray()
                offsets = []
                picture = b'\xff'
                if mode == 'wall':
                    picture = bytes([0xf2,0,0xf6,21,60,21,60,0xf3,0xff])
                elif mode in ('land', 'water'):
                    picture = bytes([0xf2,3,0xf6,21,60,22,60,0xf3,0xff])
                for payload in (logic, picture, view):
                    offsets.append(len(resources))
                    resources.extend(b'\x12\x34\0' + len(payload).to_bytes(2,'little') * 2 + payload)
                files = {'/game/vol.0': bytes(resources),
                    '/game/logDir': b'\xff' * 3 + offsets[0].to_bytes(3,'big'),
                    '/game/picDir': b'\xff' * 3 + offsets[1].to_bytes(3,'big'),
                    '/game/viewDir': offsets[2].to_bytes(3,'big')}
                error, output, state = exercise(d, files, module='wbgame', base=0xa000,
                    database=0x0000, window=0x8000, blocks=None, multiple=True,
                    firstblock=0x10, capture=True,
                    keyboard=b'\x09' if mode in ('arrow','arrowtoggle','programarrow') else (b'\x08' if mode == 'backspace' else b''),
                    key_sense=0x40 if mode in ('arrow','arrowtoggle','programarrow') else 0,
                    keyboard_by_cycle={2:(b'\x09',0x40)} if mode=='arrowtoggle' else None)
                assert not error and not output, (mode, error)
                assert state['vmvariables'][248:250] == bytes([0,255]), 'shared object distance visibility/self cases'
                assert state['vmflags'][210:214] == bytes([1]*4), 'position tests failed'
                assert state['vmflags'][214] == 0, 'position test overwrote false AND accumulator'
                if mode == 'programarrow':
                    assert state['vmflags'][219] == 0, 'ignored Right arrow triggered an ASCII Tab controller'
                ego = state['vmobjects'][:43]
                if mode == 'arrowtoggle':
                    assert ego[3:5] == bytes([21,60]) and ego[0x21] == 0, ('same arrow did not stop ego',ego.hex())
                elif mode == 'wander':
                    assert ego[0x22] == 1 and ego[0x21] <= 8 and 6 <= ego[0x27] <= 50
                elif mode in ('programarrow', 'backspace', 'wall', 'land', 'block'):
                    assert ego[3:5] == bytes([20,60]), (mode, ego.hex())
                elif mode in ('normal', 'arrow', 'water', 'ignoreblock', 'unblock'):
                    assert ego[3:5] == bytes([22,60]), (mode, ego.hex())
                elif mode == 'move':
                    assert ego[3:5] == bytes([23,60]), (mode, ego.hex())
                    assert ego[0x1e] == 1 and ego[0x21] == 0 and ego[0x22] == 0
                    assert state['vmflags'][200] == 1
                else:
                    assert ego[0x0e] == 1 and not (ego[0x26] & 0x20)
                    assert state['vmflags'][200] == 1
            # display writes true 8-by-8 cells, including a row that straddles
            # an 8K frame page, and survives the next show.pic refresh.
            import re
            font = bytes(int(v,16) for v in re.findall(r'\$([0-9A-F]{2})',
                (ROOT / 'objs/font-data.asm').read_text()))
            message = b'Ab!\0'
            key = b'Avis Durgan'
            encrypted = bytes(value ^ key[i % len(key)] for i,value in enumerate(message))
            expected_frame = bytearray([1]) * 76800
            row, column = 3, 39
            for character in message[:-1]:
                for glyphrow in range(8):
                    bits = font[character*8 + glyphrow]
                    for pixel in range(8):
                        expected_frame[(row*8+glyphrow)*320+column*8+pixel] = 15 if bits & (128 >> pixel) else 2
                column += 1
                if column == 40:
                    column, row = 0, row+1
            for label,display in (
                    ('literal',bytes([103,3,39,1])),
                    ('variable',bytes([3,200,3,3,201,39,3,202,1,104,200,201,202]))):
                print('Checking display command:',label,flush=True)
                script = bytes([109,14,1]) + display + bytes([26,134,1,0])
                logic = len(script).to_bytes(2, 'little') + script
                logic += bytes([1]) + (4+len(message)).to_bytes(2,'little') + bytes([4,0]) + encrypted
                files = {'/game/logDir': b'\xff' * 3 + bytes(3),
                    '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2,'little') * 2 + logic}
                error, frame = exercise(d, files, module='wbgame', base=0xa000,
                    database=0x0000, window=0x8000, blocks=None, multiple=True,
                    firstblock=0x10, frame_capture=True)
                assert not error, (label,error)
                assert frame == expected_frame, ('native text glyphs/colors/wrapping differ or were erased by show.pic',label)
            for clearcolor in (0,1):
                script = bytes([109,14,1,103,3,39,1,105,3,3,clearcolor,26,134,1,0])
                logic = len(script).to_bytes(2,'little') + script
                logic += bytes([1]) + (4+len(message)).to_bytes(2,'little') + bytes([4,0]) + encrypted
                files = {'/game/logDir': b'\xff'*3 + bytes(3),
                    '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2,'little')*2 + logic}
                error, frame = exercise(d, files, module='wbgame', base=0xa000,
                    database=0x0000, window=0x8000, blocks=None, multiple=True,
                    firstblock=0x10, frame_capture=True)
                assert not error, error
                cleared = bytearray(expected_frame)
                cleared[24*320:32*320] = bytes([16 if clearcolor else 1]) * (8*320)
                assert frame == cleared, 'clear.lines range/color/persistence'
            # Inclusive rectangles preserve neighboring glyphs and reject invalid
            # geometry before changing cells. Expected pixels are independent of
            # the renderer's row/cell addressing.
            rectangles = [(3,39,4,39,0), (3,0,4,0,1), (0,0,24,39,0),
                          (23,0,24,0,1), (23,0,255,0,1),
                          (24,39,24,39,15), (25,0,25,0,0), (3,38,4,39,1),
                          (3,39,3,40,7), (3,40,3,40,15)]
            rectangles += [(25,0,25,0,0), (0,40,0,40,0),
                           (4,0,3,1,0), (3,2,4,1,0)]
            for top,left,bottom,right,color in rectangles:
                invalid = top > bottom or left > right or right >= 41
                script = bytes([109,14,1,103,3,39,1,154,top,left,bottom,right,color,
                                26,134,1,0])
                logic = len(script).to_bytes(2,'little') + script
                logic += bytes([1]) + (4+len(message)).to_bytes(2,'little') + bytes([4,0]) + encrypted
                files = {'/game/logDir': b'\xff'*3 + bytes(3),
                    '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2,'little')*2 + logic}
                error, frame = exercise(d, files, module='wbgame', base=0xa000,
                    database=0x0000, window=0x8000, blocks=None, multiple=True,
                    firstblock=0x10, frame_capture=True)
                assert error == (187 if invalid else 0), ('clear.text.rect', error)
                cleared = bytearray(expected_frame)
                if not invalid:
                    for textrow in range(top,min(bottom,23)+1):
                        for textcolumn in range(left,right+1):
                            cell=textrow*40+textcolumn
                            cellrow,cellcolumn=divmod(cell,40)
                            for pixelrow in range(cellrow*8,(cellrow+1)*8):
                                start=pixelrow*320+cellcolumn*8
                                cleared[start:start+8]=bytes([color+1])*8
                assert frame == cleared, ('clear.text.rect pixels', (top,left,bottom,right,color))
            # text.screen selects the CoCo-style transparent text overlay;
            # only explicit text cells/clear operations change the picture.
            # graphics clears the overlay and restores the same game picture.
            screen_picture = bytearray([1]) * 76800
            for row in range(168):
                pixels = bytes(value for pixel in expected[row*160:(row+1)*160]
                               for value in [(pixel&15)+1]*2)
                screen_picture[(row+8)*320:(row+9)*320] = pixels
            for background in (0,1,7,15):
                for mode in ('text', 'graphics', 'cycles', 'rectangle', 'discard'):
                    print('Checking text/graphics mode:', mode, background, flush=True)
                    script = bytes([255,1,250,0,255,2,0,142,64,3,0,1,24,0,25,0,26,119,109,14,background])
                    script += bytes([1,250,106,103,24,0,1])
                    if mode == 'graphics':
                        script += bytes([107,106,107])
                    if mode == 'discard':
                        script += bytes([107,27,0])
                    if mode == 'rectangle':
                        script += bytes([154,24,0,24,0,15])
                    if mode == 'cycles':
                        script += bytes([255,1,250,3,255,2,0,134,1,0])
                    else:
                        script += bytes([134,1,0])
                    logic = len(script).to_bytes(2,'little') + script
                    logic += bytes([1]) + (4+len(message)).to_bytes(2,'little') + bytes([4,0]) + encrypted
                    files = {'/game/logDir': b'\xff'*3 + bytes(3),
                        '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2,'little')*2 + logic,
                        '/game/picDir': (game/'picDir').read_bytes(),
                        f'/game/vol.{volume}': (game/f'vol.{volume}').read_bytes()}
                    error, frame, state = exercise(d, files, module='wbgame',
                        base=0xa000,database=0x0000,window=0x8000,blocks=None,
                        multiple=True,firstblock=0x10,frame_capture=True,capture=True)
                    assert not error, (mode, background, error)
                    assert state['vmgraphics']==bytes([1 if mode in ('graphics','discard') else 0]), \
                        ('text/graphics mode state',mode,state['vmgraphics'])
                    wanted = bytearray(screen_picture)
                    if mode in ('text','cycles','rectangle'):
                        for column, character in enumerate(message[:-1]):
                            for row in range(8):
                                bits = font[character*8+row]
                                for pixel in range(8):
                                    wanted[(24*8+row)*320+column*8+pixel] = (
                                        15 if bits&(128>>pixel) else background+1)
                    if mode == 'rectangle':
                        # Row 24 is below CoCo's text rectangle bottom (23),
                        # so the command is a successful no-op there.
                        pass
                    assert frame == wanted, ('text/graphics mode pixels', mode, background)
                    assert state['vmvariables'][250] == (3 if mode == 'cycles' else 1)
                    replay = bytes([2,1]) + bytes([4,1]) * (3 if mode == 'cycles' else 1)
                    if mode == 'discard':
                        replay += bytes([6,1])
                    assert int.from_bytes(state['replayused'],'big') == len(replay)
                    assert state['replaybuffer'][:len(replay)] == replay, ('picture replay',mode)
            # Inventory locations are private and names come from encrypted object data.
            raw_object = bytes([6,0,2,6,0,255,10,0,1]) + b'key\0coin\0'
            cipher = b'Avis Durgan'
            encrypted = bytes(value ^ cipher[i % len(cipher)] for i,value in enumerate(raw_object))
            for selected, keys, expected_item in ((False,b'x',0),(True,b'\n\r',1),(True,b'\x1b',255)):
                script = bytes([3,239,1,3,238,3,92,1,97,239,240,95,1,238,97,239,241,255,10,1,238,255,2,0,12,221,93,239,97,239,242,255,9,1,255,2,0,12,222] +
                    ([12,13] if selected else []) + [124,97,239,243,134,1,0])
                logic = len(script).to_bytes(2,'little') + script
                files = {'/game/logDir': b'\xff'*3 + bytes(3),
                    '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2,'little')*2 + logic,
                    '/game/object': encrypted}
                error, output, state = exercise(d, files, module='wbgame', base=0xa000,
                    database=0x0000, window=0x8000, blocks=None, multiple=True,
                    firstblock=0x10, capture=True, frame_capture=True, keyboard=keys)
                assert not error, ('inventory',error)
                assert output == bytes([1])*76800, 'inventory left pixels outside the restored picture'
                assert state['vmvariables'][240:243] == bytes([255,3,255]), 'inventory item locations'
                assert state['vmvariables'][243] == 255, 'status reload reset modified item rooms'
                assert state['vmflags'][221:223] == bytes([1,1]), 'inventory possession/room predicates'
                if selected:
                    assert state['vmvariables'][25] == expected_item, 'inventory selection/cancel'
            # Selection must scroll beyond the 21 visible rows without losing IDs.
            table = bytearray((69).to_bytes(2,'little') + bytes([23]))
            names = bytearray()
            for item in range(23):
                table.extend((69+len(names)).to_bytes(2,'little') + bytes([255]))
                names.extend(f'item {item}'.encode() + b'\0')
            raw_object = table + names
            encrypted = bytes(value ^ cipher[i % len(cipher)] for i,value in enumerate(raw_object))
            script = bytes([12,13,124,134,1,0])
            logic = len(script).to_bytes(2,'little') + script
            files = {'/game/logDir': b'\xff'*3 + bytes(3),
                '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2,'little')*2 + logic,
                '/game/object': encrypted}
            error, output, state = exercise(d, files, module='wbgame', base=0xa000,
                database=0x0000, window=0x8000, blocks=None, multiple=True,
                firstblock=0x10, capture=True, frame_capture=True, keyboard=b'\n'*22 + b'\r', os_call_limit=100000)
            assert not error and state['vmvariables'][25] == 22, 'inventory scrolling lost item identity'
            assert output == bytes([1])*76800, 'scrolled inventory left an overlay'
            for bad_font in (b'', bytes(1023), bytes(1025)):
                failed_files = {**files, 'sierrafont': bad_font}
                error, output, state = exercise(d, failed_files, module='wbgame', base=0xa000,
                    database=0x0000, window=0x8000, blocks=None, multiple=True,
                    firstblock=0x10, capture=True)
                assert error, 'malformed font accepted'
            for malformed in (b'bad', encrypted[:10], encrypted + bytes(4096)):
                files['/game/object'] = malformed
                error, output, state = exercise(d, files, module='wbgame', base=0xa000,
                    database=0x0000, window=0x8000, blocks=None, multiple=True,
                    firstblock=0x10, capture=True)
                assert error, 'malformed object file accepted'
            for sound_enabled in (False, True):
                script = bytes(([12,9] if sound_enabled else [13,9]) + [99,0,200,100,134,1,0])
                logic = len(script).to_bytes(2,'little') + script
                files = {'/game/logDir': b'\xff' * 3 + bytes(3),
                    '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2,'little') * 2 + logic}
                error, output, state = exercise(d, files, module='wbgame', base=0xa000,
                    database=0x0000, window=0x8000, blocks=None, multiple=True,
                    firstblock=0x10, capture=True)
                assert not error and state['vmflags'][200] == 1, 'sound-off completion flag missing'
                assert state['vmflags'][9] == 0, 'unsupported audio remained enabled'
                assert output == b'', 'audio fallback interrupted game output'
            # Adjacent high controllers exercise every bit, including controller
            # 255. Exactly one must be active in each cycle, then all must clear.
            script = bytearray()
            for bit in range(8):
                script.extend([121, ord('a') + bit, 0, 248 + bit])
            for bit in range(8):
                script.extend([255, 12, 248 + bit, 255, 4, 0,
                               1, 220 + bit, 12, 220 + bit])
            script.extend([1, 250, 255, 1, 250, 10, 255, 2, 0, 134, 1, 0])
            logic = len(script).to_bytes(2, 'little') + script
            files = {'/game/logDir': b'\xff' * 3 + bytes(3),
                '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2, 'little') * 2 + logic}
            error, output, state = exercise(d, files, module='wbgame', base=0xa000,
                database=0x0000, window=0x8000, blocks=None, multiple=True,
                firstblock=0x10, capture=True, keyboard=b'abcdefgh')
            assert not error and not output, (error, output)
            assert state['vmvariables'][220:228] == bytes([1]) * 8, 'controller bits aliased or survived their cycle'
            assert state['vmflags'][220:228] == bytes([1]) * 8, 'high controller bit was lost'
            script = bytes([121,ord('q'),0,7,1,250,255,12,7,255,2,0,134,1,0])
            logic = len(script).to_bytes(2, 'little') + script
            files = {'/game/logDir': b'\xff' * 3 + bytes(3),
                '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2, 'little') * 2 + logic}
            error, output, state = exercise(d, files, module='wbgame', base=0xa000,
                database=0x0000, window=0x8000, blocks=None, multiple=True,
                firstblock=0x10, capture=True, keyboard=b'q', clock=(59,0))
            assert not error and not output
            assert state['vmvariables'][250] == 2, 'controller did not reach the next logic cycle'
            assert state['vmvariables'][11] == 1, 'clock lost the second at minute rollover'
            print('PASS: native picture/view composition matches every castle pixel and handles transparent/mirrored/clipped/occluded/erased sprites and ego-hidden flag ownership with persistent native text, inclusive text rectangles and exact invalid-bound errors, repeated logic cycles, keyboard controllers, clock rollover, stepping, move-to completion, end-of-loop animation, arrows/backspace, shared object distance, blocking/ignoring/clearing rectangles, inventory transfers/predicates/selection/scrolling, font validation, full-frame restoration, one mapping and complete cleanup')
        finally:
            d.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill()
                emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
