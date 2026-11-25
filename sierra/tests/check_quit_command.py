#!/usr/bin/env python3
"""Pair the actual CoCo and Wild Bits quit-command decisions."""
from pathlib import Path
import tempfile
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom, start_cpu


def pop_return(debugger, regs, **updates):
    ret = int.from_bytes(debugger.read(regs['s'], 2), 'big')
    debugger.regs(pc=ret, s=regs['s'] + 2, **updates)


def run_coco(debugger, code, syms, base, operand, response):
    stop, args, stack = 0x7e00, 0x6100, 0x7ef0
    debugger.write(base, code)
    debugger.write(args, bytes([operand]) + b'GUARD')
    debugger.write(stack, stop.to_bytes(2, 'big') + b'STACK')
    debugger.write(0x0009, b'\0')
    debugger.write(0x0022, b'\0\0')
    debugger.regs(pc=base + syms['cmd_quit'], s=stack, y=args, dp=0, cc=0x50)
    prompt = None
    exit_count = 0
    for _ in range(12):
        debugger.call('c')
        regs = debugger.regs()
        if regs['pc'] == stop:
            break
        if regs['pc'] == base + syms['message_box']:
            assert operand != 1, 'immediate CoCo quit displayed a prompt'
            prompt = debugger.read(regs['u'], 128).split(b'\0', 1)[0]
            pop_return(debugger, regs, a=response, cc=(0x54 if response == 0 else 0x50))
        elif regs['pc'] == 0x0701:
            exit_count += 1
            assert debugger.read(0x0009, 1) == b'\x03'
            pop_return(debugger, regs)
        else:
            raise AssertionError(('unexpected CoCo quit boundary', regs))
    else:
        raise AssertionError('CoCo quit command did not return')
    assert regs['pc'] == stop and regs['s'] == stack + 2, regs
    assert debugger.read(args + 1, 5) == b'GUARD'
    assert debugger.read(stack + 2, 5) == b'STACK'
    assert debugger.read(base, len(code)) == code
    return exit_count == 1, prompt


def run_native(debugger, code, syms, base, operand, key):
    stop, private, stack = 0x7e00, 0x1000, 0x7ef0
    debugger.write(base, code)
    debugger.write(private, bytes(syms['size']) + b'GUARD')
    debugger.write(syms['resourcebase'], private.to_bytes(2, 'big'))
    debugger.write(private + syms['vmarguments'], bytes([operand]))
    debugger.write(private + syms['gamequit'], b'\0')
    debugger.write(private + syms['parsercharacter'], b'\0')
    debugger.write(stack, stop.to_bytes(2, 'big') + b'STACK')
    debugger.regs(pc=base + syms['GameQuitCommand'], s=stack,
                  dp=0, u=0, cc=0x50)
    prompt = None
    for _ in range(8):
        debugger.call('c')
        regs = debugger.regs()
        if regs['pc'] == stop:
            break
        if regs['pc'] == base + syms['GamePrintText']:
            assert operand != 1, 'immediate Wild Bits quit displayed a prompt'
            prompt = debugger.read(regs['x'], 128).split(b'\0', 1)[0]
            debugger.write(private + syms['parsercharacter'], bytes([key]))
            pop_return(debugger, regs, cc=regs['cc'] & 0xfe)
        else:
            raise AssertionError(('unexpected Wild Bits quit boundary', regs))
    else:
        raise AssertionError('Wild Bits quit command did not return')
    assert regs['pc'] == stop and regs['s'] == stack + 2, regs
    assert debugger.read(private + syms['size'], 5) == b'GUARD'
    assert debugger.read(stack + 2, 5) == b'STACK'
    assert debugger.read(base, len(code)) == code
    return debugger.read(private + syms['gamequit'], 1) == b'\1', prompt


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-quit-command-') as name:
        tmp = Path(name)
        coco, cs = compile_module(ROOT / 'objs/mnln.asm', tmp / 'mnln')
        native, ns = compile_module(ROOT / 'objs/sierra.asm', tmp / 'wbgame',
                                    defines=('WILDBITS=1',))
        debugger, emulator = start_cpu(idle_rom(tmp / 'idle.rom'), timeout=300)
        try:
            debugger.write(0xffdf, b'\0')
            debugger.write(0xff90, b'\x4c')
            debugger.write(0xff91, b'\x01')
            debugger.write(0xffa8, bytes(range(8)))
            stop = 0x7e00
            debugger.breakpoint(stop)
            debugger.breakpoint(0x0701)
            count = 0
            for coco_base, native_base in ((0x8000, 0x9000), (0x9000, 0xa000)):
                debugger.write(coco_base, coco)
                debugger.write(native_base, native)
                debugger.breakpoint(coco_base + cs['message_box'])
                debugger.breakpoint(native_base + ns['GamePrintText'])
                # Modal positive/negative results correspond to Enter and
                # Escape; argument 1 is the immediate, prompt-free path.
                for operand, response, key, expected in (
                        (0, 1, 13, True), (0, 0, 27, False), (1, 0, 27, True)):
                    coco_quit, coco_prompt = run_coco(
                        debugger, coco, cs, coco_base, operand, response)
                    native_quit, native_prompt = run_native(
                        debugger, native, ns, native_base, operand, key)
                    assert coco_quit == native_quit == expected, (
                        operand, response, key, coco_quit, native_quit)
                    if operand == 0:
                        assert coco_prompt == (
                            b'Press ENTER to quit.\nPress CTRL-BREAK to keep playing.')
                        assert native_prompt == b'Press ENTER to quit.\nESC keeps playing.'
                    else:
                        assert coco_prompt is None and native_prompt is None
                    count += 1
                debugger.breakpoint(coco_base + cs['message_box'], False)
                debugger.breakpoint(native_base + ns['GamePrintText'], False)
            print(f'PASS: {count} paired actual CoCo/Wild Bits quit-command calls; Enter exits, Escape cancels, immediate operand skips prompt, caller stacks/operands/private state and code are guarded; prompt wording remains platform-specific')
        finally:
            debugger.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except Exception:
                emulator.kill()
                emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
