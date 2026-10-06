#!/usr/bin/env python3
"""Exercise the native AGI LZW component on an actual emulated 6809."""
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_wbres import idle_rom, start_cpu
from check_logic_executor import compile_module

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


def exercise_coco(d, code, syms, data, expected, base=0x8000):
    """Run PicRenderSetup; mock only file reads and shadow-page mapping."""
    output = 0x2000
    assert expected < 0x4000-16
    d.write(base, code)
    d.write(0, bytes(256))
    d.write(output, bytes([0xcc])*(expected+16))
    # The CoCo layout is a 1-KiB input buffer followed by a 6-KiB dictionary.
    d.write(0x6000, bytes(0x1c00)+b'GUARD')
    stack = 0x1df0
    d.write(stack, b'\x1d\x00\x03\x00'+output.to_bytes(2,'big')+
            len(data).to_bytes(2,'big')+b'STACK')
    finish = 0x1d00
    mapping = base+syms['MapShdwPage']
    reading = base+syms['ReadFile']
    for address in (finish, mapping, reading): d.breakpoint(address)
    consumed = 0
    try:
        d.regs(pc=base+syms['PicRenderSetup'],s=stack,dp=0,cc=0x50)
        for _ in range(32):
            d.call('c'); regs = d.regs()
            if regs['pc'] == finish: break
            assert regs['pc'] in (mapping, reading), regs
            updates = {}
            if regs['pc'] == reading:
                count = min(regs['y'],len(data)-consumed)
                assert count > 0
                d.write(regs['x'],data[consumed:consumed+count])
                consumed += count
                d.write(0x9f,b'\0')
                updates = {'a':count >> 8,'b':count & 255,'y':count,
                           'cc':regs['cc'] & ~1}
            target = int.from_bytes(d.read(regs['s'],2),'big')
            d.regs(pc=target,s=regs['s']+2,**updates)
        else:
            raise AssertionError('CoCo decoder did not return')
        assert regs['s'] == stack+2 and regs['dp'] == 0, regs
        assert (regs['a'] << 8 | regs['b']) == expected, regs
        assert d.read(output+expected,16) == bytes([0xcc])*16
        assert d.read(0x7c00,5) == b'GUARD'
        assert d.read(stack+8,5) == b'STACK'
        assert d.read(base,len(code)) == code
        return d.read(output,expected)
    finally:
        for address in (finish, mapping, reading): d.breakpoint(address,False)


def check_windows(d, native, ns, coco, cs):
    """Read code values directly, without dictionary validation masking bits."""
    patterns = (bytes(32), b'\xff'*32, bytes(range(32)),
                bytes((n*37+0xa5) & 255 for n in range(32)))
    calls = 0
    d.breakpoint(0x1d00)
    try:
        for owner, code, syms, bases in (
                ('CoCo', coco, cs, (0x8000,0x9000)),
                ('native', native, ns, (0xd000,0xe000))):
            private = 0x8000 if owner == 'native' else 0
            for base in bases:
                d.write(base,code)
                for pattern in patterns:
                    for width, prime in ((9,False),(10,False),(10,True),(11,False)):
                        if private:
                            d.write(private,bytes(syms['size'])+b'GUARD')
                            d.write(private+syms['inputpointer'],b'\x10\x00')
                            d.write(private+syms['inputend'],(0x1000+len(pattern)).to_bytes(2,'big'))
                        else:
                            d.write(0,bytes(256))
                        source = 0x1000 if private else 0x6000
                        d.write(source,pattern+b'GUARD')
                        bit = 0
                        # Both starts cover even/odd alignments for 10-bit
                        # codes; widths 9 and 11 visit every alignment themselves.
                        for current in ([9] if prime else [])+[width]*8:
                            if private:
                                d.write(private+syms['lzwwidth'],bytes((current,)))
                            else:
                                d.write(0xa4,current.to_bytes(2,'big'))
                            d.write(0x1df0,b'\x1d\x00STACK')
                            d.regs(pc=base+syms['LzwReadCode' if private else 'ReadPicPixel'],
                                   s=0x1df0,dp=private >> 8,u=private,
                                   x=0x4567,y=0x7654,cc=0x50)
                            d.call('c'); regs = d.regs()
                            value = (int.from_bytes(pattern[bit//8:bit//8+3],'little')
                                     >> (bit & 7)) & ((1 << current)-1)
                            assert regs['pc'] == 0x1d00 and regs['s'] == 0x1df2
                            assert regs['a'] << 8 | regs['b'] == value, (owner,bit,current,regs)
                            bit += current
                            if private:
                                assert not regs['cc'] & 1 and regs['u'] == private
                                consumed = int.from_bytes(d.read(private+syms['inputpointer'],2),'big')
                                assert consumed == source+(bit+7)//8, (bit,current,consumed)
                            else:
                                assert regs['x'] == 0x4567 and regs['y'] == 0x7654
                                assert int.from_bytes(d.read(0xba,2),'big') == bit
                            assert d.read(0x1df2,5) == b'STACK'
                            calls += 1
                        assert d.read(source,len(pattern)+5) == pattern+b'GUARD'
                        if private:
                            assert d.read(private+syms['size'],5) == b'GUARD'
                assert d.read(base,len(code)) == code
    finally:
        d.breakpoint(0x1d00,False)
    return calls


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-lzw-') as temp:
        temp = Path(temp)
        binary = temp / 'lzwtest'
        subprocess.run(['lwasm.orig', '--6809', '--format=os9',
            '--pragma=pcaspcr,nosymbolcase,condundefzero',
            '-I' + str(ROOT / 'objs'), '-I' + str(ROOT.parent.parent / 'nitros9/defs'),
            '--map=' + str(binary) + '.map', '-o', str(binary),
            str(ROOT / 'tests/lzw-harness.asm')], check=True)
        syms = symbols(Path(str(binary) + '.map'))
        coco, cs = compile_module(ROOT/'objs/mnln.asm', temp/'mnln')
        d, emulator = start_cpu(idle_rom(temp / 'idle.rom'), timeout=900)
        try:
            d.write(0xffdf, b'\0')
            d.write(0xff90, b'\x4c'); d.write(0xff91, b'\x01')
            d.write(0xffa8, bytes(range(8)))
            code = binary.read_bytes()
            # KwKwK special case, repeated clears, literal/end and truncation.
            fixtures = [([256, 65, 258, 257], b'AAA'),
                        ([256, 65, 256, 66, 257], b'AB'),
                        ([256, 0, 255, 257], b'\0\xff')]
            for codes, reference in fixtures:
                data = packed([(n, 9) for n in codes])
                assert exercise(d, code, syms, data, len(reference)) == reference
                assert exercise_coco(d, coco, cs, data, len(reference)) == reference
            for codes, length in [([256, 258, 257], 1), ([256, 65, 260, 257], 3),
                                  ([256, 65, 257], 2), ([256, 65, 66, 257], 1),
                                  ([256, 65], 1), ([257], 0)]:
                exercise(d, code, syms, packed([(n, 9) for n in codes]), length, False)
            count = 0
            for name, data, reference in resources():
                actual = exercise(d, code, syms, data, len(reference))
                assert actual == reference, name
                assert exercise_coco(d, coco, cs, data, len(reference)) == reference, name
                count += 1
            # Relocation changes both code and private-state addresses.
            data = packed([(n, 9) for n in [256, 65, 258, 257]])
            assert exercise(d, code, syms, data, 3, base=0xd000, database=0x9000) == b'AAA'
            assert exercise_coco(d, coco, cs, data, 3, base=0x9000) == b'AAA'
            windows = check_windows(d, code, syms, coco, cs)
            print(f'PASS: {count} compressed KQ1 logic/view/sound resources in '
                  'actual CoCo and native decoders; shared oracle bytes, native '
                  f'malformed-stream rejection, {windows} direct code reads covering '
                  'all bit alignments/widths, exact native input consumption, '
                  'guards, relocation and immutable code')
        finally:
            d.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
