#!/usr/bin/env python3
"""Run both real decimal converters and native expansion/overflow stack cleanup."""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
WIDE = [256, 257, 999, 1000, 9999, 10000, 32767, 32768, 65534, 65535]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-decimal-output-') as name:
        tmp = Path(name)
        coco, cs = compile_module(ROOT/'objs/mnln.asm', tmp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame', defines=('WILDBITS=1',))
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
                        start, end = 0x7400, 0x7403
                    else:
                        start, end = base+syms['NumConvBuf'], base+syms['NumConvEnd']
                    guards = d.read(start-1, 1), d.read(end+1, 1)
                    for value in list(range(256))+(WIDE if not private else []):
                        d.write(start, b'\xa5'*(end-start+1))
                        before = d.read(private, syms['size']) if private and value in (0, 9, 10, 99, 100, 255) else None
                        d.write(0x7ef0, b'\x7e\x00STACK')
                        d.regs(pc=base+syms['UIntToDecStr'], s=0x7ef0, x=end,
                               y=0x7777, u=private, a=value >> 8, b=value & 255,
                               dp=private >> 8, cc=0x50)
                        try:
                            d.call('c'); regs = d.regs()
                        except Exception:
                            print('Converter failure:', owner, hex(base), value, flush=True)
                            d.s.sendall(b'\x03')
                            try:
                                d.receive()
                                print('Stopped registers:', d.regs(), flush=True)
                            except Exception as diagnostic:
                                print('Stop diagnostic:', diagnostic, flush=True)
                            raise
                        wanted = str(value).encode()
                        assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                        assert regs['x'] == end-len(wanted) and regs['y'] == 0x7777
                        assert regs['u'] == 0 and regs['a'] == 0 and regs['b'] == 0
                        expected = b'\xa5'*(end-start-len(wanted))+wanted+b'\0'
                        assert d.read(start, end-start+1) == expected, (owner, value)
                        assert (d.read(start-1, 1), d.read(end+1, 1)) == guards
                        assert d.read(0x7ef2, 5) == b'STACK'
                        if private:
                            assert d.read(private+syms['size'], 5) == b'GUARD'
                            if before is not None:
                                expected_private = bytearray(before)
                                expected_private[syms['DivideDivisor']] = 10
                                expected_private[syms['DivideBits']] = 0
                                assert d.read(private, syms['size']) == expected_private
                        calls += 1
                    if private:
                        variables = bytes(range(256))
                        d.write(private+syms['vmvariables'], variables)
                        d.write(private+syms['vmstrings'], b'Z'*39+b'\0')
                        sourceaddr = private+syms['assetinput']
                        output = private+syms['fillstack']+2048
                        cases = [(b'[%v'+str(n).encode()+b']', ('['+str(n)+']').encode(), 0)
                                 for n in range(256)]
                        cases += [(b'%v0/%v9/%v10/%v99/%v100/%v255', b'0/9/10/99/100/255', 0)]
                        # Reach the output limit through bounded string substitution,
                        # then fail inside numeric output while its stack buffer is live.
                        cases += [(b'%s0'*52+b'A'*19+b'%v255', None, syms['E$BMode'])]
                        for source, wanted, error in cases:
                            # assetinput ends immediately before fillstack; its last
                            # byte is also the left guard of the source-frame area.
                            input_bytes = source+b'\0'+b'Q'*(510-len(source))+b'G'
                            d.write(sourceaddr, input_bytes)
                            d.write(private+syms['fillstack']-1, b'G')
                            d.write(private+syms['fillstack']+4096, b'H')
                            d.write(0x7ef0, b'\x7e\x00STACK')
                            d.regs(pc=base+syms['GameFormatMessage'], s=0x7ef0,
                                   x=sourceaddr, u=private, dp=private >> 8, cc=0x50)
                            d.call('c'); regs = d.regs()
                            assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                            assert regs['u'] == private and regs['b'] == error
                            assert bool(regs['cc'] & 1) == bool(error)
                            assert d.read(sourceaddr, 512) == input_bytes
                            assert d.read(private+syms['vmvariables'], 256) == variables
                            assert d.read(private+syms['vmstrings'], 40) == b'Z'*39+b'\0'
                            assert d.read(private+syms['formatdepth'], 1) == b'\0'
                            assert d.read(private+syms['fillstack']-1, 1) == b'G'
                            assert d.read(private+syms['fillstack']+4096, 1) == b'H'
                            assert d.read(0x7ef2, 5) == b'STACK'
                            if wanted is not None:
                                assert regs['x'] == output
                                assert d.read(output, len(wanted)+1) == wanted+b'\0'
                            else:
                                assert d.read(private+syms['parserreadlength'], 2) == (2047).to_bytes(2, 'big')
                                assert d.read(output, 2048) == b'Z'*(52*39)+b'A'*19+b'\0'
                            calls += 1
                    current = bytearray(d.read(base, len(code)))
                    if not private:
                        # The legacy CoCo converter intentionally writes its private
                        # engine conversion buffer; all instruction bytes stay intact.
                        current[syms['NumConvBuf']:syms['NumConvEnd']+1] = code[syms['NumConvBuf']:syms['NumConvEnd']+1]
                    assert current == code
            print(f'PASS: {calls} real decimal converter/formatter calls; all bytes, CoCo wide values through 65535, exact digits/termination, native message preservation, numeric output-limit failure/frame unwinding, two load addresses, state/buffer/stack guards and instruction immutability')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
