#!/usr/bin/env python3
"""Execute the native resource probe on a 6809 with adversarial file services."""
from pathlib import Path
import re
import socket
import subprocess
import time
from check_instances import Debugger, symbols

ROOT = Path(__file__).resolve().parents[1] / 'wildbits'


def exercise(d, files, arguments=b'/game 1\r', base=0xE000, database=0x2000, zero_read=False, seek_error=False, write_error=False):
    syms = symbols(ROOT / 'wbres.map')
    calls = {base + int(m[1], 16): int(m[2], 16) for m in re.finditer(
        r'^([0-9A-F]{4}) 103F([0-9A-F]{2}).*os9', (ROOT / 'wbres.list').read_text(), re.M)}
    d.write(database, bytes(syms['size']))
    d.write(base, (ROOT / 'wbres').read_bytes())
    argv = database + syms['size'] - 160
    d.write(argv, arguments)
    for address in calls:
        d.breakpoint(address)
    d.regs(pc=base + syms['start'], s=database + syms['size'] - 256,
           dp=database >> 8, u=database, x=argv, cc=0x50)
    paths, output, nextpath = {}, bytearray(), 3
    for _ in range(20000):
        d.call('c')
        r = d.regs()
        service = calls[r['pc']]
        updates = {'pc': r['pc'] + 3, 'cc': r['cc'] & ~1}
        if service == syms['F$Exit']:
            assert not paths, f'leaked file paths: {paths}'
            for address in calls:
                d.breakpoint(address, False)
            return r['b'], bytes(output)
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
        elif service == syms['I$Read']:
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
            if write_error:
                updates.update(cc=r['cc'] | 1, b=syms['E$Write'])
            else:
                count = min(r['y'], 83)
                output.extend(d.read(r['x'], count))
                updates['y'] = count
        else:
            assert service == syms['I$WritLn']  # usage text stays on stderr
        d.regs(**updates)
    raise AssertionError('probe did not exit')


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
    emulator = subprocess.Popen(['xroar', '-machine', 'coco3', '-ui', 'null', '-ao', 'null',
        '-ram', '2048', '-gdb', '-gdb-port', str(port), '-timeout', '300',
        '-no-bas', '-no-extbas', '-no-altbas'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        emulator.terminate()
        try:
            emulator.wait(timeout=2)
        except subprocess.TimeoutExpired:
            emulator.kill()
            emulator.wait(timeout=2)


if __name__ == '__main__':
    main()
