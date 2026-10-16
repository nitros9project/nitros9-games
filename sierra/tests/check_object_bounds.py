#!/usr/bin/env python3
"""Exercise actual shared placement geometry in both production owners."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def main():
    cases = []
    for field in range(6):
        for value in range(256):
            case = [10,100,20,20,48,0]
            if field == 5: case[4] = 100  # Force ignore-horizon to matter.
            case[field] = value
            cases.append(tuple(case))
    cases += [(x,100,w,20,48,0) for x in (0,1,15,159,160,161,255)
              for w in (0,1,15,159,160,161,255)]
    cases += [(10,y,20,h,0,8) for y in (0,1,47,48,49,166,167,168,254,255)
              for h in (0,1,2,48,49,168,169,255)]
    cases += [(10,y,20,1,horizon,flags) for horizon in (0,47,48,49,167,168,255)
              for y in (0,1,47,48,49,166,167,168,254,255) for flags in (0,8,255)]
    with tempfile.TemporaryDirectory(prefix='sierra-bounds-') as name:
        tmp = Path(name)
        coco, cs = compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm',tmp/'wbgame',defines=('WILDBITS=1',))
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'),timeout=900)
        calls = 0
        try:
            d.write(0xffdf,b'\0'); d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01'); d.write(0xffa8,bytes(range(8)))
            d.breakpoint(0x7e00)
            for owner,code,syms,bases in [('CoCo',coco,cs,(0x8000,0x9000)),
                                         ('native',native,ns,(0x9000,0xa000))]:
                private = 0 if owner == 'CoCo' else 0x1000
                for base in bases:
                    d.write(base,code)
                    if private:
                        expected_private = bytearray(syms['size'])
                        expected_private[syms['resourcebase']:syms['resourcebase']+2] = b'\x10\x00'
                        expected_private[syms['motionobject']:syms['motionobject']+2] = b'\x70\x00'
                        d.write(private,expected_private+b'GUARD')
                        success = base+syms['RepositionBounds']; failure = base+syms['RepositionReject']
                        d.breakpoint(success); d.breakpoint(failure)
                    for x,y,width,height,horizon,flags in cases:
                        record = bytearray(range(43))
                        record[3:5] = bytes([x,y]); record[0x1c:0x1e] = bytes([width,height])
                        record[0x26] = flags
                        d.write(0x6fff,b'G'+record+b'H')
                        d.write(private+syms['vmhorizon'] if private else 0x1d6,bytes([horizon]))
                        d.write(0x7ef0,b'\x7e\x00STACK')
                        d.regs(pc=base+syms['RepositionCandidate' if private else 'CheckObjBounds'],
                               s=0x7ef0,u=0x7000,x=private or 0x4567,y=0x7777,
                               dp=private>>8,cc=0x50)
                        d.call('c'); regs = d.regs()
                        accepted = (not private or width != 0) and x+width <= 160 and y <= 167
                        accepted &= y+1 >= height and (y > horizon or bool(flags & 8))
                        if private:
                            assert regs['pc'] == (success if accepted else failure), (owner,(x,y,width,height,horizon,flags),regs)
                            assert regs['s'] == 0x7ef0
                        else:
                            assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                            assert regs['a'] == int(accepted), (owner,(x,y,width,height,horizon,flags),regs)
                        assert regs['u'] == 0x7000 and regs['y'] == 0x7777
                        assert regs['x'] == (private or 0x4567)
                        assert d.read(0x6fff,45) == b'G'+record+b'H'
                        assert d.read(0x7ef2,5) == b'STACK'
                        calls += 1
                    if private:
                        expected_private[syms['vmhorizon']] = cases[-1][4]
                        assert d.read(private,syms['size']) == expected_private
                        assert d.read(private+syms['size'],5) == b'GUARD'
                        d.breakpoint(success,False); d.breakpoint(failure,False)
                    assert d.read(base,len(code)) == code
            print(f'PASS: {calls} real CoCo/native bounds checks at two addresses; every '
                  'coordinate/size/horizon/control byte, right-edge overflow and screen/height '
                  'boundaries, zero-width policy, ignore-horizon flags, unchanged records/private '
                  'state, guards/stack/registers and immutable code')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except Exception: emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
