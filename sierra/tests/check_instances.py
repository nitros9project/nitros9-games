#!/usr/bin/env python3
"""Execute assembled instance-isolation routines on XRoar's 6809 CPU.

Build kingsquest1's modules and the neighboring NitrOS-9 co3hires.sb first.
OS-9 calls are intercepted: this is CPU/MMU regression coverage, not a
replacement for booting two real games and exercising their UI.
"""
import argparse
from pathlib import Path
import re
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
SHELF = ROOT.parent


def symbols(path):
    return {m[1]: int(m[2], 16) for m in re.finditer(
        r'^Symbol: (\S+) .* = ([0-9A-F]+)$', path.read_text(), re.M)}


class Debugger:
    def __init__(self, port):
        self.s = socket.create_connection(('127.0.0.1', port), 5)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.s.settimeout(15)
        self.call('?')

    def call(self, command):
        data = command.encode()
        packet = b'$' + data + b'#' + f'{sum(data) % 256:02x}'.encode()
        for attempt in range(100):
            self.s.sendall(packet)
            result = self.receive()
            if result is not None:
                return result
            time.sleep(0.01)
        raise RuntimeError('debugger repeatedly rejected the packet')

    def receive(self):
        while True:
            c = self.s.recv(1)
            if c == b'$':
                break
            if c == b'-':
                return None
            if not c:
                raise ConnectionError('debugger disconnected')
        data = b''
        while (c := self.s.recv(1)) != b'#':
            data += c
        self.s.recv(2)
        self.s.sendall(b'+')
        return data.decode()

    def write(self, address, data):
        for start in range(0, len(data), 200):
            part = data[start:start + 200]
            assert self.call(f'M{address + start:x},{len(part):x}:{part.hex()}') == 'OK'

    def read(self, address, size):
        return b''.join(bytes.fromhex(self.call(f'm{address + n:x},{min(200, size-n):x}'))
                        for n in range(0, size, 200))

    def regs(self, **updates):
        raw = bytes.fromhex(self.call('g'))
        names = [('cc', 1), ('a', 1), ('b', 1), ('dp', 1), ('x', 2),
                 ('y', 2), ('u', 2), ('s', 2), ('pc', 2)]
        result = {}
        offset = 0
        for name, length in names:
            result[name] = int.from_bytes(raw[offset:offset+length], 'big')
            offset += length
        if updates:
            result.update(updates)
            encoded = b''.join(result[name].to_bytes(length, 'big') for name, length in names)
            assert self.call('G' + encoded.hex()) == 'OK'
        return result

    def breakpoint(self, address, enabled=True):
        assert self.call(f'{"Z" if enabled else "z"}0,{address:x},1') == 'OK'

    def run(self, entry, calls=None, **regs):
        # Return to a debugger breakpoint instead of an OS-9 caller.
        self.write(0x1DF0, bytes.fromhex('1d00'))
        self.breakpoint(0x1D00)
        self.regs(cc=0x50, dp=0, s=0x1DF0, pc=entry, **regs)
        count = 0
        # Continuing at a breakpoint skips that instruction in XRoar. Mock
        # an OS call at the routine's very first instruction before resuming.
        if calls and entry in calls:
            state = self.regs()
            service = self.read(entry + 2, 1)[0]
            updates = calls[entry](service, state)
            self.regs(**dict(updates, pc=entry + 3))
        while True:
            reply = self.call('c')
            state = self.regs()
            if state['pc'] == 0x1D00:
                assert state['s'] == 0x1DF2, state
                return state
            assert calls and state['pc'] in calls, (reply, state)
            count += 1
            assert count < 30, state
            service = self.read(state['pc'] + 2, 1)[0]
            updates = calls[state['pc']](service, state)
            updates['pc'] = state['pc'] + 3
            self.regs(**updates)


def check(d):
    game = ROOT / 'sierra/kingsquest1'
    syms = symbols(game / 'sierra.map')
    driver = SHELF / 'nitros9/level2/coco3/modules/co3hires.sb'
    hs = symbols(SHELF / 'nitros9/recipes/coco3/floppy/co3hires.sb.map')
    assert hs['H6309'] == 0, 'rebuild the 6809 driver: its symbol map was replaced by a 6309 build'
    code = (game / 'sierra').read_bytes()
    # Enable all-RAM, task 1, and the MMU, with a known 0..7 mapping.
    d.write(0xFFDF, b'\0')
    d.write(0xFF90, b'\x4c')
    d.write(0xFF91, b'\x01')
    for address in (0xFF92, 0xFF93, 0xFF01, 0xFF03, 0xFF21, 0xFF23):
        d.write(address, b'\0')  # no kernel interrupt handlers in the isolated CPU fixture
    d.write(0xFFA8, bytes(range(8)))
    d.write(0xE000, code)
    assert d.read(0xE000, len(code)) == code, 'RAM setup failed'
    # Copy four source pages, then copy the same template for a second instance.
    template = bytes((n * 37 + 11) % 256 for n in range(0x8000))
    template = bytearray(template)
    template[2:4] = (0x6372).to_bytes(2, 'big')
    d.write(0x6000, template)
    calls = {}
    link_count = 0
    def syscall(service, state):
        nonlocal link_count
        if service == syms['F$Link']:
            link_count += 1
            return {'cc': 0x50, 'u': 0x6000}
        assert service == syms['F$UnLink'], hex(service)
        link_count -= 1
        return {'cc': 0x50}
    for offset in range(len(code) - 2):
        if code[offset:offset + 2] == bytes.fromhex('103f'):
            address = 0xE000 + offset
            calls[address] = syscall
            d.breakpoint(address)
    pages = []
    for first in (80, 100):
        d.write(syms['PrivateNext'], bytes([first]))
        d.write(syms['PrivateLimit'], bytes([first+8]))
        d.write(syms['MmuBlk2Orig'], b'\0')
        result = d.run(0xE000 + syms['NMLoadModule'], calls,
                       x=0x1000, u=0x0A)
        assert not result['cc'] & 1, result
        assert link_count == 0, 'template reference leak'
        assert d.read(syms['PrivateNext'], 1) == bytes([first+4])
        assert d.read(0x0D, 4) == bytes(range(first, first+4)), 'wrong runtime map'
        assert d.read(0x6000, 0x8000) == template, 'shared template was modified'
        for i in range(4):
            d.write(0xFFAA, bytes([first+i]))
            assert d.read(0x4000, 0x2000) == template[i*0x2000:(i+1)*0x2000]
        pages.append(first)
        d.write(0xFFAA, b'\x02')
    # Simulate interpreter self-modification in instance 1, verify instance 2.
    d.write(0xFFAA, bytes([pages[0]]))
    d.write(0x4020, b'private instance')
    d.write(0xFFAA, bytes([pages[1]]))
    assert d.read(0x4020, 16) == template[0x20:0x30]
    d.write(0xFFAA, b'\x02')
    # Exhaustion must balance the acquired template reference and return error.
    d.write(syms['PrivateNext'], b'\x78')
    d.write(syms['PrivateLimit'], b'\x78')
    result = d.run(0xE000 + syms['NMLoadModule'], calls, x=0x1000, u=0x0A)
    assert result['cc'] & 1 and result['b'] == syms['E$MemFul']
    assert link_count == 0
    for fail_timer in (False, True):
        def timer_call(service, state):
            if service == syms['F$Icpt']:
                return {'cc': 0x50}
            if service == syms['I$Attach']:
                return {'u': 0x1600, 'cc': 0x50}
            if service == syms['I$Open']:
                return {'a': 3, 'cc': 0x50}
            assert service == syms['I$SetStt'], hex(service)
            assert state['a'] == 3, 'timer operation used another instance\'s path'
            if state['b'] == syms['SS.ARAM']:
                assert state['x'] == 21
                return {'x': 10, 'cc': 0x50}
            assert state['b'] == syms['SS.KSet']
            return {'cc': 0x51 if fail_timer else 0x50, 'b': syms['E$DevBsy'] if fail_timer else 0}
        timer_calls = {address: timer_call for address in calls}
        result = d.run(0xE000 + syms['SetupVirq'], timer_calls)
        assert bool(result['cc'] & 1) == fail_timer, result
        if fail_timer:
            assert result['b'] == syms['E$DevBsy'], 'timer error was overwritten'
        else:
            assert result['a'] == 0 and result['b'] == 10, result
    for address in calls:
        d.breakpoint(address, False)
    assert d.read(0xE000, len(code)) == code, 'Sierra code was modified'
    print('PASS: private engine pages, independent writes, immutable template, balanced links, allocation exhaustion')
    print('PASS: timer registration uses the private path and preserves failures')
    # The kernel's system DAT is distinct from PID 1's (SysGo's) image.
    system_image = b''.join(n.to_bytes(2, 'big') for n in range(8))
    own_image = bytes.fromhex('000a333e333e333e333e333e333e0007')
    d.write(syms['D.SysDAT'], bytes.fromhex('0640'))
    d.write(0x0640, system_image)
    d.write(syms['D.PrcDBT'], bytes.fromhex('0500'))
    d.write(0x0507, b'\x82')
    d.write(0xFFAA, b'\x04')
    d.write(0x4240, own_image)
    d.write(0xFFA8, bytes.fromhex('0a3e3e0304050607'))
    d.write(0, bytes(0x1C00))
    def mapping_call(service, state):
        if service == syms['F$ID']:
            return {'a': 7, 'cc': 0x50}
        assert service == syms['F$GPrDsc'], (hex(service), state, d.read(0, 0x46).hex(), d.read(syms['mmubuf'], 16).hex())
        assert state['a'] == 7, 'snapshot requested SysGo instead of this process'
        descriptor = bytearray(512)
        descriptor[0x40:0x50] = own_image
        d.write(state['x'], descriptor)
        return {'cc': 0x50}
    mapping_calls = {address: mapping_call for address in calls}
    for address in mapping_calls:
        d.breakpoint(address)
    d.run(0xE000 + syms['mmuini1'], mapping_calls)
    assert d.read(syms['mmubuf'], 16) == bytes(range(8)) + bytes.fromhex('0a3e3e3e3e3e3e07')
    d.run(0xE000 + syms['SetupProcMap'], mapping_calls)
    assert d.read(syms['SierraPdBlk'], 1) == b'\x04'
    assert d.read(syms['Sierra2ndBlk'], 2) == bytes.fromhex('2243')
    d.write(0xFFA9, b'\x04')
    assert d.read(0x2240, 16) == bytes.fromhex('000a000a000a') + own_image[6:]
    d.write(0xFFA9, b'\x0a')
    d.run(0xE000 + syms['RestoreMmu'])
    d.write(0xFFA9, b'\x04')
    assert d.read(0x2240, 16) == own_image
    d.write(0xFFA8, bytes(range(8)))
    for address in mapping_calls:
        d.breakpoint(address, False)
    print('PASS: kernel/own MMU snapshots, private descriptor lookup, alias setup and restoration')
    # Check terminal ownership using the compiled shared screen service.
    d.write(0x6000, driver.read_bytes())
    for pid, expected_busy in ((8, True), (7, False)):
        d.write(0x102A, b'\x07')
        d.write(0x1200 + hs['PD.CPR'], bytes([pid]))
        # Unknown service needs no OS calls: authorized caller reaches UnkSvc,
        # unauthorized caller returns DevBsy without changing device state.
        before = d.read(0x1000, 0x10A)
        result = d.run(0x6000 + hs['SetStat'], a=0xFF, y=0x1200, u=0x1000)
        assert result['cc'] & 1
        assert result['b'] == hs['E$DevBsy' if expected_busy else 'E$UnkSvc'], result
        assert d.read(0x1000, 0x10A) == before
    print('PASS: terminal ownership rejects a different PID and preserves the owner state')
    # A capability query must work even while another process owns the screen.
    d.write(0x1200 + hs['PD.RGS'], bytes.fromhex('1500'))
    d.write(0x1500 + hs['R$X'], bytes.fromhex('ffff'))
    before = d.read(0x1000, 0x10A)
    result = d.run(0x6000 + hs['SetStat'], a=hs['SS.AScrn'], y=0x1200, u=0x1000)
    assert not result['cc'] & 1
    assert d.read(0x1500 + hs['R$X'], 2) == bytes.fromhex('0002')
    assert d.read(0x1000, 0x10A) == before
    print('PASS: capability query does not allocate or change screen ownership')
    allocated = []
    released = []
    fail_mapping = False
    def screen_call(service, state):
        if service == hs['F$AlHRAM']:
            allocated.append(48)
            return {'a': 0, 'b': 48, 'cc': 0x50}
        if service == hs['F$MapBlk']:
            if fail_mapping:
                return {'cc': 0x51, 'b': hs['E$MemFul']}
            return {'u': 0x8000, 'cc': 0x50}
        assert service == hs['F$DelRAM'], hex(service)
        released.append((state['x'], state['b']))
        return {'cc': 0x50}
    screen_calls = {}
    driver_code = driver.read_bytes()
    for offset in range(len(driver_code) - 2):
        if driver_code[offset:offset+2] == bytes.fromhex('103f'):
            address = 0x6000 + offset
            screen_calls[address] = screen_call
            d.breakpoint(address)
    for fail_mapping in (False, True):
        d.write(0x1000, bytes(0x10A))
        d.write(hs['D.Proc'], bytes.fromhex('1200'))
        d.write(0x1200, bytes(512))
        d.write(0x1200 + hs['PD.CPR'], b'\x07')
        d.write(0x1200 + hs['PD.RGS'], bytes.fromhex('1500'))
        d.write(0x1500 + hs['R$X'], bytes.fromhex('0004'))
        result = d.run(0x6000 + hs['SetStat'], screen_calls,
                       a=hs['SS.AScrn'], y=0x1200, u=0x1000)
        if fail_mapping:
            assert result['cc'] & 1 and result['b'] == hs['E$MemFul'], result
            assert d.read(0x102A, 1) == b'\0'
            assert d.read(0x1101, 1) == b'\0'
        else:
            assert not result['cc'] & 1, result
            assert d.read(0x102A, 1) == b'\x07', 'wrong owner PID'
            assert d.read(0x1500 + hs['R$X'], 2) == bytes.fromhex('8000')
            assert d.read(0x1500 + hs['R$Y'], 2) == bytes.fromhex('0001')
            d.write(0x1500 + hs['R$Y'], bytes.fromhex('0001'))
            result = d.run(0x6000 + hs['SetStat'], screen_calls,
                           a=hs['SS.FScrn'], y=0x1200, u=0x1000)
            assert not result['cc'] & 1, result
            assert d.read(0x102A, 1) == b'\0', 'owner survives final screen release'
    assert released == [(48, 4), (48, 4)], released
    print('PASS: successful screen claim/release and mapping-failure rollback')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int)
    parser.add_argument('--boot', action='store_true', help='boot King\'s Quest I and reach the interpreter cycle')
    parser.add_argument('--disk', type=Path)
    parser.add_argument('--instances', type=int, default=1)
    parser.add_argument('--setup-module', type=Path, default=ROOT / 'sierra/kingsquest1/sierra')
    parser.add_argument('--setup-map', type=Path, default=ROOT / 'sierra/kingsquest1/sierra.map')
    args = parser.parse_args()
    if args.port is None:
        with socket.socket() as reservation:
            reservation.bind(('127.0.0.1', 0))
            args.port = reservation.getsockname()[1]
    command = ['xroar', '-machine', 'coco3', '-ui', 'null', '-ao', 'null', '-ram', '2048',
        '-gdb', '-gdb-port', str(args.port), '-timeout', '300']
    if args.boot:
        command += ['-rompath', str(SHELF / 'toolshed/cocoroms'), '-cart', 'rsdos',
            '-cart-rom', 'disk11.rom', '-load-fd0', str(args.disk or ROOT / 'sierra/kingsquest1/KingsQuestI.dsk'),
            '-no-disk-write-back', '-type', 'DOS\r']
    else:
        command += ['-no-bas', '-no-extbas', '-no-altbas']
    emulator = subprocess.Popen(command, stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE)
    try:
        time.sleep(0.5)  # let machine initialization finish before stopping its CPU
        for attempt in range(50):
            try:
                d = Debugger(args.port)
                break
            except ConnectionRefusedError:
                time.sleep(0.1)
        else:
            raise RuntimeError('XRoar debugger did not start: ' + (emulator.stderr.read().decode() if emulator.poll() is not None else 'still running'))
        if args.boot:
            d.s.settimeout(60)
            mn = symbols(ROOT / 'sierra/kingsquest1/mnln.map')
            si = symbols(args.setup_map)
            setup_header = args.setup_module.read_bytes()[:13]
            engine_header = (ROOT / 'sierra/kingsquest1/mnln').read_bytes()[:13]
            target = 0x8000 + mn['MainCycleLoop']
            starts = [0xE000 + off + si['InitEntry'] for off in range(-0x2000, 0x1A00, 0x100)]
            for address in starts:
                d.breakpoint(address)
            base = None
            passed = {}
            watched = {}
            for hit in range(500):
                reply = d.call('c')
                state = d.regs()
                address = state['pc']
                if base is None:
                    candidate = address - si['InitEntry']
                    if d.read(candidate, 13) == setup_header:
                        base = candidate
                        for point in starts:
                            d.breakpoint(point, False)
                        watched = {base + si['InitEntry']: 'entry',
                                   base + si['MainInit']: 'ready',
                                   base + si['ExitNow']: 'exit', target: 'cycle',
                                   0x8000 + mn['JoyInputCheck']: 'joystick'}
                        for point in watched:
                            d.breakpoint(point)
                    else:
                        d.breakpoint(address, False)
                        d.call('s')
                        continue
                event = watched.get(address)
                header = d.read(base if event in ('entry', 'ready', 'exit') else 0x8000, 13)
                valid = header == (setup_header if event in ('entry', 'ready', 'exit') else engine_header)
                if valid:
                    if event == 'exit':
                        raise AssertionError(('game exited before completing boot', state))
                    if event == 'entry':
                        print('Interpreter process entered', flush=True)
                    if event == 'ready':
                        print('Engine copies and screen ready, PID', d.read(si['OwnProcessId'], 1)[0], flush=True)
                    if event == 'joystick':
                        d.regs(a=0x1B)  # Ctrl-Break at the joystick setup prompt
                    if event == 'cycle':
                        pid = d.read(si['OwnProcessId'], 1)[0]
                        passed[pid] = d.read(0, si['InstanceHeapBase'])
                        print('Interpreter cycle reached, PID', pid, flush=True)
                        if len(passed) == args.instances:
                            break
                d.breakpoint(address, False)
                d.call('s')
                d.breakpoint(address)
            else:
                raise AssertionError('too many unrelated breakpoint hits')
            assert len(passed) == args.instances
            if args.instances > 1:
                states = list(passed.values())
                assert states[0][si['PrivateNext']] != states[1][si['PrivateNext']], 'engine pages are shared'
                assert states[0][si['ViPathNum']] != 0 and states[1][si['ViPathNum']] != 0
                assert states[0][si['MmuBlk2Orig']] != states[1][si['MmuBlk2Orig']], 'process data is shared'
                departing = pid
                d.regs(pc=0x8000 + mn['DoQuitAgi'])
                exited = False
                for hit in range(200):
                    d.call('c')
                    state = d.regs()
                    address = state['pc']
                    if address == base + si['ExitNow'] and d.read(base, 13) == setup_header:
                        assert d.read(si['OwnProcessId'], 1)[0] == departing
                        for name, count in (('ViPathNum', 1), ('ViDevAddr', 2), ('ProcMapReady', 1), ('HiResScrnNum', 1)):
                            assert d.read(si[name], count) == bytes(count), (name, state)
                        exited = True
                    if address == target and d.read(0x8000, 13) == engine_header:
                        survivor = d.read(si['OwnProcessId'], 1)[0]
                        if exited and survivor != departing:
                            original = passed[survivor]
                            for name in ('PrivateNext', 'PrivateLimit', 'MmuBlk2Orig', 'ViPathNum', 'HiResScrnNum'):
                                assert d.read(si[name], 1) == original[si[name]:si[name]+1], name
                            print('PASS: quitting PID', departing, 'released its resources; PID', survivor, 'continues', flush=True)
                            break
                    d.breakpoint(address, False)
                    d.call('s')
                    d.breakpoint(address)
                else:
                    raise AssertionError('surviving game did not resume after peer exit')
            print('PASS: real game initialization completed for', args.instances, 'instance(s)', flush=True)
        else:
            check(d)
        d.s.close()
    finally:
        emulator.terminate()
        try:
            emulator.wait(timeout=2)
        except subprocess.TimeoutExpired:
            emulator.kill()
            emulator.wait()


if __name__ == '__main__':
    main()
