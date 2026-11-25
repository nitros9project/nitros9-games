#!/usr/bin/env python3
"""Check force.update's command state and refresh-service contract in both owners."""
from pathlib import Path
import tempfile

from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
OBJECT_BYTES = 64 * 43


def run_hooks(d, entry, stack=0x7ef0, limit=12):
    trace = []
    for _ in range(limit):
        d.call('c')
        regs = d.regs()
        if regs['pc'] == 0x7e00:
            assert regs['s'] == stack + 2 and d.read(stack+2, 5) == b'STACK'
            return regs, trace
        name = entry.get(regs['pc'])
        assert name is not None, ('unexpected force.update service', hex(regs['pc']), regs)
        trace.append(name)
        return_address = int.from_bytes(d.read(regs['s'], 2), 'big')
        d.regs(pc=return_address, s=regs['s']+2, cc=regs['cc'] & ~1, b=0)
        if return_address == 0x7e00:
            regs = d.regs()
            assert regs['s'] == stack+2 and d.read(stack+2,5)==b'STACK'
            return regs, trace
    raise AssertionError(('force.update did not return', trace))


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-force-update-') as name:
        temp = Path(name)
        coco, cs = compile_module(ROOT/'objs/mnln.asm', temp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm', temp/'wbgame',
                                    defines=('WILDBITS=1',))
        d, emulator = start_cpu(idle_rom(temp/'idle.rom'), timeout=900)
        calls = 0
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            d.breakpoint(0x7e00)
            for owner, code, syms, bases in (
                    ('CoCo', coco, cs, (0x8000, 0x9000)),
                    ('native', native, ns, (0x9000, 0xa000))):
                private = 0 if owner == 'CoCo' else 0x1000
                objects = 0x4000 if owner == 'CoCo' else private+syms['vmobjects']
                args = 0x2000 if owner == 'CoCo' else private+syms['vmarguments']
                if private:
                    d.write(private, bytes(syms['size'])+b'GUARD')
                    d.write(private+syms['resourcebase'], private.to_bytes(2, 'big'))
                    d.write(private+syms['gamebackgroundowned'], b'\0')
                else:
                    d.write(0x30, objects.to_bytes(2, 'big'))
                for base in bases:
                    d.write(base, code)
                    if owner == 'CoCo':
                        service_names = ('ClearBothRanges','SwapObjRanges','UpdateObjSegments')
                        entry = {base+syms[item]:item for item in service_names}
                        entry_symbol = 'CmdForceUpdate'
                    else:
                        # AssetUnmap/PictureUnmap are exercised on their
                        # normal unmapped fast paths; intercept only the two
                        # display-service boundaries that require a terminal.
                        service_names = ('GameComposeScene','PresentPicture')
                        entry = {base+syms[item]:item for item in service_names}
                        entry_symbol = 'GameForceUpdate'
                    for address in entry:
                        d.breakpoint(address)
                    for index in (0,1,32,63):
                        records = bytearray((i*47+23)&255 for i in range(OBJECT_BYTES))
                        records[index*43+0x26] = (index*3)&255
                        d.write(objects-1, b'G'+records+b'H')
                        before_private = None
                        if private:
                            d.write(args, bytes((index,))+b'ARGS')
                            d.write(private+syms['vmopcode'], b'<')  # opcode 60
                            before_private = bytearray(d.read(private, syms['size']))
                            dp = private >> 8
                            y = args
                        else:
                            d.write(0x2000, bytes((index,))+b'ARGS')
                            dp = 0
                            y = 0x2000
                        d.write(0x7ef0, b'\x7e\0STACK')
                        d.regs(pc=base+syms[entry_symbol],s=0x7ef0,y=y,u=private,
                               dp=dp,cc=0x50)
                        regs, trace = run_hooks(d, entry)
                        if owner == 'CoCo':
                            assert regs['y'] == y+1 and trace == list(service_names), trace
                        else:
                            assert not regs['cc']&1 and regs['b']==0
                            assert trace == list(service_names), trace
                            after_private = bytearray(d.read(private, syms['size']))
                            # The routine consumes the object index through
                            # ObjectAddress; no game/object state may advance.
                            before_private[syms['vmopcode']] = ord('<')
                            assert after_private == before_private, (index, trace)
                            assert d.read(args, 5) == bytes((index,))+b'ARGS'
                            assert d.read(private+syms['size'],5)==b'GUARD'
                        assert d.read(objects-1,OBJECT_BYTES+2)==b'G'+records+b'H'
                        assert d.read(y+1,4)==b'ARGS'
                        calls += 1
                    for address in entry:
                        d.breakpoint(address,False)
                    assert d.read(base,len(code))==code
            print(f'PASS: {calls} actual CoCo/native force.update calls at two load addresses; all four object-index regions, object/private/argument/stack guards, CoCo range-refresh service order, native unmap/recompose/present service order; no motion or object-state advance')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except Exception: emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
