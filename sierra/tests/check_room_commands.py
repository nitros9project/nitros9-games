#!/usr/bin/env python3
"""Compare public new.room command operands and transition timing contracts."""
from pathlib import Path
import subprocess
import tempfile
import re

from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]


def invoke(d, entry, *, dp=0, u=0, y=0, stop=0x7e00):
    stack = 0x7ef0
    d.write(stack, stop.to_bytes(2, 'big') + b'STACK')
    d.breakpoint(stop)
    d.regs(pc=entry, s=stack, dp=dp, u=u, y=y, cc=0x50)
    d.call('c')
    regs = d.regs()
    assert regs['pc'] == stop and regs['s'] == stack + 2, regs
    assert d.read(stack + 2, 5) == b'STACK'
    d.breakpoint(stop, False)
    return regs


def room_reset_state(data):
    """Expected bytes from the shared OBJECT_ROOM_RESET contract."""
    result = bytearray(data)
    for offset in range(0, len(result), 43):
        record = result[offset:offset + 43]
        record[0x26] = (record[0x26] & 0xbe) | 0x10
        record[0x25] = 0
        record[0x10:0x12] = b'\0\0'
        record[6:8] = b'\0\0'
        record[0x16:0x18] = b'\0\0'
        record[0x1e:0x21] = b'\1\1\1'
        record[1] = 1
        record[0] = 1
        result[offset:offset + 43] = record
    return bytes(result)


def patch_success(code, symbols, labels, counter):
    """Replace external transition services with a counted successful RTS."""
    image = bytearray(code)
    for index, label in enumerate(labels):
        address = counter + index
        stub = bytes((0x7c, address >> 8, address & 255,
                      0x1c, 0xfe, 0x39))
        image[symbols[label]:symbols[label] + len(stub)] = stub
    return bytes(image)


def check_native_room_yield(d, native, ns):
    """A room request must stop nested and root scripts at its boundary."""
    base, private, stop = 0x9000, 0x1000, 0x7e00
    starts = (0x7000, 0x7100)
    scripts = (bytes((22, 1, 3, 249, 0x66, 0)),
               bytes((18, 0x3a, 3, 250, 0x55, 0)))
    d.write(base, native)
    d.write(private, bytes(ns['size']) + b'GUARD')
    d.write(private + ns['resourcebase'], private.to_bytes(2, 'big'))
    d.write(private + ns['vmvariables'], bytes(256))
    d.write(private + ns['vmflags'], bytes(256))
    d.write(private + ns['vmarguments'], bytes(255))
    d.write(private + ns['vmip'], (2).to_bytes(2, 'big'))
    d.write(private + ns['vmend'], (len(scripts[0]) + 2).to_bytes(2, 'big'))
    d.write(private + ns['vmsteps'], b'\xff\xff')
    d.write(private + ns['vmcurrent'], b'\0')
    d.write(private + ns['vmdepth'], b'\0')
    d.write(private + ns['assetfirst'], b'\0\x30')
    d.write(private + ns['assetblocks'], b'\1')
    d.write(private + ns['resourcekind'], b'\0')
    d.write(private + ns['assetmapped'], b'\0')
    d.write(private + ns['asseterror'], b'\0')
    d.write(private + ns['vmroompending'], b'\0')
    d.write(private + ns['vmnewroom'], b'\0')
    by_first = {}
    for index, (start, script) in enumerate(zip(starts, scripts)):
        payload = len(script).to_bytes(2, 'little') + script
        first = 0x30 + index
        slot = private + ns['vmcache'] + index * 12
        record = (bytes((index, 1)) + first.to_bytes(2, 'big') +
                  bytes((1, 0)) + len(payload).to_bytes(2, 'little') * 2 +
                  b'\0\2')
        assert len(record) == 12
        d.write(slot, record)
        d.write(start, payload + b'GUARD')
        by_first[first] = start
    cache_before = d.read(private + ns['vmcache'], 32 * 12)
    d.write(0x7ef0, stop.to_bytes(2, 'big') + b'STACK')
    d.breakpoint(stop)
    pointer = base + ns['AssetPointer']
    d.breakpoint(pointer)
    try:
        d.regs(pc=base + ns['ExecuteLogic'], s=0x7ef0,
               dp=private >> 8, u=private, cc=0x50)
        for _ in range(64):
            d.call('c')
            regs = d.regs()
            if regs['pc'] == stop:
                break
            assert regs['pc'] == pointer, ('unexpected native service', regs)
            first = int.from_bytes(d.read(private + ns['assetfirst'], 2), 'big')
            assert first in by_first, (first, regs)
            logical = (regs['a'] << 8) | regs['b']
            ret = int.from_bytes(d.read(regs['s'], 2), 'big')
            d.regs(pc=ret, s=regs['s'] + 2, u=by_first[first] + logical,
                   cc=regs['cc'] & ~1)
        else:
            raise AssertionError('nested new.room fixture did not return')
        assert regs['pc'] == stop and regs['s'] == 0x7ef2, regs
        assert d.read(private + ns['vmroompending'], 1) == b'\1'
        assert d.read(private + ns['vmnewroom'], 1) == b'\x3a'
        assert d.read(private + ns['vmip'], 2) == (4).to_bytes(2, 'big')
        assert d.read(private + ns['vmcurrent'], 1) == b'\0'
        assert d.read(private + ns['vmdepth'], 1) == b'\0'
        assert d.read(private + ns['assetfirst'], 2) == b'\0\x30'
        assert d.read(private + ns['vmcache'], len(cache_before)) == cache_before
        assert d.read(private + ns['vmvariables'] + 249, 2) == b'\0\0'
        assert d.read(private + ns['vmvariables'] + 250, 1) == b'\0'
        assert d.read(0x7ef2, 5) == b'STACK'
        for start, script in zip(starts, scripts):
            assert d.read(start + 2 + len(script), 5) == b'GUARD', (
                'script overrun', hex(start),
                d.read(start + 2 + len(script), 5))
        assert d.read(private + ns['size'], 5) == b'GUARD'
        assert d.read(base, len(native)) == native
    finally:
        d.breakpoint(stop, False)
        d.breakpoint(pointer, False)
    print('PASS: native new.room stops its child script, unwinds to root, restores caller state and skips commands in both scripts')


def check_native_room_destination(d, native, ns, room=0x3a):
    """Apply a room change, then execute its cached destination logic via root."""
    base, private, stop = 0x9000, 0x1000, 0x7e00
    root_start, room_start = 0x7000, 0x7100
    if room == 0:
        root_script = bytes((3, 249, 0x77, 3, 250, 0x66, 0))
        room_script = b''
    else:
        root_script = bytes((22, room, 3, 250, 0x66, 0))
        room_script = bytes((3, 249, 0x77, 0))
    root_payload = len(root_script).to_bytes(2, 'little') + root_script
    room_payload = len(room_script).to_bytes(2, 'little') + room_script
    d.write(base, native)
    d.write(private, bytes(ns['size']) + b'GUARD')
    d.write(private + ns['resourcebase'], private.to_bytes(2, 'big'))
    d.write(private + ns['vmvariables'], bytes(256))
    d.write(private + ns['vmflags'], bytes(256))
    d.write(private + ns['vmobjects'], bytes(64 * 43) + b'GUARD')
    d.write(private + ns['vmcache'], bytes(32 * 12))
    root_slot = (bytes((0, 1)) + b'\0\x30' + bytes((1, 0)) +
                 len(root_payload).to_bytes(2, 'big') * 2 + b'\0\2')
    old_room_slot = (bytes((0x37, 1)) + b'\x20\0' + bytes((1, 0)) +
                     b'\0\x08\0\x08\0\x02')
    assert len(root_slot) == len(old_room_slot) == 12
    d.write(private + ns['vmcache'], root_slot + old_room_slot + bytes(30 * 12))
    d.write(private + ns['vmcurrent'], b'\0')
    d.write(private + ns['vmdepth'], b'\0')
    d.write(private + ns['vmip'], b'\0\2')
    d.write(private + ns['vmend'], len(root_payload).to_bytes(2, 'big'))
    d.write(private + ns['vmsteps'], b'\xff\xff')
    d.write(private + ns['vmroompending'], b'\1')
    d.write(private + ns['vmnewroom'], bytes((room,)))
    d.write(private + ns['vmroomchanges'], b'\0')
    d.write(private + ns['gamequit'], b'\0')
    d.write(private + ns['assetfirst'], b'\0\x30')
    d.write(private + ns['assetblocks'], b'\1')
    d.write(private + ns['resourcekind'], b'\0')
    d.write(private + ns['resourcelength'], len(root_payload).to_bytes(2, 'big'))
    d.write(private + ns['resourcestored'], len(root_payload).to_bytes(2, 'big'))
    d.write(private + ns['assetmapped'], b'\0')
    d.write(private + ns['asseterror'], b'\0')
    d.write(root_start, root_payload + b'GUARD')
    d.write(room_start, room_payload + b'GUARD')
    by_first = {0x30: root_start, 0x31: room_start}
    services = ('AssetRelease', 'PictureUnmap', 'GameSoundStop',
                'GameCancelLine', 'VmLoadLogic', 'GameNextCycle', 'AssetPointer')
    for service in services:
        d.breakpoint(base + ns[service])
    d.breakpoint(stop)
    counts = {name: 0 for name in services}

    def run(entry):
        d.write(0x7ef0, stop.to_bytes(2, 'big') + b'STACK')
        d.regs(pc=base + ns[entry], s=0x7ef0,
               dp=private >> 8, u=private, cc=0x50)
        for _ in range(512):
            d.call('c')
            regs = d.regs()
            if regs['pc'] == stop:
                return regs
            service = next((name for name in services
                            if regs['pc'] == base + ns[name]), None)
            assert service is not None, ('unexpected destination service', entry, regs)
            counts[service] += 1
            if service == 'AssetPointer':
                first = int.from_bytes(d.read(private + ns['assetfirst'], 2), 'big')
                assert first in by_first, (
                    first, entry, regs,
                    d.read(private + ns['assetfirst'], 2),
                    d.read(private + ns['vmcache'], 24), counts.copy(),
                    d.read(private + ns['gamequit'], 1))
                logical = (regs['a'] << 8) | regs['b']
                ret = int.from_bytes(d.read(regs['s'], 2), 'big')
                d.regs(pc=ret, s=regs['s'] + 2,
                       u=by_first[first] + logical, cc=regs['cc'] & ~1)
                continue
            if service == 'VmLoadLogic':
                if room == 0:
                    # Room zero is the root resource already resident in slot 0.
                    d.breakpoint(base + ns[service], False)
                    continue
                if counts[service] > 1:
                    # The room-entry service below publishes the fixture as
                    # though it were freshly read. Let the subsequent public
                    # call execute the real cache-hit lookup.
                    d.breakpoint(base + ns[service], False)
                    continue
                slot = private + ns['vmcache'] + 12
                entry_bytes = (bytes((room, 1)) + b'\0\x31' + bytes((1, 0)) +
                               len(room_payload).to_bytes(2, 'big') * 2 + b'\0\2')
                d.write(slot, entry_bytes)
                d.write(private + ns['vmcacheindex'], b'\1')
            if service == 'GameNextCycle':
                d.write(private + ns['gamequit'], b'\1')
            ret = int.from_bytes(d.read(regs['s'], 2), 'big')
            return_regs = {'pc': ret, 's': regs['s'] + 2, 'u': private,
                           'cc': regs['cc'] & ~1}
            if service == 'VmLoadLogic':
                return_regs['x'] = slot
            d.regs(**return_regs)
        raise AssertionError((entry, 'room transition did not return'))

    try:
        regs = run('ApplyRoomChange')
        assert regs['s'] == 0x7ef2 and d.read(0x7ef2, 5) == b'STACK', regs
        assert d.read(private + ns['vmroompending'], 1) == b'\0'
        assert d.read(private + ns['assetfirst'], 2) == b'\0\x30'
        if room != 0:
            assert d.read(private + ns['vmcache'] + 12, 12) == bytes((room, 1, 0, 0x31, 1, 0)) + len(room_payload).to_bytes(2, 'big') * 2 + b'\0\2'
        assert d.read(private + ns['vmip'], 2) == b'\0\2'
        regs = run('VmRunRoot')
        assert regs['s'] == 0x7ef2 and d.read(0x7ef2, 5) == b'STACK', regs
        assert d.read(private + ns['vmvariables'] + 249, 2) == b'\x77\x66'
        assert d.read(private + ns['vmcurrent'], 1) == b'\0'
        assert d.read(private + ns['vmdepth'], 1) == b'\0'
        # The gamequit flag is observed at VmRunRoot before the completed
        # script can execute again; the process is exiting, so root IP has
        # already been reset for that non-resuming path.
        assert d.read(private + ns['vmip'], 2) == (2).to_bytes(2, 'big')
        assert d.read(private + ns['gamequit'], 1) == b'\1'
        assert counts == {'AssetRelease': 1, 'PictureUnmap': 1,
                          'GameSoundStop': 1, 'GameCancelLine': 1,
                          'VmLoadLogic': 1 if room == 0 else 2,
                          'GameNextCycle': 1,
                          'AssetPointer': 7 if room == 0 else 12}, counts
        assert d.read(root_start + 2 + len(root_script), 5) == b'GUARD'
        assert d.read(room_start + 2 + len(room_script), 5) == b'GUARD'
        assert d.read(private + ns['size'], 5) == b'GUARD'
        assert d.read(base, len(native)) == native
    finally:
        for service in services:
            d.breakpoint(base + ns[service], False)
        d.breakpoint(stop, False)
    print('PASS: room apply executes destination/root logic and completes its cycle', room)
    return d.read(private + ns['vmvariables'] + 249, 2)


def check_native_room_load_failure(d, native, ns):
    """A failed destination load must propagate through the real root owner."""
    base, private, stop = 0x9000, 0x1000, 0x7e00
    services = ('AssetUnmap', 'AssetRelease', 'PictureUnmap',
                'GameSoundStop', 'GameCancelLine')
    image = patch_success(native, ns, services, 0x7000)
    d.write(base, image)
    d.write(0x7000, bytes(len(services)))
    d.write(private, bytes(ns['size']) + b'GUARD')
    d.write(private + ns['resourcebase'], private.to_bytes(2, 'big'))
    d.write(private + ns['vmvariables'], bytes(256))
    d.write(private + ns['vmflags'], bytes(256))
    d.write(private + ns['vmobjects'], bytes(64 * 43) + b'GUARD')
    root_slot = bytes((0, 1, 0, 0x30, 1, 0, 0, 8, 0, 8, 0, 2))
    old_room_slot = bytes((0x37, 1, 0x20, 0, 1, 0, 0, 8, 0, 8, 0, 2))
    d.write(private + ns['vmcache'], root_slot + old_room_slot + bytes(30 * 12))
    d.write(private + ns['vmcacheindex'], b'\1')
    d.write(private + ns['vmcurrent'], b'\0')
    d.write(private + ns['vmdepth'], b'\0')
    root_logic = b'\x03\0\x12\x3a\0'  # room 58, followed by no-op
    root_address = 0x7100
    d.write(root_address, root_logic + b'GUARD')
    d.write(private + ns['vmip'], b'\0\2')
    d.write(private + ns['vmend'], len(root_logic).to_bytes(2, 'big'))
    d.write(private + ns['vmsteps'], b'\xff\xff')
    d.write(private + ns['vmroompending'], b'\0')
    d.write(private + ns['vmnewroom'], b'\0')
    d.write(private + ns['vmroomchanges'], b'\0')
    d.write(private + ns['assetfirst'], b'\0\x30')
    d.write(private + ns['assetblocks'], b'\1')
    d.write(private + ns['resourcekind'], b'\0')
    d.write(private + ns['resourcelength'], b'\0\x08')
    d.write(private + ns['resourcestored'], b'\0\x08')
    d.write(private + ns['assetmapped'], b'\0')
    d.write(private + ns['asseterror'], b'\0')
    load = base + ns['VmLoadLogic']
    pointer = base + ns['AssetPointer']
    ui_entry = base + ns['GameUiCommand']
    d.breakpoint(load)
    d.breakpoint(pointer)
    d.breakpoint(ui_entry)
    d.breakpoint(stop)
    d.write(0x7ef0, stop.to_bytes(2, 'big') + b'STACK')
    d.regs(pc=base + ns['VmRunRoot'], s=0x7ef0,
           dp=private >> 8, u=private, cc=0x50)
    try:
        for _ in range(64):
            d.call('c')
            regs = d.regs()
            if regs['pc'] == stop:
                break
            if regs['pc'] == pointer:
                logical = (regs['a'] << 8) | regs['b']
                assert logical < len(root_logic), ('root logic read bound', regs)
                ret = int.from_bytes(d.read(regs['s'], 2), 'big')
                d.regs(pc=ret, s=regs['s'] + 2,
                       u=root_address + logical, cc=regs['cc'] & ~1)
                continue
            if regs['pc'] == load:
                ret = int.from_bytes(d.read(regs['s'], 2), 'big')
                d.regs(pc=ret, s=regs['s'] + 2, b=ns['E$PNNF'],
                       cc=regs['cc'] | 1)
                continue
            if regs['pc'] == ui_entry:
                assert d.read(private + ns['vmopcode'], 1) == b'\xb8'
                ret = int.from_bytes(d.read(regs['s'], 2), 'big')
                d.regs(pc=ret, s=regs['s'] + 2, b=ns['E$PNNF'],
                       cc=regs['cc'] | 1)
                continue
            raise AssertionError(('unexpected root room-error path', regs))
        else:
            raise AssertionError('root VM did not propagate destination load failure')
        assert regs['pc'] == stop and regs['s'] == 0x7ef2, regs
        assert regs['cc'] & 1 and regs['b'] == ns['E$PNNF'], regs
        assert d.read(0x7ef2, 5) == b'STACK'
        assert d.read(private + ns['vmcache'], 12) == root_slot
        assert d.read(private + ns['vmcache'] + 13, 1) == b'\0', (regs, d.read(private + ns['vmcache'], 24), calls)
        assert d.read(private + ns['vmroompending'], 1) == b'\1'
        assert d.read(private + ns['vmnewroom'], 1) == b'\x3a'
        assert d.read(private + ns['size'], 5) == b'GUARD'
        counts = d.read(0x7000, len(services))
        assert counts == bytes((2, 1, 1, 1, 1)), ('failure cleanup calls', counts)
        assert d.read(root_address + len(root_logic), 5) == b'GUARD'
        assert d.read(base, len(image)) == image
    finally:
        d.breakpoint(load, False)
        d.breakpoint(pointer, False)
        d.breakpoint(ui_entry, False)
        d.breakpoint(stop, False)
    print('PASS: actual root VM dispatches new.room; failed destination load releases old cache, preserves E$PNNF through the UI retry boundary and VmNativeReturn, retains request and guards state/stack/code')


def check_coco_missing_logic_path(d, coco, cs):
    """Run CoCo's real missing-logic lookup and observe its error/quit path."""
    base, directory, stop, stack = 0x8000, 0x5000, 0x7e00, 0x7ef0
    room = 0x3a
    d.write(base, coco)
    d.write(directory, b'\xff' * (room * 3 + 3))
    d.write(base + cs['LogDirPtr'], directory.to_bytes(2, 'big'))
    d.write(base + cs['LogDirPage'], b'\0\0')
    code_baseline = d.read(base, len(coco))
    d.write(0x0009, b'\0')
    d.write(0x0022, b'\0\0')
    d.write(stack, stop.to_bytes(2, 'big') + b'STACK')
    labels = ('SetLogicPage', 'ResNotFoundErr', 'PrintFmtStr', 'message_box')
    for label in labels:
        d.breakpoint(base + cs[label])
    d.breakpoint(0x0701)
    d.breakpoint(stop)
    seen = []
    displayed_message = None
    try:
        d.regs(pc=base + cs['FetchLogic'], s=stack, dp=0, u=0,
               b=room, cc=0x50)
        for _ in range(32):
            d.call('c')
            regs = d.regs()
            if regs['pc'] == stop:
                break
            if regs['pc'] == 0x0701:
                assert d.read(0x0009, 1) == b'\x03', (
                    'CoCo did not request quit after a missing logic', regs)
                seen.append('quit')
            else:
                label = next((item for item in labels
                              if regs['pc'] == base + cs[item]), None)
                assert label is not None, ('unexpected missing-logic path', regs)
                if label == 'ResNotFoundErr':
                    assert regs['b'] == room
                    assert regs['x'] == base + cs['StrLogics']
                    seen.append('not-found')
                    d.call('s')
                    continue
                elif label == 'PrintFmtStr':
                    assert d.read(base + cs['StrResNotFound'], 24).startswith(
                        b'%s #%d not found.')
                    seen.append('formatted-error')
                    d.breakpoint(base + cs[label], False)
                    continue
                elif label == 'message_box':
                    message = d.read(regs['u'], 128).split(b'\0', 1)[0]
                    assert message == f'Logics #{room} not found.'.encode(), message
                    displayed_message = message
                    seen.append('message-box')
            ret = int.from_bytes(d.read(regs['s'], 2), 'big')
            d.regs(pc=ret, s=regs['s'] + 2, cc=regs['cc'] & ~1)
        else:
            raise AssertionError(('CoCo missing-logic path did not return', seen))
        assert seen == ['not-found', 'formatted-error', 'message-box', 'quit'], seen
        assert regs['s'] == stack + 2 and d.read(stack + 2, 5) == b'STACK'
        for start, end in ((cs['FetchLogic'], cs['FetchView']),
                           (cs['ResNotFoundErr'], cs['SoundScratchBuf'])):
            assert d.read(base + start, end - start) == \
                code_baseline[start:end], ('CoCo error-path code changed', start, end)
    finally:
        for label in labels:
            d.breakpoint(base + cs[label], False)
        d.breakpoint(0x0701, False)
        d.breakpoint(stop, False)
    print('PASS: missing CoCo room logic formats "Logics #58 not found.", passes it to message_box, requests quit through the MMU handler, and preserves caller stack/code')
    return displayed_message


def check_coco_room_volume_io_errors(d, coco, cs):
    """Exercise both real CoCo ErrorDialog choices after volume I/O errors."""
    base, descriptor, stop, stack = 0x8000, 0x5000, 0x7e00, 0x7ef0
    service_sites = {}
    for service, first, last in (
            ('I$Seek', 'SeekFile', 'SeekFileRet'),
            ('I$Read', 'ReadFile', 'ReadFileRet')):
        needle = bytes((0x10, 0x3f, cs[service]))
        for offset in range(cs[first], cs[last]):
            if coco[offset:offset + 3] == needle:
                service_sites[offset] = service
    assert sorted(service_sites.values()) == ['I$Read', 'I$Seek', 'I$Seek'], service_sites

    for failed_service in ('I$Seek', 'I$Read'):
        for choice in ('enter', 'ctrl-break'):
            print('Checking CoCo room volume I/O:', failed_service, choice, flush=True)
            d.write(base, coco)
            d.write(0x004f, b'\x05\x31')  # existing volume handle table
            d.write(0x0531, b'\x03')       # volume zero is open as path 3
            d.write(descriptor, b'\0\0\0')
            d.write(0x009f, b'\0')
            d.write(0x0009, b'\0')
            d.write(stack, stop.to_bytes(2, 'big') + b'STACK')
            d.breakpoint(stop)
            d.breakpoint(base + cs['ErrorDialog'])
            d.breakpoint(0x0701)
            for offset in service_sites:
                d.breakpoint(base + offset)
            calls = []
            try:
                d.regs(pc=base + cs['FindVol'], s=stack, dp=0,
                       u=descriptor, x=0, y=0x6100, cc=0x50)
                for _ in range(32):
                    d.call('c')
                    regs = d.regs()
                    if regs['pc'] == stop:
                        break
                    if regs['pc'] == 0x0701:
                        # ErrorDialog's zero return selects its real quit path.
                        # Stop at the MMU exit boundary before the nonreturning OS
                        # transfer, with its request and original caller intact.
                        assert choice == 'ctrl-break', (failed_service, choice, regs)
                        assert d.read(0x0009, 1) == b'\x03', (failed_service, regs)
                        calls.append('quit')
                        break
                    if regs['pc'] == base + cs['ErrorDialog']:
                        # BooleanPoll returns one for ENTER/try-again and zero for
                        # CTRL-BREAK. Return through the actual FindVol branch.
                        calls.append('error-dialog-' + choice)
                        ret = int.from_bytes(d.read(regs['s'], 2), 'big')
                        result = 1 if choice == 'enter' else 0
                        flags = (regs['cc'] & ~0x05) | (0x04 if result == 0 else 0)
                        d.regs(pc=ret, s=regs['s'] + 2, a=result, cc=flags)
                        continue
                    service = service_sites.get(regs['pc'] - base)
                    if service:
                        calls.append(service)
                        if service == failed_service:
                            d.regs(pc=regs['pc'] + 3, b=cs['E$EOF'],
                                   cc=regs['cc'] | 1)
                        else:
                            d.regs(pc=regs['pc'] + 3,
                                   cc=regs['cc'] & ~1)
                        continue
                    if regs['pc'] == base + cs['OsErrorHandler']:
                        # Run the actual handler; it stores the OS error byte and
                        # returns the original carry state to SeekFile/ReadFile.
                        d.call('s')
                        continue
                    raise AssertionError(('unexpected CoCo volume I/O path',
                                          failed_service, regs, calls))
                else:
                    raise AssertionError(('CoCo FindVol did not return',
                                          failed_service, calls))
                expected_calls = ([failed_service, 'error-dialog-' + choice]
                                  if failed_service == 'I$Seek' else
                                  ['I$Seek', failed_service,
                                   'error-dialog-' + choice])
                if choice == 'ctrl-break':
                    expected_calls.append('quit')
                assert calls == expected_calls, (
                    failed_service, calls, regs, d.read(0x009f, 1),
                    d.read(0x0009, 1))
                if choice == 'enter':
                    assert regs['pc'] == stop and regs['s'] == stack + 2, regs
                    assert regs['u'] == 0, ('failed volume resource was returned', regs)
                    assert d.read(0x0009, 1) == b'\0'
                else:
                    assert regs['pc'] == 0x0701, regs
                    assert d.read(stack, 7) == stop.to_bytes(2, 'big') + b'STACK'
                    assert regs['s'] < stack, ('exit path lost its active frame', regs)
                assert d.read(0x009f, 1) == bytes((cs['E$EOF'],))
                assert d.read(0x0531, 1) == b'\x03'
                assert d.read(stack + 2, 5) == b'STACK'
                current = d.read(base, len(coco))
                expected_code = bytearray(coco)
                expected_code[cs['VolFileIdx']] = 3
                assert current == expected_code, [
                    (i, expected_code[i], current[i]) for i in range(len(coco))
                    if current[i] != expected_code[i]][:16]

            finally:
                d.breakpoint(stop, False)
                d.breakpoint(base + cs['ErrorDialog'], False)
                d.breakpoint(0x0701, False)
                for offset in service_sites:
                    d.breakpoint(base + offset, False)
    print('PASS: actual CoCo FindVol/SeekFile/ReadFile preserve E$EOF; Enter returns null to the caller and CTRL-BREAK requests the MMU exit path')


def check_coco_open_volume_retry(d, coco, cs):
    """Verify OpenVolFile retries after the real Enter/try-again branch."""
    base, descriptor, stop, stack = 0x8000, 0x5000, 0x7e00, 0x7ef0
    service_sites = {}
    for service, first, last in (
            ('I$Seek', 'SeekFile', 'SeekFileRet'),
            ('I$Read', 'ReadFile', 'ReadFileRet')):
        needle = bytes((0x10, 0x3f, cs[service]))
        for offset in range(cs[first], cs[last]):
            if coco[offset:offset + 3] == needle:
                service_sites[offset] = service
    assert sorted(service_sites.values()) == ['I$Read', 'I$Seek', 'I$Seek']

    d.write(base, coco)
    d.write(0x004f, b'\x05\x31')
    d.write(0x0531, b'\x03')
    d.write(descriptor, b'\0\0\0')
    d.write(base + cs['VolWrongDisk'], b'\0')
    d.write(0x009f, b'\0')
    d.write(0x0009, b'\0')
    d.write(stack, stop.to_bytes(2, 'big') + b'STACK')
    d.breakpoint(stop)
    findvol = base + cs['FindVol']
    d.breakpoint(findvol)
    d.breakpoint(base + cs['ErrorDialog'])
    d.breakpoint(base + cs['SetLogicPage'])
    for offset in service_sites:
        d.breakpoint(base + offset)

    attempts = dialogs = reloads = 0
    reads = 0
    failed = False
    try:
        d.regs(pc=base + cs['OpenVolFile'], s=stack, dp=0,
               u=descriptor, x=0, y=0x6100, cc=0x50)
        for _ in range(64):
            d.call('c')
            regs = d.regs()
            if regs['pc'] == stop:
                break
            if regs['pc'] == findvol:
                attempts += 1
                if attempts == 1:
                    # Run the real first FindVol attempt.
                    d.breakpoint(findvol, False)
                    continue
                assert attempts == 2, attempts
                # Let OpenVolFile's second attempt execute real FindVol,
                # SeekFile, ReadFile and resource-header handling.
                d.breakpoint(findvol, False)
                continue
            if regs['pc'] == base + cs['ErrorDialog']:
                dialogs += 1
                assert dialogs == 1, 'more than one failed volume attempt'
                ret = int.from_bytes(d.read(regs['s'], 2), 'big')
                # Real message_box returns one for Enter/try again.
                d.regs(pc=ret, s=regs['s'] + 2, a=1,
                       cc=regs['cc'] & ~0x05)
                continue
            if regs['pc'] == base + cs['SetLogicPage']:
                reloads += 1
                ret = int.from_bytes(d.read(regs['s'], 2), 'big')
                d.regs(pc=ret, s=regs['s'] + 2,
                       cc=regs['cc'] & ~1)
                d.breakpoint(findvol)
                continue
            service = service_sites.get(regs['pc'] - base)
            if service:
                if service == 'I$Seek' and not failed:
                    failed = True
                    d.regs(pc=regs['pc'] + 3, b=cs['E$EOF'],
                           cc=regs['cc'] | 1)
                elif service == 'I$Read':
                    reads += 1
                    if reads == 1:
                        assert regs['y'] == 7, ('volume header read', regs)
                        d.write(regs['x'], b'\x12\x34\0\x08\0\x08\0')
                    elif reads == 2:
                        assert regs['y'] == 8, ('volume resource read', regs)
                        d.write(regs['x'], b'KQ4DATA!')
                    else:
                        raise AssertionError(('unexpected second-attempt read', reads, regs))
                    d.regs(pc=regs['pc'] + 3, cc=regs['cc'] & ~1)
                else:
                    d.regs(pc=regs['pc'] + 3,
                           cc=regs['cc'] & ~1)
                continue
            if regs['pc'] == base + cs['OsErrorHandler']:
                d.call('s')
                continue
            raise AssertionError(('unexpected OpenVolFile retry path', regs,
                                  attempts, dialogs, reloads))
        else:
            raise AssertionError(('OpenVolFile retry did not return',
                                  attempts, dialogs, reloads))
        assert regs['pc'] == stop and regs['s'] == stack + 2, regs
        assert regs['u'] != 0, ('retry did not return the second resource buffer', regs)
        assert (attempts, dialogs, reloads) == (2, 1, 2), (
            attempts, dialogs, reloads)
        assert reads == 2, ('second attempt did not read header and resource data', reads)
        assert d.read(regs['u'], 8) == b'KQ4DATA!'
        assert d.read(0x009f, 1) == b'\0'
        assert d.read(0x0531, 1) == b'\x03'
        assert d.read(stack + 2, 5) == b'STACK'
        expected_code = bytearray(coco)
        expected_code[cs['VolFileIdx']] = 3
        assert d.read(base, len(coco)) == expected_code
    finally:
        d.breakpoint(stop, False)
        d.breakpoint(findvol, False)
        d.breakpoint(base + cs['ErrorDialog'], False)
        d.breakpoint(base + cs['SetLogicPage'], False)
        for offset in service_sites:
            d.breakpoint(base + offset, False)
    print('PASS: actual CoCo OpenVolFile retries after Enter, reloads logic-page state, reads a second volume header and payload, and returns that resource to its caller')


def check_native_missing_room_resource(d, native, ns, listing, fail_service=None,
                                       fail_volume_service=None,
                                       retry_after_error=False):
    """Run ApplyRoomChange through the native loader against a missing entry or injected I/O failure."""
    base, private, directory, stop = 0x9000, 0x1000, 0x5000, 0x7e00
    room = 58
    services = ('PictureUnmap', 'GameSoundStop', 'GameCancelLine')
    image = bytearray(patch_success(native, ns, services, 0x7000))
    if retry_after_error:
        # Keep the resource loader real while mapping its private asset writes
        # into a harmless test buffer.
        image[ns['AssetPointer']:ns['AssetPointer'] + 4] = b'\xce\x30\x00\x39'
    image = bytes(image)
    d.write(base, image)
    d.write(0x7000, bytes(len(services)))
    d.write(private, bytes(ns['size']) + b'GUARD')
    d.write(private + ns['resourcebase'], private.to_bytes(2, 'big'))
    d.write(private + ns['argdirectory'], directory.to_bytes(2, 'big'))
    d.write(directory, b'/game\r')
    d.write(private + ns['vmvariables'], bytes(256))
    d.write(private + ns['vmflags'], bytes(256))
    d.write(private + ns['vmobjects'], bytes(64 * 43) + b'GUARD')
    root_slot = bytes((0, 1, 0, 0x30, 1, 0, 0, 8, 0, 8, 0, 2))
    old_room_slot = bytes((0x37, 1, 0x20, 0, 1, 0, 0, 8, 0, 8, 0, 2))
    d.write(private + ns['vmcache'], root_slot + old_room_slot + bytes(30 * 12))
    d.write(private + ns['vmcacheindex'], b'\1')
    d.write(private + ns['vmcurrent'], b'\0')
    d.write(private + ns['vmdepth'], b'\0')
    d.write(private + ns['vmip'], b'\0\2')
    d.write(private + ns['vmend'], b'\0\x08')
    d.write(private + ns['vmsteps'], b'\xff\xff')
    d.write(private + ns['vmroompending'], b'\1')
    d.write(private + ns['vmnewroom'], bytes((room,)))
    d.write(private + ns['vmopcode'], b'\x12')
    d.write(private + ns['vmroomchanges'], b'\0')
    d.write(private + ns['assetfirst'], b'\0\x30')
    d.write(private + ns['assetblocks'], b'\1')
    d.write(private + ns['resourcekind'], b'\0')
    d.write(private + ns['resourcelength'], b'\0\x08')
    d.write(private + ns['resourcestored'], b'\0\x08')
    d.write(private + ns['assetmapped'], b'\0')
    d.write(private + ns['asseterror'], b'\0')

    # Only OS-9 file calls are simulated. Directory lookup, LoadAsset,
    # VmLoadLogic, transition cleanup and their error returns are production
    # instructions in the assembled wbgame image.
    os_sites = {base + int(match.group(1), 16): int(match.group(2), 16)
                for match in re.finditer(r'^([0-9A-F]{4}) 103F([0-9A-F]{2}).*os9',
                                         listing, re.M)}
    d.write(0x7ef0, stop.to_bytes(2, 'big') + b'STACK')
    d.breakpoint(stop)
    for address in os_sites:
        d.breakpoint(address)
    paths = {}
    path_names = {}
    file_data = bytearray(b'\xff' * (room * 3 + 3))
    if fail_service == 'close' or fail_volume_service is not None:
        # A valid directory entry makes ResourceLocate close the directory
        # before it can advance to the volume path. Fail that close once so
        # ResourceFailed exercises its retry/cleanup path.
        file_data[room * 3:room * 3 + 3] = b'\0\0\0'
    volume_data = b'\x12\x34\0\x08\0\x08\0' + b'\0' * 8
    file_reads = 0
    calls = {'open': 0, 'seek': 0, 'read': 0, 'close': 0, 'release': 0}
    ui_events = []
    retry_error_injected = False
    retry_context = None
    retry_return = 0x7ed0
    ui_entry = base + ns['GameUiCommand']
    d.breakpoint(ui_entry)
    if retry_after_error:
        d.breakpoint(retry_return)
    try:
        d.regs(pc=base + ns['ApplyRoomChange'], s=0x7ef0,
               dp=private >> 8, u=private, cc=0x50)
        for _ in range(256):
            d.call('c')
            regs = d.regs()
            if regs['pc'] == stop:
                break
            if retry_context and regs['pc'] == retry_return:
                assert not regs['cc'] & 1, ('second volume read failed', regs)
                ret, stack = retry_context
                d.regs(pc=ret, s=stack + 2, b=0,
                       cc=regs['cc'] & ~1)
                retry_context = None
                continue
            if regs['pc'] == ui_entry:
                event = d.read(private + ns['vmopcode'], 1)[0]
                assert event in (0xb7, 0xb8), event
                ui_events.append(event)
                ret = int.from_bytes(d.read(regs['s'], 2), 'big')
                if event == 0xb8 and retry_after_error:
                    # Choose Enter, then execute the actual resource loader
                    # again under the same OS-9 file-service hooks.
                    stack = regs['s']
                    d.write(stack - 2, retry_return.to_bytes(2, 'big'))
                    retry_context = (ret, stack)
                    d.regs(pc=base + ns['VmLoadResource'], s=stack - 2,
                           a=0, b=room, u=private, cc=regs['cc'] & ~1)
                elif event == 0xb8 and (fail_service or fail_volume_service):
                    # Stand in for the room-error UI selecting Escape. The
                    # loader and room transition remain production code.
                    d.write(private + ns['gamequit'], b'\1')
                    d.write(private + ns['vmroompending'], b'\0')
                    d.regs(pc=ret, s=regs['s'] + 2, b=0,
                           cc=regs['cc'] & ~1)
                elif event == 0xb8:
                    # Missing logic has already displayed its message from
                    # ResourceLocate; the room-error callback returns PNNF.
                    d.regs(pc=ret, s=regs['s'] + 2, b=ns['E$PNNF'],
                           cc=regs['cc'] | 1)
                else:
                    # ResourceLocate's existing missing-logic message.
                    d.regs(pc=ret, s=regs['s'] + 2,
                           cc=regs['cc'] & ~1)
                continue
            service = os_sites.get(regs['pc'])
            assert service is not None, ('unexpected native missing-resource path', regs)
            updates = {'pc': regs['pc'] + 3, 'cc': regs['cc'] & ~1}
            if service == ns['I$Open']:
                path = d.read(regs['x'], 160).split(b'\r', 1)[0]
                calls['open'] += 1
                if path == b'/game/logDir':
                    handle, data = 3, bytes(file_data)
                elif path == b'/game/vol.0':
                    handle, data = 4, volume_data
                else:
                    raise AssertionError(('unexpected resource path', path))
                paths[handle] = [data, 0]
                path_names[handle] = path
                updates['a'] = handle
            elif service == ns['I$Seek']:
                handle = regs['a']
                assert handle in paths, (handle, paths)
                offset = (regs['x'] << 16) | regs['u']
                expected_offset = room * 3 if handle == 3 else 0
                assert offset == expected_offset, (path_names[handle], offset)
                calls['seek'] += 1
                failed = ((fail_service == 'seek' and handle == 3) or
                          (fail_volume_service == 'seek' and handle == 4 and
                           (not retry_after_error or not retry_error_injected)))
                if failed:
                    updates.update(cc=regs['cc'] | 1, b=211)  # E$EOF
                    if fail_volume_service and retry_after_error:
                        retry_error_injected = True
                else:
                    paths[handle][1] = offset
            elif service == ns['I$Read']:
                handle = regs['a']
                assert handle in paths, (handle, paths)
                data, offset = paths[handle]
                calls['read'] += 1
                failed = ((fail_service == 'read' and handle == 3) or
                          (fail_service == 'partial-read' and handle == 3 and
                           calls['read'] == 2) or
                          (fail_volume_service == 'read' and handle == 4 and
                           (not retry_after_error or not retry_error_injected)))
                if failed:
                    updates.update(cc=regs['cc'] | 1, b=211)  # E$EOF
                    if fail_volume_service and retry_after_error:
                        retry_error_injected = True
                else:
                    limit = 1 if fail_service == 'partial-read' else regs['y']
                    chunk = data[offset:offset + min(regs['y'], limit)]
                    d.write(regs['x'], chunk)
                    paths[handle][1] += len(chunk)
                    updates['y'] = len(chunk)
            elif service == ns['I$Close']:
                handle = regs['a']
                assert handle in paths, (handle, paths)
                calls['close'] += 1
                failed = (fail_service == 'close' and handle == 3 and
                          calls['close'] == 1)
                if failed:
                    updates.update(cc=regs['cc'] | 1, b=211)  # E$EOF
                else:
                    del paths[handle]
                    del path_names[handle]
            elif service == ns['I$SetStt']:
                assert regs['a'] == 0, regs
                if regs['b'] == 0xd4:
                    # AssetAllocate receives a test block number; actual
                    # decompression and cache publication still run natively.
                    updates['x'] = 0x0100
                elif regs['b'] == 0xd5:
                    calls['release'] += 1
                else:
                    raise AssertionError(('unexpected asset SS.SetStt', regs))
            elif service == ns['I$GetStt']:
                assert regs['a'] == 0, regs
                # SS.Opt reads the zeroed assetinput options in this fixture.
            else:
                raise AssertionError(('unexpected OS-9 service', service, regs))
            d.regs(**updates)
        else:
            raise AssertionError('native missing-room resource path did not return')

        assert paths == {}, ('leaked missing-resource path', paths)
        if fail_service is None and fail_volume_service is None:
            assert calls == {'open': 1, 'seek': 1, 'read': 1, 'close': 1,
                             'release': 1}, calls
        elif retry_after_error:
            assert retry_error_injected and ui_events == [0xb8], (
                retry_error_injected, ui_events)
            assert calls['open'] >= 4 and calls['seek'] >= 4
            assert calls['read'] >= 3 and calls['close'] >= 3, calls
        else:
            assert regs['b'] == 0 and not regs['cc'] & 1, (fail_service, fail_volume_service, regs)
            assert ui_events == [0xb8], (fail_service, fail_volume_service, ui_events)
            assert calls['close'] >= 1 and not paths, (fail_service, fail_volume_service, calls, paths)
        assert regs['s'] == 0x7ef2 and d.read(0x7ef2, 5) == b'STACK', regs
        expected_error = ns['E$PNNF'] if fail_service is None and fail_volume_service is None else 211
        if retry_after_error:
            assert not regs['cc'] & 1 and regs['b'] == 0, regs
            assert d.read(private + ns['gamequit'], 1) == b'\0'
            assert d.read(private + ns['vmroompending'], 1) == b'\0'
        elif fail_service or fail_volume_service:
            assert not regs['cc'] & 1 and regs['b'] == 0, regs
            assert d.read(private + ns['gamequit'], 1) == b'\1'
            assert d.read(private + ns['vmroompending'], 1) == b'\0'
        else:
            assert regs['cc'] & 1 and regs['b'] == expected_error, regs
            assert ui_events == [0xb7, 0xb8], ui_events
        assert d.read(private + ns['vmcache'], 12) == root_slot
        if retry_after_error:
            assert d.read(private + ns['vmcache'] + 12, 1) == bytes((room,)), (
                regs, d.read(private + ns['vmcache'], 24), calls)
        else:
            assert d.read(private + ns['vmcache'] + 13, 1) == b'\0', (
                regs, d.read(private + ns['vmcache'], 24), calls)
        expected_pending = (b'\0' if retry_after_error or fail_service or
                            fail_volume_service else b'\1')
        assert d.read(private + ns['vmroompending'], 1) == expected_pending
        assert d.read(private + ns['vmnewroom'], 1) == bytes((room,))
        assert d.read(private + ns['size'], 5) == b'GUARD'
        assert d.read(base, len(image)) == image
    finally:
        d.breakpoint(stop, False)
        d.breakpoint(ui_entry, False)
        if retry_after_error:
            d.breakpoint(retry_return, False)
        for address in os_sites:
            d.breakpoint(address, False)
    if retry_after_error:
        result = (f'volume {fail_volume_service} first-attempt failure followed '
                  'by a real successful second read')
    elif fail_volume_service:
        result = f'volume {fail_volume_service} failure E$EOF with handle cleanup'
    elif fail_service:
        result = f'{fail_service} failure E$EOF with handle cleanup'
    else:
        result = 'missing-room E$PNNF with sierraui callback'
    print(f'PASS: {result}; production ResourceLocate/LoadAsset/VmLoadLogic preserves room/cache/stack/code guards')


def check_native_missing_room_message(d, ui, us):
    """Run the sierraui formatter and print callback for the missing-logic text."""
    base, private, dispatch, callbacks, target, stop = (
        0x9000, 0x1000, 0x7400, 0x7420, 0x7500, 0x7e00)
    d.write(base, ui)
    d.write(private, bytes(us['size']) + b'GUARD')
    d.write(private + us['resourcebase'], private.to_bytes(2, 'big'))
    d.write(private + us['resourcenumber'], bytes((0, 58)))
    d.write(dispatch, (callbacks - dispatch).to_bytes(2, 'big'))
    d.write(callbacks + 16, (target - callbacks).to_bytes(2, 'big'))
    d.write(target, b'\x39')
    regs = invoke(d, base + us['AuxMissingRoomLogic'],
                  dp=private >> 8, u=private, y=dispatch, stop=stop)
    assert not regs['cc'] & 1, regs
    text = d.read(private + us['messagebuffer'], 64).split(b'\0', 1)[0]
    assert text == b'Logics #58 not found.', text
    assert d.read(private + us['size'], 5) == b'GUARD'
    assert d.read(base, len(ui)) == ui
    print('PASS: sierraui formats "Logics #58 not found." and hands it to the ShowCallbacks print-text slot with stack/private/code guards intact')
    return text


def check_native_room_error_ui(d, ui, us):
    """Exercise the real sierraui room-I/O prompt, retry callback and quit path."""
    base, private, dispatch, callbacks, print_entry, load_entry, stop = (
        0x9000, 0x1000, 0x7400, 0x7420, 0x7500, 0x7520, 0x7e00)
    d.write(base, ui)

    def run(keys, load_results, error=211):
        d.write(private, bytes(us['size']) + b'GUARD')
        d.write(private + us['resourcebase'], private.to_bytes(2, 'big'))
        d.write(private + us['vmopcode'], bytes((0xb8,)))
        d.write(private + us['vmnewroom'], bytes((58,)))
        d.write(private + us['vmroompending'], b'\1')
        d.write(private + us['gamequit'], b'\0')
        d.write((private & 0xff00) | (us['resourceerror'] & 0xff), bytes((error,)))
        d.write(dispatch, (callbacks - dispatch).to_bytes(2, 'big'))
        d.write(callbacks + 8, (load_entry - callbacks).to_bytes(2, 'big'))
        d.write(callbacks + 16, (print_entry - callbacks).to_bytes(2, 'big'))
        d.write(0x7ef0, stop.to_bytes(2, 'big') + b'STACK')
        d.breakpoint(stop)
        d.breakpoint(print_entry)
        d.breakpoint(load_entry)
        printed, loads = [], []
        d.regs(pc=base + us['AuxUiCommand'], s=0x7ef0,
               dp=private >> 8, u=private, y=dispatch, cc=0x50)
        try:
            for _ in range(128):
                d.call('c')
                regs = d.regs()
                if regs['pc'] == stop:
                    break
                if regs['pc'] == print_entry:
                    printed.append(d.read(regs['x'], 64).split(b'\0', 1)[0])
                    assert d.read(private + us['dialoginputmode'], 1) == b'\6'
                    key_index = len(printed) - 1
                    assert key_index < len(keys), ('unexpected prompt', printed)
                    d.write(private + us['parsercharacter'], bytes((keys[key_index],)))
                    ret = int.from_bytes(d.read(regs['s'], 2), 'big')
                    d.regs(pc=ret, s=regs['s'] + 2,
                           cc=regs['cc'] & ~1)
                    continue
                if regs['pc'] == load_entry:
                    loads.append((regs['a'], regs['b']))
                    assert loads[-1] == (0, 58), loads
                    result = load_results[len(loads) - 1]
                    ret = int.from_bytes(d.read(regs['s'], 2), 'big')
                    if result:
                        d.write((private & 0xff00) | (us['resourceerror'] & 0xff), bytes((result,)))
                        d.regs(pc=ret, s=regs['s'] + 2, b=result,
                               cc=regs['cc'] | 1)
                    else:
                        d.regs(pc=ret, s=regs['s'] + 2, b=0,
                               cc=regs['cc'] & ~1)
                    continue
                raise AssertionError(('unexpected room-error UI callback', regs))
            else:
                raise AssertionError('room-error UI did not return')
            assert regs['s'] == 0x7ef2 and d.read(0x7ef2, 5) == b'STACK', regs
            assert d.read(private + us['dialoginputmode'], 1) == b'\0'
            assert d.read(private + us['size'], 5) == b'GUARD'
            assert d.read(base, len(ui)) == ui
            return printed, loads, regs
        finally:
            d.breakpoint(stop, False)
            d.breakpoint(print_entry, False)
            d.breakpoint(load_entry, False)

    prompt = b'Room load failed.\nENTER retries; ESC quits.'
    printed, loads, regs = run([13], [0])
    assert printed == [prompt] and loads == [(0, 58)], (printed, loads)
    assert not regs['cc'] & 1 and d.read(private + us['gamequit'], 1) == b'\0'
    assert d.read(private + us['vmroompending'], 1) == b'\1'
    printed, loads, regs = run([13, 27], [211])
    assert printed == [prompt, prompt] and loads == [(0, 58)], (printed, loads)
    assert not regs['cc'] & 1 and d.read(private + us['gamequit'], 1) == b'\1'
    assert d.read(private + us['vmroompending'], 1) == b'\0'
    print('PASS: actual sierraui room-error callback renders retry/quit prompt, retries logic on Enter and exits cleanly on Escape')


def check_coco_room_destination(d, coco, cs, room=0x3a):
    """Run the paired CoCo room-entry and post-transition logic fixture."""
    base, stop = 0x8000, 0x7e00
    root_slot, room_slot = 0x3000, 0x3100
    objects, root_start, room_start = 0x2000, 0x4100, 0x4200
    if room == 0:
        root_script = bytes((3, 249, 0x77, 3, 250, 0x66, 0))
        room_script = b''
    else:
        root_script = bytes((22, room, 3, 250, 0x66, 0))
        room_script = bytes((3, 249, 0x77, 0))
    services = ('ResetHeap', 'events_clear', 'InitScriptBuf',
                'StatusLineWrite', 'InputRedraw')
    code = patch_success(coco, cs, services, 0x7300)
    d.write(base, code)
    d.write(0x002e, base.to_bytes(2, 'big'))
    d.run(base + cs['PatchCmdTable'])
    d.run(base + cs['FixupEvalTbl'])
    code = d.read(base, len(code))
    logic_table = base + cs['LogicTableData']
    d.write(logic_table, root_slot.to_bytes(2, 'big'))
    root_entry = (bytes(6) + root_start.to_bytes(2, 'big') * 2 + bytes(2))
    d.write(root_slot, root_entry)
    d.write(room_slot, bytes(2) + bytes((room, 0)) + bytes(2) +
            room_start.to_bytes(2, 'big') * 2 + bytes(2))
    d.write(root_start, root_script + b'GUARD')
    d.write(room_start, room_script + b'GUARD')
    d.write(0x0030, objects.to_bytes(2, 'big'))
    d.write(0x0032, (objects + 64 * 43).to_bytes(2, 'big'))
    d.write(objects, bytes(64 * 43) + b'GUARD')
    d.write(0x0431, bytes(256))
    d.write(0x0062, root_slot.to_bytes(2, 'big'))
    d.write(0x006a, b'\0')
    d.write(0x01ac, b'\0')
    d.write(0x0250, b'\0')
    d.write(0x01d6, b'\0')
    d.write(0x01ae, b'\0')
    d.write(0x0435, b'\0\0')
    d.write(0x05b1, b'\0')
    d.write(0x6100, bytes((room,)) + b'GUARD')
    d.write(0x7ef0, stop.to_bytes(2, 'big') + b'STACK')
    d.breakpoint(stop)
    d.breakpoint(base + cs['LoadLogicNum'])
    d.breakpoint(base + cs['SetLogicPage'])
    try:
        d.regs(pc=base + cs['cmd_new_room'], s=0x7ef0, dp=0,
               u=0, y=0x6100, cc=0x50)
        for _ in range(64):
            d.call('c')
            regs = d.regs()
            if regs['pc'] == stop:
                break
            assert regs['pc'] == base + cs['LoadLogicNum'], (
                'CoCo room-load boundary', regs)
            assert d.read(root_slot, 2) == b'\0\0', 'room reset retained stale logic links'
            # Simulate a successfully loaded destination logic resource while
            # preserving the real CoCo room reset and logic-table structures.
            d.write(root_slot, room_slot.to_bytes(2, 'big'))
            ret = int.from_bytes(d.read(regs['s'], 2), 'big')
            d.regs(pc=ret, s=regs['s'] + 2, cc=regs['cc'] & ~1)
        else:
            raise AssertionError('CoCo new.room did not return')
        assert regs['y'] == 0 and regs['s'] == 0x7ef2, regs
        assert d.read(room_slot + 2, 1) == bytes((room,))
        assert d.read(objects + 64 * 43, 5) == b'GUARD'

        # Room setup clears resident module tables, so take the immutable-code
        # baseline after those documented state writes have completed.
        code = d.read(base, len(code))
        d.write(0x0062, root_slot.to_bytes(2, 'big'))
        d.write(0x7ef0, stop.to_bytes(2, 'big') + b'STACK')
        d.regs(pc=base + cs['ExecLogicScript'], s=0x7ef0,
               dp=0, u=0, y=0, cc=0x50)
        for _ in range(128):
            d.call('c')
            regs = d.regs()
            if regs['pc'] == stop:
                break
            assert regs['pc'] == base + cs['SetLogicPage'], (
                'CoCo destination logic page service', regs)
            ret = int.from_bytes(d.read(regs['s'], 2), 'big')
            d.regs(pc=ret, s=regs['s'] + 2, cc=regs['cc'] & ~1)
        else:
            raise AssertionError('CoCo destination/root scripts did not return')
        assert regs['s'] == 0x7ef2 and regs['y'] == root_start + len(root_script), regs
        actual = d.read(0x0431 + 249, 2)
        assert actual == b'\x77\x66', ('CoCo destination/root effects', actual)
        assert d.read(root_start + len(root_script), 5) == b'GUARD'
        assert d.read(room_start + len(room_script), 5) == b'GUARD'
        assert d.read(objects + 64 * 43, 5) == b'GUARD'
        current_code = d.read(base, len(code))
        assert current_code == code, [
            (offset, code[offset], current_code[offset])
            for offset in range(len(code)) if current_code[offset] != code[offset]][:16]
        assert d.read(0x7ef2, 5) == b'STACK'
    finally:
        d.breakpoint(stop, False)
        d.breakpoint(base + cs['LoadLogicNum'], False)
        d.breakpoint(base + cs['SetLogicPage'], False)
    print('PASS: CoCo room reset loads its destination logic; the root calls it, observes its effect, continues, and returns')
    return actual


def check_completed_transition(d, coco, cs, native, ns):
    """Compare both public room commands through their room-entry boundary.

    Resource I/O is counted as a successful boundary. The actual room reset,
    room variables, ego-edge placement, saved root IP, flags and
    resource table/cache cleanup execute in each production owner.
    """
    coco_services = ('ResetHeap', 'events_clear', 'InitScriptBuf', 'LoadLogicNum',
                     'StatusLineWrite', 'InputRedraw')
    coco_code = patch_success(coco, cs, coco_services, 0x7000)
    native_services = ('AssetUnmap', 'AssetRelease')
    native_code = patch_success(native, ns, native_services, 0x7001)
    native_image = bytearray(native_code)
    load_stub = bytes((0xf7, 0x70, 0x05, 0x7c, 0x70, 0x03,
                       0x1c, 0xfe, 0x39))
    native_image[ns['VmLoadLogic']:ns['VmLoadLogic'] + len(load_stub)] = load_stub
    native_code = bytes(native_image)
    source = bytearray((i * 73 + 19) & 255 for i in range(64 * 43))
    source[0x1c] = 12
    source[5] = 3

    for side in (1, 2, 3, 4):
        for variable, room in ((False, 0x3a), (True, 0x91),
                               (False, 0), (True, 0)):
            expected_objects = bytearray(room_reset_state(source))
            if side == 1:
                expected_objects[4] = 167
            elif side == 2:
                expected_objects[3] = 0
            elif side == 3:
                expected_objects[4] = 37
            else:
                expected_objects[3] = (160 - expected_objects[0x1c]) & 255

            # CoCo performs the public command and complete NewRoomSetup
            # synchronously. Only allocation, disk loading and presentation
            # services are replaced; the room reset itself is real code.
            coco_base = 0x8000
            d.write(coco_base, coco_code)
            coco_objects = 0x3000
            d.write(coco_objects, source + b'GUARD')
            d.write(0x0030, coco_objects.to_bytes(2, 'big'))
            d.write(0x0032, (coco_objects + 64 * 43).to_bytes(2, 'big'))
            variables = bytearray((i * 17 + 3) & 255 for i in range(256))
            variables[0:6] = bytes((7, 8, side, 33, 44, 55))
            variables[77] = room
            d.write(0x0431, variables)
            d.write(0x006a, b'\0')
            d.write(0x01ac, b'\x99')
            d.write(0x0250, b'\0')
            d.write(0x01d6, b'\0')
            d.write(0x01ae, b'\xa1')
            d.write(0x0435, b'\x88\x99')
            d.write(0x05b1, b'\0')
            d.write(0x7000, b'\0' * (len(coco_services) + 2))
            operand = 77 if variable else room
            d.write(0x6100, bytes((operand,)) + b'GUARD')
            entry = cs['cmd_new_room_v' if variable else 'cmd_new_room']
            regs = invoke(d, coco_base + entry, y=0x6100)
            assert regs['y'] == 0 and d.read(0x6100, 5) == bytes((operand,)) + b'GUAR'
            expected_vars = bytearray(variables)
            expected_vars[0:6] = bytes((room, 7, 0, 33, 0, 0))
            expected_vars[16] = expected_objects[5]
            assert d.read(0x0431, 256) == expected_vars, ('CoCo variables', side, variable)
            assert d.read(coco_objects, 64 * 43) == expected_objects, ('CoCo objects', side, variable)
            assert d.read(coco_objects + 64 * 43, 5) == b'GUARD'
            assert d.read(0x01ac, 1) == b'\0'
            assert d.read(0x0250, 1) == b'\1'
            assert d.read(0x01d6, 1) == b'\x24'
            assert d.read(0x01ae, 1) == b'\xa5'
            assert d.read(0x0435, 2) == b'\0\0'
            assert d.read(0x0433, 1) == b'\0'
            assert d.read(0x05b1, 1) == b'\1'
            assert d.read(0x7000, len(coco_services)) == b'\1' * len(coco_services)

            # Wild Bits applies the same request at its root safe point. The
            # real ApplyRoomChange, all object resets and root-IP restoration
            # run; successful resource IO and room-logic fetch are observed
            # through counted stubs.
            native_base = 0x9000
            private = 0x1000
            d.write(native_base, native_code)
            d.write(private, bytes(ns['size']) + b'GUARD')
            d.write(private + ns['resourcebase'], private.to_bytes(2, 'big'))
            nvars = bytearray(variables)
            nvars[0:6] = bytes((7, 8, side, 33, 44, 55))
            nvars[77] = room
            d.write(private + ns['vmvariables'], nvars)
            native_objects = private + ns['vmobjects']
            d.write(native_objects, source + b'GUARD')
            root_slot = bytes((0, 1, 0, 0, 0, 0, 0, 2, 0, 2, 0x12, 0x34))
            room_slot = bytes((0x37, 1, 0x20, 0x00, 1, 0, 0, 8, 0, 8, 0, 8))
            d.write(private + ns['vmcache'], root_slot + room_slot + bytes(30 * 12))
            d.write(private + ns['vmdepth'], b'\0')
            d.write(private + ns['vmcurrent'], b'\0')
            d.write(private + ns['vmip'], b'\x00\x02')
            d.write(private + ns['vmroompending'], b'\0')
            d.write(private + ns['vmnewroom'], b'\0')
            d.write(private + ns['vmroomchanges'], b'\0')
            d.write(private + ns['vmplayercontrol'], b'\0')
            d.write(private + ns['vmhorizon'], b'\0')
            d.write(private + ns['vmflags'] + 5, b'\0')
            d.write(private + ns['replayused'], b'\x12\x34')
            d.write(private + ns['replaycheckpoint'], b'\x56\x78')
            d.write(0x7001, bytes(5))
            d.write(private + ns['vmarguments'], bytes((operand,)))
            regs = invoke(d, native_base + ns['VmCommandNewRoomVariable' if variable
                                                else 'VmCommandNewRoom'],
                          dp=private >> 8, u=private, y=0x6100)
            assert not regs['cc'] & 1 and d.read(private + ns['vmroompending'], 1) == b'\1'
            assert d.read(private + ns['vmnewroom'], 1) == bytes((room,))
            d.write(0x7001, b'\0\0')
            regs = invoke(d, native_base + ns['ApplyRoomChange'],
                          dp=private >> 8, u=private)
            assert not regs['cc'] & 1 and regs['b'] == 0, ('ApplyRoomChange', regs)
            assert d.read(private + ns['vmvariables'], 256) == expected_vars, ('Wild Bits variables', side, variable)
            assert d.read(native_objects, 64 * 43) == expected_objects, ('Wild Bits objects', side, variable)
            assert d.read(private + ns['vmroompending'], 1) == b'\0'
            assert d.read(private + ns['vmnewroom'], 1) == bytes((room,))
            assert d.read(private + ns['vmroomchanges'], 1) == b'\1'
            assert d.read(private + ns['vmplayercontrol'], 1) == b'\1'
            assert d.read(private + ns['vmhorizon'], 1) == b'\x24'
            assert d.read(private + ns['vmflags'] + 5, 1) == b'\1'
            assert d.read(private + ns['replayused'], 2) == b'\0\0'
            assert d.read(private + ns['replaycheckpoint'], 2) == b'\0\0'
            assert d.read(private + ns['vmip'], 2) == b'\x12\x34'
            assert d.read(private + ns['vmcache'], 12) == root_slot
            assert d.read(private + ns['vmcache'] + 12 + 1, 1) == b'\0'
            assert d.read(private + ns['vmcache'] + 24, 30 * 12) == bytes(30 * 12)
            assert d.read(0x7001, 5) == bytes((1, 1, 1, 0, room)), (
                'transition service counts', side, variable,
                d.read(0x7001, 5))
            assert d.read(private + ns['size'], 5) == b'GUARD'
            assert d.read(native_base, len(native)) == native_code

    print('PASS: literal and variable CoCo/Wild Bits room commands complete room-entry setup for ordinary and zero room numbers at all four borders; room variables, 64 object records, edge placement, input/control flags, cache teardown and saved root IP match; resource/reset/logic-load service boundaries are counted')


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-room-command-') as directory:
        tmp = Path(directory)
        coco, cs = compile_module(ROOT/'objs/mnln.asm', tmp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame',
                                    defines=('WILDBITS=1',), listing=True)
        ui, us = compile_module(ROOT/'objs/sierraui.asm', tmp/'sierraui')
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=300)
        try:
            d.write(0xffdf, b'\0')
            d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01')
            d.write(0xffa8, bytes(range(8)))
            results = {}

            # CoCo starts room setup inside each public command. Stop at its
            # entry, before the setup's destructive resource reset begins.
            for base in (0x8000, 0x9000):
                d.write(base, coco)
                setup = base + cs['NewRoomSetup']
                d.breakpoint(setup)
                for name, operand, room in (('cmd_new_room', 0x3a, 0x3a),
                                            ('cmd_new_room_v', 0x4d, 0x91)):
                    if name.endswith('_v'):
                        d.write(0x0431 + operand, bytes((room,)))
                    d.write(0x6100, bytes((operand,)) + b'GUARD')
                    d.write(0x7ef0, b'\x7e\x00STACK')
                    d.regs(pc=base + cs[name], s=0x7ef0, dp=0,
                           y=0x6100, cc=0x50)
                    d.call('c')
                    regs = d.regs()
                    assert regs['pc'] == setup and regs['a'] == room, (name, regs)
                    return_address = int.from_bytes(d.read(0x7eee, 2), 'big')
                    assert regs['s'] == 0x7eee and base <= return_address < base+len(coco), (name, regs, return_address)
                    assert d.read(0x6100, 2) == bytes((operand,)) + b'G'
                    results[('CoCo', name, base)] = (regs['a'], 'setup entered synchronously')
                d.breakpoint(setup, False)

            # Wild Bits public handlers only publish a request. The root VM
            # applies it after the current logic call stack unwinds.
            for base in (0x9000, 0xa000):
                d.write(base, native)
                private = 0x1000
                d.write(private, bytes(ns['size']) + b'GUARD')
                d.write(private + ns['resourcebase'], private.to_bytes(2, 'big'))
                d.write(private + ns['vmip'], bytes.fromhex('0002'))
                d.write(private + ns['vmroompending'], b'\0')
                d.write(private + ns['vmnewroom'], b'\0')
                for name, operand, room in (('VmCommandNewRoom', 0x3a, 0x3a),
                                            ('VmCommandNewRoomVariable', 0x4d, 0x91)):
                    d.write(private + ns['vmarguments'], bytes((operand,)))
                    d.write(private + ns['vmvariables'] + operand, bytes((room,)))
                    regs = invoke(d, base + ns[name], dp=private >> 8,
                                  u=private, y=0x6100)
                    assert not regs['cc'] & 1 and regs['b'] == 0, (name, regs)
                    assert d.read(private + ns['vmnewroom'], 1) == bytes((room,)), name
                    assert d.read(private + ns['vmroompending'], 1) == b'\1', name
                    assert d.read(private + ns['vmip'], 2) == bytes.fromhex('0002'), name
                    assert d.read(private + ns['size'], 5) == b'GUARD'
                    results[('Wild Bits', name, base)] = (room, 'request queued')
                assert d.read(base, len(native)) == native

            # Both production owners expand the common reset macro in their
            # real room-entry loops. Compare every field of all 64 records.
            object_source = bytes((i*73 + 19) & 255 for i in range(64*43))
            expected_objects = room_reset_state(object_source)
            for base in (0x8000, 0x9000):
                d.write(base, coco)
                coco_objects = 0x3000
                d.write(coco_objects, object_source + b'GUARD')
                d.write(0x0030, coco_objects.to_bytes(2, 'big'))
                d.write(0x0032, (coco_objects+64*43).to_bytes(2, 'big'))
                stop = base + cs['NewRoomObjsDone']
                d.breakpoint(stop)
                d.regs(pc=base+cs['NewRoomObjLoop'], s=0x7ef0, dp=0,
                       u=coco_objects, cc=0x50)
                d.call('c')
                regs = d.regs()
                assert regs['pc'] == stop and regs['u'] == coco_objects+64*43, regs
                assert regs['s'] == 0x7ef0
                assert d.read(coco_objects, 64*43) == expected_objects
                assert d.read(coco_objects+64*43, 5) == b'GUARD'
                d.breakpoint(stop, False)

            for base in (0x9000, 0xa000):
                d.write(base, native)
                private = 0x1000
                d.write(private, bytes(ns['size']) + b'GUARD')
                native_objects = private + ns['vmobjects']
                d.write(native_objects, object_source + b'GUARD')
                stop = base + ns['RoomVariablesBegin']
                d.breakpoint(stop)
                d.regs(pc=base+ns['RoomResetObject'], s=0x7ef0,
                       dp=private >> 8, u=private, x=native_objects,
                       y=64, cc=0x50)
                d.call('c')
                regs = d.regs()
                assert regs['pc'] == stop and regs['y'] == 0, regs
                assert regs['s'] == 0x7ef0
                assert d.read(native_objects, 64*43) == expected_objects
                assert d.read(native_objects+64*43, 5) == b'GUARD'
                d.breakpoint(stop, False)

            check_completed_transition(d, coco, cs, native, ns)
            check_native_room_yield(d, native, ns)
            check_native_room_load_failure(d, native, ns)
            coco_missing_message = check_coco_missing_logic_path(d, coco, cs)
            check_coco_room_volume_io_errors(d, coco, cs)
            check_coco_open_volume_retry(d, coco, cs)
            check_native_missing_room_resource(
                d, native, ns, (tmp/'wbgame.list').read_text())
            for failed_call in ('seek', 'read', 'partial-read', 'close'):
                check_native_missing_room_resource(
                    d, native, ns, (tmp/'wbgame.list').read_text(),
                    fail_service=failed_call)
            for failed_call in ('seek', 'read'):
                check_native_missing_room_resource(
                    d, native, ns, (tmp/'wbgame.list').read_text(),
                    fail_volume_service=failed_call)
                check_native_missing_room_resource(
                    d, native, ns, (tmp/'wbgame.list').read_text(),
                    fail_volume_service=failed_call, retry_after_error=True)
            native_missing_message = check_native_missing_room_message(d, ui, us)
            assert coco_missing_message == native_missing_message, (
                'CoCo/Wild Bits missing-room message differs',
                coco_missing_message, native_missing_message)
            check_native_room_error_ui(d, ui, us)
            coco_destination = check_coco_room_destination(d, coco, cs)
            native_destination = check_native_room_destination(d, native, ns)
            assert coco_destination == native_destination == b'\x77\x66', (
                'paired destination and root effects', coco_destination,
                native_destination)
            coco_zero = check_coco_room_destination(d, coco, cs, room=0)
            native_zero = check_native_room_destination(d, native, ns, room=0)
            assert coco_zero == native_zero == b'\x77\x66', (
                'paired room-zero root effects', coco_zero, native_zero)
            print('PASS: actual public literal/variable new.room handlers at two bases; CoCo enters NewRoomSetup synchronously, Wild Bits records the same requested room and defers application to the root VM; both real room-entry loops reset all 64 object records identically; operand, stack, private-state and code guards pass', results)
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
