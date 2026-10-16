#!/usr/bin/env python3
"""Measure native print timeouts against the real Wild Bits raster service.

Uses generated AGI messages and a private disk/firmware clone; no game assets
or visible emulator are needed. The disk/optional boot must contain the shared
SOL counter driver. Run with the wbjr2 turbo MAME fork.
"""
from pathlib import Path
import argparse,shutil,subprocess,json,re
from check_instances import symbols
from check_wbpic_mame import png_rgb


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('mame','disk','firmware','output'):
        ap.add_argument('--'+name,required=True,type=Path)
    ap.add_argument('--boot-file',type=Path,help='Optional matching boot image with the public SOL counter driver')
    a=ap.parse_args()
    root=Path(__file__).resolve().parents[1]
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    disk=out/'test.dsk';shutil.copyfile(a.disk,disk)
    roms=out/'roms/wbjr2';roms.mkdir(parents=True)
    for name in ('booter','f0.dsk'):shutil.copyfile(a.firmware/name,roms/name)
    def os9(*args):return subprocess.check_output(['os9',*map(str,args)],stderr=subprocess.STDOUT)
    def install(name,data,target=None,text=False):
        p=out/name;p.write_bytes(data);os9('copy','-r',*(['-l'] if text else []),p,f'{disk},{target or name}')
    os9('makdir',f'{disk},timed')
    for name in ('wbgame','wbstate','wbui','wbfont'):
        install(name,(root/'objs'/name).read_bytes(),'CMDS/'+name);os9('attr',f'{disk},CMDS/{name}','-e','-pe')
    install('startup',b'load utilpak1\nlink shell\nload wbgame\nload grfdrv256\n',text=True)
    install('feu.startup',b'bootos9 /s0/OS9Boot\n','FEU/startup',text=True)
    if a.boot_file:install('OS9Boot',a.boot_file.read_bytes())
    script=bytes([3,21,1,101,1,3,21,2,3,6,2,102,6,3,21,1,151,3,3,7,12,3,21,1,3,6,4,152,6,4,8,12,101,5,134,1,0])
    messages=[b'TIMER ONE',b'TIMER TWO',b'POSITION ONE',b'POSITION TWO',b'TIMERS COMPLETE']
    plain=b'';offsets=[]
    for msg in messages:offsets.append(2+2*len(messages)+len(plain));plain+=msg+b'\0'
    key=b'Avis Durgan';encrypted=bytes(v^key[i%len(key)] for i,v in enumerate(plain))
    logic=len(script).to_bytes(2,'little')+script+bytes([len(messages)])+(2+2*len(messages)+len(plain)).to_bytes(2,'little')+b''.join(p.to_bytes(2,'little') for p in offsets)+encrypted
    install('logDir',b'\xff'*3+bytes(3),'timed/logDir');install('vol.0',b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic,'timed/vol.0')
    with disk.open('ab') as f:f.truncate(1<<(disk.stat().st_size-1).bit_length())
    syms=symbols(root/'objs/wbgame.map');size=(root/'objs/wbgame').stat().st_size;base=0xa000
    condition=f'w@{base:x} == 87cd && w@{base+2:x} == {size:x}'
    lines=['local cpu=manager.machine.devices[":maincpu"]','manager.machine.debugger.execution_state="run"','local frames=0','local function post(s) manager.machine.natkeyboard:post(s) end',f'local function shot(name) manager.machine.screens[":screen"]:snapshot({json.dumps(str(out)+"/")}..name..".png") end','stopped=emu.add_machine_stop_notifier(function() local log=manager.machine.debugger.consolelog;for index=1,#log do if log[index] then print(log[index]) end end end)','sub=emu.add_machine_frame_notifier(function()',' frames=frames+1',' if frames==950 then']
    for label,tag in [('GamePrintWait','START'),('GamePrintRestore','END')]:
        action=f'printf "TIMER {tag} %d %d %d %d",totalcycles,b@{syms["vmopcode"]:x},b@(u+{syms["vmvariables"]+21:x}),b@(u+{syms["gameclockpath"]:x}); g'
        lines.append(f'  cpu.debug:bpset({base+syms[label]},{json.dumps(condition)},{json.dumps(action)})')
    lines+=[' end',' if frames==800 then post("mfree >/s0/free-before\\n") end',' if frames==1000 then post("wbgame /s0/timed 1\\n") end',' if frames==1800 then shot("timers-complete") end',' if frames==1900 then post(" ") end',' if frames==2100 then post("mfree >/s0/free-after\\n") end',' if frames==2300 then post("echo DONE >/s0/done\\n") end',' if frames==3100 then shot("closed");manager.machine:exit() end','end)']
    lua=out/'drive.lua';lua.write_text('\n'.join(lines)+'\n')
    cmd=[str(a.mame.resolve()),'wbjr2','-bios','turbo','-rompath',str(roms.parent),'-hard',str(disk),'-skip_gameinfo','-noui_mouse','-mouseprovider','none','-video','none','-sound','none','-nothrottle','-autoboot_script',str(lua),'-seconds_to_run','60','-nvram_directory',str(out/'nvram'),'-cfg_directory',str(out/'cfg'),'-debug','-debugger','none']
    (out/'command.json').write_text(json.dumps(cmd,indent=2))
    with (out/'mame.log').open('w') as log:subprocess.run(cmd,cwd=out,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
    log=(out/'mame.log').read_text();events=re.findall(r'TIMER (START|END) (\d+) (\d+) (\d+) (\d+)',log)
    (out/'events.json').write_text(json.dumps(events,indent=2)+'\n')
    assert len(events)==10,events
    elapsed=[]
    for i,(opcode,value) in enumerate([(101,1),(102,2),(151,1),(152,1),(101,0)]):
        start,end=events[2*i:2*i+2];assert start[0]=='START' and end[0]=='END' and int(start[2])==opcode and int(start[3])==value and int(end[3])==0,(start,end)
        assert int(start[4])!=255 and start[4]==end[4], ("SOL counter unavailable",start,end)
        # Turbo Jr2: 2 * 25.175 MHz input divided by four for MC6809 cycles.
        seconds=(int(end[1])-int(start[1]))/12587500;elapsed.append(seconds)
        if value:assert value*.5-.04<=seconds<=value*.5+.08,(opcode,seconds)
    for name in ('free-before','free-after','done'):
        target=out/(name+'.txt');os9('copy',f'{disk},{name}',target)
        assert target.is_file(),f'missing shell output: {name}'
    assert (out/'free-before.txt').read_bytes()==(out/'free-after.txt').read_bytes()
    assert b'DONE' in (out/'done.txt').read_bytes()
    w,h,pixels=png_rgb(out/'timers-complete.png');font=(root/'objs/wbfont').read_bytes();assert (w,h)==(640,480)
    for col,char in enumerate('TIMERS COMPLETE'):
        for y in range(8):
            for x in range(8):
                expected=bytes(3) if font[ord(char)*8+y]&(128>>x) else bytes([255])*3
                at=((128+y*2)*w+32+col*16+x*2)*3;assert pixels[at:at+3]==expected,(col,x,y)
    (out/'timing.json').write_text(json.dumps({'seconds':elapsed,'cpu_clock':12587500},indent=2)+'\n')
    print('PASS: real SOL half-second dismissal for all four prints, completion glyphs, keyboard dismissal of untimed print and exact memory cleanup',elapsed)


if __name__ == "__main__":
    main()
