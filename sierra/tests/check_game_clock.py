#!/usr/bin/env python3
"""Run both real clock owners, mocking only native F$Time delivery."""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
EDGES = {0, 1, 23, 24, 59, 60, 127, 128, 254, 255}


def advance(clock, ticks=1):
    clock = list(clock)
    for _ in range(ticks):
        for field, modulus in enumerate((60, 60, 24, 256)):
            clock[field] = (clock[field]+1) & 255
            if clock[field] < modulus: break
            clock[field] = 0
    return bytes(clock)


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-clock-') as name:
        tmp = Path(name)
        coco, cs = compile_module(ROOT/'objs/sierra.asm', tmp/'sierra')
        native, ns = compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame', defines=('WILDBITS=1',))
        vectors = []
        for field in range(4):
            for value in range(256):
                clock = [59, 59, 23, 7]
                clock[field] = value
                vectors.append((bytes(clock), value in EDGES))
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=900)
        calls = 0
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            d.breakpoint(0x7e00)
            for owner, code, syms, bases in [('CoCo', coco, cs, (0x8000, 0x9000)),
                                            ('native', native, ns, (0x9000, 0xa000))]:
                private = 0x1000
                clockaddr = private + (syms['TimeOfDay'] if owner == 'CoCo' else syms['vmvariables']+11)
                for base in bases:
                    d.write(base, code)
                    d.write(private, b'\x91'*syms['size'] + b'GUARD')
                    if owner == 'native':
                        d.write(private+syms['resourcebase'], private.to_bytes(2, 'big'))
                        kernel = base+syms['GameClockTimeCall']
                        d.breakpoint(kernel)
                    for clock, full_guard in vectors:
                        d.write(clockaddr-1, b'G'+clock+b'H')
                        if owner == 'CoCo':
                            timeraddr = private+syms['GameTimerB3']
                            # Carry all the way through the 32-bit timer.
                            d.write(timeraddr, b'\xff'*4)
                            d.write(private+syms['GamePausedFlag'], b'\0')
                            d.write(private+syms['TickAccum'], b'\0\x13')
                            d.write(private+syms['TickCountHi'], b'\x12\xff')
                        else:
                            d.write(private+syms['gameclocklast'], b'\x0c')
                            d.write(private+syms['gameclockreset'], b'\0')
                            d.write(private+syms['gameclockdelta'], b'\0')
                        before = d.read(private, syms['size']) if full_guard else None
                        d.write(0x7ef0, b'\x7e\x00STACK')
                        entry = base+syms['SigHandlerCore' if owner == 'CoCo' else 'GameReadClock']
                        d.regs(pc=entry, s=0x7ef0, u=private, dp=private >> 8, cc=0x50)
                        d.call('c'); regs = d.regs()
                        if owner == 'native':
                            assert regs['pc'] == kernel and regs['x'] == private+syms['gametime']
                            timebuf = bytes([26, 10, 5, 10, 11, 13])
                            d.write(regs['x'], timebuf)
                            d.regs(pc=kernel+3, cc=regs['cc'] & ~1)
                            d.call('c'); regs = d.regs()
                            assert not regs['cc'] & 1 and regs['b'] == 0
                            assert d.read(private+syms['gameclocklast'], 1) == b'\x0d'
                            assert d.read(private+syms['gameclockdelta'], 1) == b'\0'
                            assert d.read(private+syms['gameclockreset'], 1) == b'\0'
                        else:
                            assert d.read(timeraddr, 4) == b'\0'*4
                            assert d.read(private+syms['TickCountHi'], 2) == b'\x13\0'
                            assert d.read(private+syms['TickAccum'], 2) == b'\0\0'
                        wanted = advance(clock)
                        assert d.read(clockaddr-1, 6) == b'G'+wanted+b'H', (owner, clock, wanted)
                        assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2 and regs['u'] == private
                        assert d.read(0x7ef2, 5) == b'STACK'
                        assert d.read(private+syms['size'], 5) == b'GUARD'
                        if full_guard:
                            expected = bytearray(before)
                            offset = clockaddr-private
                            expected[offset:offset+4] = wanted
                            if owner == 'CoCo':
                                expected[syms['GameTimerB3']:syms['GameTimerB3']+4] = b'\0'*4
                                expected[syms['TickCountHi']:syms['TickCountHi']+2] = b'\x13\0'
                                expected[syms['TickAccum']:syms['TickAccum']+2] = b'\0\0'
                            else:
                                expected[syms['gametime']:syms['gametime']+6] = timebuf
                                expected[syms['gameclocklast']] = 13
                            assert d.read(private, syms['size']) == expected, (owner, clock)
                        calls += 1
                    if owner == 'CoCo':
                        for paused, accum in [(1, 19), (0, 0), (0, 18)]:
                            clock = bytes([59, 59, 23, 255])
                            d.write(clockaddr, clock)
                            d.write(private+syms['GamePausedFlag'], bytes([paused]))
                            d.write(private+syms['TickAccum'], accum.to_bytes(2, 'big'))
                            d.write(timeraddr, b'\0'*4)
                            d.write(private+syms['TickCountHi'], b'\0\x01')
                            d.write(0x7ef0, b'\x7e\x00STACK')
                            d.regs(pc=base+syms['SigHandlerCore'], s=0x7ef0, u=private, dp=private >> 8, cc=0x50)
                            d.call('c'); regs = d.regs()
                            assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                            assert d.read(clockaddr, 4) == clock
                            assert d.read(timeraddr, 4) == b'\0\0\0\x01'
                            assert d.read(private+syms['TickCountHi'], 2) == (1 if paused else 2).to_bytes(2, 'big')
                            assert d.read(private+syms['TickAccum'], 2) == (accum if paused else accum+1).to_bytes(2, 'big')
                            calls += 1
                    else:
                        # Minute wrap, multi-second delta, initial sample, modal reset,
                        # unchanged second, invalid OS second, and F$Time failure.
                        for last, now, reset, error in [(59,0,0,0), (58,1,0,0), (10,13,0,0),
                                                       (255,40,0,0), (10,40,1,0), (12,12,0,0),
                                                       (12,60,0,0), (12,13,0,syms['E$NotRdy'])]:
                            clock = bytes([59, 59, 23, 255])
                            d.write(clockaddr, clock)
                            d.write(private+syms['gameclocklast'], bytes([last]))
                            d.write(private+syms['gameclockreset'], bytes([reset]))
                            d.write(private+syms['gameclockdelta'], b'\0')
                            d.write(0x7ef0, b'\x7e\x00STACK')
                            d.regs(pc=base+syms['GameReadClock'], s=0x7ef0, u=private, dp=private >> 8, cc=0x50)
                            d.call('c'); regs = d.regs()
                            assert regs['pc'] == kernel
                            if not error: d.write(regs['x'], bytes([26,10,5,10,11,now]))
                            d.regs(pc=kernel+3, b=error, cc=(regs['cc'] & ~1) | bool(error))
                            d.call('c'); regs = d.regs()
                            rejected = bool(error or now >= 60)
                            ticks = 0 if rejected or reset or last == 255 else (now-last) % 60
                            assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                            assert bool(regs['cc'] & 1) == rejected
                            assert regs['b'] == (error or syms['E$BMode'] if rejected else 0)
                            assert d.read(clockaddr, 4) == advance(clock, ticks)
                            assert d.read(private+syms['gameclocklast'], 1) == bytes([last if rejected else now])
                            assert d.read(private+syms['gameclockreset'], 1) == bytes([reset if rejected else 0])
                            assert d.read(0x7ef2, 5) == b'STACK'
                            calls += 1
                        d.breakpoint(kernel, False)
                    assert d.read(base, len(code)) == code
            print(f'PASS: {calls} real CoCo/native clock calls; every byte in all four fields, sec/min/hour/day rollover and byte wrapping, paused/subsecond CoCo timer and 32-bit carry, native OS time/delta/reset/error policy, two code bases, full-state edge checks, guards/stack and immutable code')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
