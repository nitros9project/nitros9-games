#!/usr/bin/env python3
"""Run original game resources on real Wild Bits drivers; optional private fixtures."""
import argparse,binascii,json,re,shutil,subprocess,shlex
from pathlib import Path
from check_wbpic_mame import VIEWER,png_rgb
from check_instances import symbols
from check_kq3_mame import text_rows
import statistics

def check_status_pixels(image,font,score,maximum,sound):
    """Independent font oracle for the original KQ1 status row in MAME."""
    w,h,pixels=image
    assert (w,h)==(640,480)
    cells=bytearray(b' '*40)
    label=f'Score:{score} of {maximum}'.encode();cells[1:1+len(label)]=label
    label=b'Sound: '+(b'on' if sound else b'off');cells[30:30+len(label)]=label
    for column,char in enumerate(cells):
        for row,bits in enumerate(font[char*8:char*8+8]):
            for bit in range(8):
                wanted=bytes(3) if bits&(128>>bit) else bytes([255])*3
                x=column*16+bit*2;y=row*2
                assert pixels[(y*w+x)*3:(y*w+x)*3+3]==wanted,('status glyph',column,row,bit)

def check_dialog_panel(image,label):
    """Require the standard white dialog, black frame and visible scene margins."""
    w,h,pixels=image
    assert (w,h)==(640,480)
    black=bytes(3);white=bytes([255])*3
    inside=[pixels[(y*w+x)*3:(y*w+x)*3+3]
            for y in range(80,320) for x in range(16,624)]
    colors=set(inside)
    assert colors <= {black,white}, \
        (label,'dialog interior is not opaque black/white',[tuple(c) for c in colors])
    assert inside.count(white)>len(inside)*0.7, \
        (label,'dialog does not have a white text area')
    for x,y in ((320,80),(320,319),(16,180),(623,180)):
        assert pixels[(y*w+x)*3:(y*w+x)*3+3]==black, \
            (label,'black frame missing',x,y)
    for y0,y1 in ((16,80),(320,384)):
        edge_colors={pixels[(y*w+x)*3:(y*w+x)*3+3]
                     for y in range(y0,y1) for x in range(16,624)}
        assert len(edge_colors)>=6, \
            (label,'game scene is missing outside the frame',y0,y1)


def check_snapshot_replay(data, saved_symbols):
    """Validate the actual replay log and checkpoint stored in a save file."""
    assert data[:3]==b'WS\x01' and len(data)==18+int.from_bytes(data[4:6],'big')
    assert binascii.crc_hqx(data[18:],0xffff)==int.from_bytes(data[6:8],'big')
    replay=18+saved_symbols['SavedReplay']
    replay_buffer=18+saved_symbols['SavedReplayBuffer']
    limit=data[replay]
    used=int.from_bytes(data[replay+1:replay+3],'big')
    checkpoint=int.from_bytes(data[replay+3:replay+5],'big')
    assert 0<used<=min(510,limit*2) and used%2==0, ('invalid replay length',limit,used)
    assert checkpoint<=used and checkpoint%2==0, ('invalid replay checkpoint',checkpoint,used)
    return used,checkpoint,data[replay_buffer:replay_buffer+used]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('mame','disk','firmware','game','output'):
        ap.add_argument('--'+name,required=True,type=Path)
    ap.add_argument('--os9',default='os9')
    ap.add_argument('--prepare-play',action='store_true',help='Prepare a private interactive image and launcher without running scripted tests')
    ap.add_argument('--start-frame',type=int,default=1000,help='Emulated frame at which the interactive launcher types sierra (default: 1000)')
    ap.add_argument('--module-file',type=Path)
    ap.add_argument('--helper-file',type=Path,help='Matching persistence provider for a supplied module build')
    ap.add_argument('--ui-helper-file',type=Path,help='Matching immutable UI/audio provider')
    ap.add_argument('--psg-driver',type=Path,help='PSGdrv module to install and load for the private MAME image')
    ap.add_argument('--psg-device',type=Path,help='fPSG descriptor to install and load for the private MAME image')
    ap.add_argument('--typed-command', help='Exercise one command after inventory dismissal')
    ap.add_argument('--menu',action='store_true',help='Open and cancel the actual game menu')
    ap.add_argument('--sustained',action='store_true',help='Repeat commands and select Pause through the real game menu')
    ap.add_argument('--video-mode',action='store_true',help='Select KQ1 Video Mode twice and verify palette changes')
    ap.add_argument('--restart',action='store_true',help='Restart original KQ1 through its menu, then verify resumed play')
    ap.add_argument('--persistence',action='store_true',help='Save original KQ1, walk, restore, and issue another command')
    ap.add_argument('--hall',action='store_true',help='Exercise original KQ1 hall logic after stop.motion/new.room')
    ap.add_argument('--king-dialog',action='store_true',help='Exercise a synthetic king-speech text.screen/hold sequence and fresh-key wait')
    ap.add_argument('--trace',action='store_true',help='Inject trace.info/trace.on into KQ1 room logic and step the native trace in MAME')
    ap.add_argument('--quest-chain',choices=('basic','acquisitions','quest-items','quest-save'),nargs='?',const='basic',help='Run original root/rooms through controlled encounters, pickups, transfers and ending')
    ap.add_argument('--encounter',choices=('fiddle','dragon','giant'),help='Type an original encounter command and verify its outcome')
    ap.add_argument('--coronation',action='store_true',help='Exercise the original three-treasure throne-room ending')
    ap.add_argument('--pickup',choices=('clover','mirror','shield','chest'),help='Type a pickup command twice in an original puzzle room with controlled encounter preconditions')
    ap.add_argument('--journey',action='store_true',help='Walk original KQ1 to the lake, look, and return to the castle')
    ap.add_argument('--movement',action='store_true',help='Measure KQ1 movement over 200 emulated frames')
    ap.add_argument('--larry',action='store_true',help='Exercise Larry age quiz, street walking and look response')
    ap.add_argument('--larry-enter',action='store_true',help="Exercise Larry quiz and entering Lefty's")
    ap.add_argument('--larry-pair',type=Path,help="Run Larry and this King's Quest I directory on two terminals (requires --expanded-krnp2)")
    ap.add_argument('--expanded-krnp2',type=Path,help='Install an emulator-only expanded-memory Jr2 kernel in the private test image')
    ap.add_argument('--sol-driver',type=Path,help='Install a verified shared raster-clock driver in the private test image')
    ap.add_argument('--audio-trace',action='store_true',help='Require owned PSG hardware writes during real game startup')
    ap.add_argument('--profile',action='store_true',help='Profile production Larry phase boundaries during its movement window')
    ap.add_argument('--startup-only',action='store_true',help='Verify an original game reaches a changed display, then exits cleanly without KQ1-specific controls')
    a=ap.parse_args()
    if a.larry_pair and not a.expanded_krnp2:
        ap.error('--larry-pair needs --expanded-krnp2; the default test kernel aborts when both games are resident')
    out=a.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    if a.profile and (not a.larry or a.module_file):ap.error('--profile requires --larry and the production module/map')
    disk=out/'test.dsk'; shutil.copyfile(a.disk,disk)
    roms=out/'roms/wbjr2'; roms.mkdir(parents=True)
    for name in ('booter','f0.dsk'):shutil.copyfile(a.firmware/name,roms/name)
    def os9(*args):return subprocess.check_output([a.os9,*map(str,args)],stderr=subprocess.STDOUT)
    def install(name,data,target=None,text=False):
        source=out/name;source.write_bytes(data)
        os9('copy','-r',*(['-l'] if text else []),source,f'{disk},{target or name}')
    os9('makdir',f'{disk},game')
    for source in a.game.iterdir():
        if source.is_file() and (source.name.startswith('vol.') or source.name in ('logDir','picDir','viewDir','sndDir','words.tok','object')):
            install(source.name,source.read_bytes(),'game/'+source.name)
    if a.quest_chain:
        from check_wbgame import original_quest_chain_files
        fixture=original_quest_chain_files(a.quest_chain!='basic',a.quest_chain in ('quest-items','quest-save'),a.quest_chain=='quest-save')
        for name in ('vol.0','logDir'):
            install('quest-chain-'+name,fixture['/game/'+name],'game/'+name)
    if a.encounter:
        if a.encounter=='fiddle':
            setup=bytes([3,250,1,3,0,76,3,1,77,12,5,12,87,12,171,92,8,92,22,
                         33,0,30,0,41,0,0,37,0,73,150,121,113,0,1])
        elif a.encounter=='dragon':
            setup=bytes([3,250,1,3,0,51,12,5,12,88,12,167,92,26,
                         33,0,30,0,41,0,0,37,0,80,140,121,113,0,1])
        else:
            setup=bytes([3,250,1,3,0,58,3,1,57,12,5,12,93,12,97,92,13,92,14,
                         33,0,30,0,41,0,0,37,0,50,120,121,113,0,1])
        root=bytes([255,1,250,0,255])+len(setup).to_bytes(2,'little')+setup
        root+=bytes([255,12,1,255,2,0,134,1,23,0,13,5,0])
        logic=len(root).to_bytes(2,'little')+root
        volume=(a.game/'vol.0').read_bytes();offset=len(volume)
        install('encounter-vol.0',volume+b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic,'game/vol.0')
        directory=bytearray((a.game/'logDir').read_bytes());directory[:3]=offset.to_bytes(3,'big')
        install('encounter-logDir',bytes(directory),'game/logDir')
    if a.coronation:
        setup=bytes([3,250,1,3,0,53,3,1,54,3,74,3,3,3,24,12,5,
                     33,0,30,0,41,0,0,37,0,50,110,92,19,92,21,92,2])
        root=bytes([255,1,250,0,255])+len(setup).to_bytes(2,'little')+setup
        root+=bytes([22,53,13,5,255,7,195,255,2,0,134,1,0])
        logic=len(root).to_bytes(2,'little')+root
        volume=(a.game/'vol.0').read_bytes();offset=len(volume)
        install('coronation-vol.0',volume+b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic,'game/vol.0')
        directory=bytearray((a.game/'logDir').read_bytes());directory[:3]=offset.to_bytes(3,'big')
        install('coronation-logDir',bytes(directory),'game/logDir')
    if a.pickup:
        room,item,x,y,preconditions={
            'clover':(24,8,50,134,b''),
            'mirror':(51,19,40,115,bytes([3,75,2,12,167])),
            'shield':(77,21,130,128,bytes([12,186,12,187])),
            'chest':(58,2,75,115,bytes([3,86,4])),
        }[a.pickup]
        setup=preconditions+bytes([3,250,1,3,0,room,33,0,30,0,41,0,0,37,0,x,y,121,113,0,1])
        root=bytes([255,1,250,0,255])+len(setup).to_bytes(2,'little')+setup
        root+=bytes([255,12,1,255,2,0,134,1,23,0,3,240,item,97,240,200,0])
        logic=len(root).to_bytes(2,'little')+root
        volume=(a.game/'vol.0').read_bytes();offset=len(volume)
        install('pickup-vol.0',volume+b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic,'game/vol.0')
        directory=bytearray((a.game/'logDir').read_bytes());directory[:3]=offset.to_bytes(3,'big')
        install('pickup-logDir',bytes(directory),'game/logDir')
    if a.king_dialog:
        from check_lzw import expand
        entry=int.from_bytes((a.game/'logDir').read_bytes()[53*3:54*3],'big')
        source=(a.game/f'vol.{entry>>20}').read_bytes();offset=entry&0xfffff
        expanded=int.from_bytes(source[offset+3:offset+5],'little')
        stored=int.from_bytes(source[offset+5:offset+7],'little')
        original=source[offset+7:offset+7+stored]
        assert expanded!=stored,'king fixture expects original compressed KQ1 logic'
        original=expand(original);assert len(original)==expanded
        end=int.from_bytes(original[:2],'little')+2;code=original[2:end]
        first=code.index(bytes([106,103,0,4,32]))
        last=code.index(bytes([103,22,5,54]),first)+4
        speech=code[first:last]+bytes([3,19,0])+bytes.fromhex('ff fd 0d ff 03 00 fe f7 ff')+bytes([107])
        setup=bytes([3,250,53,24,250,25,250,26])
        root=bytes([255,1,250,0,255])+len(setup).to_bytes(2,'little')+setup
        root+=bytes([255,7,2,255])+len(speech).to_bytes(2,'little')+speech+b'\0'
        messages=original[end:];pool=3+2*messages[0];key=b'Avis Durgan'
        messages=messages[:pool]+bytes(v^key[i%11] for i,v in enumerate(messages[pool:]))
        logic=len(root).to_bytes(2,'little')+root+messages
        volume=(a.game/'vol.0').read_bytes();offset=len(volume)
        install('king-vol.0',volume+b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic,'game/vol.0')
        directory=bytearray((a.game/'logDir').read_bytes());directory[:3]=offset.to_bytes(3,'big')
        install('king-logDir',bytes(directory),'game/logDir')
    if a.trace:
        from check_lzw import expand
        directory=bytearray((a.game/'logDir').read_bytes())
        logic_number=0
        entry=int.from_bytes(directory[logic_number*3:logic_number*3+3],'big');volume_number=entry>>20;offset=entry&0xfffff
        volume_path=a.game/f'vol.{volume_number}';volume=bytearray(volume_path.read_bytes())
        resource_header=bytes(volume[offset:offset+3])
        assert resource_header[:2]==b'\x12\x34','KQ1 test logic resource header missing'
        expanded=int.from_bytes(volume[offset+3:offset+5],'little')
        stored=int.from_bytes(volume[offset+5:offset+7],'little')
        packed=volume[offset+7:offset+7+stored]
        logic=bytearray(packed if expanded==stored else expand(packed))
        assert len(logic)==expanded
        code_end=int.from_bytes(logic[:2],'little')+2
        code=bytes(logic[2:code_end]);messages=bytes(logic[code_end:])
        # Replace private root logic with a deterministic trace exercise while
        # retaining every original room, view, sound and message resource.
        # Set permission flag 10, configure trace, and execute a harmless
        # assignment after trace.on. Return to the normal cycle so MAME can
        # capture the active overlay before and after key advancement.
        logic_body=bytes([12,10,150,1,1,8,149,3,10,42,0])
        logic=len(logic_body).to_bytes(2,'little')+logic_body+messages
        new_offset=len(volume)
        assert new_offset<0x100000,'trace fixture exceeds volume-zero directory range'
        volume.extend(resource_header+len(logic).to_bytes(2,'little')*2+logic)
        install('trace-vol.'+str(volume_number),bytes(volume),'game/vol.'+str(volume_number))
        directory[logic_number*3:logic_number*3+3]=((volume_number<<20)|new_offset).to_bytes(3,'big')
        install('trace-logDir',bytes(directory),'game/logDir')
    if a.hall:
        # Keep original hall picture, views and logic 55. The private fixture
        # replaces only root logic to reproduce the door's control transition
        # without depending on a long exterior navigation route.
        transition=bytes([3,10,2,77,0,3,0,2,18,55])
        root=bytes([255,1,0,0,255])+len(transition).to_bytes(2,'little')+transition
        setup=bytes([33,0,30,0,41,0,0])
        root+=bytes([255,7,5,255])+len(setup).to_bytes(2,'little')+setup
        root+=bytes([121,113,0,1,255,12,1,255,2,0,134,1,23,0,0])
        logic=len(root).to_bytes(2,'little')+root
        volume=(a.game/'vol.0').read_bytes();offset=len(volume)
        assert offset<0x100000,'hall fixture exceeds volume-zero directory range'
        install('hall-vol.0',volume+b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic,'game/vol.0')
        directory=bytearray((a.game/'logDir').read_bytes())
        assert len(directory)>55*3 and directory[55*3:56*3]!=b'\xff'*3,'KQ1 hall logic missing'
        directory[:3]=offset.to_bytes(3,'big')
        install('hall-logDir',bytes(directory),'game/logDir')
    if a.larry_pair:
        os9('makdir',f'{disk},castle')
        for source in a.larry_pair.iterdir():
            if source.is_file() and (source.name.startswith('vol.') or source.name in ('logDir','picDir','viewDir','sndDir','words.tok','object')):
                install('castle-'+source.name,source.read_bytes(),'castle/'+source.name)
    module_source = a.module_file or (VIEWER/('sierra' if a.prepare_play else 'wbgame'))
    module_bytes = module_source.read_bytes()
    # Keep the old internal test command available in prepared test images; the
    # playable Wild Bits command uses the CoCo-compatible `sierra` filename.
    install('sierra',module_bytes,'CMDS/sierra')
    os9('attr',f'{disk},CMDS/sierra','-e','-pe')
    install('wbgame',module_bytes,'CMDS/wbgame')
    os9('attr',f'{disk},CMDS/wbgame','-e','-pe')
    install('sierrastate',(a.helper_file or (VIEWER/'sierrastate')).read_bytes(),'CMDS/sierrastate')
    os9('attr',f'{disk},CMDS/sierrastate','-e','-pe')
    install('sierraui',(a.ui_helper_file or (VIEWER/'sierraui')).read_bytes(),'CMDS/sierraui')
    os9('attr',f'{disk},CMDS/sierraui','-e','-pe')
    install('sierrafont',(VIEWER/'sierrafont').read_bytes(),'CMDS/sierrafont')
    os9('attr',f'{disk},CMDS/sierrafont','-e','-pe')
    psg_driver=a.psg_driver
    psg_device=a.psg_device
    if psg_driver is None and psg_device is None:
        candidate_driver=a.firmware.parent/'l2'/'.mods'/'PSGdrv'
        candidate_device=a.firmware.parent/'l2'/'.mods'/'fPSG'
        if candidate_driver.is_file() and candidate_device.is_file():
            psg_driver,psg_device=candidate_driver,candidate_device
    elif psg_driver is None or psg_device is None:
        ap.error('--psg-driver and --psg-device must be supplied together')
    startup=b'load utilpak1\n'+(b'load vt\n' if a.larry_pair else b'')
    if psg_driver is not None:
        for module,source in (('PSGdrv',psg_driver),('fPSG',psg_device)):
            install(module,source.read_bytes(),'CMDS/'+module)
            os9('attr',f'{disk},CMDS/{module}','-e','-pe')
        startup+=b'load PSGdrv\nload fPSG\n'
    startup_command = b'load sierra\n' if a.prepare_play else b'load wbgame\n'
    install('startup',startup+b'link shell\n'+startup_command+b'load grfdrv256\n',text=True)
    install('feu.startup',b'bootos9 /s0/OS9Boot\n','FEU/startup',text=True)
    for module,replacement_path in (('krnp2',a.expanded_krnp2),('soldrv',a.sol_driver)):
        if not replacement_path:continue
        # The recipe prepends FF padding so the bootfile ends at $FE00.
        # Replace only the requested kernel and retain that alignment/limit.
        original=out/('OS9Boot-before-'+module);os9('copy',f'{disk},OS9Boot',original)
        boot=original.read_bytes();first=boot.index(b'\x87\xcd')
        assert boot[:first]==b'\xff'*first,'unexpected bootfile prefix'
        boot=boot[first:];cursor=0;replaced=False
        replacement=replacement_path.read_bytes()
        assert replacement[:2]==b'\x87\xcd' and int.from_bytes(replacement[2:4],'big')==len(replacement),'invalid replacement module'
        def module_name(data):
            offset=int.from_bytes(data[4:6],'big');name=''
            for value in data[offset:]:
                name+=chr(value&127)
                if value&128:return name.lower()
            raise AssertionError('unterminated module name')
        assert module_name(replacement)==module,('unexpected replacement',module)
        while cursor<len(boot):
            assert boot[cursor:cursor+2]==b'\x87\xcd','invalid boot module'
            size=int.from_bytes(boot[cursor+2:cursor+4],'big')
            assert size>=12 and cursor+size<=len(boot),'invalid boot module size'
            if module_name(boot[cursor:cursor+size])==module:
                boot=boot[:cursor]+replacement+boot[cursor+size:];replaced=True;break
            cursor+=size
        assert replaced,(module,'not found')
        boot=b'\xff'*((-len(boot))%256)+boot
        assert len(boot)<=32256,'expanded bootfile exceeds the recipe limit'
        install('OS9Boot-with-'+module,boot,'OS9Boot')

    with disk.open('ab') as f:f.truncate(1 << (disk.stat().st_size-1).bit_length())
    if a.prepare_play:
        if any((a.menu,a.typed_command,a.sustained,a.hall,a.king_dialog,a.trace,a.quest_chain,a.encounter,a.coronation,a.pickup,a.journey,a.movement,a.persistence,a.larry,
                a.larry_enter,a.larry_pair,a.restart,a.video_mode,a.audio_trace,a.profile,a.startup_only)):
            ap.error('--prepare-play cannot be combined with scripted diagnostic modes')
        if a.start_frame<1:
            ap.error('--start-frame must be positive')
        lua=out/'play.lua'
        lua.write_text('local frames=0\nemu.register_frame_done(function()\n'
                       ' frames=frames+1\n'
                       f' if frames=={a.start_frame} then manager.machine.natkeyboard:post("sierra /s0/game 0\\r") end\n'
                       'end)\n')
        command=[str(a.mame.resolve()),'wbjr2','-bios','turbo',
                 '-rompath',str(out/'roms'),'-hard',str(disk),'-skip_gameinfo',
                 '-window','-sound','auto','-volume','12','-noui_active',
                 '-autoboot_script',str(lua),
                 '-nvram_directory',str(out/'nvram'),'-cfg_directory',str(out/'cfg')]
        launcher=out/'play.sh'
        launcher.write_text('#!/bin/sh\nset -e\ncd '+shlex.quote(str(out))+'\nexec '+shlex.join(command)+'\n')
        launcher.chmod(0o755)
        print('Prepared interactive game. Run:',launcher)
        print('Press Space at the introduction; press an arrow to move and again to stop; Escape opens the menu.')
        print('Scroll Lock toggles MAME UI controls; Ctrl-C exits the game to NitrOS-9.')
        return
    response_frame=4000+max(700,120*len(a.typed_command or ""))
    if sum(bool(v) for v in (a.menu,a.typed_command,a.sustained,a.hall,a.king_dialog,a.trace,a.quest_chain,a.encounter,a.coronation,a.pickup,a.journey,a.movement,a.persistence,a.larry,a.larry_enter,a.larry_pair,a.restart,a.video_mode,a.startup_only))>1:
        ap.error("choose menu, typed-command, sustained, movement, larry larry-enter or larry-pair")
    if a.menu: response_frame=4700
    delay=response_frame+1000-3900 if a.typed_command or a.menu else 0
    command_events=''
    if a.typed_command:
        command_events = f'''
 if frames==4000 then post({json.dumps(a.typed_command+chr(13))}) end
 if frames=={response_frame} then shot("game-command-response") end
 if frames=={response_frame+50} then post(" ") end
 if frames=={5100+delay} then shot("game-command-restored") end
'''
    if a.menu:
        command_events='''
 if frames==4000 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:set_value(1) end
 if frames==4010 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:clear_value() end
 if frames==4700 then shot("game-command-response") end
 if frames==4750 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:set_value(1) end
 if frames==4760 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:clear_value() end
 if frames==5100 then shot("game-command-restored") end
'''
    if a.sustained:
        delay=8000
        command_events='''
 if frames==4000 then post("look room\\n") end
 if frames==5300 then shot("play-first-response") end
 if frames==5350 then post(" ") end
 if frames==5800 then post("nonsense\\n") end
 if frames==7100 then shot("play-unknown-response") end
 if frames==7150 then post(" ") end
 if frames==7500 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:set_value(1) end
 if frames==7510 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:clear_value() end
 -- Move from Sierra through File, Game and Action to Special; Right
 -- selects each menu's last item, which is Pause in the Special menu.
 if frames==8000 or frames==8050 or frames==8100 or frames==8150 then keys["Right"]:set_value(1) end
 if frames==8010 or frames==8060 or frames==8110 or frames==8160 then keys["Right"]:clear_value() end
 if frames==8200 then shot("play-pause-selected") end
 if frames==8250 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:set_value(1) end
 if frames==8260 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:clear_value() end
 if frames==8700 then shot("play-paused") end
 if frames==9000 then post(" ") end
 if frames==9300 then shot("play-resumed") end
 if frames==9500 then post("look room\\n") end
 if frames==10800 then shot("play-second-response") end
 if frames==10850 then post(" ") end
 if frames==11200 then shot("play-final-scene") end
'''
    if a.persistence:
        delay=7000
        command_events='''
 if frames==4000 then post("save game\\n") end
 if frames==4700 then shot("save-prompt") end
 if frames==4800 then post("/s0/kqsave\\n") end
 if frames==5700 then shot("save-scene") end
 if frames==5800 then keys["Right"]:set_value(1) end
 if frames==6200 then keys["Right"]:clear_value() end
 if frames==6300 then shot("save-moved") end
 if frames==6400 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:set_value(1) end
 if frames==6410 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:clear_value() end
 -- From the default Sierra selection, move through the title/item list to
 -- File: Restore using the same arrow events handled by the real menu.
 if frames==6500 then keys["Right"]:set_value(1) end
 if frames==6510 then keys["Right"]:clear_value() end
 if frames==6550 or frames==6600 or frames==6650 or frames==6700 then keys["Up"]:set_value(1) end
 if frames==6560 or frames==6610 or frames==6660 or frames==6710 then keys["Up"]:clear_value() end
 if frames==6800 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:set_value(1) end
 if frames==6810 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:clear_value() end
 if frames==7200 then shot("restore-prompt") end
 if frames==7300 then post("/s0/kqsave\\n") end
 if frames==8500 then shot("restore-scene") end
 if frames==8600 then post("look room\\n") end
 if frames==9900 then shot("restore-response") end
 if frames==9950 then post(" ") end
 if frames==10300 then shot("restore-final") end
'''
    if a.restart:
        delay=6000
        command_events=''
        command_events+='''
 if frames==4000 then keys["Right"]:set_value(1) end
 if frames==4200 then keys["Right"]:clear_value() end
 if frames==4300 then shot("restart-moved") end
 if frames==4500 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:set_value(1) end
 if frames==4510 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:clear_value() end
 if frames==4800 then shot("restart-menu-open") end
 -- From the default Sierra entry, move to File: Restart in the real menu.
 if frames==5000 then keys["Right"]:set_value(1) end
 if frames==5010 then keys["Right"]:clear_value() end
 if frames==5050 or frames==5100 then keys["Up"]:set_value(1) end
 if frames==5060 or frames==5110 then keys["Up"]:clear_value() end
 if frames==5200 then shot("restart-selected") end
 if frames==5350 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:set_value(1) end
 if frames==5360 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:clear_value() end
 if frames==5500 then shot("restart-prompt") end
 if frames==5650 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:set_value(1) end
 if frames==5660 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:clear_value() end
 if frames==7000 then shot("restart-reset") end
 if frames==7100 then keys["Right"]:set_value(1) end
 if frames==7300 then keys["Right"]:clear_value() end
 if frames==7400 then shot("restart-moved-after") end
 if frames==7450 then keys["Right"]:set_value(1) end
 if frames==7460 then keys["Right"]:clear_value() end
 if frames==9000 then shot("restart-stopped") end
 if frames==9600 then shot("restart-final") end
'''
    if a.video_mode:
        delay=5000
        events=[' if frames==4000 or frames==6000 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:set_value(1) end',
                ' if frames==4010 or frames==6010 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:clear_value() end']
        for start in (4600,6200):
            for n in range(4):
                events+=[f' if frames=={start+n*50} then keys["Right"]:set_value(1) end',
                         f' if frames=={start+n*50+10} then keys["Right"]:clear_value() end']
            events+=[f' if frames=={start+200} then keys["Up"]:set_value(1) end',
                     f' if frames=={start+210} then keys["Up"]:clear_value() end']
        events+=[' if frames==4850 then shot("video-mode-selected") end',
                 ' if frames==4900 or frames==6500 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:set_value(1) end',
                 ' if frames==4910 or frames==6510 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:clear_value() end',
                 ' if frames==5500 then shot("video-mode-alternate") end',
                 ' if frames==7100 then shot("video-mode-standard") end']
        command_events='\n'.join(events)+'\n'
    if a.quest_chain:
        delay=18000
        command_events='''
 if frames>=1800 and frames<19500 and frames%120==0 then post(" ") end
 if frames%3000==0 then shot("quest-chain-"..frames) end
'''
    if a.encounter:
        delay=15000
        text={'fiddle':'play fiddle','dragon':'throw water','giant':'use sling'}[a.encounter]
        command_events=f'''
 if frames==4000 then post("{text}\\r") end
 if frames==6000 then shot("encounter-message") end
 if frames>=6100 and frames<17000 and frames%300==100 then post(" ") end
 if frames==17000 then shot("encounter-finished");post("q") end
'''
    if a.coronation:
        delay=24000
        command_events='''
 if frames>=4000 and frames<28000 and frames%300==0 then post(" ") end
'''
    if a.pickup:
        delay=7500
        command_events=f'''
 if frames==4000 or frames==7500 then post("get {a.pickup}\\r") end
 if frames==6500 then shot("pickup-message") end
 if frames==6600 or frames==9000 then post(" ") end
 if frames==7200 then shot("pickup-scene") end
 if frames==10000 then post("q") end
'''
    if a.king_dialog:
        delay=10500
        command_events='''
 if frames==4000 then post("talk king\\n") end
 if frames==9000 then shot("king-speech") end
 if frames==11000 then shot("king-still-visible") end
 if frames==11500 then post("p") end
 if frames==13000 then shot("king-dismissed") end
'''
    if a.trace:
        delay=1000
        command_events='''
 if frames>=2400 and frames<4500 and frames%10==0 then post(" ") end
 if frames==3800 then shot("trace-active") end
 if frames==4600 then shot("trace-stepped") end
 if frames==4700 then manager.machine:exit() end
'''
    if a.hall:
        delay=2000
        command_events='''
 if frames==3900 then shot("hall-before") end
 if frames==4000 or frames==4200 then keys["Up"]:set_value(1) end
 if frames==4010 or frames==4210 then keys["Up"]:clear_value() end
 if frames==4800 then shot("hall-after") end
'''
    if a.journey:
        delay=7000
        command_events='''
 -- AGI directions toggle on a new press. Release alone does not stop walking.
 -- Hold long enough to reach the east room edge from the original start X.
 if frames==4000 or frames==4700 then keys["Right"]:set_value(1) end
 if frames==4010 or frames==4710 then keys["Right"]:clear_value() end
 if frames==5500 then shot("journey-lake") end
 if frames==6000 then post("look room\\n") end
 if frames==7000 then shot("journey-look") end
 if frames==7050 then post(" ") end
 -- The lake entry point is near the west edge; walk back across it before
 -- toggling Left off so this checks a real room transition in both directions.
 if frames==7500 or frames==8100 then keys["Left"]:set_value(1) end
 if frames==7510 or frames==8110 then keys["Left"]:clear_value() end
 if frames==10000 then shot("journey-return") end
 if frames==10100 then post("look room\\n") end
 if frames==10800 then shot("journey-castle-look") end
 if frames==10850 then post(" ") end
'''
    if a.movement:
        delay=2000
        command_events='''
 if frames==3900 then shot("move-before") end
 if frames==4000 then keys["Right"]:set_value(1) end
 if frames==4190 then keys["Right"]:clear_value() end
 if frames==4200 then shot("move-after") end
'''
    if a.startup_only:
        startup_events=' if frames==3000 then shot("game-before-input") end\n'
    elif a.trace:
        delay=0
        startup_events=' if frames==3000 then shot("game-before-input") end\n'
        command_events='''
 if frames==3000 then shot("trace-active") end
 if frames>=3100 and frames<3700 and frames%10==0 then post(" ") end
 if frames==3800 then shot("trace-stepped") end
 if frames==3900 then manager.machine:exit() end
'''
    else:
        startup_events=''' if frames==3000 then shot("game-before-input") end
 -- Ctrl-I delivers ASCII Tab without MAME host Tab handling.
 if frames==3100 then keys["Ctrl"]:set_value(1) end
 if frames==3110 then i:set_value(1) end
 if frames==3120 then i:clear_value() end
 if frames==3130 then keys["Ctrl"]:clear_value() end
 if frames==3700 then shot("game-after-input") end
 if frames==3750 then post(" ") end
 if frames==3860 then shot("game-after-inventory") end
'''
    lua=out/'drive.lua'
    lua.write_text(f"""local frames=0
local keys=manager.machine.ioport.ports[":KEY3"].fields
local letters=manager.machine.ioport.ports[":KEY0"].fields
local i=nil
for _,field in pairs(letters) do if field.mask==256 then i=field end end
assert(i,"I key not found")
local c=letters["C"] or letters["c"]
for name,field in pairs(letters) do print("KEY0 "..name); if field.mask==4 then c=field end end
assert(c,"C key not found")
local function post(s) manager.machine.natkeyboard:post(s) end
local function shot(name) manager.machine.screens[":screen"]:snapshot({json.dumps(str(out)+'/')}..name..".png") end
sub=emu.add_machine_frame_notifier(function()
 frames=frames+1
 if frames==900 then shot("shell-before-game") end
 if frames==800 then post("mfree >/s0/free-before\\n") end
 if frames==1000 then post("wbgame /s0/game 0\\n") end
 if frames==1800 then post(" \\n") end
{startup_events}
{command_events}
 if frames=={3900+delay} then keys["Ctrl"]:set_value(1) end
 if frames=={3910+delay} then c:set_value(1) end
 if frames=={3920+delay} then c:clear_value() end
 if frames=={3930+delay} then keys["Ctrl"]:clear_value() end
 if frames=={4500+delay} then post("\\n") end
 if frames=={4600+delay} then post("mfree >/s0/free-after\\n") end
 if frames=={4800+delay} then post("echo WBGAME-DONE >/s0/wbgame-done\\n") end
 if frames=={5100+delay} then shot("game-closed");manager.machine:exit() end
end)
""")
    if a.larry or a.larry_enter:
        # Keep quiz events independent of the KQ1 inventory and exit schedule.
        source=lua.read_text()
        begin=source.index(' if frames==3100 then');end=source.index(' if frames==3900 then',begin)
        events=' if frames==3100 then post(" ") end\n if frames==3800 then shot("larry-question") end\n'
        for index,answer in enumerate('bbdbd a  '):
            events+=f' if frames=={4000+index*800} then post({json.dumps(answer)}) end\n'
        if a.larry_enter:
            events+=' if frames==11200 then keys["Up"]:set_value(1) end\n'
            events+=' if frames==11210 then keys["Up"]:clear_value() end\n'
            events+=' if frames==13200 then shot("larry-at-door") end\n'
            events+=' if frames==13400 then post("open door\\r") end\n'
            events+=' if frames==15400 then shot("larry-open") end\n'
            events+=' if frames==15500 then post("\\r") end\n'
            events+=' if frames==17200 then shot("larry-inside") end\n'
            events+=' if frames==17500 then post("look\\r") end\n'
            events+=' if frames==19200 then shot("larry-inside-look") end\n'
            for frame in (19300,19700,20100,20500):
                events+=f' if frames=={frame} then post("\\r") end\n'
            events+=' if frames==21100 then shot("larry-inside-restored") end\n'
            delay=18000
        else:
            events+=' if frames==11200 then shot("larry-before");keys["Right"]:set_value(1) end\n'
            events+=' if frames==11600 then keys["Right"]:clear_value();shot("larry-after") end\n'
            events+=' if frames==11700 then keys["Right"]:set_value(1) end\n'
            events+=' if frames==11710 then keys["Right"]:clear_value() end\n'
            events+=' if frames==12000 then post("look\\r") end\n'
            events+=' if frames==13500 then shot("larry-look") end\n'
            events+=' if frames==13600 then post("\\r") end\n'
            for frame in (14000,14400,14800):
                events+=f' if frames=={frame} then post("\\r") end\n'
            events+=' if frames==15400 then shot("larry-restored") end\n'
            delay=12300
        source=source[:begin]+'LARRY_EVENTS'+source[end:]
        for frame in (3900,3910,3920,3930,4500,4600,4800,5100):
            source=source.replace('frames=='+str(frame)+' then','frames=='+str(frame+delay)+' then')
        # Explicit CR: MAME normalizes a later LF after a dialog CR away,
        # even when the two post() calls are separated by many frames.
        source=source.replace('frames=='+str(4500+delay)+' then post("\\n")',
                              'frames=='+str(4500+delay)+' then post("\\r")')
        # Allow complete natural-keyboard strings to drain before posting again.
        source=source.replace('frames=='+str(4800+delay)+' then','frames=='+str(4800+delay+700)+' then')
        source=source.replace('frames=='+str(5100+delay)+' then','frames=='+str(5100+delay+1200)+' then')
        lua.write_text(source.replace('LARRY_EVENTS',events))
    if a.larry_pair:
        commands={600:'iniz /vt1\r',720:'shell i=/vt1&\r',800:'mfree >/s0/free-before\r',
                  1000:'wbgame /s0/game 0\r',1800:' \r',3100:' ',
                  11800:'mfree >/s0/free-larry\r',12600:'wbgame /s0/castle 0\r',13500:' \r',
                  17300:'\r',19000:'\r',19600:'mfree >/s0/free-larry-after\r',
                  20400:'wbgame /s0/castle 0\r',21300:' \r',23800:'\r',
                  24600:'mfree >/s0/free-lr2\r',26100:'\r',
                  26900:'mfree >/s0/free-after\r',27600:'echo WBGAME-DONE >/s0/wbgame-done\r'}
        for index,answer in enumerate('bbdbd a  '):commands[4000+index*800]=answer
        shots={3800:'larry-question',11000:'larry-first',15100:'castle-first',15800:'larry-restored',
               17200:'castle-inventory',18000:'castle-restored',22900:'castle-relaunch',
               23800:'after-second-exit-enter',24600:'after-second-free-map',
               25100:'larry-survives-again'}
        switches={11200:'Right',15300:'Left',16000:'Right',24800:'Left'}
        source=lua.read_text();source=source[:source.index('sub=emu.add_machine_frame_notifier')]
        source+='sub=emu.add_machine_frame_notifier(function()\n frames=frames+1\n'
        for frame,command in sorted(commands.items()):
            source+=f' if frames=={frame} then post({json.dumps(command)}) end\n'
        for frame,name in sorted(shots.items()):
            source+=f' if frames=={frame} then shot({json.dumps(name)}) end\n'
        for frame,direction in switches.items():
            source+=f' if frames=={frame} then keys["Alt"]:set_value(1);keys["{direction}"]:set_value(1) end\n'
            source+=f' if frames=={frame+5} then keys["{direction}"]:clear_value();keys["Alt"]:clear_value() end\n'
        for frame,key in ((16600,'i'),(18300,'c'),(23000,'c'),(25300,'c')):
            source+=f' if frames=={frame} then keys["Ctrl"]:set_value(1) end\n'
            source+=f' if frames=={frame+10} then {key}:set_value(1) end\n'
            source+=f' if frames=={frame+20} then {key}:clear_value() end\n'
            source+=f' if frames=={frame+30} then keys["Ctrl"]:clear_value() end\n'
        source+=' if frames==27800 then manager.machine:exit() end\nend)\n'
        lua.write_text(source)
    if a.quest_chain:
        module=a.module_file or (VIEWER/'wbgame');syms=symbols(module.with_suffix('.map'))
        code=module.read_bytes();base=(8-(len(code)+8191)//8192)*8192
        if a.quest_chain!='quest-save':
            guard=f'w@{base:x} == 87cd && w@{base+2:x} == {len(code):x}'
            action=f'printf "QUESTCHAIN SCORE=%d QUEST=%d END=%d ITEMS=%d,%d,%d",b@(u+{syms["vmvariables"]+3:x}),b@(u+{syms["vmvariables"]+74:x}),b@(u+{syms["vmflags"]+195:x}),b@(u+{syms["vmvariables"]+200:x}),b@(u+{syms["vmvariables"]+201:x}),b@(u+{syms["vmvariables"]+202:x}); g'
            action=action[:-3]+f'; printf "QUESTCHAIN REMAINING=%d,%d,%d,%d",b@(u+{syms["vmvariables"]+203:x}),b@(u+{syms["vmvariables"]+204:x}),b@(u+{syms["vmvariables"]+205:x}),b@(u+{syms["vmvariables"]+206:x}); g'
            event=f' if frames==950 then cpu.debug:bpset({base+syms["GameQuitCommand"]},{json.dumps(guard)},{json.dumps(action)}) end'
        else:
            event=''
        source=lua.read_text().replace(' frames=frames+1',' frames=frames+1\n'+event,1)
        if a.quest_chain=='quest-save':
            # Supply the controlled save/restore inputs from VM state rather
            # than guessing when a blocking dialog has finished animating.
            prompts=f'''
 local mem=cpu.spaces["program"]
 if mem:read_u16({base})==0x87cd and mem:read_u16({base+2})=={len(code)} then
  local dp=cpu.state["DP"].value*256
  local private=mem:read_u16(dp+{syms["resourcebase"]})
  if private+{max(syms["vmvariables"]+251,syms["vmflags"]+195)}<65536 then
   if frames==3000 or frames==6000 or frames==9000 or frames==12000 or frames==15000 or frames==18000 then
    local state_vars=private+{syms["vmvariables"]}
    print("QUESTSAVE STATE "..frames.." room="..mem:read_u8(state_vars).." stage="..mem:read_u8(state_vars+250).." phase="..mem:read_u8(state_vars+251).." logic="..mem:read_u8(private+{syms["vmcurrent"]}).." opcode="..mem:read_u8(dp+{syms["vmopcode"]}).." input="..mem:read_u8(private+{syms["dialoginputmode"]}).." score="..mem:read_u8(state_vars+3).." quest="..mem:read_u8(state_vars+74))
   end
   if frames==12000 or frames==15000 or frames==18000 then
    local used=mem:read_u16(private+{syms["replayused"]})
    local bytes={{}}
    for index=0,used-1 do bytes[#bytes+1]=string.format("%02X",mem:read_u8(private+{syms["replaybuffer"]}+index)) end
    print("QUESTSAVE REPLAYSTATE "..frames.." "..mem:read_u8(private+{syms["replaylimit"]}).." "..used.." "..mem:read_u16(private+{syms["replaycheckpoint"]}).." "..table.concat(bytes))
   end
   local mode=mem:read_u8(private+{syms["dialoginputmode"]})
   local stage=mem:read_u8(private+{syms["vmvariables"]+250})
   local state_vars=private+{syms["vmvariables"]}
   if not ending_injected and mem:read_u8(state_vars+250)==5 and mem:read_u8(state_vars)==53 then
    local used=mem:read_u16(private+{syms["replayused"]})
    local bytes={{}}
    for index=0,used-1 do bytes[#bytes+1]=string.format("%02X",mem:read_u8(private+{syms["replaybuffer"]}+index)) end
    print("QUESTSAVE RESTORED "..used.." "..table.concat(bytes))
    -- The controlled quest fixture is waiting for its final room flag. Set
    -- that condition only after the restored run reaches the ending room.
    mem:write_u8(private+{syms["vmflags"]+195},1)
    ending_injected=true
   end
   local op=mem:read_u8(dp+{syms["vmopcode"]})
   local key=stage*256+op
   if not ending_state_logged and stage==14 and op==125 then
    local used=mem:read_u16(private+{syms["replayused"]})
    local bytes={{}}
    for index=0,used-1 do bytes[#bytes+1]=string.format("%02X",mem:read_u8(private+{syms["replaybuffer"]}+index)) end
    print("QUESTSAVE ENDSTATE "..used.." "..table.concat(bytes))
    ending_state_logged=true
   end
   if stage==13 and op==125 and quest_prompt~=key then print("QUESTSAVE REPLAY "..mem:read_u8(private+{syms["replaylimit"]}).." "..mem:read_u16(private+{syms["replayused"]})) end
   if mode==1 and ((stage==13 and (op==125 or op==126)) or (stage==14 and op==125)) and quest_prompt~=key then
    quest_prompt=key;print("QUESTSAVE PROMPT "..op.." STAGE "..stage)
    post(stage==14 and "/s0/questend\\r" or "/s0/questsave\\r")
   end
  end
 end
'''
            source=source.replace(' frames=frames+1',' frames=frames+1\n'+prompts,1)
            source='local quest_prompt=0\nlocal ending_injected=false\nlocal ending_state_logged=false\n'+source
        source='local cpu=manager.machine.devices[":maincpu"]\nmanager.machine.debugger.execution_state="run"\n'+source
        if not a.audio_trace:
            source='quest_stop=emu.add_machine_stop_notifier(function() local log=manager.machine.debugger.consolelog;for index=1,#log do if log[index] then print(log[index]) end end end)\n'+source
        lua.write_text(source)
    if a.encounter:
        module=a.module_file or (VIEWER/'wbgame');syms=symbols(module.with_suffix('.map'))
        code=module.read_bytes();base=(8-(len(code)+8191)//8192)*8192
        guard=f'w@{base:x} == 87cd && w@{base+2:x} == {len(code):x}'
        flag={'fiddle':186,'dragon':88,'giant':93}[a.encounter]
        variable=86 if a.encounter=='giant' else 75
        action=f'printf "ENCOUNTER SCORE=%d FLAG=%d STATE=%d INPUT=%d",b@(u+{syms["vmvariables"]+3:x}),b@(u+{syms["vmflags"]+flag:x}),b@(u+{syms["vmvariables"]+variable:x}),b@(u+{syms["vminputenabled"]:x}); g'
        event=f' if frames==950 then cpu.debug:bpset({base+syms["GameQuitCommand"]},{json.dumps(guard)},{json.dumps(action)}) end'
        source=lua.read_text().replace(' frames=frames+1',' frames=frames+1\n'+event,1)
        source='local cpu=manager.machine.devices[":maincpu"]\nmanager.machine.debugger.execution_state="run"\n'+source
        if not a.audio_trace:
            source='encounter_stop=emu.add_machine_stop_notifier(function() local log=manager.machine.debugger.consolelog;for index=1,#log do if log[index] then print(log[index]) end end end)\n'+source
        lua.write_text(source)
    if a.coronation:
        module=a.module_file or (VIEWER/'wbgame');syms=symbols(module.with_suffix('.map'))
        code=module.read_bytes();base=(8-(len(code)+8191)//8192)*8192
        guard=f'w@{base:x} == 87cd && w@{base+2:x} == {len(code):x}'
        action=f'printf "CORONATION END=%d QUEST=%d ACTIVE=%d",b@(u+{syms["vmflags"]+195:x}),b@(u+{syms["vmvariables"]+74:x}),b@(u+{syms["vmflags"]+95:x}); g'
        event=f' if frames==950 then cpu.debug:bpset({base+syms["GameQuitCommand"]},{json.dumps(guard)},{json.dumps(action)}) end'
        source=lua.read_text().replace(' frames=frames+1',' frames=frames+1\n'+event,1)
        source='local cpu=manager.machine.devices[":maincpu"]\nmanager.machine.debugger.execution_state="run"\n'+source
        if not a.audio_trace:
            source='coronation_stop=emu.add_machine_stop_notifier(function() local log=manager.machine.debugger.consolelog;for index=1,#log do if log[index] then print(log[index]) end end end)\n'+source
        lua.write_text(source)
    if a.pickup:
        module=a.module_file or (VIEWER/'wbgame');syms=symbols(module.with_suffix('.map'))
        code=module.read_bytes();base=(8-(len(code)+8191)//8192)*8192
        guard=f'w@{base:x} == 87cd && w@{base+2:x} == {len(code):x}'
        action=f'printf "PICKUP SCORE=%d ITEMROOM=%d QUEST=%d",b@(u+{syms["vmvariables"]+3:x}),b@(u+{syms["vmvariables"]+200:x}),b@(u+{syms["vmvariables"]+74:x}); g'
        event=f' if frames==950 then cpu.debug:bpset({base+syms["GameQuitCommand"]},{json.dumps(guard)},{json.dumps(action)}) end'
        source=lua.read_text().replace(' frames=frames+1',' frames=frames+1\n'+event,1)
        source='local cpu=manager.machine.devices[":maincpu"]\nmanager.machine.debugger.execution_state="run"\n'+source
        if not a.audio_trace:
            source='pickup_stop=emu.add_machine_stop_notifier(function() local log=manager.machine.debugger.consolelog;for index=1,#log do if log[index] then print(log[index]) end end end)\n'+source
        lua.write_text(source)
    if a.hall:
        module=a.module_file or (VIEWER/'wbgame')
        syms=symbols(module.with_suffix('.map'));code=module.read_bytes()
        base=(8-(len(code)+8191)//8192)*8192
        guard=f'w@{base:x} == 87cd && w@{base+2:x} == {len(code):x}'
        action=f'printf "HALL INPUT ROOM=%d X=%d Y=%d CONTROL=%d KEY=%d",b@(u+{syms["vmvariables"]:x}),b@(u+{syms["vmobjects"]+3:x}),b@(u+{syms["vmobjects"]+4:x}),b@(dp*100+{syms["vmplayercontrol"]:x}),b@(dp*100+{syms["vmkeybyte"]:x}); g'
        event=f' if frames==950 then cpu.debug:bpset({base+syms["GameDirectionalKey"]},{json.dumps(guard)},{json.dumps(action)}) end'
        source=lua.read_text().replace(' frames=frames+1',' frames=frames+1\n'+event,1)
        source='local cpu=manager.machine.devices[":maincpu"]\nmanager.machine.debugger.execution_state="run"\nhall_stop=emu.add_machine_stop_notifier(function() local log=manager.machine.debugger.consolelog;for index=1,#log do if log[index] then print(log[index]) end end end)\n'+source
        lua.write_text(source)
    if a.profile:
        syms=symbols(VIEWER/'wbgame.map');code=(VIEWER/'wbgame').read_bytes()
        base=(8-(len(code)+8191)//8192)*8192
        phases=('VmRunRoot','GameNextCycle','GameClockGate','GameUpdateObjects',
                'GameComposeScene','PresentPicture','GameDrawText')
        details=('CheckTerminal','terminalok','PresentReuseBitmap','PresentBandReady',
                 'PresentReadRow','PresentConvertBatch','writespan','PresentFinishBands')
        condition=f'w@{base:x} == 87cd && w@{base+2:x} == {len(code):x} && w@{base+syms["name"]:x} == 7762'
        # wbjr2 turbo uses 2*25.175 MHz input; MC6809 divides by four.
        events=[' if frames==11100 then','  print("PROFILE CLOCK 12587500")']
        for label in phases+details:
            action=f'printf "PROFILE {label} %d",totalcycles; g'
            entry=syms.get('GameDrawTextDirty',syms[label]) if label=='GameDrawText' else syms[label]
            events.append(f'  cpu.debug:bpset({base+entry},{json.dumps(condition)},{json.dumps(action)})')
        # Record the actual clipped footprint and update flags of every cel.
        # The interpreter private base is U-independent here; spriteobject is
        # passed directly in U at this entry before any resource mapping.
        sprite_action='printf "SPRITE %d %d %d %d %d %d %d %d %d",totalcycles,b@(u+3),b@(u+4),b@(u+0x1c),b@(u+0x1d),b@(u+0x26),b@(u+5),b@(u+0xa),b@(u+0xe); g'
        events.append(f'  cpu.debug:bpset({base+syms["SpriteRenderObject"]},{json.dumps(condition)},{json.dumps(sprite_action)})')
        events+=[' end',' if frames==11900 then','  cpu.debug:bpclear()',
                 '  local log=manager.machine.debugger.consolelog',
                 '  for index=1,#log do if log[index] then print(log[index]) end end',' end']
        source=lua.read_text()
        source='local cpu=manager.machine.devices[":maincpu"]\nmanager.machine.debugger.execution_state="run"\n'+source
        source=source.replace(' frames=frames+1',' frames=frames+1\n'+'\n'.join(events),1)
        lua.write_text(source)
    if a.audio_trace:
        syms=symbols(VIEWER/'wbgame.map');code=(VIEWER/'wbgame').read_bytes()
        base=(8-(len(code)+8191)//8192)*8192
        condition=f'w@{base:x} == 87cd && w@{base+2:x} == {len(code):x}'
        action=f'printf "AUDIO COMMAND %d %d %d",b@{syms["vmopcode"]:x},b@(u+{syms["vmarguments"]:x}),b@(u+{syms["vmarguments"]+1:x}); g'
        events=[' if frames==950 then',
            f'  cpu.debug:bpset({base+syms["GameSoundCommand"]},{json.dumps(condition)},{json.dumps(action)})',
            '  cpu.debug:wpset(cpu.spaces["program"],"w",0x4200,1,"b@1a != 0 && ((b@pc == f7 && w@(pc+1) == 4200) || (b@(pc-3) == f7 && w@(pc-2) == 4200))",\'printf "AUDIO PSG %02X OWNER %02X",wpdata,b@1a; g\')',
            ' end']
        for label in ('GameSoundLoad','SoundLoadReturn','SoundOffline'):
            event=f'printf "AUDIO {label} B=%02X CC=%02X FLAG9=%02X PATH=%02X X=%04X",b,cc,b@{syms["vmflags"]+9:x},b@{syms["soundpath"]:x},x; g'
            events.insert(-1,f'  cpu.debug:bpset({base+syms[label]},{json.dumps(condition)},{json.dumps(event)})')
        source=lua.read_text()
        source=source.replace(' frames=frames+1',' frames=frames+1\n'+'\n'.join(events),1)
        source='local cpu=manager.machine.devices[":maincpu"]\nmanager.machine.debugger.execution_state="run"\naudio_stop=emu.add_machine_stop_notifier(function() local log=manager.machine.debugger.consolelog;for index=1,#log do if log[index] then print(log[index]) end end end)\n'+source
        lua.write_text(source)
    if a.video_mode:
        syms=symbols(VIEWER/'wbgame.map');code=(VIEWER/'wbgame').read_bytes();base=(8-(len(code)+8191)//8192)*8192
        condition=f'w@{base:x} == 87cd && w@{base+2:x} == {len(code):x} && b@(w@{syms["resourcebase"]:x}+{syms["vmopcode"]:x})==8c'
        action=f'printf "VIDEO MODE %d",b@(u+{syms["monitorprofile"]:x}); g'
        event=f' if frames==950 then cpu.debug:bpset({base+syms["GameMonitorCommand"]},{json.dumps(condition)},{json.dumps(action)}) end'
        source=lua.read_text().replace(' frames=frames+1',' frames=frames+1\n'+event,1)
        if not a.audio_trace:
            source='local cpu=manager.machine.devices[":maincpu"]\nmanager.machine.debugger.execution_state="run"\nvideo_stop=emu.add_machine_stop_notifier(function() local log=manager.machine.debugger.consolelog;for index=1,#log do if log[index] then print(log[index]) end end end)\n'+source
        lua.write_text(source)
    command=[str(a.mame.resolve()),'wbjr2','-bios','turbo','-rompath',str(roms.parent),'-hard',str(disk),'-skip_gameinfo', '-noui_mouse', '-mouseprovider', 'none','-keyboardprovider','none','-video','none','-sound','none','-nothrottle','-autoboot_script',str(lua),'-seconds_to_run',str(70 if a.trace else 450 if a.larry_pair else (5100+delay+(1200 if a.larry or a.larry_enter else 0))//60+10 if a.typed_command or a.menu or a.sustained or a.hall or a.king_dialog or a.quest_chain or a.encounter or a.coronation or a.pickup or a.journey or a.movement or a.persistence or a.restart or a.larry or a.larry_enter or a.video_mode or a.startup_only else 100),'-nvram_directory',str(out/'nvram'),'-cfg_directory',str(out/'cfg')]
    if a.profile or a.audio_trace or a.video_mode or a.hall or a.quest_chain or a.encounter or a.coronation or a.pickup:command+=['-debug','-debugger','none']
    (out/'command.json').write_text(json.dumps(command,indent=2)+'\n')
    with (out/'mame.log').open('w') as log:subprocess.run(command,cwd=out,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=360 if a.larry_pair else 300 if a.larry or a.larry_enter else 180)
    if a.audio_trace:
        log=(out/'mame.log').read_text(errors='replace')
        writes=[(int(value,16),int(owner,16)) for value,owner in re.findall(r'AUDIO PSG ([0-9A-F]{2}) OWNER ([0-9A-F]{2})',log)]
        assert writes and all(owner for value,owner in writes), 'no process-owned PSG writes observed'
        assert any(value&0x90==0x90 and value&15!=15 for value,owner in writes), 'only mute writes observed'
        assert re.search(r'AUDIO COMMAND 99 ',log), 'no native AGI sound command observed'
        (out/'audio-writes.json').write_text(json.dumps(writes)+'\n')
        print('PASS: native AGI sound reaches real process-owned PSG registers; writes',len(writes))
    if a.profile:
        log=(out/'mame.log').read_text()
        rows=[(label,int(cycles)) for label,cycles in re.findall(r'PROFILE (\w+) (\d+)',log)]
        clock=float(re.search(r'PROFILE CLOCK ([0-9.]+)',log)[1])
        top=[row for row in rows if row[0] in phases]
        report={'e_clock_hz':clock,'phases':{}}
        for first,last in (('VmRunRoot','GameNextCycle'),('GameClockGate','GameUpdateObjects'),
                           ('GameUpdateObjects','GameComposeScene'),('GameComposeScene','PresentPicture'),
                           ('PresentPicture','GameDrawText'),('GameDrawText','VmRunRoot')):
            costs=[end[1]-start[1] for start,end in zip(top,top[1:]) if (start[0],end[0])==(first,last)]
            assert costs,('missing profile phase',first,last)
            report['phases'][first+' -> '+last]={'samples':len(costs),'median_cycles':statistics.median(costs),
                                                'median_ms':statistics.median(costs)*1000/clock}
        (out/'profile.json').write_text(json.dumps(report,indent=2)+'\n')
        (out/'profile-events.json').write_text(json.dumps(rows)+'\n')
        fields=('cycles','x','baseline','width','height','flags','view','loop','cel')
        sprites=[dict(zip(fields,map(int,row))) for row in re.findall(
            r'SPRITE (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)',log)]
        assert sprites,'missing production sprite profile'
        (out/'profile-sprites.json').write_text(json.dumps(sprites,indent=2)+'\n')
        print('PASS: bounded production phase profile; artifacts',out/'profile.json')
    exits=re.findall(r'wbgame error, opcode: ([0-9A-F]{2})', (out/'mame.log').read_text())
    assert all(code == 'E4' for code in exits), f'unexpected game exit {exits}; inspect opcode trace'
    if a.trace:
        active=png_rgb(out/'trace-active.png');stepped=png_rgb(out/'trace-stepped.png')
        assert active[:2]==(640,480) and stepped[:2]==(640,480)
        assert active!=stepped,'native trace overlay did not advance after scripted key steps'
        print('PASS: active native trace overlay advances through real KQ1 logic events')
        return
    assert 'WBGAME-DONE' in os9('list',f'{disk},wbgame-done').decode(),'game did not return to shell'
    questsave_data=None
    saved_symbols=None
    if a.quest_chain=='quest-save':
        saved_path=out/'questsave.bin'
        os9('copy','-r',f'{disk},questsave',saved_path)
        questsave_data=saved_path.read_bytes()
        saved_symbols=symbols(VIEWER/'sierrastate.map')
        replay_used,replay_checkpoint,replay_prefix=check_snapshot_replay(questsave_data,saved_symbols)
        print('PASS: original quest-save snapshot contains a bounded replay stream',
              replay_used,'bytes; checkpoint',replay_checkpoint)
    before=os9('list',f'{disk},free-before');after=os9('list',f'{disk},free-after')
    (out/'free-before.txt').write_bytes(before);(out/'free-after.txt').write_bytes(after)
    assert before==after,'real game leaked memory'
    if a.startup_only:
        shell=png_rgb(out/'shell-before-game.png');scene=png_rgb(out/'game-before-input.png')
        assert shell[:2]==scene[:2]==(640,480)
        assert len(set(scene[2][i:i+3] for i in range(0,len(scene[2]),3)))>=2,'original game display is blank'
        changed=sum(left!=right for left,right in zip(shell[2],scene[2]))
        assert changed>1000,('screen did not change from shell to original-game startup',changed)
        print('PASS: original-resource startup reaches a changed game display and returns to the shell with unchanged free memory')
        return
    if a.quest_chain:
        log_text=(out/'mame.log').read_text()
        score={'basic':'34','acquisitions':'39','quest-items':'61','quest-save':'61'}[a.quest_chain]
        if a.quest_chain=='quest-save':
            end_prompts=re.findall(r'QUESTSAVE PROMPT (\d+) STAGE (\d+)',log_text)
            assert end_prompts==[('125','13'),('126','13'),('125','14')],('quest save/restore/ending prompts',end_prompts)
            data=questsave_data
            variables=18+saved_symbols['SavedVariables']
            inventory=18+saved_symbols['SavedInventory']
            assert data[variables+3]==38 and data[variables+74]==1,'checkpoint did not contain earned score/progress'
            assert data[variables+250:variables+252]==bytes([13,1]),'checkpoint phase differs'
            assert data[variables+256+188]==1 and data[inventory+21]==255,'checkpoint lacked the earned shield'
            ended=out/'questend.bin';os9('copy',f'{disk},questend',ended)
            end_data=ended.read_bytes()
            assert end_data[:3]==b'WS\x01' and len(end_data)==18+int.from_bytes(end_data[4:6],'big')
            assert binascii.crc_hqx(end_data[18:],0xffff)==int.from_bytes(end_data[6:8],'big')
            end_variables=18+saved_symbols['SavedVariables']
            end_inventory=18+saved_symbols['SavedInventory']
            assert end_data[end_variables+3]==int(score),'ending snapshot score differs'
            assert end_data[end_variables+74]==3 and end_data[end_variables+250]==14,'ending snapshot stage/progress differs'
            assert end_data[end_variables+200:end_variables+203]==b'\xff'*3,'ending snapshot lacks all three treasures'
            assert end_data[end_variables+256+195]==1,'original ending flag was not set before snapshot'
            assert end_data[end_variables+203:end_variables+207]==b'\0\xff\xff\0','ending prerequisites remain incorrect'
            assert end_data[end_inventory+21]==255,'ending snapshot lost the clover'
            replay_offset=18+saved_symbols['SavedReplay']
            end_replay_used=int.from_bytes(end_data[replay_offset+1:replay_offset+3],'big')
            assert end_replay_used>=replay_used,('restore truncated the replay stream',replay_used,end_replay_used)
            end_replay_buffer=18+saved_symbols['SavedReplayBuffer']
            ending_state=re.search(r'QUESTSAVE ENDSTATE (\d+) ([0-9A-F]*)',log_text)
            assert ending_state, 'restored quest did not reach the ending save prompt'
            ending_used=int(ending_state.group(1));ending_prefix=bytes.fromhex(ending_state.group(2))
            assert ending_used==len(ending_prefix)>0 and ending_used%2==0
            assert end_replay_used>=ending_used
            assert end_data[end_replay_buffer:end_replay_buffer+ending_used]==ending_prefix, \
                'ending snapshot replay differs from the live log at the ending save prompt'
            if replay_checkpoint==0:
                assert ending_prefix[:2]!=replay_prefix[:2], \
                    'replay tail was not replaced after restoring checkpoint zero'
        else:
            states=re.findall(r'QUESTCHAIN SCORE=(\d+) QUEST=(\d+) END=(\d+) ITEMS=(\d+),(\d+),(\d+)',log_text)
            assert states==[(score,'3','1','255','255','255')],('combined quest outcome',states)
            remaining=re.findall(r'QUESTCHAIN REMAINING=(\d+),(\d+),(\d+),(\d+)',log_text)
            assert remaining==[('0','255','255','0')],('remaining prerequisites',remaining)
        print('PASS: original-root combined quest, carried inventory/score, room transfers, ending and unchanged exit memory')
        return
    if a.encounter:
        states=re.findall(r'ENCOUNTER SCORE=(\d+) FLAG=(\d+) STATE=(\d+) INPUT=(\d+)',(out/'mame.log').read_text())
        expected={'fiddle':('3','1','0','1'),'dragon':('5','0','2','1'),'giant':('2','0','4','1')}[a.encounter]
        assert states==[expected],('original encounter outcome',a.encounter,states)
        print('PASS: original',a.encounter,'encounter through terminal parsing, restored input and unchanged exit memory')
        return
    if a.coronation:
        states=re.findall(r'CORONATION END=(\d+) QUEST=(\d+) ACTIVE=(\d+)',(out/'mame.log').read_text())
        assert states==[('1','3','0')],('original ending did not complete',states)
        print('PASS: original throne-room succession and closing credits, quest progress and unchanged exit memory')
        return
    if a.pickup:
        states=re.findall(r'PICKUP SCORE=(\d+) ITEMROOM=(\d+) QUEST=(\d+)',(out/'mame.log').read_text())
        expected=(2,255,0) if a.pickup=='clover' else (8,255,1)
        assert states==[tuple(map(str,expected))],('pickup/repeat state',a.pickup,states)
        message=png_rgb(out/'pickup-message.png')
        assert set(message[2][i:i+3] for i in range(0,len(message[2]),3))=={bytes(3),bytes([255])*3},'pickup dialog absent'
        scene=png_rgb(out/'pickup-scene.png')
        assert len(set(scene[2][i:i+3] for i in range(0,len(scene[2]),3)))>=12,'pickup dialog did not restore scene'
        (out/'pickup.json').write_text(json.dumps({'item':a.pickup,'score':expected[0],'item_room':255,'quest_progress':expected[2]})+'\n')
        print('PASS: original',a.pickup,'pickup through terminal parsing, repeat scoring, inventory/quest progress and unchanged exit memory')
        return
    if a.king_dialog:
        scene=png_rgb(out/'game-before-input.png')
        speech=png_rgb(out/'king-speech.png');held=png_rgb(out/'king-still-visible.png')
        dismissed=png_rgb(out/'king-dismissed.png')
        assert speech==held,'king speech did not remain stable without fresh input'
        assert speech!=scene and dismissed!=speech,'king speech missing or not dismissed by fresh input'
        check_dialog_panel(speech,'king speech')
        font=(VIEWER/'sierrafont').read_bytes();w,h,pixels=speech
        assert (w,h)==(640,480)
        assert scene[2][18*w*3:350*w*3]==dismissed[2][18*w*3:350*w*3],'king dismissal did not restore the exact throne picture'
        speech_rows=text_rows(out/'king-speech.png',font)
        assert any('Sir Graham, I am an old man.' in row for row in speech_rows), \
            ('king speech text missing from white panel',speech_rows)
        (out/'king-dialog.json').write_text(json.dumps({
            'held_frames':2000,'fresh_key':'p','memory_recovered':True,
            'text_mode':'opaque black-frame/white-panel','speech_lines':speech_rows})+'\n')
        print('PASS: original king speech stays inside the black-frame white panel for 2000 frames, fresh key restores the scene, and exit recovers memory')
        return
    if a.hall:
        log=(out/'mame.log').read_text()
        controls=re.findall(r'HALL INPUT ROOM=(\d+) X=(\d+) Y=(\d+) CONTROL=(\d+) KEY=12',log)
        assert len(controls)==2 and all(room=='55' and control=='1' for room,x,y,control in controls),('hall arrow control',controls)
        ego=[(int(x),int(y)) for room,x,y,control in controls]
        assert ego[1][1]<ego[0][1]-8,('hall ego coordinates did not move',ego)
        positions=[]
        for name in ('hall-before','hall-after'):
            w,h,pixels=png_rgb(out/(name+'.png'));assert (w,h)==(640,480)
            shirt=[(x,y) for y in range(200,352) for x in range(296,328)
                   if pixels[(y*w+x)*3:(y*w+x)*3+3]==bytes([255,85,85])]
            assert shirt,(name,'Graham absent from hall')
            positions.append((min(y for x,y in shirt)+max(y for x,y in shirt))/2)
        assert positions[1]<positions[0]-16,('hall arrow input did not move Graham',positions)
        (out/'hall-movement.json').write_text(json.dumps({'shirt_y':positions,'ego_xy':ego})+'\n')
        print('PASS: original KQ1 hall logic/picture, scripted stop-motion room entry, arrow-controlled walking and unchanged free memory',positions)
        return
    if a.journey:
        castle=png_rgb(out/'game-before-input.png')
        check_status_pixels(castle,(VIEWER/'sierrafont').read_bytes(),0,158,True)
        lake=png_rgb(out/'journey-lake.png')
        returned=png_rgb(out/'journey-return.png')
        assert all(image[:2]==(640,480) for image in (castle,lake,returned))
        def wall(image):
            w,h,pixels=image
            return b''.join(pixels[(y*w+20)*3:(y*w+360)*3] for y in range(60,260))
        assert wall(lake)!=wall(castle),'east boundary did not load the lake room'
        assert wall(returned)==wall(castle),'west boundary did not restore the castle'
        w,h,pixels=lake
        assert pixels[(200*w+590)*3:(200*w+590)*3+3]==bytes([85,85,255]),'lake water missing'
        lake_look=png_rgb(out/'journey-look.png')
        font=(VIEWER/'sierrafont').read_bytes()
        lake_rows=text_rows(out/'journey-look.png',font)
        for phrase in ('A rapidly moving','stream is flowing','out of this lake.'):
            assert any(phrase in line for line in lake_rows), \
                ('lake description',phrase,lake_rows)
        check_dialog_panel(lake_look,'lake')
        # The castle tree can correctly occlude Graham at the arrival point.
        # A second exact room description proves continued play without assuming
        # that the hero must always be visible through foreground scenery.
        castle_look=png_rgb(out/'journey-castle-look.png')
        castle_rows=text_rows(out/'journey-castle-look.png',font)
        for phrase in ('You are standing','outside a castle',
                       'surrounded by an','alligator filled','moat.'):
            assert any(phrase in line for line in castle_rows), \
                ('returned castle description',phrase,castle_rows)
        check_dialog_panel(castle_look,'castle')
        print('PASS: original KQ1 east/west room transitions, exact lake/castle descriptions, continued play, interrupt exit and unchanged free memory')
        return
    if a.video_mode:
        log=(out/'mame.log').read_text()
        assert re.findall(r'VIDEO MODE (\d+)',log)==['0','1'],'actual menu did not invoke both palette switches'
        for name,color in [('video-mode-alternate',bytes([85,170,0])),('video-mode-standard',bytes([0,170,0]))]:
            w,h,pixels=png_rgb(out/(name+'.png'));assert (w,h)==(640,480)
            assert sum(pixels[i:i+3]==color for i in range(0,len(pixels),3))>100,(name,'expected green absent')
            forbidden=bytes([0,170,0]) if name.endswith('alternate') else bytes([85,170,0])
            assert not any(pixels[i:i+3]==forbidden for i in range(0,len(pixels),3)),(name,'other palette remains')
        print('PASS: original KQ1 Video Mode menu switches to CoCo RGB and back, with continued gameplay and recovered memory')
        return
    if a.restart:
        prompt_rows=text_rows(out/'restart-prompt.png',(VIEWER/'sierrafont').read_bytes())
        assert any('restarts;' in row for row in prompt_rows) and \
               any('ESC cancels' in row for row in prompt_rows) and \
               not any('Game menu' in row for row in prompt_rows), \
            ('KQ1 File: Restart action did not open its confirmation prompt',prompt_rows)
        def center(name):
            w,h,pixels=png_rgb(out/(name+'.png'))
            assert (w,h)==(640,480)
            shirt=[i//3%w for i in range(0,len(pixels),3)
                   if pixels[i:i+3]==bytes([255,85,85]) and 120<=i//3//w<240]
            assert shirt,(name,'hero absent')
            return (min(shirt)+max(shirt))/2
        centers=[center(name) for name in ('game-before-input','restart-moved','restart-reset','restart-moved-after','restart-stopped','restart-final')]
        assert centers[1]>centers[0]+8,('pre-restart movement absent',centers)
        assert abs(centers[2]-centers[0])<2,('restart position not reset',centers)
        assert centers[3]>centers[2]+8,('player input did not resume after restart',centers)
        assert centers[4]>=centers[3] and abs(centers[5]-centers[4])<=2,('post-restart movement did not settle and remain stable',centers)
        assert (out/'free-before.txt').read_bytes()==(out/'free-after.txt').read_bytes(), \
            'restart did not recover the original free-memory map'
        (out/'restart.json').write_text(json.dumps({'shirt_centers':centers},indent=2)+'\n')
        print('PASS: original KQ1 menu restart, root-stack unwind, reset position, resumed arrow input, stable stop and unchanged free memory',centers)
        return
    if a.larry_pair:
        live=os9('list',f'{disk},free-larry')
        after_first=os9('list',f'{disk},free-larry-after')
        after_repeat=os9('list',f'{disk},free-lr2')
        (out/'free-larry.txt').write_bytes(live)
        (out/'free-larry-after.txt').write_bytes(after_first)
        (out/'free-lr2.txt').write_bytes(after_repeat)
        assert live==after_first==after_repeat,'repeated KQ1 exits did not restore Larry-only memory map'
        for name in ('castle-first','castle-relaunch'):
            assert png_rgb(out/(name+'.png'))==png_rgb(out/'castle-first.png'),(name,'fresh KQ1 relaunch differs')
        font=(VIEWER/'sierrafont').read_bytes()
        w,h,pixels=png_rgb(out/'castle-inventory.png');assert (w,h)==(640,480)
        for col,char in enumerate('You are carrying:'):
            for y in range(8):
                for x in range(8):
                    expected=bytes(3) if font[ord(char)*8+y] & (128>>x) else bytes([255])*3
                    offset=((16+y*2)*w+32+col*16+x*2)*3
                    assert pixels[offset:offset+3]==expected,'second game inventory font/input failed'
        for name in ('castle-first','castle-restored'):
            w,h,pixels=png_rgb(out/(name+'.png'));assert (w,h)==(640,480)
            green=sum(1 for i in range(0,len(pixels),3) if pixels[i+1]>120 and pixels[i]<80 and pixels[i+2]<80)
            assert green>10000,(name,'KQ1 castle absent')
        background=None
        for name in ('larry-first','larry-restored','larry-survives-again'):
            w,h,pixels=png_rgb(out/(name+'.png'));assert (w,h)==(640,480)
            assert len(set(pixels[i:i+3] for i in range(0,len(pixels),3)))>=12,(name,'Larry absent')
            sample=b''.join(pixels[(y*w+350)*3:(y*w+500)*3] for y in range(200,255))
            if background is None:background=sample
            else:assert sample==background,(name,'Larry background changed across terminal switches')
        print('PASS: simultaneous original Larry/KQ1 games, terminal restoration, independent inventory input, two KQ1 exit/relaunch cycles while Larry remains resident, repeated Larry-only and final free-memory maps restored')
        return
    if a.larry or a.larry_enter:
        font=(VIEWER/'sierrafont').read_bytes()
        def title(name,text):
            rows=text_rows(out/(name+'.png'),font)
            # Graphics behind a popup can coincidentally resemble cells or
            # decode as unknown glyphs. Remove those markers, then collapse
            # row/word spacing so the check permits natural message wrapping.
            visible=' '.join(row.replace('?',' ').replace('_',' ').strip()
                             for row in rows)
            visible=' '.join(visible.split())
            assert text in visible,(name,text,rows)
        title('larry-question','In some personal ads, TV stands for')
        if a.larry_enter:
            title('larry-open','Ok.')
            street=png_rgb(out/'larry-at-door.png');inside=png_rgb(out/'larry-inside.png')
            assert street!=inside,'opening the door did not change rooms'
            w,h,pixels=inside;assert (w,h)==(640,480)
            red=sum(1 for i in range(0,len(pixels),3) if pixels[i]>200 and pixels[i+1]<120 and pixels[i+2]<120)
            cyan=sum(1 for i in range(0,len(pixels),3) if pixels[i]<120 and pixels[i+1]>120 and pixels[i+2]>120)
            assert red>20000 and cyan>10000,('bar interior absent',red,cyan)
            w,h,pixels=png_rgb(out/'larry-inside-look.png')
            rows=text_rows(out/'larry-inside-look.png',font)
            visible=' '.join(row.replace('?',' ').replace('_',' ').strip()
                             for row in rows)
            visible=' '.join(visible.split())
            assert ("This is the sleaziest bar you've ever been in. And you've been in quite a few."
                    in visible),('inside look response absent',rows)
            assert len(set(pixels[i:i+3] for i in range(0,len(pixels),3)))>=12,\
                'inside look obscured the bar scene'
            for left,right in ((0,128),(512,640)):
                scene_colors={pixels[(y*w+x)*3:(y*w+x)*3+3]
                              for y in range(144,272)
                              for x in range(left,right)}
                assert len(scene_colors)>=8,('bar scene obscured outside popup',left,right,len(scene_colors))
            w,h,pixels=png_rgb(out/'larry-inside-restored.png')
            assert len(set(pixels[i:i+3] for i in range(0,len(pixels),3)))>=12,'bar did not return after look'
            print('PASS: original Larry quiz, successful open-door response, room transition into Lefty bar, inside look/dismissal, interrupt cleanup and unchanged free memory')
            return
        title('larry-look',"You are outside Lefty's bar. Isn't it")
        centers=[]
        for name in ('larry-before','larry-after','larry-restored'):
            w,h,pixels=png_rgb(out/(name+'.png'))
            assert (w,h)==(640,480)
            assert len(set(pixels[i:i+3] for i in range(0,len(pixels),3)))>=12,(name,'street absent')
            shirt=[(x,y) for y in range(280,335) for x in range(200,640)
                   if pixels[(y*w+x)*3:(y*w+x)*3+3]==bytes([255])*3]
            assert shirt,(name,'Larry absent')
            centers.append(sum(x for x,y in shirt)/len(shirt))
        assert centers[1]>centers[0]+8,('Larry did not walk right',centers)
        result={'frames':400,'before_x':centers[0]/4,'after_x':centers[1]/4,
                'delta_agi_pixels':(centers[1]-centers[0])/4}
        (out/'movement.json').write_text(json.dumps(result,indent=2)+'\n')
        print('PASS: original Larry age quiz, Lefty street, walking, exact look-message glyphs, modal dismissal, interrupt cleanup and unchanged free memory',result)
        return
    images={name:png_rgb(out/(name+'.png')) for name in ('game-before-input','game-after-input','game-after-inventory','game-closed')}
    w,h,pixels=images['game-before-input'];assert (w,h)==(640,480)
    assert len(set(pixels[i:i+3] for i in range(0,len(pixels),3)))>=12,'game graphics did not appear'
    w,h,pixels=images['game-after-input']
    assert (w,h)==(640,480), 'inventory dimensions'
    font=(VIEWER/'sierrafont').read_bytes()
    # The first intro credit is a white D on black at row 17, column 12.
    # It must not survive the switch to the castle or reappear after a modal.
    for name in ('game-before-input','game-after-inventory'):
        credit_width,credit_height,credit_pixels=images[name]
        stale=all(credit_pixels[((272+gy*2)*credit_width+192+gx*2)*3:((272+gy*2)*credit_width+192+gx*2)*3+3]
                  == (bytes([255])*3 if font[ord('D')*8+gy] & (128>>gx) else bytes(3))
                  for gy in range(8) for gx in range(8))
        assert not stale, ('intro credit returned over the castle',name)
    for col,char in enumerate('You are carrying:'):
        for gy in range(8):
            bits=font[ord(char)*8+gy]
            for gx in range(8):
                expected=bytes(3) if bits & (128>>gx) else bytes([255])*3
                address=((16+gy*2)*w + 32+col*16+gx*2)*3
                assert pixels[address:address+3]==expected, 'inventory title glyphs differ from the shared font'
    w,h,pixels=images['game-after-inventory']
    assert (w,h)==(640,480) and len(set(pixels[i:i+3] for i in range(0,len(pixels),3)))>=12, 'game scene did not return after dismissing inventory'
    green=sum(1 for i in range(0,len(pixels),3) if pixels[i+1]>120 and pixels[i]<80 and pixels[i+2]<80)
    assert green>10000,'castle scene disappeared; console logo colors are not game rendering'
    assert images['game-before-input']!=images['game-after-input'],'inventory did not open'
    assert images['game-after-inventory']!=images['game-closed'],'graphics did not close'
    if a.typed_command or a.menu:
        response=png_rgb(out/'game-command-response.png')
        restored=png_rgb(out/'game-command-restored.png')
        colors=set(response[2][i:i+3] for i in range(0,len(response[2]),3))
        if a.menu:
            menu_rows=text_rows(out/'game-command-response.png',(VIEWER/'sierrafont').read_bytes())
            assert any('Game menu' in row for row in menu_rows) and \
                   any('Arrows select' in row for row in menu_rows), \
                ('game menu text missing',menu_rows)
            for x0,x1 in ((0,144),(480,640)):
                scene_colors={response[2][(y*w+x)*3:(y*w+x)*3+3]
                              for y in range(16,352) for x in range(x0,x1)}
                assert len(scene_colors)>=8, \
                    ('game menu obscured the scene at a screen margin',x0,len(scene_colors))
        else:
            assert bytes(3) in colors and bytes([255])*3 in colors, 'typed command popup text/background missing'
            popup_corner=((150*w)+150)*3
            assert response[2][popup_corner:popup_corner+3]==bytes([255])*3, 'typed command popup is not centered over the game scene'
            green=sum(1 for i in range(0,len(response[2]),3) if response[2][i+1]>120 and response[2][i]<80 and response[2][i+2]<80)
            assert green>1000, 'typed command popup obscured the underlying game scene'
        assert len(set(restored[2][i:i+3] for i in range(0,len(restored[2]),3)))>=12, 'command dismissal did not restore the scene'
    if a.sustained:
        sustained_rows = {}
        for name in ('play-first-response','play-unknown-response','play-paused','play-second-response'):
            w,h,pixels=png_rgb(out/(name+'.png'))
            assert (w,h)==(640,480), ('modal dimensions',name,w,h)
            def region(x0,y0,x1,y1):
                colors=set();light=0;total=0
                for y in range(y0,y1):
                    for x in range(x0,x1):
                        color=pixels[(y*w+x)*3:(y*w+x)*3+3]
                        colors.add(color)
                        light+=min(color)>220
                        total+=1
                return len(colors),light/total
            popup_colors,popup_light=region(144,144,480,256)
            left_colors,_=region(0,16,144,352)
            right_colors,_=region(480,16,640,352)
            assert 3<=popup_colors<=12 and 0.04<popup_light<0.45, \
                ('centered text overlay missing',name,popup_colors,popup_light)
            assert left_colors>=8 and right_colors>=8, \
                ('text popup obscured the game scene',name,left_colors,right_colors)
            sustained_rows[name]=text_rows(out/(name+'.png'),font)
        expected_rows={
            'play-first-response':('You are standing','outside a castle','moat.'),
            'play-unknown-response':("I don't understand",'"nonsense".'),
            'play-paused':('Game paused. Press','a key to resume.'),
            'play-second-response':('You are standing','outside a castle','moat.'),
        }
        for name,phrases in expected_rows.items():
            for phrase in phrases:
                assert any(phrase in row for row in sustained_rows[name]), \
                    ('expected modal text missing',name,phrase,sustained_rows[name])
        # The default print window starts at cell (10,10); its text begins one
        # cell inside at (10,11), white glyphs on the black window interior.
        w,h,pixels=png_rgb(out/'play-paused.png')
        for line_number,line in enumerate(('Game paused. Press','a key to resume.')):
            for col,char in enumerate(line):
                for gy in range(8):
                    for gx in range(8):
                        expected=bytes([255])*3 if font[ord(char)*8+gy] & (128>>gx) else bytes(3)
                        address=((160+(line_number*16+gy*2))*w+176+col*16+gx*2)*3
                        assert pixels[address:address+3]==expected, \
                            ('Pause command glyph differs',line_number,col,char,gy,gx)
        for name in ('play-resumed','play-final-scene'):
            w,h,pixels=png_rgb(out/(name+'.png'))
            assert len(set(pixels[i:i+3] for i in range(0,len(pixels),3)))>=12, ('scene missing',name)
        print('PASS: sustained original-game commands, unknown-word response, real menu Pause selection, resume and subsequent command')
    if a.persistence:
        centers=[]
        for name in ('save-scene','save-moved','restore-scene','restore-final'):
            w,h,pixels=png_rgb(out/(name+'.png'))
            shirt=[i//3%w for i in range(0,len(pixels),3)
                if pixels[i:i+3]==bytes([255,85,85])
                and 120<=i//3//w<240]
            assert shirt,('Graham absent',name)
            centers.append((min(shirt)+max(shirt))/2)
        restore_prompt_rows=text_rows(out/'restore-prompt.png',font)
        assert any(row.strip()=='File:' for row in restore_prompt_rows) and \
               not any('Game menu' in row for row in restore_prompt_rows), \
            ('KQ1 File: Restore menu action did not open its filename prompt',restore_prompt_rows)
        assert abs(centers[1]-centers[0])>8,('game did not change position before restore',centers)
        assert abs(centers[2]-centers[0])<=4 and abs(centers[3]-centers[0])<=4,('restore did not recover position',centers)
        response_w,response_h,response=png_rgb(out/'restore-response.png')
        popup_colors=set(response[(y*response_w+x)*3:(y*response_w+x)*3+3]
                         for y in range(144,256) for x in range(144,480))
        response_rows=text_rows(out/'restore-response.png',font)
        for phrase in ('You are standing','outside a castle','moat.'):
            assert any(phrase in row for row in response_rows), \
                ('look response text missing after restore',phrase,response_rows)
        green_outside=sum(1 for y in range(16,352) for x in range(response_w)
                          if not (144<=x<480 and 144<=y<256)
                          and response[(y*response_w+x)*3+1]>120
                          and response[(y*response_w+x)*3]<80
                          and response[(y*response_w+x)*3+2]<80)
        assert len(popup_colors)<=8 and bytes(3) in popup_colors and \
               bytes([255])*3 in popup_colors and \
               response[(180*response_w+300)*3:(180*response_w+300)*3+3]==bytes(3), \
            ('look response after restore missing from centered popup',popup_colors)
        assert green_outside>1000, \
            ('look response obscured the KQ1 scene',green_outside)
        saved=out/'kqsave.bin';os9('copy',f'{disk},kqsave',saved)
        data=saved.read_bytes()
        assert data[:3]==b'WS\x01' and len(data)==18+int.from_bytes(data[4:6],'big')
        print('PASS: original KQ1 save dialog, walking, restored position, subsequent look command and unchanged free memory',centers)
    if a.movement:
        # The castle's other bright-red pixels are below this region. Graham's
        # shirt gives an observable centre; cel shape may shift it slightly.
        centres=[]
        for name in ('move-before','move-after'):
            w,h,pixels=png_rgb(out/(name+'.png'))
            assert (w,h)==(640,480)
            shirt=[i//3%w for i in range(0,len(pixels),3)
                   if pixels[i:i+3]==bytes([255,85,85])
                   and 120<=i//3//w<260 and 300<=i//3%w]
            assert shirt, ('Graham absent from movement measurement',name)
            centres.append((min(shirt)+max(shirt))/2)
        distance=(centres[1]-centres[0])/4
        assert distance>0, 'Right input did not move Graham'
        result={'frames':200,'seconds':200/60,'shirt_centres':centres,
                'estimated_agi_pixels':distance,'module_bytes':len((a.module_file or VIEWER/'wbgame').read_bytes())}
        (out/'movement.json').write_text(json.dumps(result,indent=2)+'\n')
        print(f'Movement: approximately {distance:g} AGI pixels in {200/60:.2f} emulated seconds')
    print('PASS: real-resource startup, inventory glyphs, modal interaction/restoration, interrupt exit and unchanged memory on Wild Bits drivers; full gameplay/audio not claimed')
    print('Artifacts:',out)
if __name__=='__main__':main()
