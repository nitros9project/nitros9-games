#!/usr/bin/env python3
"""Compare the CoCo volume reader with the native loader on original KQ1 logic 0."""
from pathlib import Path
import subprocess
import tempfile

from check_instances import symbols
from check_lzw import resources
from check_wbres import exercise, idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / 'kingsquest1'


def compile_coco(output):
    subprocess.run([
        'lwasm.orig', '--6809', '--format=os9', '--no-warn=ifp1',
        '--pragma=pcaspcr,nosymbolcase,condundefzero',
        '-I' + str(GAME), '-I' + str(ROOT / 'objs'),
        '-I' + str(ROOT.parent.parent / 'nitros9/defs'),
        '--map=' + str(output) + '.map', '--list=' + str(output) + '.list',
        '-o' + str(output), str(ROOT / 'objs/mnln.asm')], check=True)


def main():
    name, packed, expected = next(item for item in resources()
                                  if item[0] == 'logDir/0')
    assert len(packed) == 5941 and len(expected) == 8950
    directory = (GAME / 'logDir').read_bytes()
    entry = directory[:3]
    volume_number = int.from_bytes(entry, 'big') >> 20
    volume_path = f'/game/vol.{volume_number}'
    volume = (GAME / f'vol.{volume_number}').read_bytes()
    offset = int.from_bytes(entry, 'big') & 0xfffff
    header = volume[offset:offset + 7]
    assert header[:3] == b'\x12\x34\x00'
    assert int.from_bytes(header[3:5], 'little') == len(expected)
    assert int.from_bytes(header[5:7], 'little') == len(packed)
    assert volume[offset + 7:offset + 7 + len(packed)] == packed

    with tempfile.TemporaryDirectory(prefix='sierra-coco-volume-load-') as temp:
        temp = Path(temp)
        coco = temp / 'mnln'
        compile_coco(coco)
        coco_syms = symbols(Path(str(coco) + '.map'))
        d, emulator = start_cpu(idle_rom(temp / 'idle.rom'), timeout=900)
        # CoCo's real 6809 LZW routine decodes the 8,950-byte resource between
        # debugger stops. Give that uninterrupted CPU span more than the
        # debugger client's default 15-second reply window.
        d.s.settimeout(120)
        try:
            d.write(0xffdf, b'\0')
            d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01')
            d.write(0xffa8, bytes(range(8)))
            coco_files = {volume_path: volume}
            for base in (0x8000, 0x9000):
                # The expanded logic must not cross into $6000, where the
                # CoCo decoder maps its 8-KiB shadow/input/dictionary window.
                target = 0x2000
                directory_pointer = 0x7000
                d.write(0x0531, bytes([3]) + bytes([0xff]) * 15)
                d.write(0x004f, (0x5500).to_bytes(2, 'big'))
                d.write(0x5500, bytes(32))
                files = [
                    (directory_pointer, entry),
                    (target, bytes([0xcc]) * len(expected)),
                ]
                # Seed the normal cached-volume fast path: volume zero is
                # already open as OS file handle 3. FindVol then exercises its
                # real seek, header validation and LZW resource decode.
                d.write(0x0531, b'\x03' + bytes([0xff]) * 15)
                error, _, state = exercise(
                    d, coco_files, module='mnln', module_root=temp,
                    base=base, database=0x5000, entry_symbol='FindVol',
                    stop_address=0x7e00, initial_dp=0,
                    initial_stack=(0x7e00).to_bytes(2, 'big'), initial_memory=files,
                    initial_regs={'u': directory_pointer, 'x': target},
                    preopened_paths=((3, volume_path),),
                    allow_open_paths=True,
                    read_limit=len(volume), os_call_limit=20000)
                assert error == 0 and not _, (error, state)
                output_pointer = state['registers']['u']
                actual = d.read(output_pointer, len(expected))
                assert actual == expected, (base, name, hex(output_pointer),
                                            actual[:32], expected[:32],
                                            d.read(target, 32))
                assert state['file_reads'].get(volume_path, 0) >= 2, state

            # Feed both production loaders the same volume truncated after a
            # valid header and an incomplete LZW stream. CoCo follows its
            # user-facing I/O error path; Wild Bits must fail and release the
            # partially allocated asset without writing a completed payload.
            truncated = volume[:offset + 7 + 64]
            error_prompts = []

            def choose_quit(cpu, regs, syms):
                error_prompts.append(regs['pc'])
                ret = int.from_bytes(cpu.read(regs['s'], 2), 'big')
                cpu.regs(pc=ret, s=regs['s'] + 2, a=1,
                         cc=regs['cc'] & ~0x05)
                return True

            base = 0x8000
            d.write(0x0531, b'\x03' + bytes([0xff]) * 15)
            d.write(0x004f, (0x5500).to_bytes(2, 'big'))
            d.write(0x5500, bytes(32))
            error, _, state = exercise(
                d, {volume_path: truncated}, module='mnln', module_root=temp,
                base=base, database=0x5000, entry_symbol='FindVol',
                stop_address=0x7e00, initial_dp=0,
                initial_stack=(0x7e00).to_bytes(2, 'big'),
                initial_memory=[(directory_pointer, entry),
                                (target, bytes([0xcc]) * len(expected))],
                initial_regs={'u': directory_pointer, 'x': target},
                preopened_paths=((3, volume_path),), allow_open_paths=True,
                breakpoint_hooks={'ErrorDialog': choose_quit},
                read_limit=128, os_call_limit=20000)
            assert error == 0 and error_prompts, ('CoCo did not take its read-error prompt', state)
            assert state['registers']['u'] == 0 and error_prompts, state

            native_files = {volume_path: volume, '/game/logDir': directory}
            for base in (0xe000, 0xd000):
                error, actual = exercise(
                    d, native_files, module='wbasset', base=base,
                    database=0x2000 if base == 0xe000 else 0x1000,
                    arguments=b'/game 0\r', blocks=2, resource_kind=0)
                assert error == 0 and actual == expected, (base, error, len(actual))

            # Exercise both direct-read branches using the same expanded
            # original logic bytes in a controlled, uncompressed volume record.
            plain_header = b'\x12\x34\0' + len(expected).to_bytes(2, 'little') * 2
            plain_volume = volume[:offset] + plain_header + expected
            base = 0x8000
            d.write(0x0531, b'\x03' + bytes([0xff]) * 15)
            d.write(0x004f, (0x5500).to_bytes(2, 'big'))
            d.write(0x5500, bytes(32))
            error, _, state = exercise(
                d, {volume_path: plain_volume}, module='mnln', module_root=temp,
                base=base, database=0x5000, entry_symbol='FindVol',
                stop_address=0x7e00, initial_dp=0,
                initial_stack=(0x7e00).to_bytes(2, 'big'),
                initial_memory=[(directory_pointer, entry),
                                (target, bytes([0xcc]) * len(expected))],
                initial_regs={'u': directory_pointer, 'x': target},
                preopened_paths=((3, volume_path),), allow_open_paths=True,
                read_limit=len(expected),
                capture=True)
            assert error == 0, ('CoCo direct-read fixture failed', state)
            assert d.read(state['registers']['u'], len(expected)) == expected
            error, actual = exercise(
                d, {volume_path: plain_volume, '/game/logDir': directory},
                module='wbasset', base=0xe000, database=0x2000,
                arguments=b'/game 0\r', blocks=2, resource_kind=0)
            assert error == 0 and actual == expected, (
                'Wild Bits direct-read fixture failed', error, len(actual))
            error, output = exercise(
                d, {volume_path: truncated, '/game/logDir': directory},
                module='wbasset', base=0xe000, database=0x2000,
                arguments=b'/game 0\r', blocks=2, resource_kind=0)
            assert error and not output, ('Wild Bits accepted the same truncated LZW resource', error)

            # Inject an actual OS-9 read-service error on the second volume
            # read, after each production loader has consumed the valid header.
            # CoCo must take its normal I/O prompt and return a null resource;
            # Wild Bits must propagate the error and release its partial slab.
            error_prompts.clear()
            coco_base = 0x8000
            error, _, state = exercise(
                d, {volume_path: volume}, module='mnln', module_root=temp,
                base=coco_base, database=0x5000, entry_symbol='FindVol',
                stop_address=0x7e00, initial_dp=0,
                initial_stack=(0x7e00).to_bytes(2, 'big'),
                initial_memory=[(directory_pointer, entry),
                                (target, bytes([0xcc]) * len(expected))],
                initial_regs={'u': directory_pointer, 'x': target},
                preopened_paths=((3, volume_path),), allow_open_paths=True,
                breakpoint_hooks={'ErrorDialog': choose_quit}, read_error_path=volume_path,
                read_error_at=2, capture=True)
            assert error == 0 and error_prompts, (
                'CoCo did not report the injected payload read error', state)
            assert state['registers']['u'] == 0 and state['file_reads'][volume_path] == 2, state

            error, output, state = exercise(
                d, {volume_path: volume, '/game/logDir': directory},
                module='wbasset', base=0xe000, database=0x2000,
                arguments=b'/game 0\r', blocks=2, capture=True,
                read_error_path=volume_path, read_error_at=2)
            assert error and not output, ('Wild Bits accepted an injected payload read error', state)
            assert state['file_reads'][volume_path] == 2 and state['asseterror'] != b'\0', state

            print('PASS: original KQ1 LZW logic 0 loads identically through CoCo FindVol '
                  'and Wild Bits wbasset at two code bases; both direct-read paths match '
                  'on an explicitly synthetic plain volume record; both reject truncated '
                  'LZW and injected payload read errors')
        finally:
            d.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill()
                emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
