#!/usr/bin/env python3
"""Exercise shared room-entry placement in both production engine owners."""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-room-entry-') as directory:
        tmp = Path(directory)
        owners = [
            ('CoCo', *compile_module(ROOT/'objs/mnln.asm', tmp/'mnln')),
            ('Wild Bits', *compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame', defines=('WILDBITS=1',))),
        ]
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=900)
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            for owner, code, syms in owners:
                for base in (0x8000, 0x9000):
                    d.write(base, code)
                    private = 0x1000
                    record = 0x7000 if owner == 'CoCo' else private + syms['vmobjects']
                    variables = 0x0431 if owner == 'CoCo' else private + syms['vmvariables']
                    stop = base + syms['RoomEntryFinished']
                    d.breakpoint(stop)
                    cases = [(side, 20, x, y) for side in range(256)
                             for x, y in ((0, 0), (159, 167), (255, 255))]
                    cases += [(4, width, 73, 99) for width in range(256)]
                    for side, width, x, y in cases:
                        before = bytearray((i*37+11)&255 for i in range(43))
                        before[3:5] = bytes([x, y]); before[0x1c] = width
                        wanted = bytearray(before)
                        if side == 1: wanted[4] = 167
                        elif side == 2: wanted[3] = 0
                        elif side == 3: wanted[4] = 37
                        elif side == 4: wanted[3] = (160-width)&255
                        d.write(record-1, b'G'+before+b'H')
                        state = bytearray((i*19+7)&255 for i in range(256))
                        state[2] = side; d.write(variables, state); state[2] = 0
                        u = record if owner == 'CoCo' else private
                        d.regs(pc=base+syms['RoomEntryStart'], s=0x7ef0,
                               u=u, x=variables, y=0x7654, b=0x93, dp=0, cc=0x50)
                        d.call('c'); result = d.regs()
                        assert result['pc'] == stop, (owner, result)
                        assert d.read(record-1, 45) == b'G'+wanted+b'H', (owner, side, width)
                        assert d.read(variables, 256) == state, (owner, side, width)
                        for reg, value in [('s',0x7ef0),('u',u),('x',variables),('y',0x7654),('b',0x93)]:
                            assert result[reg] == value, (owner, reg, result)
                    d.breakpoint(stop, False)
                    # Room publication retains the old room before writing
                    # the request, independently of owner resource teardown.
                    stop = base+syms['RoomVariablesDone']; d.breakpoint(stop)
                    room_cases={(value,255-value) for value in range(256)}
                    edges=(0,1,127,128,254,255)
                    room_cases |= {(old,new) for old in edges for new in edges}
                    for old,new in sorted(room_cases):
                        before=bytearray((i*19+7)&255 for i in range(256))
                        before[0]=old; wanted=bytearray(before); wanted[0]=new; wanted[1]=old
                        d.write(variables-1,b'G'+before+b'H')
                        d.write(0x7ef0,bytes([new])+b'STACK')
                        u=0x7000 if owner=='CoCo' else private
                        x=0x3456 if owner=='CoCo' else variables
                        if owner!='CoCo':d.write(private+syms['vmnewroom'],bytes([new]))
                        d.regs(pc=base+syms['RoomVariablesBegin'],s=0x7ef0,u=u,x=x,y=0x7654,
                               dp=0 if owner=='CoCo' else private>>8,cc=0x50)
                        d.call('c'); result=d.regs()
                        assert result['pc']==stop and result['a']==old and result['b']==new,(owner,old,new,result)
                        assert d.read(variables-1,258)==b'G'+wanted+b'H'
                        assert d.read(0x7ef0,6)==bytes([new])+b'STACK'
                        for reg,value in [('s',0x7ef0),('u',u),('x',x),('y',0x7654)]:
                            assert result[reg]==value,(owner,reg,result)
                        if owner!='CoCo':assert d.read(private+syms['vmnewroom'],1)==bytes([new])
                    d.breakpoint(stop,False)
                    assert d.read(base, len(code)) == code, owner
            print('PASS: both production owners at two code bases; all 256 entry values, all byte widths, coordinate extremes, old/new room bytes and request preservation, neighboring state/record guards, preserved registers and immutable code')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
