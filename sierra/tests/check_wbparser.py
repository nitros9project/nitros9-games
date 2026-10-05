#!/usr/bin/env python3
"""Execute typed vocabulary/said scenarios with native 6809 instructions."""
from pathlib import Path
import tempfile
import subprocess
from check_wbres import exercise, idle_rom, start_cpu


def dictionary(entries):
    result = bytearray(52)
    previous = ''
    for word, group in sorted(entries):
        prefix = 0
        while prefix < min(len(word), len(previous)) and word[prefix] == previous[prefix]:
            prefix += 1
        suffix = bytearray(ord(c) ^ 127 for c in word[prefix:])
        suffix[-1] |= 128
        result.extend(bytes([prefix]) + suffix + group.to_bytes(2, 'big'))
        previous = word
    return bytes(result)


def main():
    vocab = dictionary([('a', 0), ('look', 2), ('look at', 3), ('tree', 4)])
    # A real index may point beyond padding, and the dictionary ends in zero.
    vocab = (62).to_bytes(2, 'big') + vocab[2:52] + bytes(10) + vocab[52:] + b'\0'
    cases = [(b'LOOK\r', [2], 0), (b'look at tree\r', [3, 4], 0),
             (b'a look\r', [2], 0), (b'  look, at  tree!\r', [3,4], 0), (b'lo-ok\r', [2], 0), (b'loox\x08k\r', [2], 0),
             (b'look tree\r', [1, 4], 0), (b'look tree\r', [9999], 0),
             (b'look unknown\r', [2], 2), (b'unknown\r', [2], 1)]
    with tempfile.TemporaryDirectory(prefix='wbparser-') as tmp:
        d, emulator = start_cpu(idle_rom(Path(tmp) / 'idle.rom'), timeout=900)
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            for keys, ids, unknown in cases:
                # Capture unknown-word index while input flag is live. Repeated
                # identical said predicates may accept the sentence only once.
                script = bytearray([255,7,2,255,3,0,4,222,9])
                # A true OR arm must skip a matching said predicate so the
                # following predicate can still accept the sentence once.
                script.extend([255,252,1,255,0,14,len(ids)])
                for group in ids: script.extend(group.to_bytes(2,'little'))
                script.extend([252,255,0,0])
                for _ in range(2):
                    script.extend([255,14,len(ids)])
                    for group in ids: script.extend(group.to_bytes(2,'little'))
                    script.extend([255,2,0,1,220])
                script.extend([1,250,255,1,250,len(keys)+3,255,2,0,134,1,0])
                logic = len(script).to_bytes(2,'little') + script
                files = {'/game/logDir': b'\xff'*3 + bytes(3),
                    '/game/vol.0': b'\x12\x34\0' + len(logic).to_bytes(2,'little')*2 + logic,
                    '/game/words.tok': vocab}
                error, output, state = exercise(d,files,module='wbgame',base=0xa000,
                    database=0x1000,window=0x8000,blocks=None,multiple=True,
                    firstblock=0x10,capture=True,keyboard=keys)
                assert not error and not output, (keys,error,output)
                assert state['vmvariables'][222] == unknown, (keys,state['vmvariables'][222])
                assert state['vmvariables'][220] == (0 if unknown == 1 else 1), (keys,state['vmvariables'][220])
            for malformed in (bytes(51), bytes.fromhex('0001')+bytes(50),
                              bytes(52)+b'\x01',bytes(52)+b'\x00\xc5\x00',
                              bytes(52)+b'\0'+b'A'*40+b'\x80\0\2'):
                script=bytes([1,250,255,1,250,10,255,2,0,134,1,0])
                logic=len(script).to_bytes(2,'little')+script
                files={'/game/logDir':b'\xff'*3+bytes(3),
                       '/game/vol.0':b'\x12\x34\0'+len(logic).to_bytes(2,'little')*2+logic,
                       '/game/words.tok':malformed}
                error,_=exercise(d,files,module='wbgame',base=0xa000,database=0x1000,
                    window=0x8000,blocks=None,multiple=True,firstblock=0x10,keyboard=b'look\r')
                assert error, ('malformed vocabulary accepted',malformed[:60])
            print('PASS: typed commands, case folding, prefix-compressed phrases, ignored words, backspace, unknown indexes, said wildcards and single acceptance; closed paths and freed slabs')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)

if __name__ == '__main__': main()
