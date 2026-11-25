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
    modes.add_argument('--text-preview',action='store_true',help='Check item visibility and restoration from opaque text mode')
    modes.add_argument('--monitor',action='store_true',help='Check native/CoCo RGB palette switching on real drivers')
    modes.add_argument('--joystick',action='store_true',help='Check real-driver joystick enable, neutral polling, toggle and cleanup')
    modes.add_argument('--version',action='store_true',help='Check the interpreter information dialog instead of an item preview')
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
    for name in ('wbgame','sierrastate','sierraui','sierrafont'):
        install(name,(root/'objs'/name).read_bytes(),'CMDS/'+name);os9('attr',f'{disk},CMDS/{name}','-e','-pe')
    install('startup',b'load utilpak1\nlink shell\nload wbgame\nload grfdrv256\n',text=True)
    install('feu.startup',b'bootos9 /s0/OS9Boot\n','FEU/startup',text=True)
    if a.boot_file:install('OS9Boot',a.boot_file.read_bytes())
    # Subsequent root cycles idle until the bound q controller quits normally.
    script=bytes([255,12,1,255,3,0,134,1,0,255,7,20,255,1,0,0,3,10,2,121,113,0,1,3,0,1,24,0,25,0,26,129,0,3,240,73,119,12,20,0])
    if a.text_preview:script=script.replace(bytes([129,0]),bytes([106,129,0]))
    if a.version:script=script.replace(bytes([129,0]),bytes([141]))
    if a.joystick:
        script=bytes([255,12,1,255,3,0,134,1,0,
                      255,12,2,255,4,0,139,3,240,74,
                      255,7,20,255,1,0,0,3,10,2,121,113,0,1,121,106,0,2,
                      3,0,1,24,0,25,0,33,0,41,0,0,37,0,40,80,54,0,15,35,0,26,
                      139,3,240,73,119,12,20,0])
    if a.monitor:
        script=bytes([255,12,1,255,3,0,134,1,0,
                      255,12,2,255,3,0,140,1,240,
                      255,7,20,255,1,0,0,3,10,2,121,113,0,1,121,118,0,2,
                      3,0,1,24,0,25,0,33,0,41,0,0,37,0,40,80,54,0,15,35,0,26,
                      3,240,73,119,12,20,0])
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
    if a.monitor:
        select=f'{condition} && b@(w@{syms["resourcebase"]:x}+{syms["vmopcode"]:x})==8c'
        action=f'printf "MONITOR TOGGLE %d",b@(u+{syms["monitorprofile"]:x}); g'
        lines.append(f'  cpu.debug:bpset({base+syms["GameMonitorCommand"]},{json.dumps(select)},{json.dumps(action)})')
        action=f'printf "MONITOR QUIT %d %d",b@(u+{syms["vmvariables"]+240:x}),b@(u+{syms["monitorprofile"]:x}); g'
        lines.append(f'  cpu.debug:bpset({base+syms["GameQuitCommand"]},{json.dumps(condition)},{json.dumps(action)})')
    elif a.joystick:
        calls=[int(m[1],16)+3 for m in re.finditer(r'^([0-9A-F]{4}) 103F8D.*os9.*I\$GetStt',
               (root/'objs/wbgame.list').read_text(),re.M)
               if syms['GamePollJoystick']<=int(m[1],16)<syms['GameJoystickDisable']]
        assert len(calls)==1,calls
        for offset,action in [(calls[0],'printf "JOYSTICK SAMPLE %d %d %d",x,y,a; g'),
                              (syms['GameJoystickCommand'],'printf "JOYSTICK TOGGLE %d",b@(u+'+f'{syms["joystickenabled"]:x}'+'); g')]:
            lines.append(f'  cpu.debug:bpset({base+offset},{json.dumps(condition)},{json.dumps(action)})')
        action=f'printf "JOYSTICK QUIT %d %d",b@(u+{syms["vmvariables"]+240:x}),b@(u+{syms["joystickenabled"]:x}); g'
        lines.append(f'  cpu.debug:bpset({base+syms["GameQuitCommand"]},{json.dumps(condition)},{json.dumps(action)})')
    else:
        for label,tag in [('GamePrintWait','MODAL'),('ScreenCommand','RESUMED')]:
            action=f'printf "PREVIEW {tag} %d %d",b@{syms["vmopcode"]:x},b@(u+{syms["vmvariables"]+240:x}); g'
            lines.append(f'  cpu.debug:bpset({base+syms[label]},{json.dumps(condition)},{json.dumps(action)})')
    lines+=[' end',' if frames==800 then post("mfree >/s0/free-before\\n") end',' if frames==1000 then post("wbgame /s0/preview 1\\n") end',' if frames==1400 then shot("preview-visible") end',' if frames==1500 then post(" ") end',' if frames==1700 then shot("preview-restored") end',' if frames==2000 then post("q") end',' if frames==2300 then post("mfree >/s0/free-after\\n") end',' if frames==2500 then post("echo DONE >/s0/done\\n") end',' if frames==3100 then shot("closed");manager.machine:exit() end','end)']
    if a.monitor:
        lines[lines.index(' if frames==1500 then post(" ") end')]=' if frames==1500 then post("v") end'
        at=lines.index(' if frames==2000 then post("q") end')
        lines[at:at]=[' if frames==1800 then post("v") end',' if frames==1900 then shot("monitor-standard-again") end']
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
    if a.monitor:
        assert re.findall(r'MONITOR TOGGLE (\d+)',log)==['0','1'],log[-2000:]
        assert 'MONITOR QUIT 75 0' in log,log[-2000:]
    elif a.joystick:
        samples=[tuple(map(int,row)) for row in re.findall(r'JOYSTICK SAMPLE (\d+) (\d+) (\d+)',log)]
        assert len(samples)>=3 and all(row==(128,128,0) for row in samples),samples
        assert re.findall(r'JOYSTICK TOGGLE (\d+)',log)==['0','1'],log[-2000:]
        assert 'JOYSTICK QUIT 74 0' in log,log[-2000:]
        (out/'joystick.json').write_text(json.dumps({'samples':samples,'marker':74,'enabled_at_quit':False},indent=2)+'\n')
    else:
        assert ('PREVIEW MODAL 141 0' if a.version else 'PREVIEW MODAL 129 0') in log,log[-2000:]
        assert 'PREVIEW RESUMED 119 73' in log,log[-2000:]
    for name in ('free-before','free-after','done'):
        target=out/(name+'.txt');os9('copy',f'{disk},{name}',target)
        assert target.is_file(),f'missing shell output: {name}'
    assert (out/'free-before.txt').read_bytes()==(out/'free-after.txt').read_bytes()
    assert b'DONE' in (out/'done.txt').read_bytes()
    if a.monitor:
        def pixel(path,x,y):
            w,h,pixels=png_rgb(path);assert (w,h)==(640,480)
            at=(y*w+x)*3;return pixels[at:at+3]
        first=out/'preview-visible.png';alternate=out/'preview-restored.png';last=out/'monitor-standard-again.png'
        assert pixel(first,172,172)==bytes([0,170,0])
        assert pixel(alternate,172,172)==bytes([85,170,0])
        assert png_rgb(first)==png_rgb(last),'returning to AGI palette changed the scene'
        print('PASS: real-driver CoCo RGB palette, exact changed color, switch back, caller continuation and memory cleanup')
    elif a.joystick:
        assert png_rgb(out/'preview-visible.png')==png_rgb(out/'preview-restored.png'),'neutral joystick altered the scene'
        print('PASS: real-driver joystick enable, neutral axes/buttons, toggle, script continuation and memory cleanup')
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
        font=(root/'objs/sierrafont').read_bytes()
        # The information source has two CR-separated strings, but the first
        # long line wraps at the production modal's word boundary.
        messages=['Adventure Game','Interpreter','Version 2.072'] if a.version else ['A FINE TREASURE.']
        # Modal output uses the native text plane's white-on-black character
        # cells. The one-line preview description is centered in the 40-column
        # plane at cell (10,10), rendered as 16x16 MAME pixels per glyph. The
        # text-screen preview enters this same modal renderer.
        glyph_x,glyph_y=160,160
        glyph_fg,glyph_bg=bytes([255])*3,bytes(3)
        for row,message in enumerate(messages):
            for col,char in enumerate(message):
                for y in range(8):
                    for x in range(8):
                        expected=glyph_fg if font[ord(char)*8+y]&(128>>x) else glyph_bg
                        at=((glyph_y+row*16+y*2)*w+glyph_x+col*16+x*2)*3
                        assert pixels[at:at+3]==expected,('dialog glyph',row,col,x,y)
        w,h,pixels=png_rgb(out/'preview-restored.png')
        for y in range(h):
            expected=(bytes([255])*3 if 16<=y<352 else bytes(3))*w
            assert pixels[y*w*3:(y+1)*w*3]==expected,('restored scene row',y)
        print('PASS: real-driver '+('interpreter information' if a.version else 'item pixels and description')+', keyboard dismissal, subsequent script execution, exact scene restoration and memory cleanup')



if __name__ == "__main__":
    main()
