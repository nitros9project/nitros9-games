#!/usr/bin/env python3
"""Compare CoCo script replay checkpoints with the native resource replay log."""
from pathlib import Path
import subprocess
import tempfile

from check_logic_executor import ROOT, compile_module
from check_wbres import idle_rom, start_cpu


RECORDS_BEFORE = ((0, 17), (1, 23))
RECORD_AFTER_RESTORE = (3, 41)
DISCARDED_RECORD = (2, 31)


def invoke(d, entry, *, dp, u=0, a=0, b=0, y=0):
    d.write(0x7ef0, b'\x7e\x00STACK')
    d.breakpoint(0x7e00)
    d.regs(pc=entry, s=0x7ef0, dp=dp, u=u, a=a, b=b, y=y, cc=0x50)
    d.call('c')
    regs = d.regs()
    assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2, regs
    assert d.read(0x7ef2, 5) == b'STACK'
    d.breakpoint(0x7e00, False)
    return regs


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-replay-diff-') as directory:
        tmp = Path(directory)
        coco, cs = compile_module(ROOT / 'objs/mnln.asm', tmp / 'mnln')
        native, ns = compile_module(ROOT / 'objs/sierra.asm', tmp / 'native',
                                    defines=('WILDBITS=1',))
        d, emulator = start_cpu(idle_rom(tmp / 'idle.rom'), timeout=300)
        try:
            d.write(0xffdf, b'\0')
            d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01')
            d.write(0xffa8, bytes(range(8)))
            result = {}

            for base in (0x8000, 0x9000):
                d.write(base, coco)
                buffer = 0x3000
                d.write(buffer, bytes(12) + b'GUARD')
                d.write(0x05af, buffer.to_bytes(2, 'big'))
                d.write(0x0243, b'\0')
                d.write(0x0244, b'\0')
                d.write(0x0245, b'\x03')
                d.write(0x05b1, b'\x01')
                d.write(0x01ae, b'\0')
                d.write(base + cs['ScriptWritePtr'], buffer.to_bytes(2, 'big'))

                for operation, resource in RECORDS_BEFORE:
                    invoke(d, base + cs['PushScript'], dp=0, a=operation,
                           b=resource)
                invoke(d, base + cs['cmd_push_script'], dp=0)
                assert d.read(0x0243, 1) == b'\x02'

                invoke(d, base + cs['PushScript'], dp=0,
                       a=DISCARDED_RECORD[0], b=DISCARDED_RECORD[1])
                invoke(d, base + cs['cmd_pop_script'], dp=0)
                assert d.read(0x0244, 1) == b'\x02'
                assert int.from_bytes(d.read(base + cs['ScriptWritePtr'], 2),
                                      'big') == buffer + 4

                invoke(d, base + cs['PushScript'], dp=0,
                       a=RECORD_AFTER_RESTORE[0], b=RECORD_AFTER_RESTORE[1])
                coco_bytes = d.read(buffer, 6)
                assert coco_bytes == bytes((0, 17, 1, 23, 3, 41)), coco_bytes
                assert d.read(0x0244, 1) == b'\x03'
                assert d.read(buffer + 12, 5) == b'GUARD'

                # Public script.size shares the replay-limit contract with
                # Wild Bits ReplayInitialize. Pre-own CoCo's buffer so this
                # command comparison does not emulate AllocDataBlock.
                size_code = bytearray(coco)
                start, end = cs['cmd_script_size'], cs['cmd_push_script']
                for target_name in ('ClearBothRanges','SwapObjRanges'):
                    target = cs[target_name]
                    for site in range(start, end-2):
                        displacement = target-(site+3)
                        if (size_code[site] == 0x17
                                and size_code[site+1:site+3] == displacement.to_bytes(2,'big',signed=True)):
                            size_code[site:site+3] = b'\x12\x12\x12'
                d.write(base,size_code)
                initial_buffer=d.read(buffer,12)
                for limit in (0,1,3,255):
                    d.write(0x05af,buffer.to_bytes(2,'big'))
                    d.write(base+cs['ScriptWritePtr'],(buffer+6).to_bytes(2,'big'))
                    d.write(0x0244,b'\x05')
                    d.write(0x2000,bytes((limit,))+b'ARGS')
                    regs=invoke(d,base+cs['cmd_script_size'],dp=0,y=0x2000)
                    assert regs['y']==0x2001 and regs['s']==0x7ef2
                    assert d.read(0x0245,1)==bytes((limit,))
                    assert d.read(0x0244,1)==b'\0'
                    assert int.from_bytes(d.read(base+cs['ScriptWritePtr'],2),'big')==buffer
                    assert d.read(0x2001,4)==b'ARGS'
                    assert d.read(buffer,12)==initial_buffer
                    result[('CoCo size',base,limit)]=bytes((limit,))+b'\0\0'
                expected_size_code=bytearray(size_code)
                expected_size_code[cs['ScriptWritePtr']:cs['ScriptWritePtr']+2]=buffer.to_bytes(2,'big')
                assert d.read(base,len(size_code))==expected_size_code
                # Restore the independent replay scenario that follows.
                d.write(0x0244,b'\x03'); d.write(0x0245,b'\x03')
                d.write(base+cs['ScriptWritePtr'],(buffer+6).to_bytes(2,'big'))

                invoke(d, base + cs['ResetScriptPtrs'], dp=0)
                popped = []
                for _ in range(3):
                    regs = invoke(d, base + cs['PopScript'], dp=0)
                    popped.append(d.read(regs['u'], 2))
                assert popped == [bytes(pair) for pair in
                                  (*RECORDS_BEFORE, RECORD_AFTER_RESTORE)], popped
                result[('CoCo', base)] = coco_bytes

            for base in (0x9000, 0xa000):
                d.write(base, native)
                private = 0x1000
                d.write(private, bytes(ns['size']) + b'GUARD')
                d.write(private + ns['resourcebase'],
                        private.to_bytes(2, 'big'))
                d.write(private + ns['replaybuffer'], bytes(510) + b'GUARD')
                d.write(private + ns['replaylimit'], b'\x03')
                d.write(private + ns['replayused'], b'\0\0')
                d.write(private + ns['replaycheckpoint'], b'\0\0')
                dp = private >> 8

                for operation, resource in RECORDS_BEFORE:
                    invoke(d, base + ns['ReplayPush'], dp=dp, u=private,
                           a=operation, b=resource)
                invoke(d, base + ns['ReplaySaveCheckpoint'], dp=dp, u=private)
                assert d.read(private + ns['replaycheckpoint'], 2) == b'\0\x04'

                invoke(d, base + ns['ReplayPush'], dp=dp, u=private,
                       a=DISCARDED_RECORD[0], b=DISCARDED_RECORD[1])
                invoke(d, base + ns['ReplayRestore'], dp=dp, u=private)
                assert d.read(private + ns['replayused'], 2) == b'\0\x04'

                invoke(d, base + ns['ReplayPush'], dp=dp, u=private,
                       a=RECORD_AFTER_RESTORE[0], b=RECORD_AFTER_RESTORE[1])
                native_bytes = d.read(private + ns['replaybuffer'], 6)
                assert native_bytes == bytes((0, 17, 1, 23, 3, 41)), native_bytes
                assert d.read(private + ns['replayused'], 2) == b'\0\x06'
                assert d.read(private + ns['size'], 5) == b'GUARD'
                assert d.read(private + ns['replaybuffer'] + 510, 5) == b'GUARD'
                result[('Wild Bits', base)] = native_bytes

                replay = bytearray(d.read(private,ns['size']))
                replay[ns['replaybuffer']:ns['replaybuffer']+8]=b'KEEPDATA'
                d.write(private,replay)
                for limit in (0,1,3,255):
                    d.write(private+ns['vmarguments'],bytes((limit,)))
                    d.write(private+ns['replayused'],b'\0\x06')
                    d.write(private+ns['replaycheckpoint'],b'\0\x04')
                    invoke(d,base+ns['ReplayInitialize'],dp=dp,u=private)
                    assert d.read(private+ns['replaylimit'],1)==bytes((limit,))
                    assert d.read(private+ns['replayused'],2)==b'\0\0'
                    assert d.read(private+ns['replaycheckpoint'],2)==b'\0\0'
                    assert d.read(private+ns['replaybuffer'],8)==b'KEEPDATA'
                    result[('Wild Bits size',base,limit)]=bytes((limit,))+b'\0\0'
                assert d.read(private+ns['size'],5)==b'GUARD'

            for base_index in range(2):
                coco_base = (0x8000, 0x9000)[base_index]
                native_base = (0x9000, 0xa000)[base_index]
                assert result[('CoCo', coco_base)] == result[('Wild Bits', native_base)]
                for limit in (0,1,3,255):
                    assert result[('CoCo size',coco_base,limit)] == result[('Wild Bits size',native_base,limit)]
            print('PASS: CoCo PushScript/cmd.push.script/cmd.pop.script and native '
                  'ReplayPush/checkpoint/restore produce the same resource-record '
                  'sequence at two load bases; discarded tail is overwritten, '
                  'record counts, readback, allocation and stack guards match; '
                  'cmd.script.size/ReplayInitialize agree for limits 0/1/3/255')
        finally:
            d.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill()
                emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
