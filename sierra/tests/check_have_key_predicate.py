#!/usr/bin/env python3
"""Compare CoCo and Wild Bits have.key on pending and fresh keyboard input."""
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_wbres import idle_rom, start_cpu
from check_logic_executor import compile_module

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-have-key-') as folder:
        folder = Path(folder)
        image = folder / 'mnln'
        subprocess.run(['lwasm.orig', '--6809', '--format=os9', '--no-warn=ifp1',
                        '--pragma=pcaspcr,nosymbolcase,condundefzero',
                        '-I' + str(ROOT / 'kingsquest1'), '-I' + str(ROOT / 'objs'),
                        '-I' + str(ROOT.parent.parent / 'nitros9/defs'),
                        '--map=' + str(image) + '.map', '-o' + str(image),
                        str(ROOT / 'objs/mnln.asm')], check=True)
        coco, cs = image.read_bytes(), symbols(Path(str(image) + '.map'))
        native, ns = compile_module(ROOT / 'objs/sierra.asm', folder / 'wbgame',
                                    defines=('WILDBITS=1',))
        d, emulator = start_cpu(idle_rom(folder / 'idle.rom'), timeout=900)
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            for base, code, syms_ in ((0x8000, coco, cs), (0xa000, native, ns)):
                d.write(base, code)
                if base == 0x8000:
                    d.write(0x002e, base.to_bytes(2, 'big'))
                    d.run(base + syms_['FixupEvalTbl'])
            private = 0x1000
            d.write(private, bytes(ns['size']) + b'GUARD')
            d.write(private + ns['resourcebase'], private.to_bytes(2, 'big'))
            d.breakpoint(0x7e00)

            def invoke_coco(key=None, sentinel_first=False):
                variables = bytearray(256)
                variables[19] = 0 if key is not None else 0x7e
                d.write(0x0431, variables)
                d.write(0x7ef0, b'\x7e\x00STACK')
                d.regs(pc=0x8000 + cs['TestHaveKey'], s=0x7ef0, x=0x0431,
                       y=0x2000, cc=0x50)
                if key is None:
                    # GetKeyEvent is reached only when v19 is already pending.
                    d.call('c')
                else:
                    # HaveKeyPollLoop calls GetKeyEvent via a local JSR. Replace
                    # only that call opcode with a same-length test callback;
                    # the real predicate's poll/return/store logic still runs.
                    call = cs['HaveKeyPollLoop']
                    original = d.read(0x8000 + call, 3)
                    d.write(0x8000 + call, b'\xbd\x7e\x10')  # JSR test poll stub
                    d.write(0x7e30, b'\0')
                    if sentinel_first:
                        # Return the CoCo no-key sentinel once, then the new
                        # key. The production poll loop must ignore only the
                        # sentinel and continue polling.
                        stub = bytes([0xb6, 0x7e, 0x30, 0x26, 0x06,
                                      0x7c, 0x7e, 0x30, 0x86, 0xff,
                                      0x39, 0x86, key, 0x39])
                    else:
                        stub = bytes([0x86, key, 0x39])
                    d.write(0x7e10, stub)
                    try:
                        d.call('c')
                    finally:
                        d.write(0x8000 + call, original)
                r = d.regs()
                assert r['pc'] == 0x7e00 and r['s'] == 0x7ef2, r
                assert d.read(0x7ef2, 5) == b'STACK'
                expected = 0x7e if key is None else key
                assert r['a'] == int(key is None or key != 0)
                assert d.read(0x0431 + 19, 1) == bytes([expected if key is None or key else 0])

            def invoke_native(key=None):
                variables = bytearray(256)
                variables[19] = 0 if key is not None else 0x7e
                d.write(private + ns['vmvariables'], variables)
                d.write(private + ns['vmopcode'], b'\r')
                d.write(0x7ef0, b'\x7e\x00STACK')
                # Pending key takes the shared, direct predicate return path.
                # A cleared v19 enters the production modal path, covered by
                # the end-to-end integration below.
                if key is not None:
                    d.write(private + ns['vmvariables'] + 19, bytes([key]))
                d.regs(pc=0xa000 + ns['InputHaveKeyTest'], s=0x7ef0,
                       u=private, dp=private >> 8, cc=0x50)
                d.call('c')
                r = d.regs()
                assert r['pc'] == 0x7e00 and r['s'] == 0x7ef2, r
                assert d.read(0x7ef2, 5) == b'STACK'
                assert not r['cc'] & 1 and r['b'] == 1, r

            # Pending nonzero keys must yield boolean true without altering v19.
            for key in (1, 13, 32, 127, 128, 254):
                invoke_coco(None)
                invoke_native(key)
            # Every nonzero byte returned by the actual CoCo polling point is
            # stored verbatim in v19 and yields true.
            for key in (1, 13, 32, 127, 128, 254):
                invoke_coco(key)
            invoke_coco(0)  # CoCo treats a zero event as false, without saving it.
            invoke_coco(ord('x'), sentinel_first=True)
            print('PASS: actual CoCo have.key pending state, fresh-key values, zero-event false and retry after the $FF no-key sentinel; Wild Bits pending-key result; integration suite covers its modal fresh-key wait')
        finally:
            d.s.close(); emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
