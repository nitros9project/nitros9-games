#!/usr/bin/env python3
"""Exercise the native AGI LZW component on an actual emulated 6809."""
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def expand(data):
    """Independent byte-string dictionary oracle for AGI's 11-bit LZW."""
    bit = 0
    width = 9
    table = {n: bytes([n]) for n in range(256)}
    previous = None
    output = bytearray()
    while bit + width <= len(data) * 8:
        code = sum(((data[(bit + n) // 8] >> ((bit + n) % 8)) & 1) << n
                   for n in range(width))
        bit += width
        if code == 256:
            table = {n: bytes([n]) for n in range(256)}
            width, previous = 9, None
            continue
        if code == 257:
            return bytes(output)
        nextcode = len(table) + 2
        entry = table.get(code)
        if entry is None:
            if previous is None or code != nextcode:
                raise ValueError('invalid dictionary code')
            entry = previous + previous[:1]
        output.extend(entry)
        if previous is not None and nextcode < 2048:
            table[nextcode] = previous + entry[:1]
            if nextcode + 1 == 1 << width and width < 11:
                width += 1
        previous = entry
    raise ValueError('missing end code')


def packed(codes):
    result, accumulator, count = bytearray(), 0, 0
    for code, width in codes:
        accumulator |= code << count
        count += width
        while count >= 8:
            result.append(accumulator & 255)
            accumulator >>= 8
            count -= 8
    if count:
        result.append(accumulator)
    return bytes(result)


def resources():
    game = ROOT / 'kingsquest1'
    for directory in ('logDir', 'viewDir', 'sndDir'):
        entries = (game / directory).read_bytes()
        for number in range(len(entries) // 3):
            entry = int.from_bytes(entries[number * 3:number * 3 + 3], 'big')
            if entry == 0xffffff:
                continue
            volume = (game / f'vol.{entry >> 20}').read_bytes()
            offset = entry & 0xfffff
            header = volume[offset:offset + 7]
            expanded = int.from_bytes(header[3:5], 'little')
            stored = int.from_bytes(header[5:7], 'little')
            if expanded != stored:
                data = volume[offset + 7:offset + 7 + stored]
                reference = expand(data)
                assert len(reference) == expanded, (directory, number)
                yield f'{directory}/{number}', data, reference


def exercise(d, code, syms, data, expected, success=True, base=0xe000, database=0x8000):
    # Input and output are disjoint from private workspace and immutable code.
    inputbase, outputbase = 0x1000, 0x3000
    assert len(data) <= outputbase - inputbase
    assert expected <= database - outputbase - 16
    d.write(base, code)
    d.write(database, bytes(syms['size']) + b'GUARD')
    d.write(inputbase, data)
    d.write(outputbase, bytes([0xcc]) * (expected + 16))
    d.write(database + syms['inputpointer'], inputbase.to_bytes(2, 'big'))
    d.write(database + syms['inputend'], (inputbase + len(data)).to_bytes(2, 'big'))
    d.write(database + syms['outputpointer'], outputbase.to_bytes(2, 'big'))
    finish = base + syms['finish']
    d.breakpoint(finish)
    d.regs(pc=base + syms['start'], s=0xd000, dp=database >> 8,
           u=database, y=expected, cc=0x50)
    d.call('c')
    r = d.regs()
    assert r['pc'] == finish
    assert bool(r['cc'] & 1) != success, (r, data[:12])
    assert r['u'] == database
    assert d.read(outputbase + expected, 16) == bytes([0xcc]) * 16
    assert d.read(database + syms['size'], 5) == b'GUARD'
    assert d.read(base, len(code)) == code
    d.breakpoint(finish, False)
    return d.read(outputbase, expected)


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-lzw-') as temp:
        temp = Path(temp)
        binary = temp / 'lzwtest'
        subprocess.run(['lwasm.orig', '--6809', '--format=os9',
            '--pragma=pcaspcr,nosymbolcase,condundefzero',
            '-I' + str(ROOT / 'wildbits'), '-I' + str(ROOT.parent.parent / 'nitros9/defs'),
            '--map=' + str(binary) + '.map', '-o', str(binary),
            str(ROOT / 'tests/lzw-harness.asm')], check=True)
        syms = symbols(Path(str(binary) + '.map'))
        d, emulator = start_cpu(idle_rom(temp / 'idle.rom'))
        try:
            d.write(0xffdf, b'\0')
            code = binary.read_bytes()
            # KwKwK special case, repeated clears, literal/end and truncation.
            fixtures = [([256, 65, 258, 257], b'AAA'),
                        ([256, 65, 256, 66, 257], b'AB'),
                        ([256, 0, 255, 257], b'\0\xff')]
            for codes, reference in fixtures:
                data = packed([(n, 9) for n in codes])
                assert exercise(d, code, syms, data, len(reference)) == reference
            for codes, length in [([256, 258, 257], 1), ([256, 65, 260, 257], 3),
                                  ([256, 65, 257], 2), ([256, 65, 66, 257], 1),
                                  ([256, 65], 1), ([257], 0)]:
                exercise(d, code, syms, packed([(n, 9) for n in codes]), length, False)
            count = 0
            for name, data, reference in resources():
                actual = exercise(d, code, syms, data, len(reference))
                assert actual == reference, name
                count += 1
            # Relocation changes both code and private-state addresses.
            data = packed([(n, 9) for n in [256, 65, 258, 257]])
            assert exercise(d, code, syms, data, 3, base=0xd000, database=0x9000) == b'AAA'
            print(f'PASS: {count} compressed KQ1 logic/view/sound resources; malformed streams, guards, relocation and immutable code')
        finally:
            d.s.close()
            emulator.terminate()
            emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
