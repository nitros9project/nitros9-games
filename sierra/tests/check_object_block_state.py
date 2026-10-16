#!/usr/bin/env python3
"""Run blocked motion transitions and bulk unanimation in actual owners."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-block-state-') as name:
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
                variable = 0x0437 if not private else private+syms['vmvariables']+6
                for base in bases:
                    d.write(base, code)
                    if private:
                        d.write(private, bytes(syms['size']))
                    for flag in range(256):
                        for stopped, ego in [(False, False), (True, False), (True, True)]:
                            record = bytearray(range(43)); record[0x26] = flag; record[0x21] = 5
                            wanted = bytearray(record)
                            wanted[0x26] = flag | 0x80 if stopped else flag & 0x7f
                            if stopped: wanted[0x21] = 0
                            d.write(0x6fff, b'G'+record+b'H')
                            d.write(variable, b'\x77')
                            if private:
                                d.write(private+syms['motionid'], bytes([0 if ego else 1]))
                                d.write(private+syms['gameblockenabled'], b'\0')
                                entry = 'GameBlockCrossing' if stopped else 'GameCheckBlock'
                            else:
                                d.write(0x30, (0x7000 if ego else 0x702b).to_bytes(2, 'big'))
                                entry = 'MoveIsBlocked' if stopped else 'MoveNoBlock'
                            stack = 0x7ef0 if private else 0x7eed
                            locals_ = b'' if private else b'LOC'
                            d.write(stack, locals_+b'\x7e\x00STACK')
                            d.regs(pc=base+syms[entry], s=stack, u=0x7000,
                                   x=private or 0x7777, y=0x4567, dp=private >> 8, cc=0x50)
                            d.call('c'); regs = d.regs()
                            assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                            assert regs['u'] == 0x7000 and regs['y'] == 0x4567
                            assert regs['x'] == (private or 0x7777)
                            assert d.read(0x6fff, 45) == b'G'+wanted+b'H', (owner, flag, stopped, ego)
                            assert d.read(variable, 1) == (b'\0' if stopped and ego else b'\x77')
                            assert d.read(stack, len(locals_)) == locals_
                            assert d.read(0x7ef2, 5) == b'STACK'
                            if private: assert regs['b'] == int(stopped)
                            calls += 1
                    for count in ([0, 1, 2, 64] if not private else [1, 2, 64]):
                        records = bytearray((i*73+19) & 255 for i in range(count*43))
                        wanted = bytearray(records)
                        for index in range(count): wanted[index*43+0x26] &= 0xbe
                        d.write(0x6fff, b'G'+records+b'H')
                        d.write(0x7ef0, b'\x7e\x00STACK')
                        if private:
                            regs = dict(pc=base+syms['ObjectsUnanimateNext'], x=0x7000, u=private, y=count)
                        else:
                            d.write(0x32, (0x7000+count*43).to_bytes(2, 'big'))
                            regs = dict(pc=base+syms['UnanimateAllLoop'], x=0x4567, u=0x7000, y=0x7777)
                        d.regs(s=0x7ef0, dp=private >> 8, cc=0x50, **regs)
                        d.call('c'); actual = d.regs()
                        assert actual['pc'] == 0x7e00 and actual['s'] == 0x7ef2
                        assert actual['x' if private else 'u'] == 0x7000+count*43
                        assert d.read(0x6fff, len(records)+2) == b'G'+wanted+b'H'
                        assert d.read(0x7ef2, 5) == b'STACK'
                        calls += 1
                    assert d.read(base+syms['StepXDelta'], 18) == bytes([
                        0,0,1,1,1,0,255,255,255, 0,255,255,0,1,1,1,0,255])
                    assert d.read(base, len(code)) == code, (owner, 'modified code')
            print(f'PASS: {calls} real block-state/unanimate calls in both owners at two '
                  'load addresses; every control byte, ego/non-ego direction policy, '
                  'unrelated record preservation, empty/single/64-record bounds, '
                  'all nine direction deltas, guards/stack and immutable code')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except Exception: emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
