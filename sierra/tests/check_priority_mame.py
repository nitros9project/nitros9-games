#!/usr/bin/env python3
"""Custom priority save/restore, cold restore and isolation on real Wild Bits drivers.

Uses a small controlled AGI game; it is not an original-adventure playthrough.
"""
import argparse
import binascii
import json
from pathlib import Path
import re
import subprocess
import sys
from check_instances import symbols
from check_wbpic_mame import png_rgb

ROOT=Path(__file__).resolve().parents[1]


def fixture(base=80, identity=1, restore=False):
    def when(test,body):return bytes([255,*test,255])+len(body).to_bytes(2,'little')+bytes(body)
    setup=[3,200,1,3,202,identity,143,1]
    for key,controller in zip(b'sbrqpo',range(1,7)):setup += [121,key,0,controller]
    setup += [126,0] if restore else [174,base]
    setup += [3,0,0,24,0,25,0,33,0,41,0,0,37,0,20,100,35,0,26]
    code=when([1,200,0],setup)
    for controller,body in ((1,[125]),(2,[174,40]),(3,[126]),(4,[134,1]),(5,[29]),(6,[133,255])):
        code+=when([12,controller],body)
    code+=b'\0';message=b'PRIO\0';key=b'Avis Durgan'
    logic=len(code).to_bytes(2,'little')+code+b'\x01\x09\0\x04\0'+bytes(c^key[i%11] for i,c in enumerate(message))
    picture=b'\xf2\x08\xf8\0\0\xf3\xff'
    view=bytes([0,0,1,0,0,7,0,1,3,0,1,1,15,0x11,0])
    volume=bytearray();files={}
    for name,payload in (('logDir',logic),('picDir',picture),('viewDir',view)):
        files[name]=len(volume).to_bytes(3,'big')
        volume+=b'\x12\x34\0'+len(payload).to_bytes(2,'little')*2+payload
    files['vol.0']=bytes(volume);files['sndDir']=b'\xff'*3
    files['words.tok']=bytes(53)
    plain=b'\x03\0\0\x03\0\xffkey\0'
    files['object']=bytes(c^key[i%11] for i,c in enumerate(plain))
    return files


def check_view_result(folder,log,disk,os9,shots):
    pixels={name:png_rgb(folder/(name+'.png')) for name in shots.values()}
    assert pixels['normal']!=pixels['priority'],'diagnostic did not change visible pixels'
    assert pixels['priority']==pixels['ordinary-key'],'ordinary key dismissed priority display'
    assert pixels['priority']==pixels['priority-resumed'],'foreground switch lost priority display'
    assert pixels['normal']==pixels['restored'],'Escape did not restore the first scene'
    assert pixels['priority']==pixels['repeated'],'repeated diagnostic did not display priority'
    assert pixels['normal']==pixels['repeated-restored'],'repeated diagnostic did not restore the scene'
    assert pixels['other-normal']!=pixels['other-priority'],'second terminal did not show priority'
    assert pixels['other-normal']==pixels['other-restored'],'Enter did not restore the second scene'
    assert re.findall(r'PRIEXIT (\d+)',log)==['0','0']
    assert os9('list',f'{disk},pri-free3-before')==os9('list',f'{disk},pri-free3-after'),'priority diagnostic leaked memory'
    assert b'PRIOVIEW-DONE' in os9('list',f'{disk},prioview-done')
    assert b'wbgame' not in os9('list',f'{disk},pri-procs-after').lower(), 'a game process remains after cleanup'
    save=folder/'save-after-view.bin';save.unlink(missing_ok=True)
    os9('copy',f'{disk},pri-save',save)
    assert save.read_bytes()==(folder.parent/'save.bin').read_bytes(), 'priority diagnostic modified a save file'
    print('PASS: priority diagnostic pixels, ordinary-key rejection, Enter/Escape restoration, inactive-terminal retention, independent second diagnostic and exact memory recovery')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('mame','disk','firmware','expanded-krnp2','output'):
        ap.add_argument('--'+name,required=True,type=Path)
    a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    game=out/'fixture';game.mkdir()
    for name,data in fixture().items():(game/name).write_bytes(data)
    image=out/'image'
    subprocess.run([sys.executable,str(ROOT/'tests/check_wbgame_mame.py'),'--prepare-play',
        '--mame',str(a.mame.resolve()),'--disk',str(a.disk.resolve()),'--firmware',str(a.firmware.resolve()),
        '--expanded-krnp2',str(a.expanded_krnp2.resolve()),'--game',str(game),'--output',str(image)],check=True)
    disk=image/'test.dsk'
    def os9(*args):return subprocess.check_output(['os9',*map(str,args)],stderr=subprocess.STDOUT)
    os9('makdir',f'{disk},other')
    for name,data in fixture(20,2).items():
        source=out/('other-'+name);source.write_bytes(data);os9('copy','-r',source,f'{disk},other/{name}')
    s=symbols(ROOT/'objs/wbgame.map');size=(ROOT/'objs/wbgame').stat().st_size;base=0xa000
    guard=f'w@{base:x}==87cd && w@{base+2:x}=={size:x}'
    fields=(('b',s['vmvariables']+202),('b',s['prioritybase']),('w',s['priorityscale']),
            ('b',s['vmobjects']+0x24),('w',s['screenentry']))
    state='printf "PRISTATE %d %d %d %d %d",'+','.join(f'{kind}@(u+{off:x})' for kind,off in fields)+'; g'
    pre='printf "PRIPRE %d %d %d",'+','.join(f'{kind}@(u+{off:x})' for kind,off in (fields[0],fields[2],fields[4]))+'; g'
    def run(phase,events,shots,switches,end):
        folder=out/phase;folder.mkdir()
        lines=['local cpu=manager.machine.devices[":maincpu"]','manager.machine.debugger.execution_state="run"',
            'local frames=0','local keys=manager.machine.ioport.ports[":KEY3"].fields',
            'local function post(s) manager.machine.natkeyboard:post(s) end',
            'stopped=emu.add_machine_stop_notifier(function() local log=manager.machine.debugger.consolelog; for n=1,#log do if log[n] then print(log[n]) end end end)',
            'sub=emu.add_machine_frame_notifier(function()','frames=frames+1',
            f'if frames==950 then cpu.debug:bpset({base+s["GameCycleInputReset"]},{json.dumps(guard)},{json.dumps(state)});'
            f'cpu.debug:bpset({base+s["GameStateApply"]},{json.dumps(guard)},{json.dumps(pre)});'
            f'cpu.debug:bpset({base+s["Exit"]},{json.dumps(guard)},\'printf "PRIEXIT %d",b; g\') end']
        for frame,value in events.items():
            if value=='\x1b':
                field='manager.machine.ioport.ports[":KEY2"].fields["Escape"]'
                lines += [f'if frames=={frame} then {field}:set_value(1) end',
                          f'if frames=={frame+10} then {field}:clear_value() end']
            else:lines.append(f'if frames=={frame} then post({json.dumps(value)}) end')
        for frame,name in shots.items():
            lines.append(f'if frames=={frame} then manager.machine.debugger:command(\'printf "SNAP {name}"\'); manager.machine.screens[":screen"]:snapshot({json.dumps(str(folder/(name+".png")))}) end')
        for frame,key in switches.items():
            lines += [f'if frames=={frame} then keys["Alt"]:set_value(1);keys["{key}"]:set_value(1) end',
                      f'if frames=={frame+5} then keys["Alt"]:clear_value();keys["{key}"]:clear_value() end']
        lines += [f'if frames=={end} then manager.machine:exit() end','end)']
        lua=folder/'drive.lua';lua.write_text('\n'.join(lines)+'\n')
        command=[str(a.mame.resolve()),'wbjr2','-bios','turbo','-rompath',str(image/'roms'),'-hard',str(disk),
                 '-skip_gameinfo','-noui_mouse','-mouseprovider','none','-keyboardprovider','none','-video','none',
                 '-sound','none','-nothrottle','-autoboot_script',str(lua),'-seconds_to_run',str(end//60+10),
                 '-nvram_directory',str(folder/'nvram'),'-cfg_directory',str(folder/'cfg'),'-debug','-debugger','none']
        (folder/'command.json').write_text(json.dumps(command,indent=2)+'\n')
        with (folder/'mame.log').open('w') as log:subprocess.run(command,cwd=folder,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=360)
        log=(folder/'mame.log').read_text(errors='replace');assert '[LUA ERROR]' not in log
        last={};snapshots={}
        for line in log.splitlines():
            match=re.match(r'PRISTATE (\d+) (.*)',line)
            if match:last[int(match[1])]=list(map(int,match[2].split()))
            if line.startswith('SNAP '):snapshots[line[5:]]=dict(last)
        (folder/'snapshots.json').write_text(json.dumps(snapshots,indent=2)+'\n')
        return folder,log,snapshots
    events={500:'iniz /vt1\r',650:'shell i=/vt1&\r',800:'mfree >/s0/pri-free1-before\r',
            1000:'wbgame /s0/game 0\r',2400:'s',3000:'/s0/pri-save\r',4600:'wbgame /s0/other 0\r',
            6300:'b',7500:'r',8000:'/s0/pri-save\r',11000:'q',12500:'q',
            13200:'\rmfree >/s0/pri-free1-after\r',13700:'echo PRIORITY-DONE >/s0/priority-done\r'}
    shots={2000:'initial',3800:'saved',5600:'other',7000:'mutated',9000:'restored',
           10000:'other-survives',12300:'other-after-first-exit'}
    folder,log,snap=run('pair',events,shots,{4200:'Right',6000:'Left',9500:'Right',10500:'Left',11800:'Right'},14500)
    for name,base_value,scale_value,priority in (('saved',80,1478,7),('mutated',40,2150,9),('restored',80,1478,7)):
        assert snap[name][1][:3]==[base_value,scale_value,priority],(name,snap)
    for name in ('other','other-survives','other-after-first-exit'):
        assert snap[name][2][:3]==[20,2486,10],(name,snap)
    assert re.findall(r'PRIEXIT (\d+)',log)==['0','0']
    assert os9('list',f'{disk},pri-free1-before')==os9('list',f'{disk},pri-free1-after'),'pair memory leaked'
    assert b'PRIORITY-DONE' in os9('list',f'{disk},priority-done')
    before=png_rgb(folder/'saved.png');mutated=png_rgb(folder/'mutated.png');restored=png_rgb(folder/'restored.png')
    assert before==restored,'restored custom scene pixels differ'
    offset=(216*640+80)*3
    assert before[2][offset:offset+3]!=mutated[2][offset:offset+3],'priority change did not change occlusion'
    os9('copy',f'{disk},pri-save',out/'save.bin');data=(out/'save.bin').read_bytes()
    assert data[:3]==b'WS\1' and data[17]==81 and data[8:16]==b'PRIO\0\0\0\0'
    assert binascii.crc_hqx(data[18:],0xffff)==int.from_bytes(data[6:8],'big')
    print('PASS: actual opcode/occlusion, custom save/change/restore, two independent priorities and pair memory recovery',flush=True)
    source=out/'restore-vol.0';source.write_bytes(fixture(restore=True)['vol.0'])
    os9('copy','-r',source,f'{disk},game/vol.0')
    folder,log,snap=run('cold-restore',{800:'mfree >/s0/pri-free2-before\r',1000:'wbgame /s0/game 0\r',
                       2200:'/s0/pri-save\r',4500:'q',5200:'\rmfree >/s0/pri-free2-after\r'},
                       {1900:'prompt',3500:'restored'},{},6200)
    assert 'PRIPRE 1 0 0' in log,'cold restore unexpectedly had priority state or an entry cached'
    assert snap['restored'][1][:3]==[80,1478,7] and snap['restored'][1][3],snap
    assert png_rgb(folder/'restored.png')==before,'cold restore pixels differ'
    assert re.findall(r'PRIEXIT (\d+)',log)==['0']
    assert os9('list',f'{disk},pri-free2-before')==os9('list',f'{disk},pri-free2-after'),'cold restore memory leaked'
    print('PASS: fresh instance restores custom priority before its first logic cycle, warms the cold entry, restores exact pixels and recovers memory')

    source=out/'view-vol.0';source.write_bytes(fixture()['vol.0'])
    os9('copy','-r',source,f'{disk},game/vol.0')
    events={500:'iniz /vt1\r',650:'shell i=/vt1&\r',800:'mfree >/s0/pri-free3-before\r',
            1000:'wbgame /s0/game 0\r',2200:'p',2800:'x',3600:'wbgame /s0/other 0\r',
            4700:'p',5300:'\r',6500:'\x1b',6900:'p',7500:'\r',8100:'q',9000:'q',
            12000:'procs >/s0/pri-procs-after\r',12500:'mfree >/s0/pri-free3-after\r',
            13000:'echo PRIOVIEW-DONE >/s0/prioview-done\r'}
    shots={2000:'normal',2600:'priority',3100:'ordinary-key',4500:'other-normal',
           5100:'other-priority',5600:'other-restored',6300:'priority-resumed',6800:'restored',7300:'repeated',7800:'repeated-restored'}
    folder,log,snap=run('priority-view',events,shots,{3300:'Right',5800:'Left',8400:'Right'},14000)
    check_view_result(folder,log,disk,os9,shots)

    events={500:'iniz /vt1\r',650:'shell i=/vt1&\r',800:'mfree >/s0/status-free-before\r',
            1000:'wbgame /s0/game 0\r',2200:'o',2800:'x',3600:'wbgame /s0/other 0\r',
            4700:'o',5300:'\r',6500:'\x1b',6900:'o',7500:'\r',8100:'q',9000:'q',
            12000:'procs >/s0/status-procs-after\r',12500:'mfree >/s0/status-free-after\r',
            13000:'echo STATUS-DONE >/s0/status-done\r'}
    shots={2000:'normal',2600:'status',3100:'ordinary-key',4500:'other-normal',
           5100:'other-status',5600:'other-restored',6300:'status-resumed',6800:'restored',
           7300:'repeated',7800:'repeated-restored'}
    folder,log,snap=run('object-status',events,shots,{3300:'Right',5800:'Left',8400:'Right'},14000)
    pixels={name:png_rgb(folder/(name+'.png')) for name in shots.values()}
    assert pixels['normal']!=pixels['status'],'object diagnostic did not appear'
    assert pixels['status']==pixels['ordinary-key'],'ordinary key dismissed object status'
    assert pixels['status']==pixels['status-resumed'],'terminal switch lost object status'
    assert pixels['normal']==pixels['restored'],'Escape did not restore object-status scene'
    assert pixels['status']==pixels['repeated'],'repeated object status differed'
    assert pixels['normal']==pixels['repeated-restored'],'Enter did not restore repeated status'
    assert pixels['other-normal']!=pixels['other-status'],'second terminal lacks object status'
    assert pixels['other-normal']==pixels['other-restored'],'second terminal scene not restored'
    assert re.findall(r'PRIEXIT (\d+)',log)==['0','0']
    assert os9('list',f'{disk},status-free-before')==os9('list',f'{disk},status-free-after'),'status leaked memory'
    assert b'STATUS-DONE' in os9('list',f'{disk},status-done')
    assert b'wbgame' not in os9('list',f'{disk},status-procs-after').lower()
    print('PASS: object-status pixels, ordinary-key rejection, Enter/Escape restoration, foreground retention, repeated calls, independent terminals and exact memory recovery')

if __name__=='__main__':main()
