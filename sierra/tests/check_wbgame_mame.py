#!/usr/bin/env python3
"""Run unmodified game resources on real Wild Bits drivers; diagnostic only."""
import argparse,json,re,shutil,subprocess
from pathlib import Path
from check_wbpic_mame import VIEWER,png_rgb
from check_instances import symbols
import statistics

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('mame','disk','firmware','game','output'):
        ap.add_argument('--'+name,required=True,type=Path)
    ap.add_argument('--os9',default='os9')
    ap.add_argument('--module-file',type=Path)
    ap.add_argument('--typed-command', help='Exercise one command after inventory dismissal')
    ap.add_argument('--menu',action='store_true',help='Open and cancel the actual game menu')
    ap.add_argument('--sustained',action='store_true',help='Repeat commands and select Pause through the real game menu')
    ap.add_argument('--movement',action='store_true',help='Measure KQ1 movement over 200 emulated frames')
    ap.add_argument('--larry',action='store_true',help='Exercise Larry age quiz, street walking and look response')
    ap.add_argument('--larry-enter',action='store_true',help="Exercise Larry quiz and entering Lefty's")
    ap.add_argument('--larry-pair',type=Path,help="Run Larry and this King's Quest I directory on two terminals")
    ap.add_argument('--expanded-krnp2',type=Path,help='Install an emulator-only expanded-memory Jr2 kernel in the private test image')
    ap.add_argument('--sol-driver',type=Path,help='Install a verified shared raster-clock driver in the private test image')
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
    if a.larry_pair:
        os9('makdir',f'{disk},castle')
        for source in a.larry_pair.iterdir():
            if source.is_file() and (source.name.startswith('vol.') or source.name in ('logDir','picDir','viewDir','sndDir','words.tok','object')):
                install('castle-'+source.name,source.read_bytes(),'castle/'+source.name)
    install('wbgame',(a.module_file or (VIEWER/'wbgame')).read_bytes(),'CMDS/wbgame')
    os9('attr',f'{disk},CMDS/wbgame','-e','-pe')
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
    response_frame=4000+max(700,120*len(a.typed_command or ""))
    if sum(bool(v) for v in (a.menu,a.typed_command,a.sustained,a.movement,a.larry,a.larry_enter,a.larry_pair))>1:
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
            events.append(f'  cpu.debug:bpset({base+syms[label]},{json.dumps(condition)},{json.dumps(action)})')
        events+=[' end',' if frames==11900 then','  cpu.debug:bpclear()',
                 '  local log=manager.machine.debugger.consolelog',
                 '  for index=1,#log do if log[index] then print(log[index]) end end',' end']
        source=lua.read_text()
        source='local cpu=manager.machine.devices[":maincpu"]\nmanager.machine.debugger.execution_state="run"\n'+source
        source=source.replace(' frames=frames+1',' frames=frames+1\n'+'\n'.join(events),1)
        lua.write_text(source)
    command=[str(a.mame.resolve()),'wbjr2','-bios','turbo','-rompath',str(roms.parent),'-hard',str(disk),'-skip_gameinfo', '-noui_mouse', '-mouseprovider', 'none','-video','none','-sound','none','-nothrottle','-autoboot_script',str(lua),'-seconds_to_run',str(420 if a.larry_pair else (5100+delay+(1200 if a.larry or a.larry_enter else 0))//60+10 if a.typed_command or a.menu or a.sustained or a.movement or a.larry or a.larry_enter else 100),'-nvram_directory',str(out/'nvram'),'-cfg_directory',str(out/'cfg')]
    if a.profile:command+=['-debug','-debugger','none']
    (out/'command.json').write_text(json.dumps(command,indent=2)+'\n')
    with (out/'mame.log').open('w') as log:subprocess.run(command,cwd=out,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=360 if a.larry_pair else 300 if a.larry or a.larry_enter else 180)
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
        print('PASS: bounded production phase profile; artifacts',out/'profile.json')
    exits=re.findall(r'wbgame error, opcode: ([0-9A-F]{2})', (out/'mame.log').read_text())
    assert all(code == 'E4' for code in exits), f'unexpected game exit {exits}; inspect opcode trace'
    assert 'WBGAME-DONE' in os9('list',f'{disk},wbgame-done').decode(),'game did not return to shell'
    before=os9('list',f'{disk},free-before');after=os9('list',f'{disk},free-after')
    (out/'free-before.txt').write_bytes(before);(out/'free-after.txt').write_bytes(after)
    assert before==after,'real game leaked memory'
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
