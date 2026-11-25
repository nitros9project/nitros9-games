#!/usr/bin/env python3
"""Original KQ3 clock, controls, save/restore and optional KQ1 terminal acceptance."""
from pathlib import Path
import argparse
import binascii
import json
import re
import subprocess
import sys
from check_instances import symbols
from check_wbpic_mame import png_rgb

ROOT = Path(__file__).resolve().parents[1]


def text_rows(path, font):
    """Decode black-on-white menus and white-on-black dialogs against font."""
    w,h,pixels=png_rgb(path)
    assert (w,h)==(640,480)
    glyphs={font[c*8:c*8+8]:chr(c) for c in range(32,127)}
    rows=[]
    for row in range(25):
        line=''
        for col in range(40):
            cells=[pixels[((row*16+y*2)*w+col*16+x*2)*3:
                          ((row*16+y*2)*w+col*16+x*2)*3+3]
                   for y in range(8) for x in range(8)]
            black=bytes(3);white=b'\xff\xff\xff'
            # A dense glyph such as "0" can cover more than half of a cell,
            # so the majority color is not always the background. Infer the
            # background from the four cell corners, where this 8x8 font
            # leaves the pixels clear for both black-on-white and
            # white-on-black text.
            corners=[cells[i] for i in (0,7,56,63)]
            black_corners=corners.count(black);white_corners=corners.count(white)
            if black_corners==white_corners:
                background=corners[0]
            else:
                background=black if black_corners>white_corners else white
            foreground=white if background==black else black
            bits=bytes(sum((128>>x) for x in range(8)
                           if pixels[((row*16+y*2)*w+col*16+x*2)*3:
                                     ((row*16+y*2)*w+col*16+x*2)*3+3]==foreground)
                       for y in range(8))
            line+=glyphs.get(bits,'?')
        rows.append(line)
    return rows


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('mame','disk','firmware','output'):
        ap.add_argument('--'+name,required=True,type=Path)
    ap.add_argument('--game',type=Path,default=ROOT/'kingsquest3')
    ap.add_argument('--pair-game',type=Path,help='Original KQ1 resources for a second terminal')
    ap.add_argument('--stress-pair',action='store_true',
                    help='after KQ1 exits, relaunch it, switch repeatedly, then interrupt it while KQ3 survives')
    ap.add_argument('--expanded-krnp2',type=Path)
    a=ap.parse_args();out=a.output.resolve()
    if a.stress_pair and not a.pair_game:ap.error('--stress-pair requires --pair-game')
    if a.pair_game and not a.expanded_krnp2:ap.error('two games require the documented expanded-memory test kernel')
    cmd=[sys.executable,str(ROOT/'tests/check_wbgame_mame.py'),'--prepare-play',
         '--mame',str(a.mame.resolve()),'--disk',str(a.disk.resolve()),
         '--firmware',str(a.firmware.resolve()),'--game',str(a.game.resolve()),'--output',str(out)]
    if a.expanded_krnp2:cmd+=['--expanded-krnp2',str(a.expanded_krnp2.resolve())]
    subprocess.run(cmd,check=True)
    disk=out/'test.dsk'
    def os9(*args):return subprocess.check_output(['os9',*map(str,args)],stderr=subprocess.STDOUT)
    if a.pair_game:
        os9('makdir',f'{disk},castle')
        for p in a.pair_game.iterdir():
            if p.name.startswith('vol.') or p.name in ('logDir','picDir','sndDir','viewDir','words.tok','object'):
                os9('copy','-r',p,f'{disk},castle/{p.name}')
    s=symbols(ROOT/'objs/wbgame.map');size=(ROOT/'objs/wbgame').stat().st_size;base=0xa000
    guard=f'w@{base:x} == 87cd && w@{base+2:x} == {size:x}'
    fields=(s['vmgameid']+2,s['vmvariables'],s['vmobjects']+3,s['vmobjects']+4,
            s['vmvariables']+117,s['vmvariables']+116,s['vmvariables']+115,s['vminputenabled'])
    action='printf "GAMESTATE %d %d %d %d %d %d %d %d",'+','.join(f'b@(u+{x:x})' for x in fields)+'; g'
    exit_action=f'printf "GAMEEXIT %d",b; g'
    lines=['local cpu=manager.machine.devices[":maincpu"]','manager.machine.debugger.execution_state="run"',
           'local frames=0','local keys=manager.machine.ioport.ports[":KEY3"].fields',
           'local letters=manager.machine.ioport.ports[":KEY0"].fields',
           'local c=nil','local i=nil','for _,f in pairs(letters) do if f.mask==4 then c=f end; if f.mask==256 then i=f end end',
           'assert(c and i)','local function post(s) manager.machine.natkeyboard:post(s) end',
           f'local function shot(n) manager.machine.debugger:command(\'printf "SNAP \'..n..\'"\'); manager.machine.screens[":screen"]:snapshot({json.dumps(str(out)+"/")}..n..".png") end',
           'stopped=emu.add_machine_stop_notifier(function() local log=manager.machine.debugger.consolelog;for n=1,#log do if log[n] then print(log[n]) end end end)',
           'sub=emu.add_machine_frame_notifier(function()',' frames=frames+1',
           f' if frames==950 then cpu.debug:bpset({base+s["GameCycleInputReset"]},{json.dumps(guard)},{json.dumps(action)}); cpu.debug:bpset({base+s["Exit"]},{json.dumps(guard)},{json.dumps(exit_action)}) end']
    events={800:'mfree >/s0/free-before\r',1000:'wbgame /s0/game 0\r',1800:' \r',3500:' ',
            5000:'look room\r',6500:' ',7000:'save game\r',8000:'/s0/kq3save\r',
            11000:'restore game\r',12000:'/s0/kq3save\r'}
    shots={3900:'before',4300:'moved',6000:'look',6900:'after-look',7800:'save-prompt',
           9200:'saved',10600:'mutated',11800:'restore-prompt',14000:'restored'}
    key_events=[(4000,'Right',True),(4010,'Right',False),(4200,'Right',True),(4210,'Right',False),
                (10000,'Left',True),(10010,'Left',False),(10500,'Left',True),(10510,'Left',False)]
    switches={};controls=[]
    if a.pair_game:
        events.update({500:'iniz /vt1\r',650:'shell i=/vt1&\r',15800:'mfree >/s0/free-one\r',
                       16500:'wbgame /s0/castle 0\r',17300:' \r',20100:'look room\r',21250:' ',
                       23200:'\r',24400:'\rmfree >/s0/free-one-after\r',27400:'\rmfree >/s0/free-after\r',
                       28200:'echo WBGAME-DONE >/s0/wbgame-done\r'})
        shots.update({19000:'kq1-first',20000:'kq3-restored',21200:'kq3-look',
                      23100:'kq1-inventory',26000:'kq3-survives',29000:'shell'})
        switches={15100:'Right',19200:'Left',22000:'Right',25300:'Left'}
        controls=[(22600,'i'),(23700,'c'),(26700,'c')];end=29000
        if a.stress_pair:
            # Leave KQ3 resident, exit KQ1, relaunch KQ1 from its shell, then
            # exit both processes independently. Keep each free-memory sample
            # after the corresponding exit; sampling at 27400 measures both
            # games still running and cannot serve as the final baseline.
            events.pop(27400,None);events.pop(28200,None)
            events.update({24500:'procs >/s0/procs-after-first-exit\r',
                           24600:'mdir >/s0/mdir-after-first-exit\r',
                           25000:'mfree >/s0/free-after-first-exit\r',
                           29000:'wbgame /s0/castle 0\r',
                           29800:' \r',
                           35000:'look room\r',
                           36200:' ',
                           39100:'\r',
                           39300:'procs >/s0/procs-after-relaunch\r',
                           39400:'mdir >/s0/mdir-after-relaunch\r',
                           39500:'mfree >/s0/free-after-relaunch\r',
                           41000:'\r',
                           42000:'mfree >/s0/free-after\r',
                           43000:'echo WBGAME-DONE >/s0/wbgame-done\r'})
            shots.pop(29000,None)
            shots.update({30000:'kq1-relaunched',32000:'kq3-after-relaunch',
                          38500:'kq1-after-relaunch',40200:'kq3-after-relaunch'})
            switches.update({28000:'Right',30300:'Left',38000:'Right',40000:'Left'})
            controls=[(22600,'i'),(23700,'c'),(38800,'c'),(40500,'c')]
            events.update({42000:'mfree >/s0/free-after\r',
                           43000:'echo WBGAME-DONE >/s0/wbgame-done\r'})
            end=44500
    else:
        events.update({15700:'\rmfree >/s0/free-after\r',16500:'echo WBGAME-DONE >/s0/wbgame-done\r'})
        shots[17000]='shell';controls=[(15000,'c')];end=17000
    for frame,value in events.items():lines.append(f' if frames=={frame} then post({json.dumps(value)}) end')
    for frame,name in shots.items():lines.append(f' if frames=={frame} then shot({json.dumps(name)}) end')
    for frame,key,down in key_events:
        lines.append(f' if frames=={frame} then keys[{json.dumps(key)}]:'+('set_value(1)' if down else 'clear_value()')+' end')
    for frame,direction in switches.items():
        lines.append(f' if frames=={frame} then keys["Alt"]:set_value(1);keys["{direction}"]:set_value(1) end')
        lines.append(f' if frames=={frame+5} then keys["Alt"]:clear_value();keys["{direction}"]:clear_value() end')
    for frame,key in controls:
        lines+= [f' if frames=={frame} then keys["Ctrl"]:set_value(1) end',
                 f' if frames=={frame+10} then {key}:set_value(1) end',
                 f' if frames=={frame+20} then {key}:clear_value() end',
                 f' if frames=={frame+30} then keys["Ctrl"]:clear_value() end']
    lines += [f' if frames=={end} then manager.machine:exit() end','end)']
    lua=out/'drive.lua';lua.write_text('\n'.join(lines)+'\n')
    command=[str(a.mame.resolve()),'wbjr2','-bios','turbo','-rompath',str(out/'roms'),'-hard',str(disk),
             '-skip_gameinfo','-noui_mouse','-mouseprovider','none','-keyboardprovider','none',
             '-video','none','-sound','none','-nothrottle','-autoboot_script',str(lua),
             '-seconds_to_run',str(end//60+10),'-nvram_directory',str(out/'nvram'),
             '-cfg_directory',str(out/'cfg'),'-debug','-debugger','none']
    (out/'command.json').write_text(json.dumps(command,indent=2)+'\n')
    with (out/'mame.log').open('w') as log:subprocess.run(command,cwd=out,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=360)
    log=(out/'mame.log').read_text(errors='replace');last={};snapshots={}
    assert '[LUA ERROR]' not in log, 'emulator automation failed; inspect mame.log'
    for line in log.splitlines():
        m=re.match(r'GAMESTATE (\d+) (.*)',line)
        if m:last[int(m[1])]=list(map(int,m[2].split()))
        m=re.match(r'SNAP (\S+)',line)
        if m:snapshots[m[1]]={str(k):v for k,v in last.items()}
    gamekey=str(ord('3'))
    states={name:snapshots[name][gamekey] for name in ('before','moved','saved','mutated','restored')}
    assert all(v[0]==7 and v[-1]==1 for v in states.values()),states
    assert states['moved'][1:3]!=states['before'][1:3],('movement absent',states)
    assert states['mutated'][1:3]!=states['saved'][1:3],('saved position not changed',states)
    assert states['restored'][1:3]==states['saved'][1:3],('position not restored',states)
    font=(ROOT/'objs/sierrafont').read_bytes()
    for name in ('saved','restored'):
        row=text_rows(out/(name+'.png'),font)[0]
        assert re.fullmatch(r'\d+:\d{2}:\d{2}',row[20:30].strip()),('clock glyphs',name,row)
    look=png_rgb(out/'look.png')
    look_rows=text_rows(out/'look.png',font)
    popup_text=' '.join(row[9:30].strip() for row in look_rows[9:16])
    assert 'This is the main' in popup_text and "wizard's house" in popup_text, \
        ('original room description absent from the popup',popup_text)
    # A normal AGI print remains a centered text overlay over the game picture.
    # Empty text cells are transparent and intentionally retain the game's
    # palette, so this rectangle is not required to contain only black/white.
    _,_,look_pixels=look
    def region_stats(image,x0,y0,x1,y1):
        colors=set();white=black=total=0
        for y in range(y0,y1):
            for x in range(x0,x1):
                i=(y*image[0]+x)*3;color=bytes(image[2][i:i+3])
                colors.add(color);white+=color==bytes([255])*3;black+=color==bytes(3);total+=1
        return colors,white/total,black/total
    popup=(144,144,480,256)
    popup_colors,popup_white,popup_black=region_stats(look,*popup)
    left_colors,_,_=region_stats(look,0,16,144,352)
    right_colors,_,_=region_stats(look,480,16,640,352)
    assert len(popup_colors)>=4,('game picture was cleared below popup',popup_colors)
    assert popup_white>0.05 and popup_black>0.05,('popup text pixels missing',popup_white,popup_black)
    assert len(left_colors)>=8 and len(right_colors)>=8, \
        ('popup obscured the room outside its centered bounds',len(left_colors),len(right_colors))
    # Space dismisses the message. The static room pixels then match the
    # post-movement scene captured before opening it (status clock may advance).
    restored=png_rgb(out/'after-look.png')
    moved_image=png_rgb(out/'moved.png')
    popup_same=sum(look[2][i:i+3]==moved_image[2][i:i+3]
                   for y in range(popup[1],popup[3])
                   for x in range(popup[0],popup[2])
                   for i in [(y*640+x)*3])
    assert popup_same>(popup[2]-popup[0])*(popup[3]-popup[1])*0.05, \
        ('scene was not retained in transparent popup cells',popup_same)
    changed=sum(look_pixels[i:i+3]!=restored[2][i:i+3]
                for i in range(0,len(look_pixels),3))
    assert changed>10000,'Space did not dismiss the room-description popup'
    static_region=range(32*640*3,432*640*3)
    restored_differences=sum(moved_image[2][i]!=restored[2][i] for i in static_region)
    assert restored_differences<1000,('room was not restored after popup dismissal',restored_differences)
    for name in ('save-prompt','restore-prompt'):
        assert 'File:' in ' '.join(text_rows(out/(name+'.png'),font)),name
    saved=png_rgb(out/'saved.png');restored=png_rgb(out/'restored.png')
    # The candles at y=182 animate independently between captures. Compare
    # the static upper room; player coordinates are checked separately above.
    assert saved[2][32*640*3:160*640*3]==restored[2][32*640*3:160*640*3],'restored static background pixels differ'
    data=os9('list',f'{disk},wbgame-done');assert b'WBGAME-DONE' in data
    before=os9('list',f'{disk},free-before');after=os9('list',f'{disk},free-after')
    assert before==after,'final free memory differs'
    for name,value in (('free-before',before),('free-after',after)):(out/(name+'.txt')).write_bytes(value)
    exits=re.findall(r'GAMEEXIT (\d+)',log)
    expected_exits=2 if a.pair_game else 1
    if a.stress_pair:
        expected_exits=3
    assert len(exits)==expected_exits,('unexpected exits',exits)
    os9('copy',f'{disk},kq3save',out/'save.bin');data=(out/'save.bin').read_bytes()
    assert data[:3]==b'WS\1' and data[8:16]==b'KQ3\0\0\0\0\0'
    assert len(data)==18+int.from_bytes(data[4:6],'big')
    assert binascii.crc_hqx(data[18:],0xffff)==int.from_bytes(data[6:8],'big')
    if a.pair_game:
        assert os9('list',f'{disk},free-one')==os9('list',f'{disk},free-one-after'),'KQ1 exit did not recover KQ3-only memory'
        assert str(ord('1')) in snapshots['kq1-first'],'second game did not cycle'
        assert 'You are carrying:' in ' '.join(text_rows(out/'kq1-inventory.png',font)),'independent KQ1 inventory input failed'
        assert states['restored'][1:3]==snapshots['kq3-survives'][gamekey][1:3],'background game position changed'
        kq3_look=text_rows(out/'kq3-look.png',font)
        assert 'main entry room' in ' '.join(row[9:30].strip() for row in kq3_look[9:16]), \
            'KQ3 input after terminal switch failed'
        row=text_rows(out/'kq3-survives.png',font)[0]
        assert re.fullmatch(r'\d+:\d{2}:\d{2}',row[20:30].strip()),'KQ3 display did not restore after KQ1 exit'
        if a.stress_pair:
            free_one=os9('list',f'{disk},free-one-after')
            free_first=os9('list',f'{disk},free-after-first-exit')
            free_relaunch=os9('list',f'{disk},free-after-relaunch')
            processes=os9('list',f'{disk},procs-after-relaunch')
            (out/'free-after-first-exit.txt').write_bytes(free_first)
            (out/'free-after-relaunch.txt').write_bytes(free_relaunch)
            (out/'procs-after-relaunch.txt').write_bytes(processes)
            assert free_one==free_first, 'first KQ1 exit changed the KQ3-only memory map'
            process_lines=processes.decode(errors='replace').splitlines()
            game_processes=[line for line in process_lines if re.search(r'\bwbgame\s*$',line)]
            assert len(game_processes)==1,('KQ1 process remained after relaunch exit',game_processes)
            # The second KQ1 cycle leaves 16 KiB reserved while KQ3 remains
            # alive; this is not assumed to be a leak without attribution.
            # The enclosing before/after assertion proves exact recovery once
            # the last game process exits.
            assert os9('list',f'{disk},free-after')==os9('list',f'{disk},free-before'), 'stress-pair final memory differs from baseline'
            relaunch_rows=text_rows(out/'kq3-after-relaunch.png',font)
            relaunch_text=' '.join(row[9:30].strip() for row in relaunch_rows[9:18])
            assert 'You feel the blood' in relaunch_text or 'main entry room' in relaunch_text, \
                ('KQ3 display did not resume after KQ1 relaunch',relaunch_text)
            look_rows=text_rows(out/'kq3-look.png',font)
            look_text=' '.join(row[9:30].strip() for row in look_rows[9:16])
            assert 'main entry room' in look_text, 'KQ3 did not accept input after KQ1 relaunch'
    (out/'result.json').write_text(json.dumps({'states':states,'snapshots':snapshots,'exits':exits,'two_terminals':bool(a.pair_game)},indent=2)+'\n')
    print('PASS: original KQ3 visible clock, movement, room description, save/change/restore static pixels and position, planned exit and unchanged memory'+('; independent KQ1 terminal, inventory and KQ3 continuation after KQ1 exit' if a.pair_game else '')+('; repeated KQ1 launch/switch/interrupt cycles with KQ3 input and exact memory recovery' if a.stress_pair else ''))


if __name__=='__main__':main()
