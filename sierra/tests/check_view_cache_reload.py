#!/usr/bin/env python3
"""Compare public view load/discard/reload commands against original resources."""
from pathlib import Path
import tempfile

from check_wbres import exercise, idle_rom, start_cpu
from check_lzw import resources
from check_logic_executor import compile_module

ROOT = Path(__file__).resolve().parents[1]


def run_coco_view_lifecycle(d, code, syms, expanded_view):
    """Run the CoCo cache/list routines, stubbing only page/file services."""
    base = 0x8000
    d.write(base, code)
    d.write(base + syms['list_struct'], bytes(2))
    d.write(base + syms['ListLastNode'], bytes(2))
    d.write(0x000a, b'\x12\x34')
    d.write(0x7100, expanded_view)
    hooks = ('ClearBothRanges', 'AllocDataBlock', 'FetchView', 'OpenVolFile',
             'PushScript', 'CalcPriAddr', 'SwapObjRanges', 'UpdateFreeSpace',
             'SetLogicPage')
    for name in hooks:
        d.breakpoint(base + syms[name])
    d.breakpoint(0x7e00)
    next_node = [0x5000]
    fetches = []

    def invoke(entry, a=0, b=0, operands=None):
        nonlocal fetches
        if operands is not None:
            d.write(0x2000, operands+b'ARGS')
        d.write(0x7ef0, b'\x7e\x00STACK')
        d.regs(pc=base + syms[entry], s=0x7ef0, a=a, b=b, u=0,
               y=0x2000, dp=0, cc=0x50)
        trace = []
        for _ in range(32):
            d.call('c')
            regs = d.regs()
            if regs['pc'] == 0x7e00:
                assert regs['s'] == 0x7ef2 and d.read(0x7ef2, 5) == b'STACK'
                if operands is not None:
                    assert regs['y'] == 0x2000+len(operands)
                    assert d.read(regs['y'], 4) == b'ARGS'
                return regs, trace
            name = next(item for item in hooks if base + syms[item] == regs['pc'])
            trace.append(name)
            updates = {'cc': regs['cc'] & ~1}
            if name == 'AllocDataBlock':
                assert (regs['a'] << 8 | regs['b']) == 7
                updates['u'] = next_node[0]
                next_node[0] += 7
            elif name == 'FetchView':
                fetches.append(regs['b'])
                updates['u'] = 0x7000
            elif name == 'OpenVolFile':
                # OpenVolFile's Z result reports whether U contains a resource.
                updates.update(u=0x7100, a=len(expanded_view) >> 8,
                               b=len(expanded_view) & 255,
                               cc=regs['cc'] & ~0x05)
            elif name == 'CalcPriAddr':
                updates['u'] = 0x6000
            ret = int.from_bytes(d.read(regs['s'], 2), 'big')
            d.regs(pc=ret, s=regs['s'] + 2, **updates)
        raise AssertionError((entry, 'CoCo view routine did not return', trace))

    try:
        first, first_trace = invoke('cmd_load_view', operands=b'\0')
        node1 = first['u']
        record1 = d.read(node1, 7)
        assert node1 == 0x5000 and record1 == (
            b'\0\0\0\x71\x00' + len(expanded_view).to_bytes(2, 'big'))
        assert d.read(base + syms['list_struct'], 2) == node1.to_bytes(2, 'big')

        d.write(0x0431+250, b'\0')
        cached, cached_trace = invoke('cmd_load_view_v', operands=bytes((250,)))
        assert cached['u'] == node1 and cached_trace == [] and fetches == [0]

        _, discard_trace = invoke('cmd_discard_view_v', operands=bytes((250,)))
        assert d.read(base + syms['list_struct'], 2) == b'\0\0'
        assert 'PushScript' in discard_trace and 'CalcPriAddr' in discard_trace

        reloaded, reload_trace = invoke('cmd_load_view', operands=b'\0')
        node2 = reloaded['u']
        assert node2 == 0x5007 and d.read(node2, 7) == record1
        assert d.read(base + syms['list_struct'], 2) == node2.to_bytes(2, 'big')
        assert d.read(0x7100, len(expanded_view)) == expanded_view
        # Fill seven additional logical views, discard view zero, and load a
        # ninth ID. CoCo's linked list must continue to find all residents and
        # unlink the selected node without damaging the remaining chain.
        nodes = {0: node2}
        for view_id in range(1, 8):
            loaded, _ = invoke('cmd_load_view', operands=bytes((view_id,)))
            nodes[view_id] = loaded['u']
            assert d.read(loaded['u'] + 2, 1) == bytes((view_id,))
        _, discard_full_trace = invoke('cmd_discard_view', operands=b'\0')
        assert d.read(base + syms['list_struct'], 2) == nodes[1].to_bytes(2, 'big'), (
            'CoCo list head after discarding view zero',
            d.read(base + syms['list_struct'], 2).hex(),
            nodes[1].to_bytes(2, 'big').hex(),
            [(key, hex(value)) for key, value in nodes.items()])
        last, _ = invoke('cmd_load_view', operands=b'\x08')
        assert d.read(last['u'] + 2, 1) == b'\x08'
        assert d.read(base + syms['ListLastNode'], 2) == nodes[7].to_bytes(2, 'big')
        assert 'PushScript' in discard_full_trace
        assert fetches == [0, 0, *range(1, 8), 8], fetches
        assert 'FetchView' in first_trace and 'FetchView' in reload_trace
        # Run the real selector routines against loaded view 8. Only the
        # memory-page service is intercepted; table traversal stays real.
        _, _ = invoke('cmd_discard_view', operands=b'\x01')
        invoke('cmd_load_view', operands=b'\0')
        d.write(0x30, (0x4000).to_bytes(2, 'big'))
        d.write(0x32, (0x402b).to_bytes(2, 'big'))
        d.write(0x4000, bytes(43))
        d.write(0x0431+250, bytes((8,0,1)))

        def select(entry, operands):
            d.write(0x2000, operands+b'ARGS')
            d.write(0x7ef0, b'\x7e\0STACK')
            d.regs(pc=base+syms[entry],s=0x7ef0,y=0x2000,cc=0x50)
            for _ in range(16):
                d.call('c')
                regs=d.regs()
                if regs['pc']==0x7e00:
                    assert regs['s']==0x7ef2 and d.read(0x7ef2,5)==b'STACK'
                    assert d.read(0x2000+len(operands),4)==b'ARGS'
                    return
                assert regs['pc']==base+syms['SetLogicPage'],(entry,regs)
                ret=int.from_bytes(d.read(regs['s'],2),'big')
                d.regs(pc=ret,s=regs['s']+2)
            raise AssertionError((entry,'view selection failed to return'))

        selection_steps=[]
        for entry, operands in (('cmd_set_view',bytes((0,0))),
                                ('cmd_set_loop',bytes((0,1))),
                                ('cmd_set_cel',bytes((0,0))),
                                ('cmd_set_view_v',bytes((0,250))),
                                ('cmd_set_loop_v',bytes((0,251))),
                                ('cmd_set_cel_v',bytes((0,252)))):
            select(entry,operands)
            record=d.read(0x4000,43)
            selection_steps.append(bytes(record[index] for index in (5,0x0a,0x0b,0x0e,0x0f,0x1c,0x1d)))
        return selection_steps
    finally:
        for name in hooks:
            d.breakpoint(base + syms[name], False)
        d.breakpoint(0x7e00, False)


def main():
    # Load view 0, hit it from cache, discard/reload it, retain eight distinct
    # views, discard slot zero, then load view 8 to prove slot reuse.
    body = bytearray((30, 0, 3, 250, 0, 31, 250, 153, 250, 30, 0))
    for view_id in range(1, 8):
        body.extend((30, view_id))
    body.extend((32, 0, 30, 8, 32, 1, 30, 0,
                 3,250,8,3,251,0,3,252,1,
                 41,0,0,43,0,1,47,0,0,
                 42,0,250,44,0,251,48,0,252,
                 134,1,0))
    body = bytes(body)
    logic = len(body).to_bytes(2, 'little') + body
    _, packed_view, view = next(item for item in resources()
                                if item[0] == 'viewDir/0')
    volume = bytearray(8)
    logic_offset = len(volume)
    volume.extend(b'\x12\x34\0' + len(logic).to_bytes(2, 'little') * 2 + logic)
    view_offset = len(volume)
    volume.extend(b'\x12\x34\0' + len(view).to_bytes(2, 'little') +
                  len(packed_view).to_bytes(2, 'little') + packed_view)
    view_directory = b''.join(view_offset.to_bytes(3, 'big')
                              for _ in range(9))
    files = {'/game/logDir': logic_offset.to_bytes(3, 'big'),
             '/game/viewDir': view_directory,
             '/game/vol.0': bytes(volume)}
    loaded = []
    cache_hits = []
    cache_context = []
    discards = []
    view_command_states = []

    def trace_load(cpu, regs, syms):
        if cpu.read(syms['vmrequestedkind'], 1)[0] == 2:
            loaded.append(cpu.read(syms['vmrequested'], 1)[0])
        return True

    def trace_cache(cpu, regs, syms):
        kind = cpu.read(syms['vmrequestedkind'], 1)[0]
        number = cpu.read(syms['vmrequested'], 1)[0]
        if kind == 2 and number in (0, 8):
            cache_hits.append((regs['x'], cpu.read(regs['x'], syms['VM_CACHE_ENTRY_BYTES'])))
            cache_context.append((cpu.read(syms['vmopcode'],1)[0],
                                  cpu.read(syms['vmarguments'],3),number))
        return True

    def trace_discard(cpu, regs, syms):
        if regs['a'] == 2:
            # The hook is at VmDiscardResource's entry, before it copies A/B
            # into vmrequestedkind/vmrequested, so read the live argument regs.
            discards.append(regs['b'])
        return True

    def trace_view_command(cpu, regs, syms):
        record=cpu.read(syms['vmobjects'],43)
        view_command_states.append((cpu.read(syms['vmopcode'],1)[0],
            bytes(record[index] for index in (5,0x0a,0x0b,0x0e,0x0f,0x1c,0x1d))))
        return True

    with tempfile.TemporaryDirectory(prefix='sierra-view-cache-reload-') as name:
        temp = Path(name)
        coco, coco_syms = compile_module(ROOT / 'objs/mnln.asm', temp / 'mnln')
        d, emulator = start_cpu(idle_rom(temp / 'idle.rom'), timeout=900)
        try:
            d.write(0xffdf, b'\0')
            d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01')
            d.write(0xffa8, bytes(range(8)))
            coco_selected=run_coco_view_lifecycle(d, coco, coco_syms, view)
            error, output, state = exercise(
                d, files, arguments=b'/game 0\r', module='wbgame', base=0xa000,
                database=0, window=0x8000, blocks=None, multiple=True, firstblock=0x10,
                capture=True, module_root=ROOT / 'objs', os_call_limit=30000,
                breakpoint_hooks={'LoadAsset': trace_load,
                                  'VmCacheFound': trace_cache,
                                  'VmDiscardResource': trace_discard,
                                  'ViewCommand': trace_view_command})
        finally:
            d.s.close()
            emulator.terminate()
            try:
                emulator.wait(timeout=5)
            except Exception:
                emulator.kill()
                emulator.wait(timeout=5)
    assert error == 0, (error, output, state.get('vmerror'), state.get('asseterror'), state.get('file_reads'))
    expected_loads = [0, 0, *range(1, 8), 8, 0]
    assert loaded == expected_loads, ('view loader calls across full cache', loaded)
    assert discards == [0, 0, 1], ('discard sequence should free view 1 for selector comparison', discards)
    assert len(cache_hits) == 11, (cache_hits,cache_context)
    slot_addresses = [address for address, _ in cache_hits[:3]]
    entries = [entry for _, entry in cache_hits[:3]]
    assert slot_addresses == [slot_addresses[0]] * 3, slot_addresses
    assert [entry[0] for entry in entries] == [0, 0, 0], entries
    assert all(entry[1] == 1 and entry[5] == 2 for entry in entries), entries
    assert all(entry[6:10] == entries[0][6:10] for entry in entries), entries
    assert [entry[0] for _,entry in cache_hits]==[0,0,0,8,0,0,0,0,8,8,8],(cache_hits,cache_context)
    assert any(opcode==31 and arguments[0]==250 and number==0
               for opcode,arguments,number in cache_context), cache_context
    native_record=state['vmobjects'][:43]
    native_selected=bytes(native_record[index] for index in (5,0x0a,0x0b,0x0e,0x0f,0x1c,0x1d))
    assert [opcode for opcode,_ in view_command_states]==[41,43,47,42,44,48],view_command_states
    native_selection_steps=[record for _,record in view_command_states[1:]]+[native_selected]
    assert native_selection_steps==coco_selected,(native_selection_steps,coco_selected)
    print('PASS: CoCo and Wild Bits execute literal/variable load.view and discard.view, retain eight distinct views, discard view 0, '
          'and load view 8; CoCo preserves its remaining list, Wild Bits reuses the '
          'freed cache slot, and both reload from their tested resource paths; literal/variable view-loop-cel selection matches')


if __name__ == '__main__':
    main()
