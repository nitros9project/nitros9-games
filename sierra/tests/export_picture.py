#!/usr/bin/env python3
"""Render a plain or nibble-packed Sierra picture resource with the existing 6809 renderer.

This host-side reference bridge produces wbpic input. It is not a native
Wild Bits resource decoder. Game assets remain local and are not redistributed.
"""
import argparse
import hashlib
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from check_instances import Debugger, symbols as read_symbols
from check_wbres import idle_rom


def unpack_picture(data):
    """Expand high-first picture nibbles; only F0/F2 have half-byte operands."""
    nibs = iter(n for b in data for n in (b >> 4, b & 15))
    out = bytearray()
    try:
        while True:
            command = next(nibs)*16 + next(nibs)
            out.append(command)
            if command == 255:
                if len(list(nibs)) > 1:
                    raise ValueError('packed picture has trailing bytes')
                return bytes(out)
            if command in (240,242):
                out.append(next(nibs))
    except StopIteration as error:
        raise ValueError('truncated packed picture') from error


def resource(game, number):
    directory = (game / 'picDir').read_bytes()
    if number < 0 or number * 3 + 3 > len(directory):
        raise ValueError('picture number outside picDir')
    entry = directory[number * 3:number * 3 + 3]
    if entry == b'\xff\xff\xff':
        raise ValueError('picture is absent from picDir')
    volume = entry[0] >> 4
    offset = ((entry[0] & 15) << 16) | (entry[1] << 8) | entry[2]
    data = (game / f'vol.{volume}').read_bytes()
    header = data[offset:offset + 7]
    if len(header) != 7 or header[:2] != b'\x12\x34' or header[2] & 15 != volume:
        raise ValueError('invalid Sierra resource header')
    decoded = int.from_bytes(header[3:5], 'little')
    stored = int.from_bytes(header[5:7], 'little')
    payload = data[offset + 7:offset + 7 + stored]
    if len(payload) != stored:
        raise ValueError('truncated picture resource')
    if header[2] & 128:
        payload = unpack_picture(payload)
        if len(payload) != decoded:
            raise ValueError('packed picture expanded length differs from header')
    elif decoded != stored:
        raise ValueError('reference bridge LZW support is pending')
    if not payload or payload[-1] != 255 or len(payload) > 8192:
        raise ValueError('picture does not fit the reference command window or lacks its end marker')
    return payload, volume, offset


class _StartupTimeout(socket.timeout):
    pass


def render(game, payload, assembler, defs):
    # The headless XRoar GDB thread can time out during startup on macOS.
    # Restart a bounded number of times; a persistent failure still fails.
    for attempt in range(4):
        try:
            return _render_once(game, payload, assembler, defs)
        except _StartupTimeout:
            if attempt == 3:
                raise


def _render_once(game, payload, assembler, defs):
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='sierra-picture-reference-') as temporary:
        work = Path(temporary)
        shutil.copyfile(game / 'defsfile', work / 'defsfile')
        module = work / 'shdw'
        listing = work / 'shdw.list'
        mapping = work / 'shdw.map'
        subprocess.run([assembler, '--6809', '--format=os9', '--no-warn=ifp1',
            '--pragma=pcaspcr,nosymbolcase,condundefzero', '-I' + str(work),
            '-I' + str(root / 'objs'), '-I' + str(defs), '--symbols',
            '--list=' + str(listing), '--map=' + str(mapping), '-o' + str(module), str(root / 'objs/shdw.asm')],
            cwd=work, check=True)
        symbols = read_symbols(mapping)
        with socket.socket() as reservation:
            reservation.bind(('127.0.0.1', 0))
            port = reservation.getsockname()[1]
        bootrom = idle_rom(work / 'idle.rom')
        emulator = subprocess.Popen(['xroar', '-machine', 'coco3', '-ui', 'null', '-ao', 'null',
            '-ram', '2048', '-no-ratelimit', '-gdb', '-gdb-port', str(port), '-timeout', '900',
            '-no-bas', '-extbas', bootrom, '-no-altbas'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        debugger = None
        try:
            # Match start_cpu: finish the queued power-on reset before writes.
            time.sleep(.1)
            for attempt in range(50):
                try:
                    try:
                        debugger = Debugger(port)
                    except socket.timeout as error:
                        raise _StartupTimeout(str(error)) from error
                    break
                except ConnectionRefusedError:
                    time.sleep(.01)
            if debugger is None:
                raise RuntimeError('XRoar debugger did not start')
            d = debugger
            d.write(0xFFDF, b'\0')
            d.write(0xFF90, b'\x4c')
            d.write(0xFF91, b'\x01')
            for address in (0xFF92, 0xFF93, 0xFF01, 0xFF03, 0xFF21, 0xFF23):
                d.write(address, b'\0')
            d.write(0xFFA8, bytes(range(8)))
            d.write(0, bytes(0x800))
            d.write(0xE000, module.read_bytes())
            d.write(0x2000, payload)
            d.write(symbols['LoadOffset'], b'\xe0\x00')
            d.write(symbols['GivenPicDataPtr'], b'\x20\x00')
            # RenderPic expects a resource-node pointer on the caller's stack.
            # Its zero block pair matches the zero cache, so no MMU switch is needed.
            d.write(0x1DF2, b'\x03\x00')
            d.run(0xE000 + symbols['RenderPic'])
            return d.read(0x6040, 160 * 168)
        finally:
            if debugger:
                debugger.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=2)
            except subprocess.TimeoutExpired:
                emulator.kill()
                emulator.wait(timeout=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path)
    parser.add_argument('picture', type=int)
    parser.add_argument('output', type=Path)
    parser.add_argument('--assembler', default=shutil.which('lwasm.orig') or shutil.which('lwasm'))
    parser.add_argument('--defs', type=Path, default=Path(__file__).resolve().parents[3] / 'nitros9/defs')
    args = parser.parse_args()
    if not args.assembler:
        parser.error('lwasm must be installed or specified with --assembler')
    try:
        payload, volume, offset = resource(args.game, args.picture)
        output = render(args.game, payload, shutil.which(args.assembler) or str(Path(args.assembler).resolve()), args.defs.resolve())
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + '\n')
    args.output.write_bytes(output)
    print(f'Picture {args.picture}: vol.{volume}@{offset:#x}, {len(payload)} command bytes')
    print(f'{args.output}: {len(output)} combined bytes; SHA256 {hashlib.sha256(output).hexdigest()}')


if __name__ == '__main__':
    main()
