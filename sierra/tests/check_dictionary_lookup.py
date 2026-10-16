#!/usr/bin/env python3
"""Exercise the common dictionary kernel with mapped and cached stream cursors.

Uses the same original prefix-compressed vocabulary format as the native
parser regression, with a real per-letter index. No lookup is emulated.
"""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom, start_cpu


def indexed_dictionary(entries):
    data = bytearray(52)
    previous = ''
    for word, group in sorted(entries):
        letter = ord(word[0]) - ord('a')
        if not int.from_bytes(data[letter*2:letter*2+2], 'big'):
            data[letter*2:letter*2+2] = len(data).to_bytes(2, 'big')
        prefix = 0
        while prefix < min(len(previous), len(word)) and previous[prefix] == word[prefix]:
            prefix += 1
        suffix = bytearray(ord(c) ^ 127 for c in word[prefix:])
        suffix[-1] |= 128
        data.extend(bytes([prefix]) + suffix + group.to_bytes(2, 'big'))
        previous = word
    return bytes(data) + b'\0'


def main():
    vocabulary = indexed_dictionary([('a', 0), ('i', 0), ('look', 2),
        ('look at', 3), ('look at tree', 5), ('tree', 4)])
    cases = [(b'look', 2, b''), (b'LOOK', 2, b''),
        (b'look tree', 2, b'tree'), (b'look at tree', 5, b''),
        (b'look at tree unknown', 5, b'unknown'),
        (b'look at unknown', 3, b'unknown'),
        (b'a look', 0, b'look'), (b'i tree', 0, b'tree'),
        (b'unknown tree', 65535, None), (b'looker', 65535, None),
        (b'123 tree', 65535, None)]
    with tempfile.TemporaryDirectory(prefix='sierra-dictionary-') as name:
        tmp = Path(name)
        coco, cs = compile_module(ROOT/'objs/mnln.asm', tmp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm', tmp/'native', defines=('WILDBITS=1',))
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=900)
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            d.breakpoint(0x7e00)
            for owner, code, syms, bases in [('CoCo', coco, cs, (0x8000,0x9000)),
                                            ('stream', native, ns, (0x9000,0xa000))]:
                private = 0 if owner == 'CoCo' else 0x1000
                for base in bases:
                    d.write(base, code)
                    for sentence, expected, remaining in cases:
                        if private:
                            # Production parser normalizes before calling the kernel.
                            sentence = sentence.lower()
                            state = bytearray(syms['size'])
                            state[syms['resourcebase']:syms['resourcebase']+2] = b'\x10\x00'
                            state[syms['parserline']:syms['parserline']+len(sentence)+1] = sentence+b'\0'
                            state[syms['assetinput']:syms['assetinput']+len(vocabulary)] = vocabulary
                            state[syms['parserreadlength']:syms['parserreadlength']+2] = len(vocabulary).to_bytes(2,'big')
                            letter = sentence[0]-ord('a')
                            entry = int.from_bytes(vocabulary[letter*2:letter*2+2],'big') if 0 <= letter < 26 else 0
                            state[syms['dictionaryentry']:syms['dictionaryentry']+2] = (entry or 65535).to_bytes(2,'big')
                            d.write(private,state+b'GUARD')
                            source = private+syms['parserline']
                        else:
                            source = 0x7000
                            d.write(0x6000, vocabulary+b'GUARD')
                            d.write(0x1a8,b'\x60\x00')
                            d.write(source,sentence+b'\0GUARD')
                            d.write(base+syms['SortObjsPtr'],source.to_bytes(2,'big'))
                        d.write(0x7ef0,b'\x7e\x00STACK')
                        d.regs(pc=base+syms['LookupWord'],s=0x7ef0,u=source,dp=private>>8,cc=0x50)
                        d.call('c'); regs=d.regs()
                        result=(regs['a']<<8)|regs['b']
                        assert result == expected,(owner,sentence,result,expected)
                        assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                        if remaining is not None:
                            assert d.read(regs['u'],len(remaining)+1) == remaining+b'\0',(owner,sentence,regs)
                        if private:
                            assert not regs['cc'] & 1
                            assert d.read(private,syms['size']) == state
                            assert d.read(private+syms['size'],5) == b'GUARD'
                        else:
                            assert d.read(source+len(sentence)+1,5) == b'GUARD'
                        assert d.read(0x7ef2,5) == b'STACK'
                    if not private:
                        assert d.read(0x6000,len(vocabulary)+5) == vocabulary+b'GUARD'
                    actual=bytearray(d.read(base,len(code)))
                    if not private:
                        # SortObjsPtr is the owner's deliberately writable pointer.
                        actual[syms['SortObjsPtr']:syms['SortObjsPtr']+2] = code[syms['SortObjsPtr']:syms['SortObjsPtr']+2]
                    assert actual == code
            print('PASS: real mapped/streamed common lookup at two addresses per owner; longest phrases, '
                  'case folding, ignored words, unknowns, partial boundaries, stack and guards')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
