#!/usr/bin/env python3
"""Execute bytecode directly from a native owned physical resource slab."""
from pathlib import Path
import tempfile
from check_wbres import exercise, idle_rom, start_cpu
from check_wbasset import asset_fixture
from check_lzw import packed, resources


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-exec-') as temp:
        d, emulator = start_cpu(idle_rom(Path(temp) / 'idle.rom'))
        try:
            d.write(0xffdf, b'\0')
            d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01')
            d.write(0xffa8, bytes(range(8)))
            # Jump from code offset 2 across the physical 8KB boundary.
            script = b'\xfe' + (8192 - 5).to_bytes(2, 'little')
            script += bytes(8192 - len(script) - 2)
            script += bytes([3,250,99,12,200,0])
            payload = len(script).to_bytes(2, 'little') + script
            for base, database, window in [(0xe000, 0x2000, 0x8000), (0xd000, 0x1000, 0xa000)]:
                error, output, state = exercise(d, asset_fixture(payload, len(payload)),
                    module='wbexec', blocks=2, capture=True,
                    base=base, database=database, window=window)
                assert not error and len(output) == 512
                assert state['vmvariables'][250] == 99 and state['vmflags'][200] == 1
            def logic_files(scripts):
                volume, entries = bytearray(), bytearray()
                for script in scripts:
                    entries += len(volume).to_bytes(3, 'big')
                    payload = len(script).to_bytes(2, 'little') + script
                    length = len(payload).to_bytes(2, 'little')
                    volume += b'\x12\x34\0' + length * 2 + payload
                return {'/game/logDir': bytes(entries), '/game/vol.0': bytes(volume)}
            files = logic_files([bytes([20,1,22,1,22,1,3,250,99,0]),
                                 bytes([1,251,12,200,0])])
            error, output, state = exercise(d, files, arguments=b'/game 0\r',
                module='wbexec', blocks=None, multiple=True, capture=True)
            assert not error and len(output) == 512
            assert state['vmvariables'][250:252] == bytes([99,2]) and state['vmflags'][200] == 1
            files = logic_files([bytes([22,1,0]), bytes([22,1,0])])
            error, output = exercise(d, files, arguments=b'/game 0\r',
                module='wbexec', blocks=None, multiple=True)
            assert error and not output  # bounded nested-call depth
            malformed = logic_files([bytes([22,1,0]), b'\0'])
            offset = int.from_bytes(malformed['/game/logDir'][3:6], 'big')
            packed_bad = packed([(n,9) for n in [256,258,257]])
            malformed['/game/vol.0'] = (malformed['/game/vol.0'][:offset] +
                b'\x12\x34\0\x0a\0' + len(packed_bad).to_bytes(2,'little') + packed_bad)
            error, output = exercise(d, malformed, arguments=b'/game 0\r',
                module='wbexec', blocks=None, multiple=True)
            assert error and not output  # failed callee allocation remains owned for cleanup
            files = logic_files([bytes([22,1,0])])
            error, output = exercise(d, files, arguments=b'/game 0\r',
                module='wbexec', blocks=None, multiple=True)
            assert error and not output  # missing callee releases caller
            body = bytes([33,63,37,63,159,167,39,63,250,251,
                          3,252,8,86,63,252,87,63,253,
                          54,63,15,57,63,254,45,63,46,63,
                          56,63,34,0])
            error, output, state = exercise(d, logic_files([body]), arguments=b'/game 0\r',
                module='wbexec', blocks=None, multiple=True, capture=True)
            assert not error and len(output) == 512
            assert state['vmvariables'][250:255] == bytes([159,167,8,8,15])
            obj = state['vmobjects'][63*43:64*43]
            assert obj[2:5] == bytes([63,159,167]) and obj[0x1a:0x1c] == bytes([159,167])
            assert obj[0x21] == 8 and obj[0x24:0x27] == bytes([15,0,0x30])
            for body in [bytes([33,64,0]), bytes([54,0,16,0]), bytes([3,250,9,86,0,250,0])]:
                error, output = exercise(d, logic_files([body]), arguments=b'/game 0\r',
                    module='wbexec', blocks=None, multiple=True)
                assert error and not output
            # Same numeric ID in three resource directories must be distinct.
            files = logic_files([bytes([142,10,30,0,30,0,32,0,32,0,98,0,171,172,0])])
            volume = bytearray(files['/game/vol.0'])
            for directory, content in [('viewDir', b'view-data'), ('sndDir', b'sound-data')]:
                files['/game/' + directory] = len(volume).to_bytes(3, 'big')
                length = len(content).to_bytes(2, 'little')
                volume += b'\x12\x34\0' + length * 2 + content
            files['/game/vol.0'] = bytes(volume)
            error, output = exercise(d, files, arguments=b'/game 0\r',
                module='wbexec', blocks=None, multiple=True)
            assert not error and len(output) == 512
            # A configured one-record replay buffer must fail safely at two loads.
            files = logic_files([bytes([142,1,20,1,20,2,0]), b'\0', b'\0'])
            error, output = exercise(d, files, arguments=b'/game 0\r',
                module='wbexec', blocks=None, multiple=True)
            assert error and not output
            text = b'KQ1\0'
            encrypted = bytes(value ^ b'Avis Durgan'[n % 11] for n, value in enumerate(text))
            body = bytes([143,1,0])
            payload = len(body).to_bytes(2, 'little') + body + b'\x01\x08\0\x04\0' + encrypted
            error, output, state = exercise(d, asset_fixture(payload, len(payload)),
                module='wbexec', blocks=1, capture=True)
            assert not error and state['vmgameid'] == b'KQ1' + bytes(5)
            for payload in [payload[:-1], payload[:8] + b'\xff\xff' + payload[10:]]:
                error, output = exercise(d, asset_fixture(payload, len(payload)), module='wbexec', blocks=1)
                assert error and not output
            _, data, reference = next(resources())
            game = Path(__file__).resolve().parents[1] / 'kingsquest1'
            files = {'/game/' + p.name: p.read_bytes() for p in game.iterdir() if p.name in ('logDir','viewDir','sndDir','picDir') or p.name.startswith('vol.')}
            error, output, state = exercise(d, files, arguments=b'/game 0\r',
                module='wbexec', blocks=None, multiple=True, capture=True)
            assert error == 208 and not output  # explicit unsupported platform opcode
            assert state['vmgameid'] == b'KQ1' + bytes(5)
            print('KQ1 stop:', error, {n: state[n].hex() for n in ('asseterror','vmerror','vmend','resourcelength','vmcurrent')})
            print(f'KQ1 startup stops at unported command/test {state["vmopcode"][0]}; caller-restored IP {int.from_bytes(state["vmip"], "big")}')
            print('PASS: native mapped bytecode crosses physical pages, relocated data/code, bounded fetch, cached/nested calls, explicit unsupported-command failure and allocation cleanup')
        finally:
            d.s.close()
            emulator.terminate()
            emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
