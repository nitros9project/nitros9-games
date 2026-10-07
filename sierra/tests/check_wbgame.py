#!/usr/bin/env python3
"""Execute native AGI picture commands through the integrated game owner."""
from pathlib import Path
import subprocess
import tempfile
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
            cpu.write(0x1000+syms['parsercount'],bytes([parsed]))
            cpu.write(0x1000+syms['parserids'],b'\0\x7b'*parsed)
        error,output,state=exercise(d,files,arguments=b'/game 0\r',module='wbgame',
            base=0xa000,database=0x1000,window=0x8000,blocks=None,multiple=True,
            firstblock=0x10,capture=True,breakpoint_hooks={'ParserSaid':parsed_words})
        assert not error and not output,(len(words),error,output)
        assert bool(state['vmflags'][200])==expected,(len(words),parsed,expected)
        if replay is None:replay=state['replaybuffer']
        assert state['replaybuffer']==replay,'said operands overwrote the next private buffer'
    script=bytes([255,14,127])+b'\x7b\0'*21+bytes([255,0,0,134,1,0])
    payload=len(script).to_bytes(2,'little')+script
    files={'/game/logDir':bytes(3),'/game/vol.0':b'\x12\x34\0'+len(payload).to_bytes(2,'little')*2+payload}
    error,output=exercise(d,files,arguments=b'/game 0\r',module='wbgame',base=0xa000,
        database=0x1000,window=0x8000,blocks=None,multiple=True,firstblock=0x10)
    assert error and not output,'truncated discarded predicate tail was accepted'
    print('PASS: bounded said storage preserves 20 words plus a following wildcard, accepts complete 127-word predicates, rejects truncated tails and preserves the next private buffer')

def check_compatibility_noops(d):
    """CoCo's explicit zero-operand no-ops must not abort native scripts."""
    script=bytes([3,240,73,12,221,127,163,164,173,176,178,181,4,241,240,134,1,0])
    logic=len(script).to_bytes(2,'little')+script
    files={'/game/logDir':b'\xff'*3+bytes(3),
           '/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic}
    error,output,state=exercise(d,files,module='wbgame',base=0xa000,
        database=0x1000,window=0x8000,blocks=None,multiple=True,
        firstblock=0x10,capture=True)
    assert not error and not output,(error,output)
    assert state['vmvariables'][240:242]==bytes([73,73])
    assert state['vmflags'][221]==1
    print('PASS: CoCo-compatible zero-operand no-ops continue native scripts and preserve variables/flags')


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
            check_bounded_said(d)
            check_state_transfers(d)
            check_state_validation(d)
            error, frame = exercise(d, files, module='wbgame', base=0xa000,
                database=0x1000, window=0x8000, blocks=None, multiple=True,
                firstblock=0x10, frame_capture=True)
            assert not error, error
            failed, unused = exercise(d, files, module='wbgame', base=0xa000,
                database=0x1000, window=0x8000, blocks=None, multiple=True,
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
                    base=0xa000,database=0x1000,window=0x8000,blocks=None,
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
                    database=0x1000, window=0x8000, blocks=None, multiple=True,
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
                    database=0x1000,window=0x8000,blocks=None,multiple=True,
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
                    database=0x1000, window=0x8000, blocks=None, multiple=True,
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
                database=0x1000, window=0x8000, blocks=None, multiple=True,
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
                    database=0x1000, window=0x8000, blocks=None, multiple=True,
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
                    database=0x1000, window=0x8000, blocks=None, multiple=True,
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
                        base=0xa000,database=0x1000,window=0x8000,blocks=None,
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
                    database=0x1000, window=0x8000, blocks=None, multiple=True,
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
                database=0x1000, window=0x8000, blocks=None, multiple=True,
                firstblock=0x10, capture=True, frame_capture=True, keyboard=b'\n'*22 + b'\r', os_call_limit=100000)
            assert not error and state['vmvariables'][25] == 22, 'inventory scrolling lost item identity'
            assert output == bytes([1])*76800, 'scrolled inventory left an overlay'
            for bad_font in (b'', bytes(1023), bytes(1025)):
                failed_files = {**files, 'wbfont': bad_font}
                error, output, state = exercise(d, failed_files, module='wbgame', base=0xa000,
                    database=0x1000, window=0x8000, blocks=None, multiple=True,
                    firstblock=0x10, capture=True)
                assert error, 'malformed font accepted'
            for malformed in (b'bad', encrypted[:10], encrypted + bytes(4096)):
                files['/game/object'] = malformed
                error, output, state = exercise(d, files, module='wbgame', base=0xa000,
                    database=0x1000, window=0x8000, blocks=None, multiple=True,
                    firstblock=0x10, capture=True)
                assert error, 'malformed object file accepted'
            for sound_enabled in (False, True):
                script = bytes(([12,9] if sound_enabled else [13,9]) + [99,0,200,100,134,1,0])
                logic = len(script).to_bytes(2,'little') + script
                files = {'/game/logDir': b'\xff' * 3 + bytes(3),
                    '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2,'little') * 2 + logic}
                error, output, state = exercise(d, files, module='wbgame', base=0xa000,
                    database=0x1000, window=0x8000, blocks=None, multiple=True,
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
                database=0x1000, window=0x8000, blocks=None, multiple=True,
                firstblock=0x10, capture=True, keyboard=b'abcdefgh')
            assert not error and not output, (error, output)
            assert state['vmvariables'][220:228] == bytes([1]) * 8, 'controller bits aliased or survived their cycle'
            assert state['vmflags'][220:228] == bytes([1]) * 8, 'high controller bit was lost'
            script = bytes([121,ord('q'),0,7,1,250,255,12,7,255,2,0,134,1,0])
            logic = len(script).to_bytes(2, 'little') + script
            files = {'/game/logDir': b'\xff' * 3 + bytes(3),
                '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2, 'little') * 2 + logic}
            error, output, state = exercise(d, files, module='wbgame', base=0xa000,
                database=0x1000, window=0x8000, blocks=None, multiple=True,
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
