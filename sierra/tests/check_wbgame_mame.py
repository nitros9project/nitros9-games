#!/usr/bin/env python3
"""Run unmodified game resources on real Wild Bits drivers; diagnostic only."""
import argparse,json,re,shutil,subprocess
from pathlib import Path
from check_wbpic_mame import VIEWER,png_rgb

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
    a=ap.parse_args(); out=a.output.resolve(); out.mkdir(parents=True,exist_ok=False)
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
    install('wbgame',(a.module_file or (VIEWER/'wbgame')).read_bytes(),'CMDS/wbgame')
    os9('attr',f'{disk},CMDS/wbgame','-e','-pe')
    install('wbfont',(VIEWER/'wbfont').read_bytes(),'CMDS/wbfont')
    os9('attr',f'{disk},CMDS/wbfont','-e','-pe')
    install('startup',b'load utilpak1\nlink shell\nload wbgame\nload grfdrv256\n',text=True)
    install('feu.startup',b'bootos9 /s0/OS9Boot\n','FEU/startup',text=True)
    with disk.open('ab') as f:f.truncate(1 << (disk.stat().st_size-1).bit_length())
    response_frame=4000+max(700,120*len(a.typed_command or ""))
    if sum(bool(v) for v in (a.menu,a.typed_command,a.sustained,a.movement))>1:
        ap.error("choose menu, typed-command, sustained or movement")
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
    command=[str(a.mame.resolve()),'wbjr2','-bios','turbo','-rompath',str(roms.parent),'-hard',str(disk),'-skip_gameinfo', '-noui_mouse', '-mouseprovider', 'none','-video','none','-sound','none','-nothrottle','-autoboot_script',str(lua),'-seconds_to_run',str((5100+delay)//60+10 if a.typed_command or a.menu or a.sustained or a.movement else 100),'-nvram_directory',str(out/'nvram'),'-cfg_directory',str(out/'cfg')]
    (out/'command.json').write_text(json.dumps(command,indent=2)+'\n')
    with (out/'mame.log').open('w') as log:subprocess.run(command,cwd=out,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
    exits=re.findall(r'wbgame error, opcode: ([0-9A-F]{2})', (out/'mame.log').read_text())
    assert all(code == 'E4' for code in exits), f'unexpected game exit {exits}; inspect opcode trace'
    assert 'WBGAME-DONE' in os9('list',f'{disk},wbgame-done').decode(),'game did not return to shell'
    before=os9('list',f'{disk},free-before');after=os9('list',f'{disk},free-after')
    (out/'free-before.txt').write_bytes(before);(out/'free-after.txt').write_bytes(after)
    assert before==after,'real game leaked memory'
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
