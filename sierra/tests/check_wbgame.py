#!/usr/bin/env python3
"""Execute native AGI picture commands through the integrated game owner."""
from pathlib import Path
import subprocess
import tempfile
import re
from check_wbres import exercise, idle_rom, start_cpu
from check_instances import symbols
ROOT = Path(__file__).resolve().parents[1]
from export_picture import resource, render


def check_state_transfers(d):
    """File counts must be checked independently of the service's Z flag."""
    root=ROOT/'objs'; syms=symbols(root/'wbstate.map'); base=0x9000
    d.write(base,(root/'wbstate').read_bytes())
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


def check_state_validation(d):
    root=ROOT/'objs'; syms=symbols(root/'wbstate.map'); base=0x9000
    d.write(base,(root/'wbstate').read_bytes())
    import re
    calls={base+int(m[1],16):int(m[2],16) for m in re.finditer(
        r'^([0-9A-F]{4}) 103F([0-9A-F]{2}).*os9',
        (root/'wbstate.list').read_text(),re.M)}
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
        ('default after positioned',151,3,7,12,b'alpha beta gamma delta',[(8,2,b'alpha beta gamma delta')]),
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
            helper=bytearray((ROOT/'objs/wbstate').read_bytes())
            entry=int.from_bytes(helper[9:11],'big')
            offset=0 if label=='bad text entry' else len(helper)-(1 if label=='CRC text entry' else 0)
            helper[entry+14:entry+16]=offset.to_bytes(2,'big')
            files['wbstate']=bytes(helper)
        elif label=='missing helper':files['wbstate']=None
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
            wanted=bytearray(b' '*1000)
            for r,c,text in expected:wanted[r*40+c:r*40+c+len(text)]=text
            assert captured[0][:1000]==wanted,(label,[(i,a,b) for i,(a,b) in enumerate(zip(captured[0],wanted)) if a!=b][:12])
            assert captured[0][1000:]==bytes([15])*1000,(label,'dialog colors')
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
        seen['line']=cpu.read(syms['textcharacters']+8*40+2,len(message)-1)
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
    assert state['cycles']==5,('stale submitting key dismissed the king text screen',state['cycles'])
    assert state['vmvariables'][19]==ord('p') and seen['graphics']==b'\x01'
    assert seen['parser']==b'abc\0','dialog key changed the command line'
    helper=bytearray((ROOT/'objs/wbstate').read_bytes());entry=int.from_bytes(helper[9:11],'big')
    helper[entry+16:entry+18]=bytes(2)
    error,output,state=exercise(d,{**files,'wbstate':bytes(helper)},
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
        files['/game/logDir']=bytes(directory);observed=[]
        def message(cpu,r,syms):observed.append(cpu.read(r['x'],512).split(b'\0')[0])
        error,output,state=exercise(d,files,arguments=b'/game 0\r',module='wbgame',
            base=0xa000,database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,
            capture=True,keyboard=b'\r',breakpoint_hooks={'GamePrintText':message})
        assert not error,(score,error)
        assert len(observed)==1 and phrase in observed[0],(score,observed)
        assert state['vmvariables'][97]==0 and state['vmvariables'][3]==score
    print('PASS: original KQ1 death-support score branches, message dismissal, nested caller resume and resource cleanup')


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
        helper=bytearray((ROOT/'objs/wbstate').read_bytes())
        entry=int.from_bytes(helper[9:11],'big')
        offset=0 if offset_name=='zero' else len(helper)-(1 if offset_name=='CRC' else 0)
        helper[entry+16:entry+18]=offset.to_bytes(2,'big')
        files['wbstate']=bytes(helper)
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,
            database=0x0000,window=0x8000,blocks=None,multiple=True,
            firstblock=0x10,capture=True,keyboard=b'\r',os_call_limit=20000)
        assert error==203,(offset_name,error)
    print('PASS: timed blocking messages, keyboard interruption, held/pause exclusions, raster wrap/coarse/max samples, foreground rebase and invalid wait-entry cleanup')


def check_screen_shakes(d):
    """Compare full owned bitmaps, including reserved dialog storage."""
    helper=symbols(ROOT/'objs/wbstate.map')
    original=bytes(1+((x*3+y*5)%16) for y in range(200) for x in range(320))+bytes([1])*12800+bytes(1+i%16 for i in range(5120))
    shifted=bytes([1])*1280+b''.join(bytes([1])*8+original[y*320:y*320+312] for y in range(200))+bytes([1])*(76800-65280)+original[76800:]
    def bitmap(cpu,syms,data=None):
        block=int.from_bytes(cpu.read(syms['firstblock'],2),'big');old=cpu.read(0xffac,1);result=bytearray()
        for page in range(10):
            cpu.write(0xffac,bytes([block+page]))
            if data is None:result.extend(cpu.read(0x8000,8192))
            else:cpu.write(0x8000,data[page*8192:(page+1)*8192])
        cpu.write(0xffac,old);return bytes(result)
    def fixture(count,picture=True,depth=0,audio=False):
        prefix=bytes([3,0,1,24,0,25,0,26]) if picture else b''
        if audio:prefix+=bytes([98,0,99,0,200])
        command=bytes([12,15,3,21,2,110,count])
        body=prefix+(bytes([22,2]) if depth else command)+bytes([3,240,73,134,1,0])
        def record(data):return b'\x12\x34\0'+len(data).to_bytes(2,'little')*2+data
        volume=record(len(body).to_bytes(2,'little')+body);picture_offset=len(volume);volume+=record(b'\xff')
        logs=[b'\xff'*3,bytes(3)]
        for number in range(2,depth+2):
            logs.append(len(volume).to_bytes(3,'big'))
            script=bytes([22,number+1,0]) if number<depth+1 else command+b'\0'
            volume+=record(len(script).to_bytes(2,'little')+script)
        sound=len(volume);volume+=record(bytes([28,63,0,240,255,0,240]))
        return {'/game/vol.0':volume,'/game/logDir':b''.join(logs),
                '/game/picDir':b'\xff'*3+picture_offset.to_bytes(3,'big'),'/game/sndDir':sound.to_bytes(3,'big')}
    for label,count,picture,raster,depth,abort in [
        ('no bitmap',1,False,False,0,False),('zero',0,True,False,0,False),
        ('one fallback',1,True,False,0,False),('two raster',2,True,True,0,False),
        ('deep audio and long directory',1,True,True,16,False),
        ('maximum repeat count interrupted',255,True,True,0,True)]:
        print('Checking screen shake:',label,flush=True);seen=[]
        def seed(cpu,r,syms):bitmap(cpu,syms,original)
        def inspect(cpu,r,syms):
            assert bitmap(cpu,syms)==shifted,(label,'shifted pixels or reserved storage changed')
            assert int.from_bytes(cpu.read(syms['shakecycles'],2),'big')==count*8
            seen.append(True)
            if abort:cpu.write(syms['aborted'],b'\x01')
        def restored(cpu,r,syms):assert bitmap(cpu,syms)==original,(label,'bitmap not restored')
        hooks={'GameShakeCommand':seed,'GameQuitCommand':restored} if picture else {}
        if count and picture:hooks[0x6000+helper['AuxShakeWait']]=inspect
        files=fixture(count,picture,depth,bool(depth));arguments=b'/game 1\r'
        if depth:
            directory=b'/'+b'x'*126;files={directory.decode()+name[5:]:data for name,data in files.items()};arguments=directory+b' 1\r'
        error,output,state=exercise(d,files,arguments=arguments,module='wbgame',base=0xa000,
            database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
            os_call_limit=60000,breakpoint_hooks=hooks,sol={'start':250,'step':1} if raster else None,
            psg={'version':4} if depth else None)
        assert error==(228 if abort else 0),(label,error)
        assert state['vmvariables'][240]==(0 if abort else 73)
        assert state['gamefont']==(ROOT/'objs/wbfont').read_bytes(),(label,'font overwritten')
        if not depth:assert state['vmflags'][15]==1 and state['vmvariables'][21]==2
        if count and picture:assert seen
    original_helper=(ROOT/'objs/wbstate').read_bytes();entry=int.from_bytes(original_helper[9:11],'big')
    for offset in (0,len(original_helper),len(original_helper)-1):
        helper_data=bytearray(original_helper);helper_data[entry+28:entry+30]=offset.to_bytes(2,'big')
        files=fixture(1);files['wbstate']=bytes(helper_data)
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,database=0,
            window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,os_call_limit=60000)
        assert error==203,(offset,error)
    print('PASS: exact shifted/restored pixels, reserved dialog bytes, repeats, raster/fallback waits, zero/no-screen cases, deep audio/long-path safety and interrupted/error cleanup')


def check_object_previews(d):
    """Check item pixels during dismissal and exact restoration afterwards."""
    default=bytearray([0,0,1,0,0,7,0,1,3,0,4,3,31,0x12,0xf1,0x21,0,0x31,0x43,0,0x51,0])
    default[3:5]=len(default).to_bytes(2,'little');default+=b'A fine treasure.\0'
    def fixture(command,view=default,depth=0,audio=False):
        start=bytes([3,0,1,24,0,25,0,26])
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
                '/game/viewDir':offsets[2].to_bytes(3,'big'),'/game/sndDir':sound.to_bytes(3,'big')}
    baseline=None
    cases=[('baseline',b'',0,False),('literal',bytes([129,0]),0,False),
           ('variable',bytes([3,200,0,162,200]),0,False),
           ('already cached',bytes([30,0,129,0]),0,False),
           ('held/timer flags',bytes([12,15,3,21,2,129,0]),0,False),
           ('depth 16 and long directory',bytes([129,0]),16,True),
           ('moving-object baseline',bytes([33,0,41,0,0,37,0,20,30,54,0,15,35,0,37,0,30,40,26]),0,False),
           ('moving-object preview',bytes([33,0,41,0,0,37,0,20,30,54,0,15,35,0,129,0,37,0,30,40,26]),0,False),
           ('text-screen baseline',bytes([106]),0,False),
           ('text-screen preview',bytes([106,129,0]),0,False),
           ('text-screen held/timer flags',bytes([106,12,15,3,21,2,129,0]),0,False)]
    for label,command,depth,audio in cases:
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
        files=fixture(command,depth=depth,audio=audio);arguments=b'/game 1\r'
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
        assert state['gamefont']==(ROOT/'objs/wbfont').read_bytes(),(label,'font overwritten')
        if 'baseline' in label:baseline=frame
        else:
            assert frame==baseline,(label,'scene not restored')
            assert modal['text'][322:338]==b'A fine treasure.',(label,modal['text'][322:350])
            assert modal['frame'][173*320+156:173*320+164]==bytes([2,2,2,2,16,16,3,3]),(label,'preview pixels missing')
        if 'held/timer flags' in label:assert state['vmflags'][15]==1 and state['vmvariables'][21]==2
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
    original=(ROOT/'objs/wbstate').read_bytes();entry=int.from_bytes(original[9:11],'big')
    for offset in (0,len(original),len(original)-1):
        helper=bytearray(original);helper[entry+26:entry+28]=offset.to_bytes(2,'big')
        files=fixture(bytes([129,0]));files['wbstate']=bytes(helper)
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,database=0,
            window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,
            keyboard=b'\r',os_call_limit=60000)
        assert error==203,(offset,error)
    print('PASS: literal/variable item pixels and descriptions, exact restoration, preserved cache/print flags, deep audio/long-path safety and bounded malformed-resource cleanup')


def check_interpreter_information(d):
    """A menu version request must dismiss, restore state and resume its caller."""
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
        assert b'Adventure Game Interpreter' in modal['text'],(label,modal)
        assert b'Wild Bits NitrOS-9 engine' in modal['text'],(label,modal)
        assert state['vmflags'][15]==(1 if 15 in prefix else 0),(label,'print flag changed')
        assert state['vmvariables'][21]==(2 if 21 in prefix else 0),(label,'print timer changed')
    print('PASS: interpreter information, blocking dismissal, preserved flags/timer and deep caller resume')


def check_cold_menus(d):
    """Cold navigation must retain labels, selection policy and ownership."""
    def fixture(command,picture=True):
        script=(bytes([3,0,1,24,0,25,0,26]) if picture else b'')+command+bytes([3,240,73,134,1,0])
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
           ('disabled then next',bytes([156,1,157,2,1,157,2,255,160,1,158,161]),b'\r\n\r',255,0),
           ('paged',bytes([156,1])+b''.join(bytes([157,2,n]) for n in range(32))+bytes([158,161]),b'\n'*22+b'\r',22,0),
           ('unsubmitted',bytes([161]),b'\r',None,203)]
    for label,command,keyboard,controller,expected in cases:
        print('Checking cold menu:',label,flush=True)
        error,output,state=exercise(d,fixture(command,picture=label!='before picture'),module='wbgame',base=0xa000,
            database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,
            capture=True,keyboard=keyboard,os_call_limit=60000)
        assert error==expected,(label,error)
        if not error:
            assert state['vmvariables'][240]==73,(label,'caller did not resume')
            wanted=bytearray(32)
            if controller is not None:wanted[controller//8]=1<<(controller%8)
            assert state['vmcontrollers']==wanted,(label,state['vmcontrollers'],wanted)
        assert state['gamefont']==(ROOT/'objs/wbfont').read_bytes(),(label,'font overwritten')
    original=(ROOT/'objs/wbstate').read_bytes();entry=int.from_bytes(original[9:11],'big')
    for offset in (0,len(original),len(original)-1):
        files=fixture(bytes([156,1,157,2,1,158,161]));helper=bytearray(original)
        helper[entry+30:entry+32]=offset.to_bytes(2,'big');files['wbstate']=bytes(helper)
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
        assert state['gamefont']==(ROOT/'objs/wbfont').read_bytes(),(label,'font overwritten')
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
            state[syms['gamefont']:syms['gamefont']+1024]=(root/'wbfont').read_bytes()
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
        assert state['gamefont']==(root/'wbfont').read_bytes(),(label,'font overwritten')
    print('PASS: exact CoCo RGB conversion, owned palette writes, toggle back, early selection, unchanged picture indices and driver-error cleanup')


def check_monitor_instances(d):
    """The shared cold configuration body keeps each palette preference private."""
    root=ROOT/'objs';syms=symbols(root/'wbgame.map');hs=symbols(root/'wbstate.map')
    base=0xa000;helperbase=0x6000;code=(root/'wbgame').read_bytes();helper=(root/'wbstate').read_bytes()
    d.write(base,code);d.write(helperbase,helper)
    saved=d.read(0xffa8,3);banks={0:bytes([0x20,0x21,0x22]),1:bytes([0x23,0x24,0x25])};expected={}
    stop=helperbase+hs['ScreenReturn'];callback=base+syms['ScreenCallbacks']
    def select(owner):d.write(0xffa8,banks[owner])
    try:
        d.breakpoint(stop)
        for owner in banks:
            select(owner);state=bytearray(syms['size']);state[syms['vmopcode']]=140
            state[syms['monitorprofile']]=owner;state[syms['vmvariables']+250]=40+owner
            state[syms['gamefont']:syms['gamefont']+1024]=(root/'wbfont').read_bytes()
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
           ('configure',bytes([111,4,22,24]),0,{'vmpicturetop':4,'vminputrow':22,'vmstatusrow':24}),
           ('status on',bytes([112]),0,{'vmstatusenabled':1}),
           ('status off',bytes([112,113]),0,{'vmstatusenabled':0}),
           ('input off',bytes([119]),0,{'vminputenabled':0}),
           ('input on',bytes([119,120]),0,{'vminputenabled':1}),
           ('bad colors',bytes([109,16,0]),187,{}),
           ('bad picture row',bytes([111,5,23,0]),187,{}),
           ('bad input row',bytes([111,1,25,0]),187,{}),
           ('bad status row',bytes([111,1,23,25]),187,{}),
           ('bad cursor message',bytes([108,2]),203,{})]
    original=(ROOT/'objs/wbstate').read_bytes();entry=int.from_bytes(original[9:11],'big')
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
        files['wbstate']=bytes(helper)
        script=bytes([112,134,1,0]);logic=len(script).to_bytes(2,'little')+script
        files['/game/vol.0']=b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,database=0,window=0x8000,blocks=None,multiple=True,firstblock=0x10,capture=True,os_call_limit=20000)
        assert error==203,(offset,error)
    print('PASS: immutable screen configuration, cursor message callback, bounds and invalid-entry cleanup')


def check_cold_prefix_bounds(d):
    """Bound writable copies independently of the larger linked code image."""
    original=(ROOT/'objs/wbstate').read_bytes()
    entry=int.from_bytes(original[9:11],'big')
    script=bytes([154,0,0,24,39,0,134,1,0])
    logic=len(script).to_bytes(2,'little')+script
    cases=[('valid',None,None),
           ('short prefix',entry+18,entry+24),
           ('incomplete current metadata',entry+18,entry+34),
           ('oversized prefix',entry+18,4097),
           ('prefix beyond module',2,int.from_bytes(original[entry+18:entry+20],'big')-1),
           ('oversized module',2,8193),
           ('zero rectangle entry',entry+20,0),
           ('oversized rectangle entry',entry+20,len(original)),
           ('CRC rectangle entry',entry+20,len(original)-1)]
    for label,offset,value in cases:
        print('Checking cold prefix:',label,flush=True)
        helper=bytearray(original)
        if offset is not None:helper[offset:offset+2]=value.to_bytes(2,'big')
        files={'wbstate':bytes(helper),'/game/logDir':b'\xff'*3+bytes(3),
               '/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic}
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,
            database=0x0000,window=0x8000,blocks=None,multiple=True,
            firstblock=0x10,capture=True,os_call_limit=20000)
        assert error==(0 if offset is None else 203),(label,error)
    print('PASS: writable-prefix bounds, one-window module bounds and cold rectangle entry validation/cleanup')


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


def check_restarts(d):
    cases=[('confirmation',False,b'\r',0,False),
           ('cancellation',False,b'x',0,False),
           ('escape cancellation',False,b'\x1b',0,False),
           ('automatic at depth 16',True,b'',15,False),
           ('manual at depth 16',False,b'\r',15,False),
           ('long path at depth 16',False,b'\r',15,True)]
    for label,automatic,key,depth,long_path in cases:
        print('Checking restart:',label,flush=True)
        files=restart_fixture(automatic,depth);arguments=b'/game 1\r'
        if long_path:
            directory=b'/'+b'x'*126
            files={directory.decode()+name[5:]:data for name,data in files.items()}
            arguments=directory+b' 1\r'
        error,output,state=exercise(d,files,arguments=arguments,module='wbgame',
            base=0xa000,database=0x0000,window=0x8000,blocks=None,multiple=True,
            firstblock=0x10,capture=True,keyboard=key,psg={'version':4},
            sol={'start':250,'step':1},os_call_limit=20000)
        assert not error,(label,error,output)
        assert state['gamefont']==(ROOT/'objs/wbfont').read_bytes(),(label,'font changed')
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
        helper=bytearray((ROOT/'objs/wbstate').read_bytes());entry=int.from_bytes(helper[9:11],'big')
        offset=0 if name=='zero' else len(helper)-(1 if name=='CRC' else 0)
        helper[entry+22:entry+24]=offset.to_bytes(2,'big')
        files=restart_fixture();files['wbstate']=bytes(helper)
        error,output,state=exercise(d,files,module='wbgame',base=0xa000,
            database=0x0000,window=0x8000,blocks=None,multiple=True,
            firstblock=0x10,capture=True,keyboard=b'\r',os_call_limit=20000)
        assert error==203,(name,error)
    print('PASS: restart confirmation/cancellation/automatic mode, 16-call unwind, long-path private-code/font protection, logical reset, active sound/clock cleanup and invalid entries')


def main():
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
        d, emulator = start_cpu(idle_rom(Path(temp) / 'idle.rom'), timeout=7200)
        try:
            d.write(0xffdf, b'\0')
            d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01')
            d.write(0xffa8, bytes(range(8)))
            check_compatibility_noops(d)
            check_positioned_messages(d)
            check_text_screen_key_wait(d)
            check_original_help(d)
            check_original_death_messages(d)
            check_original_pickup_puzzles(d)
            check_timed_messages(d)
            check_screen_shakes(d)
            check_object_previews(d)
            check_interpreter_information(d)
            check_cold_menus(d)
            check_room_controls(d)
            check_room_input_sound(d)
            check_joystick_input(d)
            check_joystick_instances(d)
            check_monitor_profiles(d)
            check_monitor_instances(d)
            check_screen_backend(d)
            check_cold_prefix_bounds(d)
            check_restarts(d)
            check_bounded_said(d)
            check_state_transfers(d)
            check_state_validation(d)
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
            script = bytes([109,14,1,103,3,39,1,26,134,1,0])
            logic = len(script).to_bytes(2, 'little') + script
            logic += bytes([1]) + (4+len(message)).to_bytes(2,'little') + bytes([4,0]) + encrypted
            files = {'/game/logDir': b'\xff' * 3 + bytes(3),
                '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2,'little') * 2 + logic}
            error, frame = exercise(d, files, module='wbgame', base=0xa000,
                database=0x0000, window=0x8000, blocks=None, multiple=True,
                firstblock=0x10, frame_capture=True)
            assert not error, error
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
            assert frame == expected_frame, 'native text glyphs/colors/wrapping differ or were erased by show.pic'
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
                          (24,39,24,39,15), (3,38,4,39,1)]
            rectangles += [(25,0,25,0,0), (0,40,0,40,0),
                           (4,0,3,1,0), (3,2,4,1,0)]
            for top,left,bottom,right,color in rectangles:
                invalid = top > bottom or left > right or bottom >= 25 or right >= 40
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
                    for pixelrow in range(top*8,(bottom+1)*8):
                        start = pixelrow*320 + left*8
                        cleared[start:pixelrow*320+(right+1)*8] = bytes([16 if color else 1]) * ((right-left+1)*8)
                assert frame == cleared, ('clear.text.rect pixels', (top,left,bottom,right,color))
            # Text/graphics mode preserves the combined game picture, clears
            # text beyond the picture area on return, and remains stable over
            # multiple logic cycles with input disabled.
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
                    if mode in ('graphics','discard'):
                        wanted = bytearray([1])*76800
                        for row in range(168):
                            pixels = bytes(value for pixel in expected[row*160:(row+1)*160]
                                           for value in [(pixel&15)+1]*2)
                            wanted[(row+8)*320:(row+9)*320] = pixels
                    else:
                        wanted = bytearray([background+1])*64000 + bytearray([1])*12800
                        for column, character in enumerate(message[:-1]):
                            for row in range(8):
                                bits = font[character*8+row]
                                for pixel in range(8):
                                    wanted[(24*8+row)*320+column*8+pixel] = (
                                        15 if bits&(128>>pixel) else background+1)
                    if mode == 'rectangle':
                        for row in range(192,200):
                            wanted[row*320:row*320+8] = bytes([1])*8
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
                failed_files = {**files, 'wbfont': bad_font}
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
