#!/usr/bin/env python3
"""GDB remote helper adapted from coco-shelf Sierra CPU tests."""
import argparse
from pathlib import Path
import re
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
SHELF = ROOT.parent


def symbols(path):
    return {m[1]: int(m[2], 16) for m in re.finditer(
        r'^Symbol: (\S+) .* = ([0-9A-F]+)$', path.read_text(), re.M)}


class Debugger:
    def __init__(self, port):
        self.s = socket.create_connection(('127.0.0.1', port), 5)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.s.settimeout(15)
        try:
            self.call('?')
        except (OSError, ConnectionError):
            self.s.close()
            raise

    def call(self, command):
        data = command.encode()
        packet = b'$' + data + b'#' + f'{sum(data) % 256:02x}'.encode()
        for attempt in range(100):
            self.s.sendall(packet)
            result = self.receive()
            if result is not None:
                return result
            time.sleep(0.01)
        raise RuntimeError('debugger repeatedly rejected the packet')

    def receive(self):
        while True:
            c = self.s.recv(1)
            if c == b'$':
                break
            if c == b'-':
                return None
            if not c:
                raise ConnectionError('debugger disconnected')
        data = b''
        while (c := self.s.recv(1)) != b'#':
            data += c
        self.s.recv(2)
        self.s.sendall(b'+')
        return data.decode()

    def write(self, address, data):
        for start in range(0, len(data), 200):
            part = data[start:start + 200]
            assert self.call(f'M{address + start:x},{len(part):x}:{part.hex()}') == 'OK'

    def read(self, address, size):
        return b''.join(bytes.fromhex(self.call(f'm{address + n:x},{min(200, size-n):x}'))
                        for n in range(0, size, 200))

    def regs(self, **updates):
        raw = bytes.fromhex(self.call('g'))
        names = [('cc', 1), ('a', 1), ('b', 1), ('dp', 1), ('x', 2),
                 ('y', 2), ('u', 2), ('s', 2), ('pc', 2)]
        result = {}
        offset = 0
        for name, length in names:
            result[name] = int.from_bytes(raw[offset:offset+length], 'big')
            offset += length
        if updates:
            result.update(updates)
            encoded = b''.join(result[name].to_bytes(length, 'big') for name, length in names)
            assert self.call('G' + encoded.hex()) == 'OK'
        return result

    def breakpoint(self, address, enabled=True):
        assert self.call(f'{"Z" if enabled else "z"}0,{address:x},1') == 'OK'

    def run(self, entry, calls=None, **regs):
        # Return to a debugger breakpoint instead of an OS-9 caller.
        self.write(0x1DF0, bytes.fromhex('1d00'))
        self.breakpoint(0x1D00)
        self.regs(cc=0x50, dp=0, s=0x1DF0, pc=entry, **regs)
        count = 0
        # Continuing at a breakpoint skips that instruction in XRoar. Mock
        # an OS call at the routine's very first instruction before resuming.
        if calls and entry in calls:
            state = self.regs()
            service = self.read(entry + 2, 1)[0]
            updates = calls[entry](service, state)
            self.regs(**dict(updates, pc=entry + 3))
        while True:
            reply = self.call('c')
            state = self.regs()
            if state['pc'] == 0x1D00:
                assert state['s'] == 0x1DF2, state
                return state
            assert calls and state['pc'] in calls, (reply, state)
            count += 1
            assert count < 30, state
            service = self.read(state['pc'] + 2, 1)[0]
            updates = calls[state['pc']](service, state)
            updates['pc'] = state['pc'] + 3
            self.regs(**updates)
