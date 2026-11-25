#!/usr/bin/env python3
"""Exercise sierrastate's real exact-write loop with controlled OS-9 results."""
from pathlib import Path
import re
import tempfile

from check_instances import symbols
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1] / 'objs'


def main():
    image = (ROOT / 'sierrastate').read_bytes()
    syms = symbols(ROOT / 'sierrastate.map')
    error_syms = symbols(ROOT / 'wbgame.map')
    listing = (ROOT / 'sierrastate.list').read_text()
    matches = re.findall(r'^([0-9A-F]{4}) 103F8A.*os9 I\$Write', listing, re.M)
    assert len(matches) == 1, matches
    write_site = int(matches[0], 16)
    base, data, stop, stack = 0x8000, 0x5000, 0x7e00, 0x7ef0
    payload = bytes((i * 37 + 11) & 255 for i in range(73))

    with tempfile.TemporaryDirectory(prefix='sierra-sierrastate-transfer-') as temp:
        d, emulator = start_cpu(idle_rom(Path(temp) / 'idle.rom'), timeout=300)
        try:
            d.write(0xffdf, b'\0')
            d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01')
            d.write(0xffa8, bytes(range(8)))
            d.write(base, image)
            d.write(data, payload + b'GUARD')
            d.write(stop, b'\x39')
            d.breakpoint(stop)
            d.breakpoint(base + write_site)

            cases = [
                ('single full write', [73], None),
                ('multiple short writes', [1, 7, 16, 49], None),
                ('zero-byte write', [0], 'zero'),
                ('over-reported write', [74], 'over'),
                ('OS-9 write error', [None], 'os9'),
            ]
            calls = 0
            for label, responses, failure in cases:
                d.write(base + syms['StatePath'], b'\x04')
                d.write(base + syms['StateCreated'], b'\x01')
                d.write(0x7ed0, b'LOWGUARD')
                d.write(stack, b'\x7e\x00STACK')
                d.regs(pc=base + syms['StateWriteExact'], s=stack, x=data,
                       y=len(payload), dp=0, cc=0x50)
                response_index = 0
                writes = bytearray()
                for _ in range(12):
                    d.call('c')
                    regs = d.regs()
                    if regs['pc'] == stop:
                        break
                    assert regs['pc'] == base + write_site, (label, regs)
                    requested = regs['y']
                    assert regs['a'] == 4 and requested > 0, (label, regs)
                    response = responses[min(response_index, len(responses) - 1)]
                    response_index += 1
                    calls += 1
                    if response is None:
                        d.regs(pc=regs['pc'] + 3, b=216, cc=regs['cc'] | 1)
                        continue
                    assert regs['x'] == data + len(writes), (label, regs, len(writes))
                    if response:
                        writes.extend(d.read(regs['x'], min(response, requested)))
                    d.regs(pc=regs['pc'] + 3, y=response,
                           cc=regs['cc'] & ~1)
                else:
                    raise AssertionError((label, 'exact write did not return'))

                assert regs['s'] == stack + 2, (label, regs)
                assert d.read(stack + 2, 5) == b'STACK'
                assert d.read(0x7ed0, 8) == b'LOWGUARD'
                assert d.read(data, len(payload) + 5) == payload + b'GUARD'
                if failure is None:
                    assert not (regs['cc'] & 1) and regs['b'] == 0, (label, regs)
                    assert writes == payload, (label, len(writes), len(payload))
                    assert response_index == len(responses), (label, response_index)
                elif failure in ('zero', 'over'):
                    assert regs['cc'] & 1 and regs['b'] == 203, (label, regs)
                else:
                    assert regs['cc'] & 1 and regs['b'] == 216, (label, regs)

            # Run the complete save entry and inject a write failure after a
            # short header transfer has been retried. This verifies the real
            # StateFail path closes the open file and deletes the incomplete
            # save rather than merely testing StateWriteExact in isolation.
            private, filename = 0x1000, 0x7100
            write_offsets = {int(m[1], 16): m[3] for m in re.finditer(
                r'^([0-9A-F]{4}) 103F([0-9A-F]{2}).*os9 (I\$\w+)', listing, re.M)
                if m[3] in ('I$Delete', 'I$Create', 'I$Write', 'I$Seek', 'I$Close')}
            service_addresses = {base + offset: service for offset, service in write_offsets.items()}
            for address in service_addresses:
                d.breakpoint(address)

            d.write(base, image)
            d.write(private, bytes(0x6000))
            d.write(private + syms['vmgameid'], b'KQTEST\0\0')
            disk_full = error_syms['E$Full']
            d.write(filename, b'/s0/state1\0')
            d.write(0x7ed0, b'LOWGUARD')
            d.write(stack, b'\x7e\x00STACK')
            d.regs(pc=base + syms['StateEntry'], s=stack, u=private,
                   x=filename, y=0, a=0, dp=0, cc=0x50)
            seen = {'delete': 0, 'create': 0, 'write': 0, 'close': 0}
            stored = bytearray()
            delete_paths = []
            for _ in range(24):
                d.call('c')
                regs = d.regs()
                if regs['pc'] == stop:
                    break
                service = service_addresses.get(regs['pc'])
                assert service is not None, ('save failure path stopped unexpectedly', regs)
                if service == 'I$Delete':
                    seen['delete'] += 1
                    delete_paths.append(regs['x'])
                    assert d.read(regs['x'], 11) == b'/s0/state1\0', (service, regs)
                    if seen['delete'] == 1:
                        d.regs(pc=regs['pc'] + 3, b=205, cc=regs['cc'] | 1)
                    else:
                        d.regs(pc=regs['pc'] + 3, b=0, cc=regs['cc'] & ~1)
                elif service == 'I$Create':
                    seen['create'] += 1
                    d.regs(pc=regs['pc'] + 3, a=5, b=0, cc=regs['cc'] & ~1)
                elif service == 'I$Write':
                    seen['write'] += 1
                    if seen['write'] == 1:
                        result = 5
                    elif seen['write'] == 2:
                        result = regs['y']
                    else:
                        d.regs(pc=regs['pc'] + 3, b=disk_full, cc=regs['cc'] | 1)
                        continue
                    stored.extend(d.read(regs['x'], result))
                    d.regs(pc=regs['pc'] + 3, y=result, cc=regs['cc'] & ~1)
                elif service == 'I$Close':
                    seen['close'] += 1
                    assert regs['a'] == 5, ('close path descriptor', regs)
                    d.regs(pc=regs['pc'] + 3, b=0, cc=regs['cc'] & ~1)
                elif service == 'I$Seek':
                    d.regs(pc=regs['pc'] + 3, b=0, cc=regs['cc'] & ~1)
                else:
                    raise AssertionError((service, regs))
            else:
                raise AssertionError('StateBegin save failure path did not return')
            assert regs['s'] == stack + 2 and regs['cc'] & 1 and regs['b'] == disk_full, regs
            assert seen == {'delete': 2, 'create': 1, 'write': 3, 'close': 1}, seen
            assert len(delete_paths) == 2
            assert len(stored) == 18, len(stored)
            assert d.read(base + syms['StateOpen'], 1) == b'\0'
            assert d.read(base + syms['StateCreated'], 1) == b'\0'
            assert d.read(base + syms['StateError'], 1) == bytes([disk_full])
            assert d.read(stack + 2, 5) == b'STACK'
            assert d.read(0x7ed0, 8) == b'LOWGUARD'
            assert d.read(private + syms['vmgameid'], 8) == b'KQTEST\0\0'

            # A full medium at create time must return E$Full without opening
            # a descriptor or issuing the incomplete-file cleanup delete.
            d.write(base, image)
            d.write(private, bytes(0x6000))
            d.write(private + syms['vmgameid'], b'KQTEST\0\0')
            d.write(filename, b'/s0/state1\0')
            d.write(stack, b'\x7e\x00STACK')
            d.regs(pc=base + syms['StateEntry'], s=stack, u=private,
                   x=filename, y=0, a=0, dp=0, cc=0x50)
            full_seen = {'delete': 0, 'create': 0, 'write': 0, 'close': 0}
            for _ in range(8):
                d.call('c')
                regs = d.regs()
                if regs['pc'] == stop:
                    break
                service = service_addresses.get(regs['pc'])
                assert service is not None, ('create-full path stopped unexpectedly', regs)
                if service == 'I$Delete':
                    full_seen['delete'] += 1
                    assert d.read(regs['x'], 11) == b'/s0/state1\0'
                    d.regs(pc=regs['pc'] + 3, b=205, cc=regs['cc'] | 1)
                elif service == 'I$Create':
                    full_seen['create'] += 1
                    d.regs(pc=regs['pc'] + 3, a=0, b=disk_full, cc=regs['cc'] | 1)
                else:
                    raise AssertionError(('unexpected create-full follow-up', service, regs))
            else:
                raise AssertionError('StateBegin create-full failure did not return')
            assert regs['s'] == stack + 2 and regs['cc'] & 1 and regs['b'] == disk_full, regs
            assert full_seen == {'delete': 1, 'create': 1, 'write': 0, 'close': 0}, full_seen
            assert d.read(base + syms['StateOpen'], 1) == b'\0'
            assert d.read(base + syms['StateCreated'], 1) == b'\0'
            assert d.read(base + syms['StateError'], 1) == bytes([disk_full])
            assert d.read(stack + 2, 5) == b'STACK'
            print(f'PASS: sierrastate exact transfers retry short writes and reject malformed counts/errors; StateBegin preserves E$Full on create and write failures, with close/delete requested only for an opened incomplete file; {calls} isolated transfer calls and stack/data guards checked')
        finally:
            d.breakpoint(stop, False)
            d.breakpoint(base + write_site, False)
            d.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except Exception:
                emulator.kill()
                emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
