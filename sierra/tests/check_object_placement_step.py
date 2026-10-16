#!/usr/bin/env python3
"""Check the shared spiral against its model and the original CoCo routine."""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_instances import symbols
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
DELTAS = [(-1,0), (0,1), (1,0), (0,-1)]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-spiral-') as name:
        tmp = Path(name)
        # The frozen pre-extraction CoCo step is a standalone test fixture,
        # so this check also works from source archives and shallow checkouts.
        baseline = tmp/'baseline.bin'
        subprocess.run(['lwasm.orig','--6809','--format=raw',
                        '--map='+str(baseline)+'.map','-o'+str(baseline),
                        str(ROOT/'tests/probes/coco-placement-step.asm')],check=True)
        old = baseline.read_bytes(); os = symbols(Path(str(baseline)+'.map'))
        coco, cs = compile_module(ROOT/'objs/mnln.asm', tmp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame', defines=('WILDBITS=1',))
        old_start = os['FindObjPosIter']; old_end = os['FindObjPosDone']
        fragment = old[old_start:old_end]
        assert len(fragment) < 0x500
        old_entry = 0x7800+os['FindObjPosDirNone']-old_start
        cases = [(direction, coordinate, coordinate, 7, 2)
                 for direction in range(4) for coordinate in range(256)]
        cases += [(direction, 0 if direction & 1 else 255,
                   255 if direction & 1 else 0, length, 1)
                  for direction in range(4) for length in range(256)]
        cases += [(direction, 123, 123, 7, remaining)
                  for direction in range(4) for remaining in range(256)]
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=900)
        calls = 0
        try:
            d.write(0xffdf,b'\0'); d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01'); d.write(0xffa8,bytes(range(8)))
            d.write(0x7800, fragment); d.breakpoint(0x7800); d.breakpoint(0x7e00)
            for owner, code, syms, bases in [('CoCo',coco,cs,(0x8000,0x9000)),
                                            ('native',native,ns,(0x9000,0xa000))]:
                private = 0 if owner == 'CoCo' else 0x1000
                for base in bases:
                    d.write(base,code)
                    if private:
                        d.write(private,bytes(syms['size'])+b'GUARD')
                        d.write(private+syms['resourcebase'],private.to_bytes(2,'big'))
                        d.write(private+syms['motionobject'],b'\x70\x00')
                    candidate = base+syms['RepositionCandidate' if private else 'FindObjPosIter']
                    d.breakpoint(candidate)
                    for direction, x, y, length, remaining in cases:
                        record = bytearray(range(43)); record[3:5] = bytes([x,y])
                        record[0x1a:0x1c] = bytes([81,91])
                        frame = bytearray([direction,length,remaining,0x66,0x55] if private else
                                          [0x70,0,length,direction,remaining])
                        wanted = bytearray(record); wf = bytearray(frame)
                        dx,dy = DELTAS[direction]
                        wanted[3:5] = bytes([(x+dx)&255,(y+dy)&255])
                        count = (remaining-1)&255
                        nd,nl = direction,length
                        exhausted = False
                        if not count:
                            nd = (direction+1)&3
                            if not nd & 1: nl = (length+1)&255
                            exhausted = bool(private and not nl)
                            count = 0 if exhausted else nl
                        if private: wf[:3] = bytes([nd,nl,count])
                        else: wf[2:5] = bytes([nl,nd,count])
                        if exhausted: wanted[3:5] = record[0x1a:0x1c]
                        entries = [(base+syms['SpiralStep'], candidate)]
                        if not private: entries.insert(0,(old_entry,0x7800))
                        results = []
                        for entry, stop in entries:
                            d.write(0x6fff,b'G'+record+b'H')
                            d.write(0x7ee8,b'G!!'+frame+b'\x7e\x00STACK')
                            d.regs(pc=entry,s=0x7eeb,u=0x7000,x=private or 0x4321,
                                   y=0x4567,dp=private>>8,cc=0x50)
                            d.call('c'); regs = d.regs()
                            assert regs['pc'] == (0x7e00 if exhausted else stop), (owner,direction,length,remaining,regs)
                            assert regs['s'] == (0x7ef2 if exhausted else 0x7eeb)
                            actual_record = d.read(0x6fff,45)
                            actual_frame = d.read(0x7eeb,5)
                            assert actual_record == b'G'+wanted+b'H', (owner,direction,x,y,length,remaining)
                            assert actual_frame == wf, (owner,direction,length,remaining,actual_frame,wf)
                            assert regs['u'] == 0x7000 and regs['y'] == 0x4567
                            assert d.read(0x7ee8,1) == b'G' and d.read(0x7ef2,5) == b'STACK'
                            if exhausted: assert regs['cc'] & 1 and regs['b'] == syms['E$BMode']
                            results.append((actual_record,actual_frame))
                            calls += 1
                        if not private: assert results[0] == results[1]
                    if private:
                        # The widened budget-exhaustion branch must still
                        # restore the saved coordinates and release its frame.
                        record = bytearray(range(43)); record[3:5] = bytes([70,70])
                        record[0x1a:0x1c] = bytes([81,91])
                        d.write(0x6fff,b'G'+record+b'H')
                        d.write(0x7ee8,b'G!!'+bytes([0,1,1,0,1])+b'\x7e\x00STACK')
                        d.regs(pc=base+syms['RepositionReject'],s=0x7eeb,u=0x7000,
                               x=private,y=0x4567,dp=private>>8,cc=0x50)
                        d.call('c'); regs = d.regs()
                        assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                        assert regs['cc'] & 1 and regs['b'] == syms['E$BMode']
                        record[3:5] = bytes([81,91])
                        assert d.read(0x6fff,45) == b'G'+record+b'H'
                        assert d.read(0x7eeb,5) == bytes([0,1,1,0,0])
                        assert d.read(0x7ee8,1) == b'G' and d.read(0x7ef2,5) == b'STACK'
                        calls += 1
                    assert d.read(base,len(code)) == code
                    assert d.read(0x7800,len(fragment)) == fragment
                    if private: assert d.read(private+syms['size'],5) == b'GUARD'
            print(f'PASS: {calls} shared/baseline placement steps at two load addresses; '
                  'all four directions and byte coordinates/run lengths/counts, original CoCo '
                  'differential results, zero-count wrapping, native run/budget exhaustion and position restore, '
                  'frame/record guards, stack/cursors and immutable code')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except Exception: emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
