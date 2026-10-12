#!/usr/bin/env python3
"""Run formatter index scanners and native message expansion with real handlers."""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def reference(source, strict):
    value = count = cursor = 0
    for byte in source:
        if not 48 <= byte <= 57: break
        cursor += 1
        candidate = value*10 + byte-48
        if strict and candidate > 255: return value, count, cursor, True
        value = candidate & 255
        count = (count+1) & 255
    return value, count, cursor, False


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-index-') as name:
        tmp = Path(name)
        coco, cs = compile_module(ROOT/'objs/mnln.asm', tmp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame', defines=('WILDBITS=1',))
        edges = [b'', b'0', b'255', b'256', b'257', b'999', b'65535', b'999999999',
                 b'000000255', b'0000256', b'0'*255, b'0'*256, b'0'*257]
        cases = [str(n).encode()+b'!' for n in range(256)] + edges
        for byte in range(256):
            if not 48 <= byte <= 57:
                cases += [bytes([byte])+b'123', b'123'+bytes([byte])+b'4']
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=900)
        calls = 0
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            d.breakpoint(0x7e00)
            for owner, code, syms, bases in [('CoCo', coco, cs, (0x8000, 0x9000)),
                                            ('native', native, ns, (0x9000, 0xa000))]:
                private = 0 if owner == 'CoCo' else 0x1000
                for base in bases:
                    d.write(base, code)
                    if private:
                        d.write(private, bytes(syms['size'])+b'GUARD')
                        d.write(private+syms['resourcebase'], private.to_bytes(2, 'big'))
                    for source in cases:
                        address = 0x7400
                        data = b'G'+source+b'\0END'
                        d.write(address-1, data)
                        if private:
                            d.write(private+syms['parserwordlength'], b'\0')
                            d.write(private+syms['parserbestlength'], b'\0')
                            before = d.read(private, syms['size']) if source in edges else None
                        d.write(0x7ef0, b'\x7e\x00STACK')
                        d.regs(pc=base+syms['ParseDecStr'], s=0x7ef0, x=address,
                               y=0x7777, u=private, dp=private >> 8, cc=0x50)
                        d.call('c'); regs = d.regs()
                        value, count, cursor, rejected = reference(source, bool(private))
                        assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                        assert regs['u'] == private and regs['y'] == 0x7777
                        assert regs['x'] == address+cursor, (owner, source, cursor, regs)
                        assert regs['b'] == (syms['E$BMode'] if rejected else value), (owner, source, regs)
                        assert d.read(address-1, len(data)) == data
                        assert d.read(0x7ef2, 5) == b'STACK'
                        if private:
                            assert bool(regs['cc'] & 1) == rejected
                            assert d.read(private+syms['parserwordlength'], 1) == bytes([value])
                            assert d.read(private+syms['parserbestlength'], 1) == bytes([count])
                            assert d.read(private+syms['size'], 5) == b'GUARD'
                            if before is not None:
                                expected = bytearray(before)
                                expected[syms['parserwordlength']] = value
                                expected[syms['parserbestlength']] = count
                                assert d.read(private, syms['size']) == expected
                        calls += 1
                    if private:
                        variables = bytes(range(256))
                        d.write(private+syms['vmvariables'], variables)
                        cases_full = [(b'[%v'+str(n).encode()+b']', ('['+str(n)+']').encode(), 0)
                                      for n in range(256)]
                        cases_full += [(b'%v000255', b'255', 0), (b'%v'+b'0'*255, b'0', 0),
                                       (b'%v'+b'0'*257, b'0', 0), (b'%%', b'%', 0)]
                        cases_full += [(s, None, syms['E$BMode']) for s in
                                       [b'%v256', b'%v0000256', b'%v999', b'%v', b'%s12', b'%w0', b'%v'+b'0'*256]]
                        cases_full += [(b'%v0|2', b'00', 0),
                                       (b'%v117:%v116|2:%v115|2', b'117:116:115', 0),
                                       (b'%v7|2', b'07', 0), (b'%v255|1', b'255', 0),
                                       (b'%v7|0!', b'7!', 0),
                                       (b'%v7|255', b'0'*254+b'7', 0),
                                       (b'%v7|256', None, syms['E$BMode']),
                                       (b'%v7|', b'7', 0),
                                       (b'%v7|002!', b'07!', 0),
                                       (b'%v7|2%v7', b'077', 0),
                                       (b'%s0|2', b'|2', 0),
                                       (b'%v7|255'*9, None, syms['E$BMode'])]
                        # Every other non-NUL directive must retain the native
                        # unsupported policy, including CoCo's global/object forms.
                        cases_full += [(b'%' + bytes([letter]) + b'1', None, syms['E$UnkSvc'])
                                       for letter in range(1, 256) if letter not in b'wvsm%']
                        output = private+syms['fillstack']+2048
                        for source, wanted, error in cases_full:
                            d.write(address, source+b'\0')
                            d.write(private+syms['fillstack']-1, b'G')
                            d.write(private+syms['fillstack']+4096, b'H')
                            d.write(0x7ef0, b'\x7e\x00STACK')
                            d.regs(pc=base+syms['GameFormatMessage'], s=0x7ef0,
                                   x=address, u=private, dp=private >> 8, cc=0x50)
                            d.call('c'); regs = d.regs()
                            assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                            assert bool(regs['cc'] & 1) == bool(error) and regs['b'] == error, (source, regs)
                            assert d.read(private+syms['formatdepth'], 1) == b'\0'
                            assert d.read(private+syms['vmvariables'], 256) == variables
                            assert d.read(private+syms['fillstack']-1, 1) == b'G'
                            assert d.read(private+syms['fillstack']+4096, 1) == b'H'
                            assert d.read(0x7ef2, 5) == b'STACK'
                            if wanted is not None:
                                assert regs['x'] == output
                                assert d.read(output, len(wanted)+1) == wanted+b'\0', (source, wanted)
                                assert d.read(private+syms['parserreadlength'], 2) == len(wanted).to_bytes(2, 'big')
                            calls += 1
                    assert d.read(base, len(code)) == code
            print(f'PASS: {calls} actual CoCo/native index and native formatter calls; all byte values, every nondigit terminator, wrap/overflow and consumed cursor, leading zeros and count wrap, variable substitution/escape errors, frame cleanup, whole-state edges, guards/stack and immutable code')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
