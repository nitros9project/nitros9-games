#!/usr/bin/env python3
"""Run native AGI sound through the private adapter and adversarial OS services."""
from pathlib import Path
import tempfile
from check_lzw import expand
from check_logic_executor import compile_module
from check_wbres import exercise, idle_rom, start_cpu, symbols
ROOT=Path(__file__).resolve().parents[1]


def fixture(sound, requests=1, modal=False, discard_stub=False, sound_id=0,
            stop_sound=False, load_sound_count=0):
    # Start once, then wait for the completion flag before quitting.
    body=bytes([12,201])+bytes([98,sound_id])*load_sound_count+bytes([99,sound_id,200])*requests
    if discard_stub:body+=bytes([175,255])
    if stop_sound:body+=bytes([100])
    if modal:body+=bytes([136])
    script=bytes([255,253,7,201,255,len(body),0])+body
    script+=bytes([255,7,200,255,2,0,134,1,0])
    logic=len(script).to_bytes(2,'little')+script
    def record(payload):
        size=len(payload).to_bytes(2,'little')
        return b'\x12\x34\0'+size*2+payload
    offset=7+len(logic)
    sound_directory=bytearray(b'\xff\xff\xff'*(sound_id+1))
    sound_directory[sound_id*3:sound_id*3+3]=offset.to_bytes(3,'big')
    return {'/game/logDir':b'\xff'*3+bytes(3),
            '/game/sndDir':bytes(sound_directory),
            '/game/vol.0':record(logic)+record(sound)}


def check_coco_load_sound(debugger, temp, sound):
    """Run the real CoCo public loader against the same plain sound record."""
    coco,syms=compile_module(ROOT/'objs/mnln.asm',temp/'mnln',listing=True)
    volume=b'\x12\x34\0'+len(sound).to_bytes(2,'little')*2+sound
    volume_path='/game/vol.0'
    calls={'LoadSoundRet':0}
    def return_from_probe(cpu,regs,syms):
        ret=int.from_bytes(cpu.read(regs['s'],2),'big')
        cpu.regs(pc=ret,s=regs['s']+2)
        return True
    def coordinate(cpu,regs,syms):
        ret=int.from_bytes(cpu.read(regs['s'],2),'big')
        cpu.regs(pc=ret,s=regs['s']+2,a=0,b=0)
        return True
    def load_sound_return(cpu,regs,ss):
        calls['LoadSoundRet']+=1
        if calls['LoadSoundRet']==1:
            # Run the same public command again from its next operand. The
            # real linked-list lookup must hit without another volume read.
            cpu.write(regs['s']+5,(0x8000+syms['cmd_load_sound']).to_bytes(2,'big'))
        return True
    hooks={name:return_from_probe for name in
           ('PushScript','ClearBothRanges','SwapObjRanges','SetLogicPage')}
    hooks['CalcPriCoord']=coordinate
    hooks['LoadSoundRet']=load_sound_return
    initial=[(0x7000,b'\0\0\0'),(0x004f,b'\x30\0'),(0x004b,b'\x30\0'),
        (0x0055,b'\x50\0'),(0x000a,b'\0\0'),
        (0x0531,b'\x03'+b'\xff'*15),(0x6000,b'\0\0ARGS'),
        (0x8000+syms['SndDirPtr'],b'\x70\0'),
        (0x8000+syms['SndDirPage'],b'\0\0')]
    error,output,state=exercise(debugger,{volume_path:volume},module='mnln',
        module_root=temp,base=0x8000,database=0x5000,
        entry_symbol='cmd_load_sound',stop_address=0x7e00,
        initial_stack=b'\x7e\0STACK',initial_dp=0,initial_memory=initial,
        initial_regs={'y':0x6000},preopened_paths=((3,volume_path),),
        allow_open_paths=True,breakpoint_hooks=hooks,
        read_limit=len(volume),capture=True,os_call_limit=10000)
    assert not error and not output,(error,output)
    assert state['registers']['y']==0x6002 and debugger.read(0x6002,4)==b'ARGS'
    assert calls['LoadSoundRet']==2,calls
    assert state['file_reads']=={volume_path:2},state['file_reads']
    head=int.from_bytes(debugger.read(0x8000+syms['SoundScratch9'],2),'big')
    assert head==0x5000,hex(head)
    node=debugger.read(head,9)
    assert node[:3]==b'\0\0\0' and node[2]==0,node
    resource=int.from_bytes(node[3:5],'big')
    assert debugger.read(resource,len(sound))==sound,(hex(resource),debugger.read(resource,len(sound)),sound)
    assert debugger.read(state['registers']['s'],5)==b'STACK'
    print('PASS: actual CoCo cmd_load_sound loads the sound record, advances two public operands, and a duplicate request reuses the one node without extra volume reads; caller stack, cache link and payload match',flush=True)


def check_coco_sound_command(debugger,temp,sound):
    """Run cmd_sound and the real CoCo DAC player through flag/page/timer flow."""
    _,syms=compile_module(ROOT/'objs/mnln.asm',temp/'mnln',listing=True)
    for base in (0x8000,0x9000):
        sound_node=0x6100
        def return_from_probe(cpu,regs,ss):
            ret=int.from_bytes(cpu.read(regs['s'],2),'big')
            cpu.regs(pc=ret,s=regs['s']+2)
            return True
        head=base+syms['SoundScratch9']
        initial=[(head,sound_node.to_bytes(2,'big')),
                 (sound_node,b'\0\0\0\0\0\0\0\0\0'),
                 (0x6100+2,b'\0'),(0x6100+3,b'\x62\x00'),
                 (0x6100+5,b'\0\0'),(0x6100+7,b'\0\0'),
                 (0x01af,b'\x40'),(0x0172,b'\0'),
                 (0x6200,sound),(0x6300,b'\0\xc8')]
        initial[3]=(0x6100+3,b'\x62\x00')
        error,output,state=exercise(debugger,{},module='mnln',module_root=temp,
            base=base,database=0x3000,entry_symbol='cmd_sound',
            stop_address=0x7e00,initial_stack=b'\x7e\0STACK',
            initial_memory=initial,initial_regs={'y':0x6300},capture=True,
            breakpoint_hooks={'SetLogicPage':return_from_probe},os_call_limit=1000)
        assert not error and not output,(base,error,output)
        flag_byte=debugger.read(0x01ae+(200//8),1)[0]
        assert flag_byte & (1<<(200%8)),(base,flag_byte)
        assert state['registers']['y']==0x6302
        assert debugger.read(state['registers']['s'],5)==b'STACK'
    print('PASS: actual CoCo cmd_sound and PlaySound consume the resident note stream, set completion flag 200 and restore caller stack at two code bases',flush=True)


def original_sound_events(number):
    """Decode one bundled KQ4 CoCo sound into its four-byte note events."""
    game=ROOT/'kingsquest4'
    directory=(game/'sndDir').read_bytes()
    entry=int.from_bytes(directory[number*3:number*3+3],'big')
    if entry in (0,0xffffff):
        raise AssertionError(('missing original KQ4 sound',number,entry))
    volume_number,offset=entry>>20,entry&0xfffff
    volume=(game/f'vol.{volume_number}').read_bytes()
    header=volume[offset:offset+7]
    assert header[:2]==b'\x12\x34' and len(header)==7,(number,header)
    decoded=int.from_bytes(header[3:5],'little')
    stored=int.from_bytes(header[5:7],'little')
    packed=volume[offset+7:offset+7+stored]
    assert len(packed)==stored,(number,'truncated resource')
    payload=packed if decoded==stored else expand(packed)
    assert len(payload)==decoded,(number,'decoded resource length')
    events=[]
    cursor=0
    while cursor<len(payload) and payload[cursor]!=0xff:
        assert cursor+4<=len(payload),(number,'truncated note',cursor)
        tone,amplitude=payload[cursor:cursor+2]
        duration=int.from_bytes(payload[cursor+2:cursor+4],'big')
        assert tone<60 and amplitude<=63,(number,'invalid CoCo note',cursor,tone,amplitude)
        events.append((tone,amplitude,duration))
        cursor+=4
    assert cursor+3==len(payload) and payload[cursor:cursor+3]==b'\xff\x00\x30',(
        number,'CoCo sound terminator/elapsed word',cursor,payload[cursor:])
    return payload,events


def main():
    sound=bytes([28,63,0,2,29,0,0,3,255,0,48])
    helper=(ROOT/'objs/sierraui').read_bytes()
    stale=bytearray(helper);entry=int.from_bytes(stale[9:11],'big');stale[entry+8]^=1
    with tempfile.TemporaryDirectory(prefix='sierra-native-audio-') as name:
        d,e=start_cpu(idle_rom(Path(name)/'idle.rom'),timeout=1800)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01')
            d.write(0xffa8,bytes(range(8)))
            check_coco_load_sound(d,Path(name),sound)
            check_coco_sound_command(d,Path(name),sound)
            # Font failure precedes GameInitialize. A dirty path byte must
            # already be cleared before exit attempts any sound cleanup.
            def dirty_audio_path(debug,registers,syms):
                debug.write(0x0000+syms['soundpath'],b'\xa5')
            print('Checking native audio: early font failure with dirty sound-path state',flush=True)
            error,output,state=exercise(d,{'sierrafont':b''},module='wbgame',base=0xa000,
                database=0x0000,window=0x8000,blocks=None,multiple=True,
                firstblock=0x10,capture=True,breakpoint_hooks={'start':dirty_audio_path})
            assert error==211,error
            for label,files,driver in (
                ('converted notes',{**fixture(sound),'sierraui':helper},{}),
                ('explicit load.sound then play',
                 {**fixture(sound,load_sound_count=2),'sierraui':helper},{}),
                ('CoCo discard-sound stub during playback',{**fixture(sound,discard_stub=True),'sierraui':helper},{}),
                ('CoCo stop.sound no-op during playback',{**fixture(sound,stop_sound=True),'sierraui':helper},{}),
                ('missing helper',{**fixture(sound),'sierraui':None},None),
                ('missing driver',{**fixture(sound),'sierraui':helper},None),
                ('older driver',{**fixture(sound),'sierraui':helper},{'version':3}),
                ('stale helper',{**fixture(sound),'sierraui':bytes(stale)},{}),
                ('invalid amplitude',{**fixture(bytes([28,64,0,2,255,0,48])),'sierraui':helper},{}),
                ('busy driver',{**fixture(sound),'sierraui':helper},{'busy':True}),
                ('busy then available',{**fixture(sound,2),'sierraui':helper},{'busy_attempts':1}),
                ('truncated note',{**fixture(sound[:-3]),'sierraui':helper},{})):
                print('Checking native audio:',label,flush=True)
                cache_at_play=[]
                hooks={}
                if label=='explicit load.sound then play':
                    gs=symbols(ROOT/'objs/wbgame.map')
                    def capture_sound_cache(debug,registers,syms):
                        cache=debug.read(gs['vmcache'],32*12)
                        cache_at_play.append([cache[i:i+12] for i in range(0,len(cache),12)])
                    hooks={'GameSoundCommand':capture_sound_cache}
                error,output,state=exercise(d,files,module='wbgame',base=0xa000,
                    database=0x0000,window=0x8000,blocks=None,multiple=True,
                    firstblock=0x10,capture=True,psg=driver,os_call_limit=3000,
                    breakpoint_hooks=hooks)
                assert not error and not output,(label,error,output)
                assert state['vmflags'][200]==1,(label,'completion flag')
                if label in ('converted notes','busy then available','CoCo discard-sound stub during playback',
                             'CoCo stop.sound no-op during playback',
                             'explicit load.sound then play'):
                    expected=[bytes([128,28,63,0,2,0])]
                    expected += [bytes([ch,255,255,0,0,0]) for ch in range(1,4)]
                    expected += [bytes([128,29,0,0,3,0]),bytes([0,255,255,0,0,0])]
                    assert state['audio_packets']==expected,state['audio_packets']
                    assert state['vmflags'][9]==1
                    if label=='converted notes':
                        print('PASS: loaded Wild Bits opcode 99 emits the complete note/end stream and sets its completion flag after playback',flush=True)
                    if label=='explicit load.sound then play':
                        assert len(cache_at_play)==1,cache_at_play
                        sound_entries=[entry for entry in cache_at_play[0]
                                       if entry[1] and entry[0]==0 and entry[5]==3]
                        assert len(sound_entries)==1,sound_entries
                        assert int.from_bytes(sound_entries[0][6:8],'big')==len(sound),sound_entries[0]
                        # Two reads belong to the logic resource; the sound's
                        # header and payload are read only once despite the
                        # two explicit load.sound operands.
                        assert state['file_reads'].get('/game/vol.0')==4,state['file_reads']
                        print('PASS: Wild Bits opcode 98 loads the typed sound resource once across two requests, publishes one kind-3 cache entry, and playback matches the CoCo note packets',flush=True)
                elif label=='busy driver':
                    assert not state['audio_packets'] and state['vmflags'][9]==1
                elif label not in ('truncated note','invalid amplitude'):
                    assert not state['audio_packets']
            # KQ4 intro sounds 2/100/101/102 are original CoCo-format
            # resources. The CoCo player consumes each four-byte event
            # directly; compare the real Wild Bits adapter's emitted packets
            # event-for-event, including the big-endian duration and the end
            # marker. This covers the asset path used by the intro, not just a
            # synthetic two-note resource.
            intro_note_count=0
            for sound_id in (2,100,101,102):
                payload,events=original_sound_events(sound_id)
                print(f'Checking original KQ4 sound {sound_id}: {len(events)} note events',flush=True)
                error,output,state=exercise(d,{
                    **fixture(payload,sound_id=sound_id),'sierraui':helper},
                    module='wbgame',base=0xa000,database=0x0000,
                    window=0x8000,blocks=None,multiple=True,
                    firstblock=0x10,capture=True,psg={},os_call_limit=12000)
                note_packets=[bytes([0x80,tone,amplitude])+
                              duration.to_bytes(2,'big')+b'\0'
                              for tone,amplitude,duration in events]
                # CoCo has one DAC voice. Wild Bits immediately closes the
                # three unused PSG channels before continuing channel zero.
                expected=note_packets[:1]
                expected.extend(bytes([channel,0xff,0xff,0,0,0])
                                for channel in range(1,4))
                expected.extend(note_packets[1:])
                expected.append(bytes([0,0xff,0xff,0,0,0]))
                assert not error and not output,(sound_id,error,output)
                assert state['vmflags'][200]==1,(sound_id,'completion flag')
                assert state['audio_packets']==expected,(
                    sound_id,len(events),len(state['audio_packets']),
                    next(((i,a,b) for i,(a,b) in enumerate(zip(
                        state['audio_packets'],expected)) if a!=b),None))
                intro_note_count+=len(events)
            print('PASS: original KQ4 CoCo sound resources 2/100/101/102 match every native tone, amplitude, duration, event order and end packet',intro_note_count,flush=True)
            # More notes than the driver can hold must finish while Pause
            # remains open, without a normal interpreter cycle refilling them.
            long_sound=bytes([28,63,0,1])*14+bytes([255,0,1])
            completed=[]
            def modal_restoring(debug,registers,syms):
                completed.append(debug.read(0x0000+syms['vmflags']+200,1)==b'\x01')
            print('Checking native audio: bounded queue refill during a long modal wait',flush=True)
            error,output,state=exercise(d,{**fixture(long_sound,modal=True),'sierraui':helper},
                module='wbgame',base=0xa000,database=0x0000,window=0x8000,
                blocks=None,multiple=True,firstblock=0x10,capture=True,
                psg={'queue_capacity':8},keyboard_by_cycle={25:(b'\r',0)},
                breakpoint_hooks={'GamePrintRestore':modal_restoring},os_call_limit=8000)
            assert not error and not output and completed==[True],(error,output,completed)
            assert len(state['audio_packets'])==18,state['audio_packets']
            # Exercise the adapter at the deepest supported AGI call depth,
            # with a maximum-length directory consuming parameter-stack space.
            directory=b'/'+b'a'*126
            payloads=[len(bytes([22,n+2,0])).to_bytes(2,'little')+bytes([22,n+2,0])
                      for n in range(16)]
            payloads.append((6).to_bytes(2,'little')+bytes([99,0,200,134,1,0]))
            records=[];entries=[b'\xff'*3];offset=0
            for payload in payloads:
                entries.append(offset.to_bytes(3,'big'))
                size=len(payload).to_bytes(2,'little')
                records.append(b'\x12\x34\0'+size*2+payload)
                offset+=7+len(payload)
            size=len(sound).to_bytes(2,'little')
            files={directory.decode()+'/logDir':b''.join(entries),
                   directory.decode()+'/sndDir':offset.to_bytes(3,'big'),
                   directory.decode()+'/vol.0':b''.join(records)+b'\x12\x34\0'+size*2+sound,
                   'sierraui':helper}
            print('Checking native audio: 16 nested logic calls and 127-byte directory',flush=True)
            error,output,state=exercise(d,files,arguments=directory+b' 1\r',
                module='wbgame',base=0xa000,database=0x0000,window=0x8000,
                blocks=None,multiple=True,firstblock=0x10,capture=True,psg={},
                os_call_limit=20000)
            assert not error and not output and state['vmflags'][200]==1,(error,output)
            print('PASS: native CoCo-note/end packets, bounded resource reads, private adapter installation, root logic restoration, unavailable/busy audio completion and ownership cleanup',flush=True)
        finally:
            d.s.close();e.terminate()
            try:e.wait(timeout=5)
            except Exception:e.kill();e.wait(timeout=5)


if __name__=='__main__':main()
