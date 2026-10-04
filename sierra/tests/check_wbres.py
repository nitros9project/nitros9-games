#!/usr/bin/env python3
"""Execute the native resource probe on a 6809 with adversarial file services."""
from pathlib import Path
import re
import socket
import subprocess
import time
import tempfile
from check_instances import Debugger, symbols

ROOT = Path(__file__).resolve().parents[1] / 'wildbits'


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


def exercise(d, files, arguments=b'/game 1\r', base=0xE000, database=0x2000, zero_read=False, seek_error=False, write_error=False, module='wbres', map_failure=0, allocation_error=False, unmap_error=False, window=0x8000, terminal=True, blocks=4, capture=False, multiple=False, firstblock=0x30, frame_capture=False, keyboard=b'', clock=(0,), bitmap_error=False, key_sense=0, cycle_limit=None, os_call_limit=20000):
    if module == 'wbgame':
        files = {'wbfont': (ROOT / 'wbfont').read_bytes(), **files}
    syms = symbols(ROOT / (module + '.map'))
    calls = {base + int(m[1], 16): int(m[2], 16) for m in re.finditer(
        r'^([0-9A-F]{4}) 103F([0-9A-F]{2}).*os9', (ROOT / (module + '.list')).read_text(), re.M)}
    d.write(database, bytes(syms['size']))
    code = (ROOT / module).read_bytes()
    d.write(base, code)
    argv = database + syms['size'] - 160
    d.write(argv, arguments)
    for address in calls:
        d.breakpoint(address)
    d.regs(pc=base + syms['start'], s=database + syms['size'] - 256,
           dp=database >> 8, u=database, x=argv, cc=0x50)
    paths, output, nextpath = {}, bytearray(), 3
    owned, mapped = {}, False
    nextblock = firstblock
    bitmapfirst, frame = None, bytearray()
    keyboard = bytearray(keyboard)
    clock = list(clock)
    clocksecond = clock[0]
    cycles = 0
    maps = 0
    unmap_failed = False
    for _ in range(os_call_limit):
        d.call('c')
        r = d.regs()
        service = calls[r['pc']]
        updates = {'pc': r['pc'] + 3, 'cc': r['cc'] & ~1}
        if service == syms['F$Exit']:
            assert not paths, f'leaked file paths: {paths}'
            assert not mapped and not owned, 'leaked picture allocation/mapping'
            assert d.read(base, len(code)) == code, 'native module modified its code/tables'
            for address in calls:
                d.breakpoint(address, False)
            if capture:
                return r['b'], bytes(frame if frame_capture else output), {name: d.read(database + syms[name], length) for name, length in [('vmopcode', 1), ('vmip', 2), ('vmvariables', 256), ('vmflags', 256), ('vmgameid', 8), ('messagebuffer', 512), ('vmobjects', 2752), ('vmkeys',150), ('vmkeycount',1), ('menucount', 1), ('menuitems', 1), ('menuready', 1), ('menutext', 768), ('asseterror', 1), ('vmerror', 1), ('vmend', 2), ('resourcelength', 2), ('vmcurrent', 1)]}
            return r['b'], bytes(frame if frame_capture else output)
        elif service == syms.get('F$Time'):
            assert not mapped
            if clock:
                clocksecond = clock.pop(0)
            d.write(r['x'], bytes([126,10,4,12,0,clocksecond]))
        elif service == syms.get('F$Sleep'):
            assert not mapped
            cycles += 1
            if cycle_limit is not None and cycles >= cycle_limit:
                d.write(database + syms['aborted'], b'\x01')
        elif service == syms['I$GetStt'] and r['b'] == syms['SS.Ready']:
            assert not mapped
            if not keyboard:
                updates.update(cc=r['cc'] | 1, b=syms['E$NotRdy'])
        elif service == syms['I$GetStt'] and r['b'] == syms.get('SS.KySns'):
            assert not mapped
            updates.update(a=key_sense)
        elif service == syms['I$GetStt'] and r['b'] == syms['SS.Opt']:
            assert r['a'] == 0
            d.write(r['x'], bytes([0 if terminal else 1]) + bytes(31))
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
        elif service == syms['I$SetStt'] and r['b'] in (0xcf, 0xe1, syms.get('SS.PScrn'), syms.get('SS.DScrn'), syms.get('SS.Palet')):
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
            assert not mapped and r['b'] == 1 and any(first <= r['x'] < first + count for first, count in owned.items())
            maps += 1
            if maps == map_failure:
                updates.update(cc=r['cc'] | 1, b=syms['E$MemFul'])
            else:
                d.write(0xFFA8 + window // 8192, bytes([r['x']]))
                mapped = True
                updates['u'] = window
        elif service == syms['F$ClrBlk']:
            assert mapped and r['b'] == 1 and r['u'] == window
            if unmap_error and not unmap_failed:
                unmap_failed = True
                updates.update(cc=r['cc'] | 1, b=syms['E$MemFul'])
            else:
                d.write(0xFFA8 + window // 8192, bytes([window // 8192]))
                mapped = False
        elif service == syms['I$Open']:
            name = d.read(r['x'], 160).split(b'\r')[0].decode()
            if name not in files:
                updates.update(cc=r['cc'] | 1, b=syms['E$PNNF'])
            else:
                paths[nextpath] = [files[name], 0]
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
            del paths[r['a']]
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
    raise AssertionError(f'probe did not exit after {cycles} sleep calls; opcode=' + d.read(database + syms.get('vmopcode', 0), 1).hex())


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
