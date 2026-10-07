#!/usr/bin/env python3
"""Check native inventory previews on real Wild Bits display drivers.

Uses generated picture/view/logic resources and a private disk/firmware clone.
Checks preview pixels, description glyphs, dismissal, continuation and cleanup.
"""
from pathlib import Path
import argparse,shutil,subprocess,json,re
from check_instances import symbols
from check_wbpic_mame import png_rgb


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('mame','disk','firmware','output'):
        ap.add_argument('--'+name,required=True,type=Path)
    ap.add_argument('--boot-file',type=Path,help='Optional matching OS9 boot image')
    modes=ap.add_mutually_exclusive_group()
    modes.add_argument('--joystick',action='store_true',help='Check real-driver joystick enable, neutral polling, toggle and cleanup')
    modes.add_argument('--version',action='store_true',help='Check the interpreter information dialog instead of an item preview')
    modes.add_argument('--shake',action='store_true',help='Check shake.screen timing and restoration instead of an item preview')
    ap.add_argument('--interrupt',action='store_true',help='Exit with Ctrl-C instead of the bound quit controller')
    a=ap.parse_args()
    root=Path(__file__).resolve().parents[1]
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    disk=out/'test.dsk';shutil.copyfile(a.disk,disk)
    roms=out/'roms/wbjr2';roms.mkdir(parents=True)
    for name in ('booter','f0.dsk'):shutil.copyfile(a.firmware/name,roms/name)
    def os9(*args):return subprocess.check_output(['os9',*map(str,args)],stderr=subprocess.STDOUT)
    def install(name,data,target=None,text=False):
        p=out/name;p.write_bytes(data);os9('copy','-r',*(['-l'] if text else []),p,f'{disk},{target or name}')
    os9('makdir',f'{disk},preview')
    for name in ('wbgame','wbstate','wbfont'):
        install(name,(root/'objs'/name).read_bytes(),'CMDS/'+name);os9('attr',f'{disk},CMDS/{name}','-e','-pe')
    install('startup',b'load utilpak1\nlink shell\nload wbgame\nload grfdrv256\n',text=True)
    install('feu.startup',b'bootos9 /s0/OS9Boot\n','FEU/startup',text=True)
    if a.boot_file:install('OS9Boot',a.boot_file.read_bytes())
    # Subsequent root cycles idle until the bound q controller quits normally.
    script=bytes([255,12,1,255,3,0,134,1,0,255,7,20,255,1,0,0,3,10,2,121,113,0,1,3,0,1,24,0,25,0,26,129,0,3,240,73,119,12,20,0])
    if a.version:script=script.replace(bytes([129,0]),bytes([141]))
    if a.shake:
        script=bytes([255,12,1,255,3,0,134,1,0,255,7,20,255,1,0,0,3,10,2,121,113,0,1,
                      3,0,1,24,0,25,0,33,0,41,0,0,37,0,40,80,54,0,15,35,0,26,110,1,
                      3,240,73,119,12,20,0])
    if a.joystick:
        script=bytes([255,12,1,255,3,0,134,1,0,
                      255,12,2,255,4,0,139,3,240,74,
                      255,7,20,255,1,0,0,3,10,2,121,113,0,1,121,106,0,2,
                      3,0,1,24,0,25,0,33,0,41,0,0,37,0,40,80,54,0,15,35,0,26,
                      139,3,240,73,119,12,20,0])
    logic=len(script).to_bytes(2,'little')+script
    view=bytearray([0,0,1,0,0,7,0,1,3,0,4,3,31,0x12,0xf1,0x21,0,0x31,0x43,0,0x51,0])
    view[3:5]=len(view).to_bytes(2,'little');view+=b'A FINE TREASURE.\0'
    volume=bytearray();offsets=[]
    for payload in (logic,b'\xff',view):
        offsets.append(len(volume));volume+=b'\x12\x34\0'+len(payload).to_bytes(2,'little')*2+payload
    install('logDir',b'\xff'*3+offsets[0].to_bytes(3,'big'),'preview/logDir')
    install('picDir',b'\xff'*3+offsets[1].to_bytes(3,'big'),'preview/picDir')
    install('viewDir',offsets[2].to_bytes(3,'big'),'preview/viewDir')
    install('vol.0',volume,'preview/vol.0')
    with disk.open('ab') as f:f.truncate(1<<(disk.stat().st_size-1).bit_length())
    syms=symbols(root/'objs/wbgame.map');size=(root/'objs/wbgame').stat().st_size;base=0xa000
    condition=f'w@{base:x} == 87cd && w@{base+2:x} == {size:x}'
    lines=['local cpu=manager.machine.devices[":maincpu"]','manager.machine.debugger.execution_state="run"','local frames=0','local function post(s) manager.machine.natkeyboard:post(s) end',f'local function shot(name) manager.machine.screens[":screen"]:snapshot({json.dumps(str(out)+"/")}..name..".png") end','stopped=emu.add_machine_stop_notifier(function() local log=manager.machine.debugger.consolelog;for index=1,#log do if log[index] then print(log[index]) end end end)','sub=emu.add_machine_frame_notifier(function()',' frames=frames+1',' if frames==950 then']
    if a.joystick:
        calls=[int(m[1],16)+3 for m in re.finditer(r'^([0-9A-F]{4}) 103F8D.*os9.*I\$GetStt',
               (root/'objs/wbgame.list').read_text(),re.M)
               if syms['GamePollJoystick']<=int(m[1],16)<syms['GameJoystickDisable']]
        assert len(calls)==1,calls
        for offset,action in [(calls[0],'printf "JOYSTICK SAMPLE %d %d %d",x,y,a; g'),
                              (syms['GameJoystickCommand'],'printf "JOYSTICK TOGGLE %d",b@(u+'+f'{syms["joystickenabled"]:x}'+'); g')]:
            lines.append(f'  cpu.debug:bpset({base+offset},{json.dumps(condition)},{json.dumps(action)})')
        action=f'printf "JOYSTICK QUIT %d %d",b@(u+{syms["vmvariables"]+240:x}),b@(u+{syms["joystickenabled"]:x}); g'
        lines.append(f'  cpu.debug:bpset({base+syms["GameQuitCommand"]},{json.dumps(condition)},{json.dumps(action)})')
    elif a.shake:
        helper=symbols(root/'objs/wbstate.map')
        wait=f'printf "SHAKE WAIT %d %d %d",totalcycles,b@(w@{syms["resourcebase"]:x}+{syms["shakeshifted"]:x}),b@(w@{syms["resourcebase"]:x}+{syms["gameclockpath"]:x}); g'
        end=f'printf "SHAKE NEXT %d %d",totalcycles,b@(w@{syms["resourcebase"]:x}+{syms["shakeshifted"]:x}); g'
        shifted='snap "shake-shifted"; g'
        cold_guard=f'{condition} && b@(w@{syms["resourcebase"]:x}+{syms["vmopcode"]:x})==6e'
        shifted_guard=f'{cold_guard} && b@(w@{syms["resourcebase"]:x}+{syms["shakeshifted"]:x})==1'
        action=(f'bpset u+{helper["AuxShakeWait"]:x},{cold_guard},{{{wait}}}; '
                f'bpset u+{helper["AuxShakeNext"]:x},{cold_guard},{{{end}}}; '
                f'bpset u+{helper["AuxShakeDelta"]:x},{shifted_guard},{{{shifted}}}; '
                f'bpset u+{helper["AuxShakeSleepFallback"]:x},{shifted_guard},{{{shifted}}}; '
                f'printf "SHAKE MODULE %d",u; g')
        selector=f'{condition} && b@s == 12'
        lines.append(f'  cpu.debug:bpset({base+syms["GameColdMetadata"]},{json.dumps(selector)},{json.dumps(action)})')
        for label,tag in [('GameShakeCommand','START'),('ScreenCommand','END')]:
            action=f'printf "SHAKE {tag} %d %d",totalcycles,b@(u+{syms["vmvariables"]+240:x}); g'
            lines.append(f'  cpu.debug:bpset({base+syms[label]},{json.dumps(condition)},{json.dumps(action)})')
    else:
        for label,tag in [('GamePrintWait','MODAL'),('ScreenCommand','RESUMED')]:
            action=f'printf "PREVIEW {tag} %d %d",b@{syms["vmopcode"]:x},b@(u+{syms["vmvariables"]+240:x}); g'
            lines.append(f'  cpu.debug:bpset({base+syms[label]},{json.dumps(condition)},{json.dumps(action)})')
    lines+=[' end',' if frames==800 then post("mfree >/s0/free-before\\n") end',' if frames==1000 then post("wbgame /s0/preview 1\\n") end',' if frames==1400 then shot("preview-visible") end',' if frames==1500 then post(" ") end',' if frames==1700 then shot("preview-restored") end',' if frames==2000 then post("q") end',' if frames==2300 then post("mfree >/s0/free-after\\n") end',' if frames==2500 then post("echo DONE >/s0/done\\n") end',' if frames==3100 then shot("closed");manager.machine:exit() end','end)']
    if a.joystick:lines[lines.index(' if frames==1500 then post(" ") end')]=' if frames==1500 then post("j") end'
    if a.interrupt:
        lines.insert(0,'local c=nil;for _,field in pairs(manager.machine.ioport.ports[":KEY0"].fields) do if field.mask==4 then c=field end end;assert(c,"C key missing")')
        event=lines.index(' if frames==2000 then post("q") end')
        lines[event:event+1]=[
            ' if frames==2000 then manager.machine.ioport.ports[":KEY3"].fields["Ctrl"]:set_value(1) end',
            ' if frames==2010 then c:set_value(1) end',
            ' if frames==2020 then c:clear_value() end',
            ' if frames==2030 then manager.machine.ioport.ports[":KEY3"].fields["Ctrl"]:clear_value() end',
            ' if frames==2200 then post("\\n") end']
    lua=out/'drive.lua';lua.write_text('\n'.join(lines)+'\n')
    cmd=[str(a.mame.resolve()),'wbjr2','-bios','turbo','-rompath',str(roms.parent),'-hard',str(disk),'-skip_gameinfo','-noui_mouse','-mouseprovider','none','-video','none','-sound','none','-nothrottle','-autoboot_script',str(lua),'-seconds_to_run','60','-nvram_directory',str(out/'nvram'),'-cfg_directory',str(out/'cfg'),'-snapshot_directory',str(out),'-debug','-debugger','none']
    (out/'command.json').write_text(json.dumps(cmd,indent=2))
    with (out/'mame.log').open('w') as log:subprocess.run(cmd,cwd=out,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
    log=(out/'mame.log').read_text()
    if a.joystick:
        samples=[tuple(map(int,row)) for row in re.findall(r'JOYSTICK SAMPLE (\d+) (\d+) (\d+)',log)]
        assert len(samples)>=3 and all(row==(128,128,0) for row in samples),samples
        assert re.findall(r'JOYSTICK TOGGLE (\d+)',log)==['0','1'],log[-2000:]
        assert 'JOYSTICK QUIT 74 0' in log,log[-2000:]
        (out/'joystick.json').write_text(json.dumps({'samples':samples,'marker':74,'enabled_at_quit':False},indent=2)+'\n')
    elif a.shake:
        events=re.findall(r'SHAKE (START|WAIT|NEXT|END) (\d+) (\d+)(?: (\d+))?',log)
        (out/'shake-events.json').write_text(json.dumps(events,indent=2)+'\n')
        starts=[event for event in events if event[0]=='START'];ends=[event for event in events if event[0]=='END']
        phases=[event for event in events if event[0]=='NEXT']
        assert len(starts)==1 and len(ends)==1 and int(ends[0][2])==73,events
        assert len(phases)==8 and [int(event[2]) for event in phases]==[1,0]*4,phases
        seconds=(int(ends[0][1])-int(starts[0][1]))/12587500
        assert .49<=seconds<=1.5,seconds
        assert len([event for event in events if event[0]=='WAIT'])>=8,events
        (out/'shake-timing.json').write_text(json.dumps({'seconds':seconds,'counter_active':all(event[3]!='255' for event in events if event[0]=='WAIT')},indent=2)+'\n')
    else:
        assert ('PREVIEW MODAL 141 0' if a.version else 'PREVIEW MODAL 129 0') in log,log[-2000:]
        assert 'PREVIEW RESUMED 119 73' in log,log[-2000:]
    for name in ('free-before','free-after','done'):
        target=out/(name+'.txt');os9('copy',f'{disk},{name}',target)
        assert target.is_file(),f'missing shell output: {name}'
    assert (out/'free-before.txt').read_bytes()==(out/'free-after.txt').read_bytes()
    assert b'DONE' in (out/'done.txt').read_bytes()
    if a.joystick:
        assert png_rgb(out/'preview-visible.png')==png_rgb(out/'preview-restored.png'),'neutral joystick altered the scene'
        print('PASS: real-driver joystick enable, neutral axes/buttons, toggle, script continuation and memory cleanup')
    elif a.shake:
        def colors(path):
            w,h,pixels=png_rgb(path);assert (w,h)==(640,480)
            blue=[]
            for y in range(480):
                for x in range(640):
                    at=(y*w+x)*3
                    if pixels[at:at+3]==bytes([0,0,170]):blue.append((x,y))
            assert blue,path
            return (min(x for x,y in blue),min(y for x,y in blue))
        shifted=colors(out/'shake-shifted.png');restored=colors(out/'preview-restored.png')
        assert shifted==(restored[0]+16,restored[1]+8),(shifted,restored)
        assert restored==(160,172),restored
        print('PASS: real-driver shake displacement, eight phases, subsequent script execution, exact sprite restoration and memory cleanup',seconds)
    else:
        w,h,pixels=png_rgb(out/'preview-visible.png');assert (w,h)==(640,480)
        if not a.version:
            palette=[bytes([0,0,170]),bytes([0,170,0]),bytes([0,170,170]),bytes([170,0,0]),bytes([170,0,170])]
            rows=[[palette[0]]*4+[bytes([255])*3]*2+[palette[1]]*2,
                  [palette[2]]*2+[palette[3]]*6,[palette[4]]*2+[bytes([255])*3]*6]
            for y,row in enumerate(rows):
                for x,color in enumerate(row):
                    at=((346+y*2)*w+312+x*2)*3
                    assert pixels[at:at+3]==color,('preview pixel',x,y,pixels[at:at+3],color)
        font=(root/'objs/wbfont').read_bytes()
        messages=['Adventure Game Interpreter','Wild Bits NitrOS-9 engine'] if a.version else ['A FINE TREASURE.']
        for row,message in enumerate(messages):
            for col,char in enumerate(message):
                for y in range(8):
                    for x in range(8):
                        expected=bytes(3) if font[ord(char)*8+y]&(128>>x) else bytes([255])*3
                        at=((128+row*16+y*2)*w+32+col*16+x*2)*3
                        assert pixels[at:at+3]==expected,('dialog glyph',row,col,x,y)
        w,h,pixels=png_rgb(out/'preview-restored.png')
        for y in range(h):
            expected=(bytes([255])*3 if 16<=y<352 else bytes(3))*w
            assert pixels[y*w*3:(y+1)*w*3]==expected,('restored scene row',y)
        print('PASS: real-driver '+('interpreter information' if a.version else 'item pixels and description')+', keyboard dismissal, subsequent script execution, exact scene restoration and memory cleanup')



if __name__ == "__main__":
    main()
