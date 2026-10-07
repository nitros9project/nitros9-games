#!/usr/bin/env python3
"""Run original game resources on real Wild Bits drivers; optional private fixtures."""
import argparse,json,re,shutil,subprocess,shlex
from pathlib import Path
from check_wbpic_mame import VIEWER,png_rgb
from check_instances import symbols
import statistics

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('mame','disk','firmware','game','output'):
        ap.add_argument('--'+name,required=True,type=Path)
    ap.add_argument('--os9',default='os9')
    ap.add_argument('--prepare-play',action='store_true',help='Prepare a private interactive image and launcher without running scripted tests')
    ap.add_argument('--module-file',type=Path)
    ap.add_argument('--helper-file',type=Path,help='Matching helper for a supplied module build')
    ap.add_argument('--typed-command', help='Exercise one command after inventory dismissal')
    ap.add_argument('--menu',action='store_true',help='Open and cancel the actual game menu')
    ap.add_argument('--sustained',action='store_true',help='Repeat commands and select Pause through the real game menu')
    ap.add_argument('--video-mode',action='store_true',help='Select KQ1 Video Mode twice and verify palette changes')
    ap.add_argument('--restart',action='store_true',help='Restart original KQ1 through its menu, then issue another command')
    ap.add_argument('--persistence',action='store_true',help='Save original KQ1, walk, restore, and issue another command')
    ap.add_argument('--hall',action='store_true',help='Exercise original KQ1 hall logic after stop.motion/new.room')
    ap.add_argument('--journey',action='store_true',help='Walk original KQ1 to the lake, look, and return to the castle')
    ap.add_argument('--movement',action='store_true',help='Measure KQ1 movement over 200 emulated frames')
    ap.add_argument('--larry',action='store_true',help='Exercise Larry age quiz, street walking and look response')
    ap.add_argument('--larry-enter',action='store_true',help="Exercise Larry quiz and entering Lefty's")
    ap.add_argument('--larry-pair',type=Path,help="Run Larry and this King's Quest I directory on two terminals")
    ap.add_argument('--expanded-krnp2',type=Path,help='Install an emulator-only expanded-memory Jr2 kernel in the private test image')
    ap.add_argument('--sol-driver',type=Path,help='Install a verified shared raster-clock driver in the private test image')
    ap.add_argument('--audio-trace',action='store_true',help='Require owned PSG hardware writes during real game startup')
    ap.add_argument('--profile',action='store_true',help='Profile production Larry phase boundaries during its movement window')
    a=ap.parse_args(); out=a.output.resolve(); out.mkdir(parents=True,exist_ok=False)
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
    install('wbgame',(a.module_file or (VIEWER/'wbgame')).read_bytes(),'CMDS/wbgame')
    os9('attr',f'{disk},CMDS/wbgame','-e','-pe')
    install('wbstate',(a.helper_file or (VIEWER/'wbstate')).read_bytes(),'CMDS/wbstate')
    os9('attr',f'{disk},CMDS/wbstate','-e','-pe')
    install('wbfont',(VIEWER/'wbfont').read_bytes(),'CMDS/wbfont')
    os9('attr',f'{disk},CMDS/wbfont','-e','-pe')
    install('startup',b'load utilpak1\n'+(b'load vt\n' if a.larry_pair else b'')+b'link shell\nload wbgame\nload grfdrv256\n',text=True)
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
        if any((a.menu,a.typed_command,a.sustained,a.hall,a.journey,a.movement,a.persistence,a.larry,
                a.larry_enter,a.larry_pair,a.restart,a.video_mode,a.audio_trace,a.profile)):
            ap.error('--prepare-play cannot be combined with scripted diagnostic modes')
        lua=out/'play.lua'
        lua.write_text('local frames=0\nemu.register_frame_done(function()\n'
                       ' frames=frames+1\n'
                       ' if frames==1000 then manager.machine.natkeyboard:post("wbgame /s0/game 0\\n") end\n'
                       'end)\n')
        command=[str(a.mame.resolve()),'wbjr2','-bios','turbo',
                 '-rompath',str(out/'roms'),'-hard',str(disk),'-skip_gameinfo',
                 '-window','-noui_active','-autoboot_script',str(lua),
                 '-nvram_directory',str(out/'nvram'),'-cfg_directory',str(out/'cfg')]
        launcher=out/'play.sh'
        launcher.write_text('#!/bin/sh\nset -e\ncd '+shlex.quote(str(out))+'\nexec '+shlex.join(command)+'\n')
        launcher.chmod(0o755)
        print('Prepared interactive game. Run:',launcher)
        print('Press Space at the introduction; press an arrow to move and again to stop; Escape opens the menu.')
        print('Scroll Lock toggles MAME UI controls; Ctrl-C exits the game to NitrOS-9.')
        return
    response_frame=4000+max(700,120*len(a.typed_command or ""))
    if sum(bool(v) for v in (a.menu,a.typed_command,a.sustained,a.hall,a.journey,a.movement,a.persistence,a.larry,a.larry_enter,a.larry_pair,a.restart,a.video_mode))>1:
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
 -- The twentieth item is Slow; four Up presses from item zero select Pause.
 if frames==8000 or frames==8050 or frames==8100 or frames==8150 then keys["Up"]:set_value(1) end
 if frames==8010 or frames==8060 or frames==8110 or frames==8160 then keys["Up"]:clear_value() end
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
 if frames==6400 then post("restore game\\n") end
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
'''
        for frame in (5000,5050,5100,5150,5200):
            command_events+=f' if frames=={frame} then keys["Down"]:set_value(1) end\n'
            command_events+=f' if frames=={frame+10} then keys["Down"]:clear_value() end\n'
        command_events+='''
 if frames==5300 then shot("restart-selected") end
 if frames==5350 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:set_value(1) end
 if frames==5360 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:clear_value() end
 if frames==5500 then shot("restart-prompt") end
 if frames==5650 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:set_value(1) end
 if frames==5660 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:clear_value() end
 if frames==7000 then shot("restart-scene") end
 if frames==7100 then post("look room\\n") end
 if frames==8500 then shot("restart-response") end
 if frames==8550 then post(" ") end
 if frames==8900 then shot("restart-final") end
'''
    if a.video_mode:
        delay=5000
        events=[' if frames==4000 or frames==6000 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:set_value(1) end',
                ' if frames==4010 or frames==6010 then manager.machine.ioport.ports[":KEY2"].fields["Escape"]:clear_value() end']
        for start in (4600,6200):
            for n in range(5):
                events+=[f' if frames=={start+n*50} then keys["Up"]:set_value(1) end',
                         f' if frames=={start+n*50+10} then keys["Up"]:clear_value() end']
        events+=[' if frames==4850 then shot("video-mode-selected") end',
                 ' if frames==4900 or frames==6500 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:set_value(1) end',
                 ' if frames==4910 or frames==6510 then manager.machine.ioport.ports[":KEY2"].fields["Return"]:clear_value() end',
                 ' if frames==5500 then shot("video-mode-alternate") end',
                 ' if frames==7100 then shot("video-mode-standard") end']
        command_events='\n'.join(events)+'\n'
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
 if frames==4000 or frames==4400 then keys["Right"]:set_value(1) end
 if frames==4010 or frames==4410 then keys["Right"]:clear_value() end
 if frames==5500 then shot("journey-lake") end
 if frames==6000 then post("look room\\n") end
 if frames==7000 then shot("journey-look") end
 if frames==7050 then post(" ") end
 if frames==7500 or frames==7900 then keys["Left"]:set_value(1) end
 if frames==7510 or frames==7910 then keys["Left"]:clear_value() end
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
 if frames==800 then post("mfree >/s0/free-before\\n") end
 if frames==1000 then post("wbgame /s0/game 0\\n") end
 if frames==1800 then post(" \\n") end
 if frames==3000 then shot("game-before-input") end
 -- Ctrl-I delivers ASCII Tab without MAME host Tab handling.
 if frames==3100 then keys["Ctrl"]:set_value(1) end
 if frames==3110 then i:set_value(1) end
 if frames==3120 then i:clear_value() end
 if frames==3130 then keys["Ctrl"]:clear_value() end
 if frames==3700 then shot("game-after-input") end
 if frames==3750 then post(" ") end
 if frames==3860 then shot("game-after-inventory") end
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
                  17300:'\r',19000:'\r',19600:'mfree >/s0/free-larry-after\r',21900:'\r',
                  22500:'mfree >/s0/free-after\r',23400:'echo WBGAME-DONE >/s0/wbgame-done\r'}
        for index,answer in enumerate('bbdbd a  '):commands[4000+index*800]=answer
        shots={3800:'larry-question',11000:'larry-first',15100:'castle-first',15800:'larry-restored',
               17200:'castle-inventory',18000:'castle-restored',21000:'larry-survives',24200:'both-closed'}
        switches={11200:'Right',15300:'Left',16000:'Right',20400:'Left'}
        source=lua.read_text();source=source[:source.index('sub=emu.add_machine_frame_notifier')]
        source+='sub=emu.add_machine_frame_notifier(function()\n frames=frames+1\n'
        for frame,command in sorted(commands.items()):
            source+=f' if frames=={frame} then post({json.dumps(command)}) end\n'
        for frame,name in sorted(shots.items()):
            source+=f' if frames=={frame} then shot({json.dumps(name)}) end\n'
        for frame,direction in switches.items():
            source+=f' if frames=={frame} then keys["Alt"]:set_value(1);keys["{direction}"]:set_value(1) end\n'
            source+=f' if frames=={frame+5} then keys["{direction}"]:clear_value();keys["Alt"]:clear_value() end\n'
        for frame,key in ((16600,'i'),(18300,'c'),(21200,'c')):
            source+=f' if frames=={frame} then keys["Ctrl"]:set_value(1) end\n'
            source+=f' if frames=={frame+10} then {key}:set_value(1) end\n'
            source+=f' if frames=={frame+20} then {key}:clear_value() end\n'
            source+=f' if frames=={frame+30} then keys["Ctrl"]:clear_value() end\n'
        source+=' if frames==24200 then manager.machine:exit() end\nend)\n'
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
    if a.restart:
        syms=symbols(VIEWER/'wbgame.map');code=(VIEWER/'wbgame').read_bytes()
        base=(8-(len(code)+8191)//8192)*8192
        condition=f'w@{base:x} == 87cd && w@{base+2:x} == {len(code):x}'
        events=[' if frames==950 then']
        for label in ('GameRestartCommand','VmRestartRoot','GameInitialFlags'):
            action=f'printf "RESTART {label} DEPTH=%d PENDING=%d FLAG6=%d FLAG16=%d",b@{syms["vmdepth"]:x},b@{syms["vmroompending"]:x},b@(u+{syms["vmflags"]+6:x}),b@(u+{syms["vmflags"]+16:x}); g'
            events.append(f'  cpu.debug:bpset({base+syms[label]},{json.dumps(condition)},{json.dumps(action)})')
        events.append(' end')
        source=lua.read_text().replace(' frames=frames+1',' frames=frames+1\n'+'\n'.join(events),1)
        if not a.audio_trace:
            source='local cpu=manager.machine.devices[":maincpu"]\nmanager.machine.debugger.execution_state="run"\nrestart_stop=emu.add_machine_stop_notifier(function() local log=manager.machine.debugger.consolelog;for index=1,#log do if log[index] then print(log[index]) end end end)\n'+source
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
    command=[str(a.mame.resolve()),'wbjr2','-bios','turbo','-rompath',str(roms.parent),'-hard',str(disk),'-skip_gameinfo', '-noui_mouse', '-mouseprovider', 'none','-video','none','-sound','none','-nothrottle','-autoboot_script',str(lua),'-seconds_to_run',str(420 if a.larry_pair else (5100+delay+(1200 if a.larry or a.larry_enter else 0))//60+10 if a.typed_command or a.menu or a.sustained or a.hall or a.journey or a.movement or a.persistence or a.restart or a.larry or a.larry_enter or a.video_mode else 100),'-nvram_directory',str(out/'nvram'),'-cfg_directory',str(out/'cfg')]
    if a.profile or a.audio_trace or a.restart or a.video_mode or a.hall:command+=['-debug','-debugger','none']
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
    assert 'WBGAME-DONE' in os9('list',f'{disk},wbgame-done').decode(),'game did not return to shell'
    before=os9('list',f'{disk},free-before');after=os9('list',f'{disk},free-after')
    (out/'free-before.txt').write_bytes(before);(out/'free-after.txt').write_bytes(after)
    assert before==after,'real game leaked memory'
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
        w,h,pixels=png_rgb(out/'journey-look.png')
        font=(VIEWER/'wbfont').read_bytes()
        for row,message in enumerate(('A rapidly moving stream is flowing out','of this lake.')):
            for col,char in enumerate(message):
                for y in range(8):
                    for x in range(8):
                        expected=bytes(3) if font[ord(char)*8+y]&(128>>x) else bytes([255])*3
                        at=((128+row*16+y*2)*w+32+col*16+x*2)*3
                        assert pixels[at:at+3]==expected,('lake description',row,col,x,y)
        # The castle tree can correctly occlude Graham at the arrival point.
        # A second exact room description proves continued play without assuming
        # that the hero must always be visible through foreground scenery.
        w,h,pixels=png_rgb(out/'journey-castle-look.png')
        for col,char in enumerate('You are standing outside a castle'):
            for y in range(8):
                for x in range(8):
                    expected=bytes(3) if font[ord(char)*8+y]&(128>>x) else bytes([255])*3
                    at=((128+y*2)*w+32+col*16+x*2)*3
                    assert pixels[at:at+3]==expected,('returned castle description',col,x,y)
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
        log=(out/'mame.log').read_text()
        assert 'RESTART GameRestartCommand' in log,'original script did not request restart'
        assert 'RESTART VmRestartRoot DEPTH=0 PENDING=3' in log,'restart did not unwind to the root'
        assert 'RESTART GameInitialFlags DEPTH=0 PENDING=0 FLAG6=1' in log,'restart flag was not delivered to fresh root logic'
        def center(name):
            w,h,pixels=png_rgb(out/(name+'.png'))
            assert (w,h)==(640,480)
            shirt=[i//3%w for i in range(0,len(pixels),3)
                   if pixels[i:i+3]==bytes([255,85,85]) and 120<=i//3//w<240]
            assert shirt,(name,'hero absent')
            return (min(shirt)+max(shirt))/2
        centers=[center(name) for name in ('game-before-input','restart-moved','restart-scene','restart-final')]
        assert centers[1]>centers[0]+8,('pre-restart movement absent',centers)
        assert abs(centers[2]-centers[0])<2 and abs(centers[3]-centers[0])<2,('restart position not reset',centers)
        w,h,pixels=png_rgb(out/'restart-response.png')
        assert set(pixels[i:i+3] for i in range(0,len(pixels),3))=={bytes(3),bytes([255])*3},'post-restart look dialog absent'
        (out/'restart.json').write_text(json.dumps({'shirt_centers':centers},indent=2)+'\n')
        print('PASS: original KQ1 menu restart, root-stack unwind, restart flag, reset position, subsequent look/input and unchanged free memory',centers)
        return
    if a.larry_pair:
        live=os9('list',f'{disk},free-larry');remaining=os9('list',f'{disk},free-larry-after')
        (out/'free-larry.txt').write_bytes(live);(out/'free-larry-after.txt').write_bytes(remaining)
        assert live==remaining,'exiting KQ1 did not restore Larry-only memory map'
        font=(VIEWER/'wbfont').read_bytes()
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
        for name in ('larry-first','larry-restored','larry-survives'):
            w,h,pixels=png_rgb(out/(name+'.png'));assert (w,h)==(640,480)
            assert len(set(pixels[i:i+3] for i in range(0,len(pixels),3)))>=12,(name,'Larry absent')
            sample=b''.join(pixels[(y*w+350)*3:(y*w+500)*3] for y in range(200,255))
            if background is None:background=sample
            else:assert sample==background,(name,'Larry background changed across terminal switches')
        print('PASS: simultaneous original Larry/KQ1 games, terminal restoration, independent inventory input, Larry survives KQ1 exit, Larry-only and final free-memory maps restored')
        return
    if a.larry or a.larry_enter:
        font=(VIEWER/'wbfont').read_bytes()
        def title(name,text):
            w,h,pixels=png_rgb(out/(name+'.png'));assert (w,h)==(640,480)
            for column,char in enumerate(text):
                for y in range(8):
                    for x in range(8):
                        expected=bytes(3) if font[ord(char)*8+y] & (128>>x) else bytes([255])*3
                        offset=((128+y*2)*w+32+column*16+x*2)*3
                        assert pixels[offset:offset+3]==expected,(name,column,char,x,y)
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
            assert set(pixels[i:i+3] for i in range(0,len(pixels),3))=={bytes(3),bytes([255])*3},'inside look response absent'
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
    font=(VIEWER/'wbfont').read_bytes()
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
            assert colors <= {bytes(3),bytes([255])*3,bytes([170])*3} and bytes([255])*3 in colors, 'game menu did not appear'
        else:
            assert colors == {bytes(3),bytes([255])*3}, 'typed command did not display a modal message'
        assert len(set(restored[2][i:i+3] for i in range(0,len(restored[2]),3)))>=12, 'command dismissal did not restore the scene'
    if a.sustained:
        for name in ('play-first-response','play-unknown-response','play-paused','play-second-response'):
            w,h,pixels=png_rgb(out/(name+'.png'))
            assert (w,h)==(640,480) and set(pixels[i:i+3] for i in range(0,len(pixels),3))=={bytes(3),bytes([255])*3}, ('modal missing',name)
        w,h,pixels=png_rgb(out/'play-paused.png')
        for col,char in enumerate('Game paused. Press a key to resume.'):
            for gy in range(8):
                for gx in range(8):
                    expected=bytes(3) if font[ord(char)*8+gy] & (128>>gx) else bytes([255])*3
                    address=((128+gy*2)*w+32+col*16+gx*2)*3
                    assert pixels[address:address+3]==expected, 'Pause menu selection did not reach the pause command'
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
        assert abs(centers[1]-centers[0])>8,('game did not change position before restore',centers)
        assert abs(centers[2]-centers[0])<=4 and abs(centers[3]-centers[0])<=4,('restore did not recover position',centers)
        response=png_rgb(out/'restore-response.png')[2]
        assert set(response[i:i+3] for i in range(0,len(response),3))=={bytes(3),bytes([255])*3}, 'look response after restore missing'
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
