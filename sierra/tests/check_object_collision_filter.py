#!/usr/bin/env python3
"""Check shared eligibility through each owner's actual collision routine."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def main():
    cases = [(value,0,0x41,1) for value in range(256)]
    cases += [(0,value,0x41,1) for value in range(256)]
    cases += [(0,0,value,1) for value in range(256)]
    cases += [(0,0,0x41,0),(0,0,0,0),(2,2,0x41,1)]
    with tempfile.TemporaryDirectory(prefix='sierra-collision-') as name:
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
                objects = 0x4000 if not private else private+syms['vmobjects']
                for base in bases:
                    d.write(base,code)
                    if private:
                        d.write(private,bytes(syms['size'])+b'GUARD')
                        d.write(private+syms['motionobject'],objects.to_bytes(2,'big'))
                    else:
                        d.write(0x30,objects.to_bytes(2,'big')+(objects+86).to_bytes(2,'big'))
                    for actor_ignore,candidate_ignore,active,identity in cases:
                        records = bytearray(64*43)
                        for index in (0,1):
                            offset = index*43
                            records[offset+2] = index
                            records[offset+3:offset+5] = bytes([20,80])
                            records[offset+0x1c] = 10
                            records[offset+0x26] = 0x41
                        records[0x25] = actor_ignore
                        records[43+0x25] = candidate_ignore
                        records[43+0x26] = active
                        records[43+2] = identity
                        d.write(objects-1,b'G'+records+b'H')
                        if private: d.write(private+syms['motioncollision'],b'\x55')
                        check_all = private and (actor_ignore in (0,2,255)
                                                  and candidate_ignore in (0,2,255)
                                                  and active in (0,0x41,255))
                        before = d.read(private,syms['size']) if check_all else None
                        d.write(0x7ef0,b'\x7e\x00STACK')
                        d.regs(pc=base+syms['MotionObjectCollision' if private else 'CheckObjCollision'],
                               s=0x7ef0,u=objects,x=private or 0x5555,y=0x7777,
                               dp=private>>8,cc=0x50)
                        d.call('c'); regs = d.regs()
                        collided = not actor_ignore & 2 and not candidate_ignore & 2
                        collided &= active & 0x41 == 0x41
                        if not private: collided &= identity != 0
                        assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                        assert regs['b' if private else 'a'] == int(collided), (owner,actor_ignore,candidate_ignore,active,identity,regs)
                        assert regs['u'] == objects
                        assert d.read(objects-1,len(records)+2) == b'G'+records+b'H'
                        assert d.read(0x7ef2,5) == b'STACK'
                        if private:
                            counter = 0x55 if actor_ignore & 2 else (1 if collided else 64)
                            assert d.read(private+syms['motioncollision'],1) == bytes([counter])
                            assert d.read(private+syms['size'],5) == b'GUARD'
                            if before is not None:
                                expected = bytearray(before); expected[syms['motioncollision']] = counter
                                assert d.read(private,syms['size']) == expected
                        calls += 1
                    assert d.read(base,len(code)) == code
            print(f'PASS: {calls} actual CoCo/native collision calls at two addresses; every '
                  'actor/candidate ignore byte and candidate control byte, active-bit combinations, '
                  'self exclusion, duplicate-ID/pointer policy, record/private-state preservation, '
                  'scan bounds, guards/stack and immutable code')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except Exception: emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
