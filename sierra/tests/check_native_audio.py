#!/usr/bin/env python3
"""Run native AGI sound through the private adapter and adversarial OS services."""
from pathlib import Path
import tempfile
from check_wbres import exercise, idle_rom, start_cpu
ROOT=Path(__file__).resolve().parents[1]


def fixture(sound, requests=1):
    # Start once, then wait for the completion flag before quitting.
    body=bytes([12,201])+bytes([99,0,200])*requests
    script=bytes([255,253,7,201,255,len(body),0])+body
    script+=bytes([255,7,200,255,2,0,134,1,0])
    logic=len(script).to_bytes(2,'little')+script
    def record(payload):
        size=len(payload).to_bytes(2,'little')
        return b'\x12\x34\0'+size*2+payload
    offset=7+len(logic)
    return {'/game/logDir':b'\xff'*3+bytes(3),
            '/game/sndDir':offset.to_bytes(3,'big'),
            '/game/vol.0':record(logic)+record(sound)}


def main():
    sound=bytes([28,63,0,2,29,0,0,3,255,0,48])
    helper=(ROOT/'objs/wbstate').read_bytes()
    stale=bytearray(helper);entry=int.from_bytes(stale[9:11],'big');stale[entry+8]^=1
    with tempfile.TemporaryDirectory(prefix='sierra-native-audio-') as name:
        d,e=start_cpu(idle_rom(Path(name)/'idle.rom'),timeout=1800)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01')
            d.write(0xffa8,bytes(range(8)))
            for label,files,driver in (
                ('converted notes',{**fixture(sound),'wbstate':helper},{}),
                ('missing helper',fixture(sound),None),
                ('missing driver',{**fixture(sound),'wbstate':helper},None),
                ('older driver',{**fixture(sound),'wbstate':helper},{'version':3}),
                ('stale helper',{**fixture(sound),'wbstate':bytes(stale)},{}),
                ('invalid amplitude',{**fixture(bytes([28,64,0,2,255,0,48])),'wbstate':helper},{}),
                ('busy driver',{**fixture(sound),'wbstate':helper},{'busy':True}),
                ('busy then available',{**fixture(sound,2),'wbstate':helper},{'busy_attempts':1}),
                ('truncated note',{**fixture(sound[:-3]),'wbstate':helper},{})):
                print('Checking native audio:',label,flush=True)
                error,output,state=exercise(d,files,module='wbgame',base=0xa000,
                    database=0x1000,window=0x8000,blocks=None,multiple=True,
                    firstblock=0x10,capture=True,psg=driver,os_call_limit=3000)
                assert not error and not output,(label,error,output)
                assert state['vmflags'][200]==1,(label,'completion flag')
                if label in ('converted notes','busy then available'):
                    expected=[bytes([128,28,63,0,2,0])]
                    expected += [bytes([ch,255,255,0,0,0]) for ch in range(1,4)]
                    expected += [bytes([128,29,0,0,3,0]),bytes([0,255,255,0,0,0])]
                    assert state['audio_packets']==expected,state['audio_packets']
                    assert state['vmflags'][9]==1
                elif label=='busy driver':
                    assert not state['audio_packets'] and state['vmflags'][9]==1
                elif label not in ('truncated note','invalid amplitude'):
                    assert not state['audio_packets']
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
                   'wbstate':helper}
            print('Checking native audio: 16 nested logic calls and 127-byte directory',flush=True)
            error,output,state=exercise(d,files,arguments=directory+b' 1\r',
                module='wbgame',base=0xa000,database=0x1000,window=0x8000,
                blocks=None,multiple=True,firstblock=0x10,capture=True,psg={},
                os_call_limit=20000)
            assert not error and not output and state['vmflags'][200]==1,(error,output)
            print('PASS: native CoCo-note/end packets, bounded resource reads, private adapter installation, root logic restoration, unavailable/busy audio completion and ownership cleanup',flush=True)
        finally:
            d.s.close();e.terminate()
            try:e.wait(timeout=5)
            except Exception:e.kill();e.wait(timeout=5)


if __name__=='__main__':main()
