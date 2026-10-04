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
 if frames==3900 then keys["Ctrl"]:set_value(1) end
 if frames==3910 then c:set_value(1) end
 if frames==3920 then c:clear_value() end
 if frames==3930 then keys["Ctrl"]:clear_value() end
 if frames==4500 then post("\\n") end
 if frames==4600 then post("mfree >/s0/free-after\\n") end
 if frames==4800 then post("echo WBGAME-DONE >/s0/wbgame-done\\n") end
 if frames==5100 then shot("game-closed");manager.machine:exit() end
end)
""")
    command=[str(a.mame.resolve()),'wbjr2','-bios','turbo','-rompath',str(roms.parent),'-hard',str(disk),'-skip_gameinfo','-video','none','-sound','none','-nothrottle','-autoboot_script',str(lua),'-seconds_to_run','100','-nvram_directory',str(out/'nvram'),'-cfg_directory',str(out/'cfg')]
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
    print('PASS: real-resource startup, inventory glyphs, restored scene, interrupt exit and unchanged memory on Wild Bits drivers; parser/audio/full gameplay not claimed')
    print('Artifacts:',out)
if __name__=='__main__':main()
