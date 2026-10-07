#!/usr/bin/env python3
"""Execute the native resource probe on a 6809 with adversarial file services."""
from pathlib import Path
import re
import socket
import subprocess
import time
import tempfile
from check_instances import Debugger, symbols

ROOT = Path(__file__).resolve().parents[1] / 'objs'


def idle_rom(path):
    # A deterministic BRA loop prevents ROM-free startup from running random
    # RAM instructions while the GDB thread is attaching. Tests switch to
    # all-RAM mode before loading any routine under test.
    data = bytearray([0x12] * 32768)
    data[:2] = b'\x20\xfe'
    data[-2:] = b'\x80\x00'
    Path(path).write_bytes(data)
    return str(path)


def start_cpu(bootrom, timeout=300):
    for attempt in range(4):
        with socket.socket() as reservation:
            reservation.bind(('127.0.0.1', 0))
            port = reservation.getsockname()[1]
        emulator = subprocess.Popen(['xroar', '-machine', 'coco3', '-ui', 'null', '-ao', 'null',
            '-ram', '2048', '-no-ratelimit', '-gdb', '-gdb-port', str(port), '-timeout', str(timeout),
            '-no-bas', '-extbas', str(bootrom), '-no-altbas'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Let the emulator complete its queued power-on reset before attaching.
        # An early debugger connection can otherwise reset DP after register setup.
        time.sleep(.1)
        try:
            for _ in range(100):
                try:
                    return Debugger(port), emulator
                except ConnectionRefusedError:
                    time.sleep(.005)
        except socket.timeout:
            pass
        emulator.terminate()
        try:
            emulator.wait(timeout=2)
        except subprocess.TimeoutExpired:
            emulator.kill()
            emulator.wait(timeout=2)
    raise RuntimeError('XRoar debugger did not attach after four fresh starts')


def exercise(d, files, arguments=b'/game 1\r', base=0xE000, database=0x2000, zero_read=False, seek_error=False, write_error=False, module='wbres', map_failure=0, allocation_error=False, unmap_error=False, window=0x8000, terminal=True, blocks=4, capture=False, multiple=False, firstblock=0x30, frame_capture=False, keyboard=b'', clock=(0,), bitmap_error=False, key_sense=0, cycle_limit=None, os_call_limit=20000, keyboard_by_cycle=None, option_set_error=False, resource_kind=None, module_root=None, breakpoint_hooks=None, psg=None, sol=None, joystick=None, palette_error=0):
    if module == 'wbgame':
        files = {'wbfont': (ROOT / 'wbfont').read_bytes(), 'wbstate': (ROOT / 'wbstate').read_bytes(), **files}
    module_root = Path(module_root) if module_root is not None else ROOT
    syms = symbols(module_root / (module + '.map'))
    calls = {base + int(m[1], 16): int(m[2], 16) for m in re.finditer(
        r'^([0-9A-F]{4}) 103F([0-9A-F]{2}).*os9', (module_root / (module + '.list')).read_text(), re.M)}
    d.write(database, bytes(syms['size']))
    code = (module_root / module).read_bytes()
    assert base+len(code)<=0xfe00, 'CPU fixture code overlaps the CoCo I/O page; relocate its load address'
    d.write(base, code)
    # Kernel parameter/stack space occupies the top of the allocated 8 KB banks.
    # Keep it above permanent private code rather than assuming a 256-byte pad
    # inside the module's declared data area.
    private_end = database + ((syms['size'] + 8191)//8192)*8192
    argv = private_end - len(arguments) - 16
    d.write(argv, arguments)
    for address in calls:
        d.breakpoint(address)
    d.regs(pc=base + syms['start'], s=argv - 16,
           dp=database >> 8, u=database, x=argv, cc=0x50)
    hooks = {(name if isinstance(name,int) else base+syms[name]):callback for name,callback in (breakpoint_hooks or {}).items()}
    for address in hooks: d.breakpoint(address)
    kind_entry = base + syms['LoadAsset'] if resource_kind is not None else None
    if kind_entry is not None:
        d.breakpoint(kind_entry)
    paths, output, nextpath = {}, bytearray(), 3
    path_names, file_reads = {}, {}
    owned, mapped = {}, False
    nextblock = firstblock
    bitmapfirst, frame = None, bytearray()
    keyboard = bytearray(keyboard)
    clock = list(clock)
    clocksecond = clock[0]
    cycles = 0
    joystick_polls=0
    joystick_samples=list(joystick.get("samples",())) if joystick else []
    joystick_sample=(128,128,0)
    maps = 0
    map_sites = {}
    palettes=[]
    unmap_failed = False
    original_options=bytearray(32)
    original_options[0]=0 if terminal else 1
    original_options[syms.get('PD.EKO',0)-syms.get('PD.OPT',0)]=1
    original_options[syms.get('PD.EOF',0)-syms.get('PD.OPT',0)]=26
    original_options[syms.get('PD.INT',0)-syms.get('PD.OPT',0)]=3
    original_options[syms.get('PD.QUT',0)-syms.get('PD.OPT',0)]=27
    options=original_options[:]
    options_failed=False
    cold_loaded=0
    cold_ever_loaded=False
    sol_path=None
    sol_ticks=sol.get("start",0) if sol else 0
    audio_ever_installed=False
    audio_path=None
    audio_claimed=False
    audio_packets=[]
    audio_current_packets=[]
    audio_mode=0
    audio_polls=0
    audio_end_cycle=None
    audio_queues=[[] for _ in range(4)]
    audio_played_ends=[False]*4
    private_calls={}
    if module=='wbgame' and files.get('wbstate'):
        assert private_end<=0x6000, 'native private data overlaps the helper code window'
        cold_syms=symbols(module_root/'wbstate.map')
        blob_start=cold_syms['AudioBlobStart']; blob_end=cold_syms['AudioBlobEnd']
        private_calls={database+syms['soundcode']+int(m[1],16)-blob_start:int(m[2],16)
            for m in re.finditer(r'^([0-9A-F]{4}) 103F([0-9A-F]{2}).*os9',
                (module_root/'wbstate.list').read_text(),re.M)
            if blob_start<=int(m[1],16)<blob_end}
        cold_calls={0x6000+int(m[1],16):int(m[2],16)
            for m in re.finditer(r'^([0-9A-F]{4}) 103F([0-9A-F]{2}).*os9',
                (module_root/'wbstate.list').read_text(),re.M)
            if cold_syms['AuxPrintWait']<=int(m[1],16)<cold_syms['StateEnd']}
        calls.update(cold_calls)
        for address in cold_calls:d.breakpoint(address)
        calls.update(private_calls)
        for address in private_calls:d.breakpoint(address)

    for _ in range(os_call_limit):
        d.call('c')
        r = d.regs()
        if r['pc'] in hooks:
            callback=hooks.pop(r['pc'])
            callback(d,r,syms)
            d.breakpoint(r['pc'],False)
            continue
        if r['pc'] == kind_entry:
            d.write(database + syms['resourcekind'], bytes([resource_kind]))
            d.breakpoint(kind_entry, False)
            kind_entry = None
            continue
        service = calls[r['pc']]
        if service == syms.get('F$MapBlk'):
            site=r['pc']-base
            map_sites[site]=map_sites.get(site,0)+1
        updates = {'pc': r['pc'] + 3, 'cc': r['cc'] & ~1}
        if service == syms['F$Exit']:
            assert not paths, f'leaked file paths: {paths}'
            assert not cold_loaded and not audio_claimed, 'leaked cold module/audio ownership'
            if cold_ever_loaded:
                assert d.read(0x6000,len(files['wbstate']))==files['wbstate'], 'shared cold backend modified its module image'
            if private_calls and (audio_ever_installed or d.read(database+syms['soundinstalled'],1)==b'\x01'):
                expected=files['wbstate'][blob_start:blob_end]
                assert d.read(database+syms['soundcode'],len(expected))==expected, 'private audio code overwritten by the game stack or buffers'
            assert options==original_options, 'terminal options were not restored'
            assert not mapped and not owned, 'leaked picture allocation/mapping'
            assert d.read(base, len(code)) == code, 'native module modified its code/tables'
            for address in list(calls)+list(hooks)+([kind_entry] if kind_entry is not None else []):
                d.breakpoint(address, False)
            if capture:
                state={name: d.read(database + syms[name], length) for name, length in [('vmopcode', 1), ('vmip', 2), ('vmvariables', 256), ('vmflags', 256), ('vmgameid', 8), ('messagebuffer', 512), ('vmobjects', 2752), ('vmkeys',150), ('vmcontrollers',32), ('vmkeycount',1), ('menucount', 1), ('menuitems', 1), ('menuready', 1), ('menutext', 768), ('asseterror', 1), ('vmerror', 1), ('vmend', 2), ('resourcelength', 2), ('vmcurrent', 1)]}
                for name, length in [('replayused',2),('replaybuffer',510)]:
                    if name in syms:
                        state[name]=d.read(database+syms[name],length)
                if module=='wbgame':
                    state['vmstrings']=d.read(database+syms['vmstrings'],480)
                    state['palettes']=palettes
                    if 'monitorprofile' in syms:state['monitorprofile']=d.read(database+syms['monitorprofile'],1)
                    state['joystick_polls']=joystick_polls
                    for name in ('joystickenabled','joysticklast','joystickbuttons','joystickpressed'):
                        if name in syms:state[name]=d.read(database+syms[name],1)
                    state['gamefont']=d.read(database+syms['gamefont'],1024)
                    for name in ('vmcursor','vmtextforeground','vmtextbackground','vmpicturetop','vminputrow','vmstatusrow','vmstatusenabled','vminputenabled'):
                        state[name]=d.read(database+syms[name],1)
                state['cycles']=cycles
                state['audio_packets']=audio_packets
                state['audio_polls']=audio_polls
                state['map_calls']=maps
                state['map_sites']=map_sites
                state['file_reads']=file_reads
                return r['b'], bytes(frame if frame_capture else output), state
            return r['b'], bytes(frame if frame_capture else output)
        elif service == syms.get('F$Load'):
            assert not mapped
            name=d.read(r['x'],16).split(b'\r')[0].decode()
            if name not in files or files[name] is None:
                updates.update(cc=r['cc']|1,b=syms['E$PNNF'])
            else:
                image=files[name];cold_base=0x6000
                if not cold_loaded:d.write(cold_base,image)
                entry=int.from_bytes(image[9:11],'big')
                updates.update(u=cold_base,y=cold_base+entry)
                cold_loaded+=1
                cold_ever_loaded=True
        elif service == syms.get('F$UnLink'):
            assert cold_loaded and r['u']==0x6000
            cold_loaded-=1
        elif service == syms['I$GetStt'] and r['b']==0xc3:
            assert sol is not None and r['a']==sol_path and not mapped
            updates.update(x=7,y=sol_ticks)
        elif service == syms['I$SetStt'] and r['b'] in (0xc3,0xc4):
            assert sol is not None and r['a']==sol_path and not mapped
        elif service == syms['I$GetStt'] and r['b']==0xc5:
            assert psg is not None and r['a']==audio_path and not mapped
            audio_polls+=1
            ended=[any(packet[0]==channel and packet[1:3]==b'\xff\xff'
                for packet in audio_current_packets) for channel in range(4)]
            if all(ended) and audio_end_cycle is None:audio_end_cycle=cycles
            finished=audio_end_cycle is not None and cycles>audio_end_cycle
            available=sum(1<<channel for channel in range(4) if not ended[channel])
            if psg.get('queue_capacity'):
                available=sum(1<<channel for channel in range(4)
                    if not ended[channel] and len(audio_queues[channel])<psg['queue_capacity'])
                finished=all(audio_played_ends)
            updates.update(x=psg.get('version',4),u=(0 if finished else 0x10|available) if r['x']==1 else audio_polls)
        elif service == syms['I$SetStt'] and r['b']==0xc5:
            assert psg is not None and r['a']==audio_path and not mapped
            if r['x']==1:
                if psg.get('busy') or psg.get('busy_attempts',0)>0:
                    if psg.get('busy_attempts',0)>0:psg['busy_attempts']-=1
                    updates.update(cc=r['cc']|1,b=syms['E$DevBsy'])
                else:audio_claimed=True
            else:
                assert audio_claimed and r['x'] in (4,5)
                audio_mode=r['x']
                if audio_mode==4:
                    audio_current_packets.clear();audio_end_cycle=None
                    audio_queues=[[] for _ in range(4)];audio_played_ends=[False]*4
        elif service == syms.get('F$Time'):
            assert not mapped
            if clock:
                clocksecond = clock.pop(0)
            d.write(r['x'], bytes([126,10,4,12,0,clocksecond]))
        elif service == syms.get('F$Sleep'):
            assert not mapped
            cycles += 1
            if sol:sol_ticks=(sol_ticks+sol.get("step",1))&255
            if psg and psg.get('queue_capacity') and audio_claimed and audio_mode==5:
                for channel,queue in enumerate(audio_queues):
                    if queue:
                        packet=queue.pop(0)
                        if packet[1:3]==b'\xff\xff':audio_played_ends[channel]=True
            if keyboard_by_cycle and cycles in keyboard_by_cycle:
                keys, key_sense = keyboard_by_cycle[cycles]
                keyboard.extend(keys)
            if cycle_limit is not None and cycles >= cycle_limit:
                d.write(database + syms['aborted'], b'\x01')
        elif service == syms['I$GetStt'] and r['b'] == syms['SS.Ready']:
            assert not mapped
            if not keyboard:
                updates.update(cc=r['cc'] | 1, b=syms['E$NotRdy'])
        elif service == syms['I$GetStt'] and r['b'] == syms.get('SS.KySns'):
            assert not mapped
            updates.update(a=key_sense)
        elif service == syms['I$GetStt'] and r['b'] == syms.get('SS.Joy'):
            assert not mapped and r['a']==0 and r['x']==0,r
            joystick_polls+=1
            if joystick is None or joystick_polls==joystick.get('fail_at'):
                updates.update(cc=r['cc']|1,b=syms['E$UnkSvc'])
            else:
                if joystick_samples:joystick_sample=joystick_samples.pop(0)
                updates.update(x=joystick_sample[0],y=joystick_sample[1],a=joystick_sample[2])
        elif service == syms['I$GetStt'] and r['b'] == syms['SS.Opt']:
            assert r['a'] == 0
            d.write(r['x'],options)
        elif service == syms['I$GetStt'] and r['b'] == syms.get('SS.DevNm'):
            d.write(r['x'], b'/term\0' + bytes(26))
        elif service == syms['I$SetStt'] and r['b'] == syms.get('SS.AScrn'):
            assert r['a'] == 1 and bitmapfirst is None and not mapped, (r, bitmapfirst, mapped)
            if bitmap_error:
                updates.update(cc=r['cc'] | 1, b=syms['E$MFull'])
            else:
                bitmapfirst = nextblock
                owned[bitmapfirst] = 10
                nextblock += 10
        elif service == syms['I$GetStt'] and r['b'] == 0xe4:
            assert r['a'] == 1 and bitmapfirst is not None
            updates['x'] = bitmapfirst
        elif service == syms['I$SetStt'] and r['b'] == syms.get('SS.FScrn'):
            assert r['a'] == 1 and bitmapfirst in owned and not mapped
            if frame_capture:
                for page in range(10):
                    d.write(0xffa8 + window // 8192, bytes([bitmapfirst + page]))
                    frame.extend(d.read(window, 8192))
                del frame[76800:]
                d.write(0xffa8 + window // 8192, bytes([window // 8192]))
            del owned[bitmapfirst]
            bitmapfirst = None
        elif service == syms['I$SetStt'] and r['b'] == syms['SS.Opt']:
            assert r['a']==0 and not mapped
            options=bytearray(d.read(r['x'],32))
            assert options[syms['PD.INT']-syms['PD.OPT']]==3, 'CTRL-C interrupt was disabled'
            if option_set_error and not options_failed:
                options_failed=True
                updates.update(cc=r['cc']|1,b=syms['E$BMode'])
        elif service == syms['I$SetStt'] and r['b']==0xcf:
            assert not mapped and r['a']==1 and r['y']==0 and r['u']==17,r
            assert bitmapfirst is not None and bitmapfirst in owned,'palette without an owned bitmap'
            palettes.append(d.read(r['x'],68))
            if len(palettes)==palette_error:updates.update(cc=r['cc']|1,b=syms['E$BMode'])
        elif service == syms['I$SetStt'] and r['b'] in (0xe1, syms.get('SS.PScrn'), syms.get('SS.DScrn'), syms.get('SS.Palet')):
            assert not mapped
        elif service == syms['I$SetStt'] and r['b'] == 0xD4:
            assert r['a'] == 0 and (blocks is None or r['x'] == blocks) and (multiple or not owned)
            if allocation_error:
                updates.update(cc=r['cc'] | 1, b=syms['E$MemFul'])
            else:
                owned[nextblock] = r['x']
                updates['x'] = nextblock
                nextblock += r['x']
        elif service == syms['I$SetStt'] and r['b'] == 0xD5:
            assert not mapped and owned.get(r['x']) == r['u'], (r, owned)
            del owned[r['x']]
        elif service == syms['F$MapBlk']:
            assert not mapped and r['b'] == 1 and any(first <= r['x'] < first + count for first, count in owned.items()), (mapped,r,owned)
            maps += 1
            if (map_failure(d,r,syms) if callable(map_failure) else maps == map_failure):
                updates.update(cc=r['cc'] | 1, b=syms['E$MemFul'])
            else:
                d.write(0xFFA8 + window // 8192, bytes([r['x']]))
                mapped = True
                updates['u'] = window
        elif service == syms['F$ClrBlk']:
            assert mapped and r['b'] == 1 and r['u'] == window
            if (unmap_error(d,r,syms) if callable(unmap_error) else unmap_error) and not unmap_failed:
                unmap_failed = True
                updates.update(cc=r['cc'] | 1, b=syms['E$MemFul'])
            else:
                d.write(0xFFA8 + window // 8192, bytes([window // 8192]))
                mapped = False
        elif service == syms['I$Open']:
            name = d.read(r['x'], 160).split(b'\r')[0].decode()
            if name=='/fPSG':
                audio_ever_installed=d.read(database+syms['soundinstalled'],1)==b'\x01'
            if name=='/fSOL' and sol is not None:
                sol_path=nextpath
                paths[nextpath]=[b'',0];path_names[nextpath]=name
                updates['a']=nextpath;nextpath+=1
            elif name=='/fPSG' and psg is not None:
                assert cold_loaded==bool(int.from_bytes(d.read(database+syms['textstoremodule'],2),'big')), 'temporary adapter reference leaked into device I/O'
                audio_path=nextpath
                paths[nextpath]=[b'',0];path_names[nextpath]=name
                updates['a']=nextpath;nextpath+=1
            elif name not in files:
                updates.update(cc=r['cc'] | 1, b=syms['E$PNNF'])
            else:
                paths[nextpath] = [files[name], 0]
                path_names[nextpath] = name
                updates['a'] = nextpath
                nextpath += 1
        elif service == syms['I$Seek']:
            assert r['a'] in paths
            if seek_error:
                updates.update(cc=r['cc'] | 1, b=syms['E$Seek'])
            else:
                paths[r['a']][1] = r['x'] * 65536 + r['u']
        elif service == syms['I$Read'] and r['a'] == 0:
            assert not mapped and keyboard and r['y'] == 1
            d.write(r['x'], bytes([keyboard.pop(0)]))
            updates['y'] = 1
        elif service == syms['I$Read']:
            assert not mapped or module not in ('wbasset', 'wbexec', 'wbgame'), 'resource read with foreign mapping live'
            data, position = paths[r['a']]
            name=path_names[r['a']]
            file_reads[name]=file_reads.get(name,0)+1
            if zero_read:
                updates['y'] = 0
            elif position >= len(data):
                updates.update(cc=r['cc'] | 1, b=syms['E$EOF'])
            else:
                count = min(r['y'], 97, len(data) - position)
                d.write(r['x'], data[position:position + count])
                paths[r['a']][1] += count
                updates['y'] = count
        elif service == syms['I$Close']:
            if r['a']==audio_path:
                audio_claimed=False;audio_path=None
                audio_end_cycle=None
            del paths[r['a']]
            del path_names[r['a']]
        elif service == syms['I$Write'] and r['a']==audio_path:
            assert audio_claimed and audio_mode==5 and not mapped and r['y']==6
            packet=d.read(r['x'],6)
            if packet[0]&128 and (packet[1]>=60 or packet[2]>63 or not 0<int.from_bytes(packet[3:5],'big')<65535 or packet[5]):
                updates.update(cc=r['cc']|1,b=syms['E$IllArg'])
            else:
                if psg.get('queue_capacity'):
                    channel=packet[0]&3
                    assert len(audio_queues[channel])<psg['queue_capacity'], 'audio queue overfilled'
                    audio_queues[channel].append(packet)
                audio_packets.append(packet);audio_current_packets.append(packet);updates['y']=6
        elif service == syms['I$Write']:
            assert not paths, 'output before complete resource validation/close'
            assert not mapped, 'file write with foreign mapping live'
            if write_error:
                updates.update(cc=r['cc'] | 1, b=syms['E$Write'])
            else:
                count = min(r['y'], 83)
                output.extend(d.read(r['x'], count))
                updates['y'] = count
        else:
            assert service in (syms['I$WritLn'], syms['F$Icpt']), (service, r)  # usage text stays on stderr
        d.regs(**updates)
    raise AssertionError(f'probe did not exit after {cycles} sleep calls; opcode=' + d.read(database + syms.get('vmopcode', 0), 1).hex() + f'; audio={audio_packets}; polls={audio_polls}; flags=' + d.read(database+syms.get('vmflags',0),256).hex() + '; sound=' + d.read(database+syms.get('soundpath',0),14).hex())


def fixture(payload=b'\xf0\x00\xff', number=1, volume=1, offset=32, header=None):
    entry = bytes([(volume << 4) | (offset >> 16), (offset >> 8) & 255, offset & 255])
    length = len(payload).to_bytes(2, 'little')
    header = header if header is not None else b'\x12\x34' + bytes([volume]) + length * 2
    return {'/game/picDir': b'\xff\xff\xff' * number + entry,
            f'/game/vol.{volume}': bytes(offset) + header + payload}


def main():
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    bootrom = tempfile.NamedTemporaryFile(prefix='sierra-cpu-idle-', suffix='.rom')
    idle_rom(bootrom.name)
    emulator = subprocess.Popen(['xroar', '-machine', 'coco3', '-ui', 'null', '-ao', 'null',
        '-ram', '2048', '-no-ratelimit', '-gdb', '-gdb-port', str(port), '-timeout', '300',
        '-no-bas', '-extbas', bootrom.name, '-no-altbas'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = None
    try:
        time.sleep(.1)
        for _ in range(50):
            try:
                d = Debugger(port)
                break
            except ConnectionRefusedError:
                time.sleep(.1)
        assert d is not None
        d.write(0xFFDF, b'\0')
        d.write(0xFF90, b'\x4c')
        d.write(0xFF91, b'\x01')
        for address in (0xFF92, 0xFF93, 0xFF01, 0xFF03, 0xFF21, 0xFF23):
            d.write(address, b'\0')
        d.write(0xFFA8, bytes(range(8)))
        payload = bytes(range(256)) * 31 + bytes(255) + b'\xff'  # exactly 8192
        for base, database in ((0xE000, 0x2000), (0xA000, 0x6000)):
            assert exercise(d, fixture(payload, 255, 15, 0x23456), b'/game 255\r', base, database) == (0, payload)
            assert exercise(d, fixture(), b' /game/ 001 \r', base, database) == (0, b'\xf0\x00\xff')
        for arguments in (b'/game\r', b'/game -1\r', b'/game 256\r', b'/game 1x\r', b'/game 1 extra\r', b'x' * 128 + b' 1\r'):
            error, output = exercise(d, fixture(), arguments)
            assert error and not output
        cases = [({}, {}), (fixture(), {'arguments': b'/game 0\r'}),
                 (fixture(), {'arguments': b'/game 2\r'}), (fixture(b''), {}),
                 (fixture(b'\0'), {}), (fixture(b'\0' * 8192 + b'\xff'), {}),
                 (fixture(header=b'\0\x34\x01\x03\0\x03\0'), {}),
                 (fixture(header=b'\x12\x34\x02\x03\0\x03\0'), {}),
                 (fixture(header=b'\x12\x34\x81\x03\0\x03\0'), {}),
                 (fixture(header=b'\x12\x34\x01\x04\0\x03\0'), {}),
                 (fixture(header=b'\x12\x34\x01\x04\0\x04\0'), {}),
                 (fixture(), {'zero_read': True}), (fixture(), {'seek_error': True}),
                 (fixture(), {'write_error': True})]
        for files, options in cases:
            error, output = exercise(d, files, **options)
            assert error and not output, options
        print('PASS: native 6809 resource loading, relocated code/data, 20-bit seeks, volumes 1/15, exact 8KB boundary, short reads/writes, malformed resources, cleanup')
    finally:
        if d:
            d.s.close()
        bootrom.close()
        emulator.terminate()
        try:
            emulator.wait(timeout=2)
        except subprocess.TimeoutExpired:
            emulator.kill()
            emulator.wait(timeout=2)


if __name__ == '__main__':
    main()
