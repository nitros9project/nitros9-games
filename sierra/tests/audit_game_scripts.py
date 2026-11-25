#!/usr/bin/env python3
"""Conservatively audit original AGI script control flow and native support.

No game assets are copied to the report. Both arms of every condition are
visited; variable calls/rooms remain unresolved rather than guessed.
"""
import argparse
import hashlib
import json
import re
from collections import deque
from pathlib import Path
from check_lzw import expand
from check_native_dispatch import COMMON, GAME

ROOT = Path(__file__).resolve().parents[1]


def catalogs():
    commands = []
    for line in (ROOT/'objs/shared/agi-command-table.asm').read_text().splitlines():
        match = re.match(r'\s*AGI_COMMAND\s+([^,]+),\$([0-9a-f]+),([^,]+),([01])', line, re.I)
        if match:
            commands.append({'coco_handler': match[1].strip(), 'operands': int(match[2],16)//256,
                             'native_handler':match[3].strip(), 'game_only':bool(int(match[4]))})
    tests = [int(m[1],16)//256 for m in re.finditer(
        r'^\s*AGI_TEST\s+[^,]+,\$([0-9a-f]+)',
        (ROOT/'objs/shared/agi-test-table.asm').read_text(), re.M|re.I)]
    assert len(commands)==182 and len(tests)==19
    supported = set(range(18))
    for routes in (COMMON,GAME):
        for opcodes in routes.values(): supported.update(opcodes)
    return commands, tests, supported


def logic_resource(game, number, entry):
    volume = (game/f'vol.{entry>>20}').read_bytes()
    offset = entry&0xfffff
    header = volume[offset:offset+7]
    if len(header)!=7 or header[:2]!=b'\x12\x34':
        raise ValueError(f'logic {number}: bad resource header')
    decoded = int.from_bytes(header[3:5],'little')
    stored = int.from_bytes(header[5:7],'little')
    payload = volume[offset+7:offset+7+stored]
    if len(payload)!=stored: raise ValueError(f'logic {number}: truncated resource')
    if decoded!=stored: payload=expand(payload)
    if len(payload)!=decoded or len(payload)<2:
        raise ValueError(f'logic {number}: wrong expanded length')
    length=int.from_bytes(payload[:2],'little')
    if length+2>len(payload): raise ValueError(f'logic {number}: truncated code')
    return payload, decoded == stored


def script(game, number, entry):
    payload, _ = logic_resource(game, number, entry)
    length = int.from_bytes(payload[:2], "little")
    return payload[2:length+2]


def message_formats(payload, encrypted):
    """Report substitution locations without copying original message text.

    This scans every declared message, including messages not statically reached.
    An empty offset denotes an absent message. Escaped percent signs are literals.
    """
    at = 2 + int.from_bytes(payload[:2], "little")
    if at == len(payload):
        return []
    if at + 3 > len(payload):
        raise ValueError("truncated message header")
    count = payload[at]
    base = at + 1
    end = base + int.from_bytes(payload[base:base+2], "little")
    start = base + 2 + count * 2
    if not start <= end <= len(payload):
        raise ValueError("invalid message table extent")
    text = bytearray(payload[start:end])
    if encrypted:
        key = b"Avis Durgan"
        text = bytearray(value ^ key[i % len(key)] for i, value in enumerate(text))
    findings = []
    for index in range(count):
        slot = base + 2 + index * 2
        offset = int.from_bytes(payload[slot:slot+2], "little")
        if offset == 0:
            continue
        position = base + offset
        if not start <= position < end:
            raise ValueError("message offset outside string area")
        relative = position - start
        terminator = text.find(0, relative)
        if terminator < 0:
            raise ValueError("unterminated message")
        message = text[relative:terminator]
        cursor = 0
        while cursor < len(message):
            if message[cursor] != 37:
                cursor += 1
                continue
            origin = cursor
            cursor += 1
            if cursor < len(message) and message[cursor] == 37:
                cursor += 1
                continue
            directive = chr(message[cursor]) if cursor < len(message) else ""
            cursor += 1
            digits = cursor
            while cursor < len(message) and 48 <= message[cursor] <= 57:
                cursor += 1
            # Keep the operand as decimal text: arbitrarily long malformed
            # operands must not trigger Python integer conversion limits.
            operand = bytes(message[digits:cursor]).decode("ascii")
            if directive not in "wsmvog" or not directive or not operand:
                findings.append({"message": index + 1, "offset": origin,
                                 "directive": directive, "operand": operand,
                                 "reason": "unknown directive" if directive not in "wsmvog" or not directive
                                           else "missing operand"})
    return findings


def message_format_samples(payload, encrypted):
    """Return only unusual directive bytes from declared messages.

    These short samples preserve the actual escape spelling and operand bytes
    while keeping original game prose out of test output and reports.
    """
    at = 2 + int.from_bytes(payload[:2], "little")
    if at == len(payload):
        return []
    count = payload[at]
    base = at + 1
    end = base + int.from_bytes(payload[base:base+2], "little")
    start = base + 2 + count * 2
    text = bytearray(payload[start:end])
    if encrypted:
        key = b"Avis Durgan"
        text = bytearray(value ^ key[i % len(key)] for i, value in enumerate(text))
    samples = []
    for index in range(count):
        offset = int.from_bytes(payload[base+2+index*2:base+4+index*2], "little")
        if offset == 0:
            continue
        position = base + offset - start
        terminator = text.find(0, position)
        if terminator < 0:
            continue
        message = text[position:terminator]
        cursor = 0
        while cursor < len(message):
            if message[cursor] != 37:
                cursor += 1
                continue
            begin = cursor
            cursor += 1
            if cursor < len(message) and message[cursor] == 37:
                cursor += 1
                continue
            directive = message[cursor] if cursor < len(message) else None
            if directive is not None:
                cursor += 1
            digits = cursor
            while cursor < len(message) and 48 <= message[cursor] <= 57:
                cursor += 1
            if directive not in b"wvsmog" or directive is None or cursor == digits:
                samples.append(bytes(message[begin:cursor]))
    return samples


def analyze(code, commands, tests, overlaps=None):
    queue=deque([0]);instructions={};occupied={};predicates=set()
    def take(at,count):
        if at<0 or at+count>len(code):raise ValueError(f'truncated instruction at {at}')
        return code[at:at+count]
    def branch(at):
        return at+2+int.from_bytes(take(at,2),'little',signed=True)
    while queue:
        start=queue.popleft()
        if start in instructions:continue
        if start<0 or start>=len(code):raise ValueError(f'branch outside code: {start}')
        at=start;opcode=take(at,1)[0];at+=1;arguments=[];targets=[]
        if opcode==254:
            targets=[branch(at)];at+=2
        elif opcode==255:
            inside_or=False;negated=False
            while True:
                test=take(at,1)[0];at+=1
                if test==255:
                    if inside_or or negated:raise ValueError(f'unclosed condition at {start}')
                    break
                if test==252:
                    if negated:raise ValueError(f'NOT before OR at {start}')
                    inside_or=not inside_or;continue
                if test==253:
                    negated=not negated;continue
                if not 0<=test<len(tests):raise ValueError(f'invalid predicate {test} at {at-1}')
                predicates.add(test);negated=False
                count=tests[test]
                if test==14:
                    count=take(at,1)[0]*2;at+=1
                take(at,count);at+=count
            targets=[branch(at),at+2];at+=2
        else:
            if opcode>=len(commands):raise ValueError(f'invalid opcode {opcode} at {start}')
            count=commands[opcode]['operands'];arguments=list(take(at,count));at+=count
            # Restart and prompted quit can be cancelled; audit continuation.
            if opcode not in (0,18,19) and not (opcode==134 and arguments==[1]):targets=[at]
        for byte in range(start,at):
            if byte in occupied and occupied[byte]!=start:
                if overlaps is None:raise ValueError(f'instruction overlap at {byte}')
                finding={'byte':byte,'first_instruction':occupied[byte],'second_instruction':start}
                if finding not in overlaps:overlaps.append(finding)
            occupied[byte]=start
        instructions[start]={'offset':start,'opcode':opcode,'arguments':arguments}
        queue.extend(targets)
    return list(instructions.values()), sorted(predicates)


def audit(game):
    commands,tests,supported=catalogs();directory=(game/'logDir').read_bytes()
    if len(directory)%3:raise ValueError('partial logDir entry')
    report={'game':game.name,'method':'Both branch arms; local control flow from entry; variable destinations unresolved.',
            'resource_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(game.iterdir())
                               if p.is_file() and (p.name.startswith('vol.') or p.name in ('logDir','picDir','viewDir','sndDir','words.tok','object'))},
            'limits':['Static reachability does not establish puzzle solvability or correct command semantics.',
                      'Dynamic calls/rooms and saved scan starts require runtime coverage.',
                      'Overlapping instruction decodings are reported explicitly; byte overlap alone does not establish invalid runtime behavior.'], 'logics':[]}
    for number in range(len(directory)//3):
        entry=int.from_bytes(directory[number*3:number*3+3],'big')
        if entry==0xffffff:continue
        payload, encrypted = logic_resource(game,number,entry)
        code = payload[2:2+int.from_bytes(payload[:2], "little")]
        try: formats = message_formats(payload, encrypted)
        except ValueError as error: raise ValueError(f"logic {number}: {error}") from error
        overlaps=[]
        try:instructions,predicates=analyze(code,commands,tests,overlaps=overlaps)
        except ValueError as error:raise ValueError(f'logic {number}: {error}') from error
        operations=[i for i in instructions if i['opcode']<182]
        unsupported=[dict(i,coco_handler=commands[i['opcode']]['coco_handler']) for i in operations if i['opcode'] not in supported]
        ignored=[dict(i,coco_handler=commands[i['opcode']]['coco_handler'],classification='CoCo ignored operation')
                 for i in operations if commands[i['opcode']]['native_handler']=='VmSuccess']
        direct=[{'offset':i['offset'],'kind':'room' if i['opcode']==18 else 'call','target':i['arguments'][0]}
                for i in operations if i['opcode'] in (18,22)]
        dynamic=[{'offset':i['offset'],'kind':'room' if i['opcode']==19 else 'call','variable':i['arguments'][0]}
                 for i in operations if i['opcode'] in (19,23)]
        report['logics'].append({'logic':number,'code_bytes':len(code),'instructions':len(instructions),
            'commands':sorted({i['opcode'] for i in operations}),'predicates':predicates,
            'direct_destinations':direct,'dynamic_destinations':dynamic,'unsupported':unsupported,
            'unsupported_message_formats':formats,'overlapping_instructions':overlaps,'ignored_operations':ignored})
    by_number={item['logic']:item for item in report['logics']};reachable=set();queue=deque([0])
    while queue:
        number=queue.popleft()
        if number in reachable or number not in by_number:continue
        reachable.add(number);queue.extend(d['target'] for d in by_number[number]['direct_destinations'])
    report['direct_graph_from_root']=sorted(reachable)
    report['unresolved_dynamic_from_direct_graph']=[{'logic':n,**d} for n in sorted(reachable)
                                                   for d in by_number[n]['dynamic_destinations']]
    report['summary']={'logics':len(by_number),'instructions':sum(i['instructions'] for i in by_number.values()),
        'unsupported':[{'logic':i['logic'],**op} for i in by_number.values() for op in i['unsupported']],
        'ignored_operations':[{'logic':i['logic'],**item} for i in by_number.values() for item in i['ignored_operations']],
        'overlapping_instructions':[{'logic':i['logic'],**item} for i in by_number.values() for item in i['overlapping_instructions']],
        'unsupported_message_formats':[{'logic':i['logic'],**item} for i in by_number.values()
                                       for item in i['unsupported_message_formats']]}
    return report


def coverage_manifest():
    """Source-linked catalog inventory; route/predicate tests are not full equivalence."""
    commands,tests,supported=catalogs()
    source_files=sorted((ROOT/'objs').rglob('*.asm'))
    reference_files=[p for p in source_files if not p.name.startswith('wildbits-') and
                     p.name!='wildbits_engine.asm' and
                     p.name not in ('agi-command-table.asm','agi-test-table.asm')]
    native_files=[p for p in source_files if p.parent.name=='platform' and
                  p.name.startswith('wildbits-') or
                  p.parent.name=='shared']

    def source_hits(symbol,files,macro_call=False):
        definitions=set();macro_owners=set()
        label=re.compile(r'^\s*'+re.escape(symbol)+r'\b',re.I)
        invocation=re.compile(r'^\s*[A-Za-z_][A-Za-z0-9_]*\s+'
                              +re.escape(symbol)+r'\s*(?:,|$)',re.I)
        for path in files:
            for line in path.read_text(errors='ignore').splitlines():
                if label.search(line):
                    definitions.add(path.relative_to(ROOT).as_posix())
                    break
                if macro_call and invocation.search(line):
                    macro_owners.add(path.relative_to(ROOT).as_posix())
                    break
        return sorted(definitions or macro_owners)

    reference_sources={}
    native_sources={}
    for coco_handler,native_handler in {(c['coco_handler'],c['native_handler']) for c in commands}:
        reference_sources[coco_handler]=source_hits(coco_handler,reference_files,macro_call=True)
        native_sources[native_handler]=source_hits(native_handler,native_files)
    candidates={
        'C01':['check_priority_view.py','check_priority_mame.py','check_native_dispatch.py'],
        'C02':['check_decimal_output.py','check_wbgame.py','check_priority_mame.py','check_native_dispatch.py'],
        'C03':['check_decimal_output.py','check_wbgame.py','check_priority_mame.py','check_native_dispatch.py'],
        'C04':['check_wbgame.py','check_wbgame_mame.py','check_native_dispatch.py'],
        'C05':['check_trace.py','check_wbgame.py','check_wbgame_mame.py','check_native_dispatch.py'],
        'C06':['check_wbgame.py','check_priority_mame.py','check_native_dispatch.py'],
        'C07':['check_wbgame.py','check_priority_mame.py','check_native_dispatch.py'],
        'S01':['check_logic_executor.py','check_condition_flow.py','check_math_commands.py','check_random_command.py','check_coco_conditions.py'],
        'S02':['check_resource_lifetime.py','check_resource_format.py','check_wbasset.py','check_packed_pictures.py','check_lzw.py','check_wbgame.py','check_load_logic_cache_hit.py','check_room_commands.py'],
        'S03':['check_object_flags.py','check_object_update_control.py','check_force_update.py','check_object_visibility.py','check_object_scalar_commands.py','check_object_bounds.py','check_object_position_predicates.py','check_object_terrain.py','check_motion_setup.py','check_wbgame.py'],
        'S04':['check_wbdecode.py','check_text_graphics_mode.py','check_picture_stream.py','check_resource_lifetime.py','check_text_rect.py','check_add_to_picture.py','check_priority_bands.py','check_wbgame.py','check_wbgame_mame.py','check_kq4_mame.py'],
        'S05':['check_decimal_index.py','check_text_helpers.py','check_text_command_entry.py','check_parse_command.py','check_cursor_char.py','check_text_attribute.py','check_string_compare.py','check_said.py','check_tokenizer.py','check_wbparser.py','check_wbplay.py','check_wbgame_mame.py','check_kq4_mame.py'],
        'S06':['check_wbgame.py','check_wbparser.py','check_get_string.py','check_get_number.py','check_init_joy.py','check_wbgame_previews_mame.py','check_screen_config.py','check_inventory_commands.py','check_controller_predicate.py','check_wbplay.py','check_screen_input.py','check_set_key.py','check_persistent_window.py','check_kq4_mame.py','check_coco_kq4_inventory_mame.py'],
        'S07':['check_game_clock.py','check_native_audio.py','check_wbgame.py'],
        'S08':['check_wbgame.py','check_original_kq3.py','check_kq3_mame.py','check_game_id.py','check_quit_command.py']}
    gates={i:'S01' for i in range(182)}
    for gate,ranges in {'S02':[(18,23),(30,32),(142,142),(153,153),(171,172)],
                        'S03':[(33,91),(147,148)],
                        'S04':[(24,28),(106,107),(110,110),(122,123),(140,140),(154,154),(174,174)],
                        'S05':[(101,104),(108,109),(114,114),(116,117),(151,152)],
                        'S06':[(92,97),(105,105),(111,113),(115,115),(118,121),(124,124),(129,129),(131,132),(137,139),(141,141),(156,162),(169,169)],
                        'S07':[(98,100),(136,136)],'S08':[(125,126),(128,128),(134,134),(143,143)]}.items():
        for lo,hi in ranges:
            for i in range(lo,hi+1):gates[i]=gate
    for i,gate in {29:'C01',133:'C02',135:'C03',149:'C04',150:'C05',170:'C06',177:'C07',
                   144:'C08',175:'C09',179:'C10',180:'C11',
                   **{i:'C12' for i in (127,155,163,164,173,176,178,181)}}.items():gates[i]=gate
    rows=[]
    for i,command in enumerate(commands):
        gate=gates[i];status='unsupported' if i not in supported else 'CoCo ignored operation' if command['native_handler']=='VmSuccess' else 'routed'
        native_handler=command['native_handler']
        native_source=native_sources[native_handler]
        decision=({'policy':'Preserve the actual CoCo no-op/stub; consume the catalog operands and leave gameplay state unchanged.',
                   'reference':'WILDBITS-PARITY.md#c08-c12-coco-stub-decisions'}
                  if status=='CoCo ignored operation' else
                  {'policy':'Wild Bits queues the room change until the VM reaches a safe point, while CoCo runs NewRoomSetup synchronously. Compare complete post-transition state, room logic and caller behavior; the shared room-entry helper test alone is not command-level evidence.',
                   'reference':'WILDBITS-PARITY.md#s02-room-transition-and-logic-load-boundaries-2026-11-06'}
                  if i in (18,19) else
                  {'policy':'Compare public literal/variable loader effects against CoCo, including duplicate loads, cache/list contents, resource errors, replay records and restoration of the active logic context.',
                   'reference':'WILDBITS-PARITY.md#s02-room-transition-and-logic-load-boundaries-2026-11-06'}
                  if i in (20,21) else
                  {'policy':'Match immediate quit and modal Enter/cancel outcomes. The terminal prompt now uses the CoCo Enter wording; Escape replaces CoCo CTRL-BREAK as the platform keep-playing key. Keep equivalence open until that key mapping is explicitly accepted and complete-game exit cleanup is covered.',
                   'reference':'WILDBITS-PARITY.md#s08-quit-command-comparison-2026-11-07'}
                  if i==134 else
                  {'policy':'Accept platform-specific joystick initialization: CoCo prompts for a button and supports Escape cancellation; Wild Bits enables/polls/disables the terminal driver service and reports unavailable hardware. Compare successful enable/disable state, caller continuation, and cleanup rather than identical prompts.',
                   'reference':'WILDBITS-PARITY.md#s06-initjoy-platform-interface-checkpoint-2026-11-07'}
                  if i==139 else
                  {'policy':'No semantic difference is accepted; compare against the CoCo body under this command\'s acceptance gate.',
                   'reference':'WILDBITS-PARITY.md#2-verify-semantics-behind-existing-routes'})
        boundary=('shared VM dispatch/operand core' if i<18 else
                  'Wild Bits platform backend' if any('/platform/wildbits-' in p for p in native_source) else
                  'shared/native handler')
        s01_semantic = ({'reference':'WILDBITS-PARITY.md#script-terminator-executor-case-2026-11-06',
                         'test':'check_logic_executor.py zero-terminator case',
                         'result':'PASS: both real owners return from a zero-terminated script with matching state, cursor, stack and code guards at two code bases'}
                        if gate=='S01' and i==0 else
                        {'reference':'WILDBITS-PARITY.md#scan-marker-handler-case-2026-11-06',
                         'test':'check_logic_executor.py check_scan_start',
                         'result':'PASS: both real owners set/reset scan markers for two distinct logic slots and preserve first-slot cache isolation at two code bases'}
                        if gate=='S01' and i in (145,146) else
                        {'reference':'WILDBITS-PARITY.md#flag-command-executor-case-2026-11-06',
                         'test':'check_logic_executor.py literal/variable flag-command case',
                         'result':'PASS: both real owners match set/reset/toggle state for literal and variable flag operands at two code bases'}
                        if gate=='S01' and i in (12,13,14,15,16,17) else
                        {'reference':'WILDBITS-PARITY.md#indirect-variable-command-case-2026-11-06',
                         'test':'check_logic_executor.py complete-script indirect-variable case',
                         'result':'PASS: both real owners match indirect read/write results through the full executor at variable indexes 0 and 255 and two code bases'}
                        if gate=='S01' and i in (9,10,11) else
                        {'reference':'WILDBITS-PARITY.md#random-handler-range-boundaries-2026-11-06',
                         'test':'check_random_command.py',
                         'result':'PASS: both real owners match all 256 source bytes across eleven inclusive, singleton and wrapping ranges at two code bases'}
                        if gate=='S01' and i==130 else
                        {'reference':'WILDBITS-PARITY.md#immediate-and-variable-arithmetic-executor-case-2026-11-06',
                         'test':'check_logic_executor.py immediate/variable arithmetic case',
                         'result':'PASS: both real owners match wrapped assignn/addn/assignv/addv/subn/subv checkpoints at two code bases'}
                        if gate=='S01' and i in (3,4,5,6,7,8) else
                        {'reference':'WILDBITS-PARITY.md#multiply-and-divide-handler-boundaries-2026-11-06',
                         'test':'check_math_commands.py',
                         'result':'PASS: both real owners match byte arithmetic across full dividends, boundary products/quotients, zero divisors, variable indices and aliasing at two code bases'}
                        if gate=='S01' and i in (165,166,167,168) else
                        {'reference':'WILDBITS-PARITY.md#increment-and-decrement-paired-executor-case-2026-11-06',
                         'test':'check_logic_executor.py paired increment/decrement case',
                         'result':'PASS: both real owners save 7, incremented 8, then decremented 7 at two code bases'}
                        if gate=='S01' and i in (1,2) else None)
        s03_flag_commands={45,46,56,61,62,64,65,66,67,68,70,71,72,73,74,75,
                           76,77,78,79,80,83,84,85,88,89}
        s02_semantic = ({'reference':'WILDBITS-PARITY.md#s02-public-view-resource-commands-2026-11-06',
                         'test':'check_view_cache_reload.py public load.view/discard.view commands',
                         'result':'PASS: both real owners execute public load.view/discard.view against original view 0, retain eight resident views, discard/reload and reuse a freed slot; command cursor, CoCo list and Wild Bits cache state checked'}
                        if gate=='S02' and i in (30,31,32,153) else
                        {'reference':'WILDBITS-PARITY.md#s02-replay-checkpoint-commands-2026-11-06',
                         'test':'check_replay_differential.py cmd.push.script/ReplaySaveCheckpoint',
                         'result':'PASS: both actual checkpoint commands save the current replay-record count; subsequent CoCo/native resource records remain byte-for-byte aligned at two load bases'}
                        if gate=='S02' and i==171 else
                        {'reference':'WILDBITS-PARITY.md#s02-replay-checkpoint-commands-2026-11-06',
                         'test':'check_replay_differential.py cmd.pop.script/ReplayRestore',
                         'result':'PASS: both actual restore commands rewind the replay write boundary; discarded records are overwritten and subsequent records/readback match at two load bases'}
                        if gate=='S02' and i==172 else
                        {'reference':'WILDBITS-PARITY.md#s02-replay-checkpoint-commands-2026-11-06',
                         'test':'check_replay_differential.py cmd.script.size/ReplayInitialize',
                         'result':'PASS: both actual initialization commands match at replay limits 0/1/3/255, reset counts/checkpoints and write position, preserve the owned buffer, consume the CoCo operand and preserve stack/guards at two bases'}
                        if gate=='S02' and i==142 else
                        {'reference':'WILDBITS-PARITY.md#s02-nested-logic-call-commands-2026-11-06',
                         'test':'check_logic_executor.py nested literal call and variable call.v scripts',
                         'result':'PASS: both real owners execute call/call.v through their actual command tables, restore nested caller cursors and depths, preserve child effects, return with balanced stack and script guards at two code bases'}
                        if gate=='S02' and i in (22,23) else
                        {'reference':'WILDBITS-PARITY.md#s02-resident-loadlogics-cache-hit-comparison-2026-11-07',
                         'test':'check_load_logic_cache_hit.py actual literal/variable load.logics handlers',
                         'result':'PASS: actual literal/variable CoCo and Wild Bits load.logics handlers find resident logic and match replay entries; actual native miss-then-hit loads record each request exactly once; caller context, cache links, stacks and guards pass at two code addresses'}
                        if gate=='S02' and i in (20,21) else None)
        s02_semantic = s02_semantic or ({'reference':'WILDBITS-PARITY.md#s02-room-command-transition-and-failure-checkpoint-2026-11-07',
                         'test':'check_room_commands.py public room commands, completed transitions, destination/root continuation, room zero, and retry/error paths',
                         'result':'PASS: actual literal/variable commands match room-entry and destination/root effects for ordinary and zero rooms; controlled CoCo synchronous and Wild Bits safe-point timing is documented; actual second volume reads succeed after injected first-attempt seek/read errors, and native Enter/Escape UI retry/quit cleanup passes'}
                        if gate=='S02' and i in (18,19) else s02_semantic)
        s03_semantic = ({'reference':'WILDBITS-PARITY.md#s03-view-query-command-checkpoint-2026-11-06',
                         'test':'check_view_queries.py',
                         'result':'PASS: both real owners match all five view-query fields across 5140 calls at two code bases with record and argument guards'}
                        if gate=='S03' and i in (49,50,51,52,53) else
                        {'reference':'WILDBITS-PARITY.md#s03-object-distance-command-checkpoint-2026-11-06',
                         'test':'check_object_distance.py',
                         'result':'PASS: both real owners match the shared distance command for visible/invisible objects, reversed coordinates and saturation boundaries across 24 actual calls'}
                        if gate=='S03' and i==69 else
                        {'reference':'WILDBITS-PARITY.md#s03-view-loop-and-cel-selector-checkpoint-2026-11-06',
                         'test':'check_view_cache_reload.py literal/variable selectors',
                         'result':'PASS: both real owners match view, loop, cel counts and dimensions after each of six literal/variable selector commands using original view data'}
                        if gate=='S03' and i in (41,42,43,44,47,48) else
                        {'reference':'WILDBITS-PARITY.md#s03-unanimate-all-command-checkpoint-2026-11-06',
                         'test':'check_object_block_state.py opcode-34 whole command',
                         'result':'PASS: both real owners clear animated/visible bits across all 64 records with all other fields, stack and record guards preserved'}
                        if gate=='S03' and i==34 else
                        {'reference':'WILDBITS-PARITY.md#s03-object-flag-and-cycle-command-checkpoint-2026-11-06',
                         'test':'check_object_flags.py global block/unblock commands',
                         'result':'PASS: both real owners match block/unblock enable and all four rectangle coordinates across three boundary rectangles'}
                        if gate=='S03' and i in (90,91) else
                        {'reference':'WILDBITS-PARITY.md#s03-coordinate-and-animation-command-checkpoint-2026-11-06',
                         'test':'check_object_coordinates.py',
                         'result':'PASS: both real owners match object coordinate, animation and reposition fields at two load bases, including variable aliases and boundary values'}
                        if gate=='S03' and i in (33,37,38,39,40,147,148) else
                        {'reference':'WILDBITS-PARITY.md#s03-object-flag-and-cycle-command-checkpoint-2026-11-06',
                         'test':'check_object_flags.py',
                         'result':'PASS: both real owners match tested object flag, cycle, motion and follow/wander setup field transitions with record and stack guards'}
                        if gate=='S03' and i in s03_flag_commands else
                        {'reference':'WILDBITS-PARITY.md#s03-stop-start-update-command-checkpoint-2026-11-06',
                         'test':'check_object_update_control.py',
                         'result':'PASS: both real owners match stop.update/start.update transitions for every initial flag byte at four object indexes and two code bases; CoCo draw-range MMU maintenance is explicitly stubbed'}
                        if gate=='S03' and i in (58,59) else
                        {'reference':'WILDBITS-PARITY.md#s03-force-update-command-checkpoint-2026-11-06',
                         'test':'check_force_update.py plus check_wbplay.py frame capture',
                         'result':'PASS: both real owners preserve object state and execute their refresh-service sequence at two code bases; loaded-game frame capture confirms force.update does not advance motion/cels or change sprite pixels'}
                        if gate=='S03' and i==60 else
                        {'reference':'WILDBITS-PARITY.md#s03-draw-and-erase-command-checkpoint-2026-11-06',
                         'test':'check_object_visibility.py plus check_wbgame.py sprite pixels',
                         'result':'PASS: both real owners match public draw/erase state transitions including idempotence, stopped-visible state and clearing the single-advance flag; CoCo hardware services are stubbed for state comparison and game-level pixels are checked separately'}
                        if gate=='S03' and i in (35,36) else
                        {'reference':'WILDBITS-PARITY.md#s03-object-flag-and-cycle-command-checkpoint-2026-11-06',
                         'test':'check_object_scalar_commands.py',
                         'result':'PASS: both real owners match priority/direction fields, variable effects and set.horizon legal boundaries across 7208 actual calls at two code bases'}
                        if gate=='S03' and i in (54,55,57,63,86,87) else
                        {'reference':'WILDBITS-PARITY.md#s03-object-flag-and-cycle-command-checkpoint-2026-11-06',
                         'test':'check_motion_setup.py',
                         'result':'PASS: both real owners match move.obj setup fields, speed, flags and callback context at two code bases'}
                        if gate=='S03' and i in (81,82) else None)
        s04_semantic = ({'reference':'WILDBITS-PARITY.md#s04-custom-priority-base-command-checkpoint-2026-11-07',
                         'test':'check_priority_bands.py actual CoCo SetPriBaseStub and Wild Bits AuxPrioritySet plus pixel/sprite projection checks',
                         'result':'PASS: public CoCo set-pri-base stub and native setter match for every legal base 0..167; all 168 CoCo priority rows and native transition/boundary rows agree, invalid native bases preserve state, and actual overlapping sprites sort by the resulting projected priorities'}
                        if gate=='S04' and i==174 else
                        {'reference':'WILDBITS-PARITY.md#s04-picture-and-sprite-evidence-2026-10-19',
                         'test':'check_add_to_picture.py actual CoCo cmd_add_to_pic/cmd_add_to_pic_v through AddToPicImpl and CoCo ObjAddPicPri/ObjBlit; paired Wild Bits pixel oracle',
                         'result':'PASS: 52 Wild Bits scenarios and 104 actual CoCo command calls; 36 actual AddToPicImpl calls for immediate/variable default-priority cases dispatch to CoCo ObjAddPicPri/ObjBlit and match the paired pixels; 53 standalone CoCo renderer pixel comparisons. The fixture stubs MMU mapping and range/page services.'}
                        if gate=='S04' and i in (122,123) else
                        {'reference':'WILDBITS-PARITY.md#s04-opcode-110-coco-stub-checkpoint-2026-11-06',
                         'test':'check_logic_executor.py opcode-110 CoCo-stub case plus check_native_dispatch.py route matrix',
                         'result':'PASS: direct CoCo opcode-110 target consumes its literal operand; the native command table consumes the corresponding operand and executes the following assignment with matching variables/flags at two code bases'}
                        if gate=='S04' and i==110 else
                        {'reference':'WILDBITS-PARITY.md#s04-text-screen-and-graphics-mode-checkpoint-2026-11-06',
                         'test':'check_text_graphics_mode.py actual CoCo handlers plus check_wbgame.py native text/graphics pixel matrix',
                         'result':'PASS: CoCo text.screen/graphics select text/graphics MMU pages without clearing the picture buffer; Wild Bits actual logic preserves the 320x240 picture under text cells, clears overlay cells on graphics return and matches mode state'}
                        if gate=='S04' and i in (106,107) else None)
        s04_semantic = s04_semantic or ({'reference':'WILDBITS-PARITY.md#s04-monitor-toggle-checkpoint-2026-11-06',
                         'test':'check_monitor_command.py CoCo palette writes plus check_wbgame.py Wild Bits palette/profile scenarios',
                         'result':'PASS: actual CoCo toggle-monitor emits all 16 indexed palette writes for both mode transitions and toggles its monitor byte; Wild Bits profile selection reproduces the CoCo RGB palette while preserving picture indices and terminal ownership'}
                        if gate=='S04' and i==140 else None)
        s04_semantic = s04_semantic or ({'reference':'WILDBITS-PARITY.md#s04-picture-load-draw-and-show-checkpoint-2026-11-06',
                         'test':'check_picture_stream.py actual load.pic/draw.pic/show.pic script versus CoCo shdw.RenderPic',
                         'result':'PASS: the real Wild Bits opcode 24/25/26 script matches the CoCo shdw.RenderPic frame for 23 original large packed KQ4/SQ0 pictures and ten streamed boundary fixtures; malformed streams and map/unmap failures are rejected, and following logic resumes'}
                        if gate=='S04' and i in (24,25,26) else
                        {'reference':'WILDBITS-PARITY.md#s04-picture-load-draw-and-show-checkpoint-2026-11-06',
                         'test':'check_picture_stream.py actual load/draw/overlay/show logic versus CoCo-rendered base and overlay buffers',
                         'result':'PASS: actual Wild Bits overlay.pic retains the base picture and matches the complete 26,880-byte visual/priority composition of two CoCo shdw.RenderPic outputs; displayed pixels match and the following logic command resumes'}
                        if gate=='S04' and i==28 else
                        {'reference':'WILDBITS-PARITY.md#s04-discard-picture-single-node-unlink-checkpoint-2026-11-06',
                         'test':'check_resource_lifetime.py actual CoCo cmd_discard_pic and Wild Bits GameDiscardPicture',
                         'result':'PASS: actual public commands discard first, middle and last loaded pictures at two code bases; the CoCo linked list retains successors, and the native typed cache releases only the selected slot while preserving neighboring slots, guards and stack'}
                        if gate=='S04' and i==27 else
                        {'reference':'WILDBITS-PARITY.md#s04-clear-text-rectangle-checkpoint-2026-11-06',
                         'test':'check_text_rect.py actual CoCo cmd_clear_text_rect and native script',
                         'result':'PASS: rendered CoCo and Wild Bits text cells/attributes match for colors, clipping, row-23 boundary, column-40 spill and caller state; the CoCo inverted-row non-return remains a separately bounded legacy defect'}
                        if gate=='S04' and i==154 else None)
        s06_semantic = ({'reference':'WILDBITS-PARITY.md#s06-enable-and-disable-menu-items-checkpoint-2026-11-07',
                         'test':'check_wbgame.py actual CoCo cmd_enable_item/cmd_disable_item plus Wild Bits MenuCommand and loaded menu selection',
                         'result':'PASS: both actual command handlers toggle duplicate action codes consistently across enabled menu entries at two code bases; absent actions are harmless, operands and stacks balance, and loaded Wild Bits selects an item after disable then re-enable'}
                        if gate=='S06' and i in (159,160) else
                        {'reference':'WILDBITS-PARITY.md#s06-menu-construction-checkpoint-2026-11-07',
                         'test':'check_wbgame.py actual CoCo and loaded Wild Bits menu construction handlers',
                         'result':'PASS: actual CoCo set.menu/set.menu.item/submit.menu lists and loaded Wild Bits opcodes 156/157/158 normalize to the same two titles, three ordered actions, labels and enabled states; selected first action resumes the script'}
                        if gate=='S06' and i in (156,157,158) else
                        {'reference':'WILDBITS-PARITY.md#s06-inventory-command-state-checkpoint-2026-11-06',
                         'test':'check_inventory_commands.py actual CoCo/native inventory command handlers',
                         'result':'PASS: both owners match get/get.v/drop/put/put.v/get.room.v state effects at two code bases across item, variable and room boundaries; native invalid-item errors preserve private state and stack'}
                        if gate=='S06' and i in (92,93,94,95,96,97) else None)
        s06_semantic = s06_semantic or ({'reference':'WILDBITS-PARITY.md#s06-clear-lines-checkpoint-2026-11-06',
                         'test':'check_text_rect.py CoCo clear.lines request and check_wbgame.py Wild Bits framebuffer colors',
                         'result':'PASS: CoCo cmd_clear_lines clears inclusive full-width rows for both boolean colors, consumes all operands and restores cursor/attribute; Wild Bits loaded-game pixels match both colors and persist through the next logic cycle'}
                        if gate=='S06' and i==105 else None)
        s06_semantic = s06_semantic or ({'reference':'WILDBITS-PARITY.md#s06-cancel-and-echo-command-checkpoint-2026-11-06',
                         'test':'check_cancel_line.py actual CoCo/native cancel.line and echo.line command bodies',
                         'result':'PASS: CoCo cmd_cancel_line/cmd_echo_line match Wild Bits GameCancelLine/GameEchoLine input-enabled state, cancel-to-empty and typed-prefix/history-suffix results through 38 bytes at two code bases; only CoCo MMU character output is stubbed'}
                        if gate=='S06' and i in (137,138) else None)
        s06_semantic = s06_semantic or ({'reference':'WILDBITS-PARITY.md#s06-set-key-checkpoint-2026-11-07',
                         'test':'check_set_key.py actual CoCo CmdSetKey/RemapKeyEvent and Wild Bits SetKeyCommand/GameKeyBinding',
                         'result':'PASS: both owners append duplicate bindings, dispatch the first matching key, and silently ignore binding 51; actual command storage and event behavior match at two code bases'}
                        if gate=='S06' and i==121 else None)
        s06_semantic = s06_semantic or ({'reference':'WILDBITS-PARITY.md#s06-initjoy-platform-interface-checkpoint-2026-11-07',
                         'test':'check_init_joy.py CoCo command plus check_wbgame_previews_mame.py --joystick Wild Bits driver path',
                         'result':'PASS: CoCo enable/button, Escape-cancel, disable and event-clear state pass at two code bases; Wild Bits Jr2 MAME enables SS.Joy, polls neutral samples, disables and resumes the caller, and returns process memory to baseline under the documented available/unavailable-service policy'}
                        if gate=='S06' and i==139 else None)
        s06_semantic = s06_semantic or ({'reference':'WILDBITS-PARITY.md#s06-getstring-checkpoint-2026-11-07',
                         'test':'check_get_string.py actual CoCo cmd_get_string plus native GameGetInput modal editor',
                         'result':'PASS: actual CoCo cmd_get_string selects the prompt, forwards slot and bounded length to EditString, clears the target, consumes five operands and balances the stack; native get.string renders the prompt and matches slot commit, backspace, maximum-length and Escape behavior while restoring the suspended command line'}
                        if gate=='S06' and i==115 else None)
        s06_semantic = s06_semantic or ({'reference':'WILDBITS-PARITY.md#s06-getnum-checkpoint-2026-11-07',
                         'test':'check_get_number.py actual CoCo CmdObjStatus plus native opcode 118 modal input',
                         'result':'PASS: both real command paths store matching results for blank, 0, 255, 256 and 999; CoCo consumes the prompt and variable operands, and both return with balanced state and modal input cleared'}
                        if gate=='S06' and i==118 else None)
        s06_semantic = s06_semantic or ({'reference':'WILDBITS-PARITY.md#s06-menu-input-request-checkpoint-2026-11-07',
                         'test':'check_wbgame.py actual CoCo menu_input request/event loop plus loaded Wild Bits opcode 161',
                         'result':'PASS: CoCo menu_input and Wild Bits opcode 161 defer display until the current script finishes; flag-14 permission, visibility, room retention, selection and cancellation paths are exercised with balanced caller continuation'}
                        if gate=='S06' and i==161 else None)
        s06_semantic = s06_semantic or ({'reference':'WILDBITS-PARITY.md#s06-close-window-rendered-restoration-checkpoint-2026-11-07',
                         'test':'check_persistent_window.py actual CoCo handler plus check_coco_kq4_inventory_mame.py rendered popup dismissal and check_wbgame_mame.py Wild Bits restoration',
                         'result':'PASS: CoCo close.window direct handler guards and actual KQ4 look popup dismissal are checked; the restored CoCo display retains its 16-color scene, and Wild Bits modal dismissal restores the rendered game scene'}
                        if gate=='S06' and i==169 else None)
        s06_semantic = s06_semantic or ({'reference':'WILDBITS-PARITY.md#s06-interpreter-information-2026-11-07',
                         'test':'check_wbgame.py actual CoCo CmdShowAgiInfo message_box text plus loaded Wild Bits opcode 141 modal',
                         'result':'PASS: CoCo CmdShowAgiInfo passes the exact Adventure Game Interpreter / Version 2.072 message through message_box at two code bases; loaded Wild Bits shows the same text, dismisses, resumes its caller and preserves held/timed print state through 16 nested calls'}
                        if gate=='S06' and i==141 else None)
        s06_semantic = s06_semantic or ({'reference':'WILDBITS-PARITY.md#s06-input-acceptance-checkpoint-2026-11-06',
                         'test':'check_screen_input.py actual CoCo handlers plus check_wbgame.py native screen backend',
                         'result':'PASS: both owners set the input-acceptance state for prevent.input/accept.input at two CoCo code bases and the native screen-backend logic checkpoint; repeated transitions return with balanced stack'}
                        if gate=='S06' and i in (119,120) else None)
        s06_semantic = s06_semantic or ({'reference':'WILDBITS-PARITY.md#s06-status-line-checkpoint-2026-11-06',
                         'test':'check_status_line_commands.py CoCo entry points plus check_wbgame.py status-line pixels',
                         'result':'PASS: actual CoCo status.line.on/off set the enabled state and request row draw/clear at two code bases; loaded Wild Bits status pixels, row selection, disable and live update match the tested visible effects'}
                        if gate=='S06' and i in (112,113) else None)
        s06_semantic = s06_semantic or ({'reference':'WILDBITS-PARITY.md#s06-player-control-checkpoint-2026-11-06',
                         'test':'check_player_control.py actual CoCo/Wild Bits program.control and player.control handlers',
                         'result':'PASS: both owners match program.control/player.control control flags; player.control also resets ego motion type while preserving direction, guards and stack'}
                        if gate=='S06' and i in (131,132) else None)
        s06_semantic = s06_semantic or ({'reference':'WILDBITS-PARITY.md#s06-original-kq4-inventory-status-checkpoint-2026-11-07',
                         'test':'check_coco_kq4_inventory_mame.py and check_kq4_mame.py original KQ4 menu Inventory action',
                         'result':'PASS: original KQ4 Inventory opens as an opaque black/white full-page status screen on both platforms and a fresh key restores the game scene; Wild Bits also verifies the exact empty-inventory and dismissal prompts, while CoCo pixels and surrounding-scene restoration are checked independently'}
                        if gate=='S06' and i==124 else None)
        s07_semantic = ({'reference':'WILDBITS-PARITY.md#s07-load-sound-command-checkpoint-2026-11-07',
                         'test':'check_native_audio.py actual CoCo cmd_load_sound plus Wild Bits opcode 98 cache and playback comparison',
                         'result':'PASS: actual CoCo cmd_load_sound loads the sound record and reuses its node without extra volume reads; Wild Bits opcode 98 publishes one kind-3 cache entry across duplicate requests and playback matches the CoCo note packets'}
                        if gate=='S07' and i==98 else
                        {'reference':'WILDBITS-PARITY.md#s07-sound-command-checkpoint-2026-11-07',
                         'test':'check_native_audio.py actual CoCo cmd_sound/PlaySound plus loaded Wild Bits opcode 99 event stream and completion flag',
                         'result':'PASS: actual CoCo cmd_sound runs PlaySound over the resident note stream and sets its completion flag; loaded Wild Bits opcode 99 emits matching note/end packets and sets the flag after playback completes'}
                        if gate=='S07' and i==99 else
                        {'reference':'WILDBITS-PARITY.md#s07-stopsound-command-checkpoint-2026-11-07',
                         'test':'check_logic_executor.py opcode-100 CoCo/native no-op case plus check_native_audio.py active playback case',
                         'result':'PASS: actual CoCo opcode 100 consumes no operands and resumes the next command; Wild Bits opcode 100 leaves active playback and its completion flag intact, matching the CoCo no-op while internal exit cleanup remains available'}
                        if gate=='S07' and i==100 else
                        {'reference':'WILDBITS-PARITY.md#s07-pause-command-checkpoint-2026-11-06',
                         'test':'check_pause_command.py CoCo command plus check_wbgame.py native pause/clock behavior',
                         'result':'PASS: actual CoCo pause clears queued events, displays the paused message while clock state is paused, then restores the clock; Wild Bits loaded pause waits for dismissal and re-bases its clock'}
                        if gate=='S07' and i==136 else None)
        s05_semantic = ({'reference':'WILDBITS-PARITY.md#s05-cursor-character-checkpoint-2026-11-06',
                         'test':'check_cursor_char.py CoCo message-table handler plus check_wbgame.py native screen backend',
                         'result':'PASS: both owners select the first byte of the requested logic message as the cursor character; valid message lookup, operand consumption and invalid native message cleanup are verified'}
                        if gate=='S05' and i==108 else None)
        s05_semantic = s05_semantic or ({'reference':'WILDBITS-PARITY.md#s05-literal-and-variable-print-checkpoint-2026-11-07',
                         'test':'check_text_command_entry.py actual CoCo print handlers plus check_wbgame.py loaded literal/variable print and check_kq4_mame.py original popup/restoration',
                         'result':'PASS: actual CoCo print/print.v resolve literal or variable messages to the same message_box interface with one operand consumed and balanced stack; loaded Wild Bits tests exercise both commands, original KQ1 death-message branches verify white-on-black popup colors, and original KQ4 MAME verifies the centered popup, retained scene and dismissal restoration'}
                        if gate=='S05' and i in (101,102) else None)
        s05_semantic = s05_semantic or ({'reference':'WILDBITS-PARITY.md#s05-literal-and-variable-print-checkpoint-2026-11-07',
                         'test':'check_text_command_entry.py actual CoCo display handlers plus check_wbgame.py native literal/variable text pixels',
                         'result':'PASS: actual CoCo display/display.v format the selected message and hand identical text plus requested row/column to PrintFmtStrToScr with balanced cursor restoration; loaded Wild Bits display/display.v fixtures match exact glyph pixels/colors across a row boundary and preserve them through show.pic'}
                        if gate=='S05' and i in (103,104) else None)
        s05_semantic = s05_semantic or ({'reference':'WILDBITS-PARITY.md#s05-parse-command-checkpoint-2026-11-07',
                         'test':'check_parse_command.py actual CoCo cmd_parse plus check_wbparser.py native dictionary and check_wbgame.py original parsed encounters',
                         'result':'PASS: CoCo cmd_parse selects the requested 40-byte string, tokenizes it against indexed words.tok, stores the expected word-ID/noun-pointer tables and flags, consumes one operand, and safely rejects an invalid slot; native streaming parser and original KQ1 parse/said encounters are exercised through the loaded game'}
                        if gate=='S05' and i==117 else None)
        s05_semantic = s05_semantic or ({'reference':'WILDBITS-PARITY.md#s05-literal-and-variable-print-checkpoint-2026-11-07',
                         'test':'check_text_command_entry.py actual CoCo positioned-print handlers plus check_wbgame.py loaded print.at/print.at.v cell output',
                         'result':'PASS: actual CoCo print.at/print.at.v resolve literal or variable messages, pass requested row/column/height through message_box and reset the override; loaded Wild Bits fixtures compare positioned text cells, wrapping, clipping, invalid coordinates and return to default print geometry'}
                        if gate=='S05' and i in (151,152) else None)
        s05_semantic = s05_semantic or ({'reference':'WILDBITS-PARITY.md#s05-cursor-character-checkpoint-2026-11-06',
                         'test':'check_cursor_char.py CoCo message-table handler plus check_wbgame.py native screen backend',
                         'result':'PASS: both owners select the first byte of the requested logic message as the cursor character; valid message lookup, operand consumption and invalid native message cleanup are verified'}
                        if gate=='S05' and i==108 else None)
        s05_semantic = s05_semantic or ({'reference':'WILDBITS-PARITY.md#s05-text-attribute-checkpoint-2026-11-06',
                         'test':'check_text_attribute.py CoCo handler plus check_wbgame.py native screen backend',
                         'result':'PASS: actual CoCo set.text.attribute packs the tested foreground/background nibbles and consumes operands; the loaded native screen-backend comparison stores the same values and rejects out-of-range colors'}
                        if gate=='S05' and i==109 else None)
        s05_semantic = s05_semantic or ({'reference':'WILDBITS-PARITY.md#s05-string-slot-and-word-to-string-checkpoint-2026-11-06',
                         'test':'check_string_slots.py actual CoCo/native set.string and word.to.string handlers',
                         'result':'PASS: the actual CoCo and Wild Bits owners match set.string destination-slot writes and word.to.string destination/index operand order; boundaries through 80 bytes terminate within the 40-byte slot and preserve adjacent slots/variables at two code bases'}
                        if gate=='S05' and i in (114,116) else None)
        s08_semantic = ({'reference':'WILDBITS-PARITY.md#s08-setgameid-command-checkpoint-2026-11-07',
                         'test':'check_game_id.py actual CoCo cmd_set_game_id and loaded Wild Bits opcode 143',
                         'result':'PASS: actual CoCo cmd_set_game_id and loaded Wild Bits opcode 143 match empty, short, exact-seven, truncated, and high-bit message IDs across 7 cases; CoCo operand, stack and code guards checked at two code bases'}
                        if gate=='S08' and i==143 else None)
        semantic = s01_semantic or s02_semantic or s03_semantic or s04_semantic or s05_semantic or s06_semantic or s07_semantic or s08_semantic
        equivalence_reference=(semantic['reference'] if semantic else
                               'WILDBITS-PARITY.md#1-close-the-command-coverage-inventory'
                               if gate in ('C01','C02','C03','C04','C05','C06','C07') else
                               'WILDBITS-PARITY.md#c08-c12-coco-stub-decisions'
                               if gate in ('C08','C09','C10','C11','C12') else None)
        equivalence=('PASS: accepted command-level CoCo/native evidence' if equivalence_reference else 'open')
        focused = ({'reference':'WILDBITS-PARITY.md#s06-configscreen-all-offset-modal-preview-checkpoint-2026-11-08',
                    'test':'check_screen_config.py actual CoCo cmd_config_screen and MsgBoxColCalc at two code bases plus Wild Bits ScreenConfigure; check_trace.py; check_wbgame.py loaded all-five-offset show.obj modal previews',
                    'result':'PASS: 94 screen-config calls (76 CoCo command/helper and 18 Wild Bits owner cases); CoCo CalcMenuItemGeometry is verified for 4 item counts and offsets 0..4 at two bases; CoCo malformed bytes wrap while Wild Bits rejects them atomically; all-five-offset trace/popup behavior passes; paired AGI dropdown geometry and policy acceptance remain open'}
                   if gate=='S06' and i==111 else
                   {'reference':'WILDBITS-PARITY.md#s08-exact-state-write-transfer-checkpoint-2026-11-08',
                    'test':'check_wbstate_transfer.py actual sierrastate StateWriteExact with injected OS-9 I$Write results',
                    'result':'PASS: sierrastate retries valid short writes, completes a full transfer, rejects zero and over-reported byte counts, and propagates OS-9 write errors; actual StateBegin preserves E$Full from create/write failures and requests close/delete only after an opened incomplete save, with balanced stack/data guards; original KQ1 MAME quest-save route writes a snapshot, reloads it through the File Restore menu, reaches the ending and verifies checkpoint metadata; full-disk UI, command-level cancellation and CoCo/native equivalence remain open'}
                   if gate=='S08' and i==125 else None)
        focused = focused or ({'reference':'WILDBITS-PARITY.md#s08-coco-automatic-restart-and-normalized-outcome-comparison-2026-11-08',
                    'test':'check_wbgame.py actual CoCo cmd_restart_game branches, nested root->call->restart execution, and loaded Wild Bits check_restarts matrix',
                    'result':'PASS: CoCo confirms manual cancellation at two code bases, manual confirmation and automatic prompt bypass; nested root->call->restart dispatch/unwind passes reset-dispatch, room-change, score, timer, caller-continuation, root-context and stack checks; Wild Bits matches tested decisions at maximum nested depth and long root path; original KQ1 MAME File Restart route confirms, resets position, resumes movement and restores the exact free-memory map; reset-service effects and CoCo/native equivalence remain open'}
                   if gate=='S08' and i==128 else None)
        focused = focused or ({'reference':'WILDBITS-PARITY.md#s08-real-driver-restore-rejection-checkpoint-2026-11-08',
                    'test':'check_wbpic_mame.py --native-game sierra/kingsquest4 --interpreter --persistence with the real Wild Bits Jr2 MAME drivers',
                    'result':'PASS: actual restore rejects an invalid field count, wrong-game ID, bad CRC and truncated state without changing the displayed scene; both terminals exit and relaunch with the original free-memory map; original KQ1 MAME File Restore route accepts its filename prompt, restores the saved position, continues play and preserves the free-memory map; CoCo error-dialog equivalence and CoCo/native equivalence remain open'}
                   if gate=='S08' and i==126 else None)
        focused = focused or ({'reference':'WILDBITS-PARITY.md#s06-showobj-command-boundary-comparison-2026-11-07',
                    'test':'check_wbgame.py check_object_previews plus check_coco_show_object actual CoCo literal/variable command handlers',
                    'result':'PASS: loaded Wild Bits literal/variable show.obj paths verify selected view, description, preview pixels, popup text, scene restoration, cache and malformed-resource cleanup; actual CoCo handlers verify matching view selection and description, operand consumption, redraw-flag restoration and stack guards at two code bases; rendered CoCo sprite parity remains open'}
                   if gate=='S06' and i in (129,162) else None)
        focused = focused or ({'reference':'WILDBITS-PARITY.md#s08-quit-command-comparison-2026-11-07',
                    'test':'check_quit_command.py paired actual CoCo cmd_quit and Wild Bits GameQuitCommand calls at two code bases',
                    'result':'PASS: six paired calls verify Enter quit, Escape cancel, immediate quit without prompt, caller stack/operand/private-state guards and immutable code; CoCo uses CTRL-BREAK to keep playing while Wild Bits uses Escape; command-level behavior passes, complete-game exit cleanup and explicit mapping acceptance remain open'}
                   if gate=='S08' and i==134 else None)
        rows.append({'opcode':i,**command,'effective_native_handler':'ExecuteLogic core' if i<18 else command['native_handler'],
            'route_status':status,'acceptance_gate':gate,
            'reference_source_files':reference_sources[command['coco_handler']],
            'native_source_files':native_source,'component_boundary':boundary,
            'behavior_decision':decision,
            'route_test':'check_native_dispatch.py',
            'route_test_result':'PASS: all 256 opcodes in game/probe at two load addresses; route destination, argument table, preserved registers/stack and unsupported policy checked',
            'candidate_regressions':candidates.get(gate,['check_logic_executor.py','check_native_dispatch.py'] if gate in ('C08','C09','C10','C11','C12') else []),
            'equivalence_result':equivalence,'equivalence_reference':equivalence_reference,
            **({'focused_evidence':focused} if focused else {}),
            **({'semantic_test':semantic['test'],
                'semantic_test_result':semantic['result']} if semantic else {})})
    names=re.findall(r'^\s*AGI_TEST\s+([^,]+),', (ROOT/'objs/shared/agi-test-table.asm').read_text(),re.M)
    predicate_native={0:'VmTrue',**{i:name.strip() for i,name in enumerate(names) if 1<=i<=8},
                      9:'InventoryTest',10:'InventoryTest',
                      11:'ObjectPositionTest',16:'ObjectPositionTest',
                      17:'ObjectPositionTest',18:'ObjectPositionTest',
                      12:'InputControllerTest',13:'InputHaveKeyTest',
                      14:'InputSaidTest',15:'StringCompareTest'}
    predicates=[]
    for i,name in enumerate(names):
        reference_source=source_hits(name.strip(),reference_files,macro_call=True)
        native_handler=predicate_native[i]
        native_source=source_hits(native_handler,native_files)
        gate='S01' if i<=8 else 'S05' if i in (14,15) else 'S03' if i in (11,16,17,18) else 'S06'
        decision=({'policy':'Predicate zero is CoCo RetTrue; native command zero remains script return.',
                   'reference':'WILDBITS-PARITY.md#predicate-zero-command-versus-condition'}
                  if i==0 else
                  {'policy':'No semantic difference is accepted; compare predicate behavior against CoCo under this gate.',
                   'reference':'WILDBITS-PARITY.md#2-verify-semantics-behind-existing-routes'})
        predicates.append({'predicate':i,'coco_handler':name.strip(),'operands':tests[i],
            'reference_source_files':reference_source,'native_source_files':native_source,
            'acceptance_gate':gate,'native_handler':native_handler,
            'behavior_decision':decision,
            'predicate_test':('check_coco_conditions.py direct CoCo/native handlers' if 1<=i<=8 else
                              'check_inventory_commands.py direct CoCo/native predicate handlers' if i in (9,10) else
                              'check_controller_predicate.py direct CoCo/native handlers' if i==12 else
                              'check_have_key_predicate.py direct handlers plus check_wbgame.py fresh-key wait' if i==13 else
                              'check_said.py actual CoCo/native predicate handlers' if i==14 else
                              'check_string_compare.py actual CoCo/native predicate handlers' if i==15 else
                              'check_object_position_predicates.py direct CoCo/native handlers' if i in (11,16,17,18) else
                              'check_coco_conditions.py, check_condition_flow.py, check_logic_executor.py and predicate-specific focused tests'),
            'predicate_test_result':('PASS: both real owners match 1,728 actual unsigned-comparison and packed-flag predicate calls at two load bases, including all flag indexes 0..255, variable indexes 0/255 and cursor/state/stack/code guards' if 1<=i<=8 else
                                     'PASS: both real owners match possession and room predicates at two load bases; first/last item and variable indexes, room boundaries, operand/cursor/state/stack guards and invalid native item rejection checked' if i in (9,10) else
                                     'PASS: both real owners match 1,536 controller-predicate calls over all 256 controller values with true/false states, signed CoCo key-table offsets, native bit mapping and cursor/stack/guard/code checks' if i==12 else
                                     'PASS: actual CoCo pending-key/fresh-key results, zero-event false and retry after the $FF no-key sentinel; actual native pending-key boolean; check_wbgame.py covers cleared-v19 modal wait and graphics/input restoration' if i==13 else
                                     'PASS: both real owners match said predicate behavior with exhaustive byte folding, wildcard/mismatch/length cases, input/accepted gates, cursor guards and one-time acceptance through native opcode dispatch' if i==14 else
                                     'PASS: both real owners match string comparison across all 255 non-NUL byte classes, punctuation/length/slot boundaries, native index errors and loaded IF dispatch' if i==15 else
                                     'PASS: both real owners match 3,200 position-predicate calls for posn/box/center/right; edge objects, byte-coordinate and width wrap, inclusive rectangle edges, unchanged records and operand/stack/code guards checked' if i in (11,16,17,18) else
                                     'PASS: all 19 CoCo predicate-table addresses relocate; native focused predicate behavior is covered by condition-flow, executor, said, inventory, object-position and string-comparison regressions; remaining semantic cases stay open by gate'),
            'candidate_regressions':['check_logic_executor.py'] if i==0 else
                                    ['check_coco_conditions.py','check_condition_flow.py'] if 1<=i<=8 else
                                    ['check_have_key_predicate.py','check_wbgame.py'] if i==13 else candidates[gate],
            'equivalence_result':('constant-true/NOT/OR/AND/skip full-executor comparison' if i==0 else
                                  'PASS: actual CoCo/native unsigned comparison and packed-flag predicates' if 1<=i<=8 else
                                  'PASS: actual CoCo/native possession and room predicates' if i in (9,10) else
                                  'PASS: actual CoCo/native controller predicate' if i==12 else
                                  'PASS: actual CoCo/native have.key result; cleared-key wait verified in integration' if i==13 else
                                  'PASS: actual CoCo/native said predicate' if i==14 else
                                  'PASS: actual CoCo/native string predicate' if i==15 else
                                  'PASS: actual CoCo/native position predicates' if i in (11,16,17,18) else 'open'),
            'equivalence_reference':('WILDBITS-PARITY.md#predicate-zero-command-versus-condition' if i==0 else
                                     'WILDBITS-PARITY.md#s01-unsigned-comparison-and-packed-flag-predicates-2026-11-06' if 1<=i<=8 else
                                     'WILDBITS-PARITY.md#s06-inventory-predicate-checkpoint-2026-11-06' if i in (9,10) else
                                     'WILDBITS-PARITY.md#s06-controller-predicate-checkpoint-2026-11-06' if i==12 else
                                     'WILDBITS-PARITY.md#s06-havekey-predicate-checkpoint-2026-11-06' if i==13 else
                                     'WILDBITS-PARITY.md#s05-said-predicate-checkpoint-2026-11-06' if i==14 else
                                     'WILDBITS-PARITY.md#s05-string-predicate-checkpoint-2026-11-06' if i==15 else
                                     'WILDBITS-PARITY.md#s03-object-position-predicate-checkpoint-2026-11-06' if i in (11,16,17,18) else None)})
    return {'limits':['Candidate regression names identify where to verify behavior; they are not proof that every command is already tested or equivalent.',
                       'Predicate zero is the verified CoCo constant-true entry; native command zero remains script return.'],
            'command_catalog_sha256':hashlib.sha256((ROOT/'objs/shared/agi-command-table.asm').read_bytes()).hexdigest(),
            'commands':rows,'predicates':predicates}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,default=ROOT/'kingsquest1')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--all-games',action='store_true',help='audit every bundled words.tok directory')
    parser.add_argument('--output-dir',type=Path,help='directory for all-game reports and summary')
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:
        # One code byte, two offsets (second absent), then plain/encrypted text.
        message = b"%%g1 %x2 %o3 %v7|2 %s1 %w2 %m4 %g4 %v\0"
        header = b"\x01\0\0\x02" + (6+len(message)).to_bytes(2, "little") + b"\x06\0\0\0"
        expected = [{"message":1,"offset":5,"directive":"x","operand":"2","reason":"unknown directive"},
                    {"message":1,"offset":35,"directive":"v","operand":"","reason":"missing operand"}]
        assert message_formats(header+message, False) == expected
        assert message_format_samples(header+message, False) == [b"%x2", b"%v"]
        key = b"Avis Durgan"
        encrypted = bytes(value ^ key[i % len(key)] for i,value in enumerate(message))
        assert message_formats(header+encrypted, True) == expected
        assert message_format_samples(header+encrypted, True) == [b"%x2", b"%v"]
        for invalid in (header+message[:-1], header+message[:-1]+b"!", header[:5]):
            try: message_formats(invalid, False)
            except ValueError: pass
            else: raise AssertionError("malformed message accepted")
        commands,tests,_=catalogs()
        instructions,predicates=analyze(bytes([255,1,0,0,255,3,0,3,0,7,0]),commands,tests)
        assert {i['offset'] for i in instructions}=={0,7,10} and predicates==[1]
        instructions,predicates=analyze(bytes.fromhex('ff 0e 02 01 00 02 00 ff 00 00 00'),commands,tests)
        assert predicates==[14] and len(instructions)==2
        instructions,_=analyze(bytes([23,0,0]),commands,tests)
        assert instructions[0]['arguments']==[0]
        instructions,_=analyze(bytes([128,134,0,0]),commands,tests)
        assert {i['offset'] for i in instructions}=={0,1,3}
        ignored={n for n,c in enumerate(commands) if c['native_handler']=='VmSuccess'}
        assert ignored=={110,127,144,155,163,164,173,175,176,178,179,180,181}
        assert {commands[n]['coco_handler'] for n in ignored}<={'NoopCmdsRet','cmd_shake_screen','cmd_set_upper_left','cmd_hide_mouse'}
        manifest=coverage_manifest()
        assert len(manifest['commands'])==182 and len(manifest['predicates'])==19
        config_screen=next(row for row in manifest['commands'] if row['opcode']==111)
        assert config_screen['equivalence_result']=='open' and config_screen.get('equivalence_reference') is None
        assert config_screen['focused_evidence']['reference']=='WILDBITS-PARITY.md#s06-configscreen-all-offset-modal-preview-checkpoint-2026-11-08'
        assert config_screen['focused_evidence']['result'].startswith('PASS: 94 screen-config calls')
        save_game=next(row for row in manifest['commands'] if row['opcode']==125)
        assert save_game['equivalence_result']=='open' and save_game.get('equivalence_reference') is None
        assert save_game['focused_evidence']['reference']=='WILDBITS-PARITY.md#s08-exact-state-write-transfer-checkpoint-2026-11-08'
        assert save_game['focused_evidence']['result'].startswith('PASS: sierrastate retries valid short writes')
        restart_game=next(row for row in manifest['commands'] if row['opcode']==128)
        assert restart_game['equivalence_result']=='open' and restart_game.get('equivalence_reference') is None
        assert restart_game['focused_evidence']['reference']=='WILDBITS-PARITY.md#s08-coco-automatic-restart-and-normalized-outcome-comparison-2026-11-08'
        assert restart_game['focused_evidence']['result'].startswith('PASS: CoCo confirms manual cancellation')
        restore_game=next(row for row in manifest['commands'] if row['opcode']==126)
        assert restore_game['equivalence_result']=='open' and restore_game.get('equivalence_reference') is None
        assert restore_game['focused_evidence']['reference']=='WILDBITS-PARITY.md#s08-real-driver-restore-rejection-checkpoint-2026-11-08'
        assert restore_game['focused_evidence']['result'].startswith('PASS: actual restore rejects')
        assert all(row['reference_source_files'] and row['native_source_files']
                   and row['route_test']=='check_native_dispatch.py'
                   and row['behavior_decision']['policy'] and row['behavior_decision']['reference']
                   for row in manifest['commands'])
        markdown=(ROOT/'WILDBITS-PARITY.md').read_text()
        headings=set()
        for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*$',markdown,re.M):
            slug=re.sub(r'[^a-z0-9 -]','',heading.lower())
            headings.add(re.sub(r'\s+','-',slug).strip('-'))
        for row in manifest['commands']+manifest['predicates']:
            references=[row['behavior_decision']['reference']]
            if row.get('equivalence_reference'):
                references.append(row['equivalence_reference'])
            if row.get('focused_evidence'):
                references.append(row['focused_evidence']['reference'])
                assert row['focused_evidence']['test'] and row['focused_evidence']['result'].startswith('PASS:')
            assert (row['equivalence_result']=='open') == (row.get('equivalence_reference') is None), row
            for reference in references:
                path,anchor=reference.split('#',1)
                assert (ROOT/path).is_file() and anchor in headings, reference
        # Dispatch is necessary inventory evidence, not command-level behavior
        # evidence. Keep that distinction machine-checked so a catalog route
        # cannot accidentally close a parity gate.
        assert all(row['route_test_result'].startswith('PASS: all 256 opcodes')
                   for row in manifest['commands']
                   if row['acceptance_gate'].startswith('S'))
        accepted_s01={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,130,145,146,165,166,167,168}
        accepted_s01_rows=[row for row in manifest['commands']
                           if row['opcode'] in accepted_s01]
        assert len(accepted_s01_rows)==len(accepted_s01)
        assert all(row['acceptance_gate']=='S01'
                   and row['equivalence_result'].startswith('PASS:')
                   and row.get('semantic_test') and row.get('semantic_test_result','').startswith('PASS: both real owners')
                   for row in accepted_s01_rows)
        accepted_s02={18,19,20,21,22,23,30,31,32,142,153,171,172}
        accepted_s02_rows=[row for row in manifest['commands'] if row['opcode'] in accepted_s02]
        assert len(accepted_s02_rows)==len(accepted_s02)
        assert all(row['acceptance_gate']=='S02'
                   and row['equivalence_result'].startswith('PASS:')
                   and row.get('semantic_test') in {'check_view_cache_reload.py public load.view/discard.view commands','check_replay_differential.py cmd.push.script/ReplaySaveCheckpoint','check_replay_differential.py cmd.pop.script/ReplayRestore','check_replay_differential.py cmd.script.size/ReplayInitialize','check_logic_executor.py nested literal call and variable call.v scripts','check_load_logic_cache_hit.py actual literal/variable load.logics handlers','check_room_commands.py public room commands, completed transitions, destination/root continuation, room zero, and retry/error paths'}
                   and row.get('semantic_test_result','').startswith('PASS:')
                   for row in accepted_s02_rows)
        accepted_s03={33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,
                       70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,147,148}
        accepted_s03_rows=[row for row in manifest['commands'] if row['opcode'] in accepted_s03]
        assert len(accepted_s03_rows)==len(accepted_s03)
        assert all(row['acceptance_gate']=='S03'
                   and row['equivalence_result'].startswith('PASS:')
                   and row.get('semantic_test') in {'check_object_flags.py','check_object_flags.py global block/unblock commands','check_object_scalar_commands.py','check_motion_setup.py','check_object_coordinates.py','check_object_distance.py','check_view_queries.py','check_object_block_state.py opcode-34 whole command','check_view_cache_reload.py literal/variable selectors','check_object_update_control.py','check_force_update.py plus check_wbplay.py frame capture','check_object_visibility.py plus check_wbgame.py sprite pixels'}
                   and row.get('semantic_test_result','').startswith('PASS: both real owners')
                   for row in accepted_s03_rows)
        assert all(row['equivalence_result']=='open'
                   for row in manifest['commands']
                   if row['acceptance_gate']=='S03' and row['opcode'] not in accepted_s03)
        accepted_s04={24,25,26,27,28,106,107,110,122,123,140,154,174}
        accepted_s04_rows=[row for row in manifest['commands'] if row['opcode'] in accepted_s04]
        assert len(accepted_s04_rows)==len(accepted_s04)
        assert all(row['acceptance_gate']=='S04'
                   and row['equivalence_result'].startswith('PASS:')
                   and ((row['opcode'] in (24,25,26)
                         and row.get('semantic_test')=='check_picture_stream.py actual load.pic/draw.pic/show.pic script versus CoCo shdw.RenderPic'
                         and row.get('semantic_test_result','').startswith('PASS: the real Wild Bits opcode 24/25/26 script'))
                        or (row['opcode']==28
                            and row.get('semantic_test')=='check_picture_stream.py actual load/draw/overlay/show logic versus CoCo-rendered base and overlay buffers'
                            and row.get('semantic_test_result','').startswith('PASS: actual Wild Bits overlay.pic retains the base picture'))
                        or (row['opcode']==27
                            and row.get('semantic_test')=='check_resource_lifetime.py actual CoCo cmd_discard_pic and Wild Bits GameDiscardPicture'
                            and row.get('semantic_test_result','').startswith('PASS: actual public commands discard first, middle and last loaded pictures'))
                        or (row['opcode'] in {106,107}
                            and row.get('semantic_test')=='check_text_graphics_mode.py actual CoCo handlers plus check_wbgame.py native text/graphics pixel matrix'
                            and row.get('semantic_test_result','').startswith('PASS: CoCo text.screen/graphics select text/graphics MMU pages'))
                        or (row['opcode']==174
                            and row.get('semantic_test')=='check_priority_bands.py actual CoCo SetPriBaseStub and Wild Bits AuxPrioritySet plus pixel/sprite projection checks'
                            and row.get('semantic_test_result','').startswith('PASS: public CoCo set-pri-base stub and native setter match'))
                        or (row['opcode']==110
                            and row.get('semantic_test')=='check_logic_executor.py opcode-110 CoCo-stub case plus check_native_dispatch.py route matrix'
                            and row.get('semantic_test_result','').startswith('PASS: direct CoCo opcode-110 target consumes its literal operand'))
                        or (row['opcode'] in (122,123)
                            and row.get('semantic_test')=='check_add_to_picture.py actual CoCo cmd_add_to_pic/cmd_add_to_pic_v through AddToPicImpl and CoCo ObjAddPicPri/ObjBlit; paired Wild Bits pixel oracle'
                            and row.get('semantic_test_result','').startswith('PASS: 52 Wild Bits scenarios and 104 actual CoCo command calls; 36 actual AddToPicImpl calls'))
                        or (row['opcode']==140
                            and row.get('semantic_test')=='check_monitor_command.py CoCo palette writes plus check_wbgame.py Wild Bits palette/profile scenarios'
                            and row.get('semantic_test_result','').startswith('PASS: actual CoCo toggle-monitor emits all 16 indexed palette writes'))
                        or (row['opcode']==154
                            and row.get('semantic_test')=='check_text_rect.py actual CoCo cmd_clear_text_rect and native script'
                            and row.get('semantic_test_result','').startswith('PASS: rendered CoCo and Wild Bits text cells/attributes match')))

                   for row in accepted_s04_rows)
        assert any(row['opcode']==140
                   and row['acceptance_gate']=='S04'
                   and row.get('semantic_test')=='check_monitor_command.py CoCo palette writes plus check_wbgame.py Wild Bits palette/profile scenarios'
                   and row.get('semantic_test_result','').startswith('PASS: actual CoCo toggle-monitor emits all 16 indexed palette writes')
                   for row in accepted_s04_rows)
        assert all(row['equivalence_result']=='open'
                   for row in manifest['commands']
                   if row['acceptance_gate']=='S04' and row['opcode'] not in accepted_s04)
        accepted_s05={101,102,103,104,108,109,114,116,117,151,152}
        accepted_s05_rows=[row for row in manifest['commands'] if row['opcode'] in accepted_s05]
        assert all(row['acceptance_gate']=='S05' and row['equivalence_result'].startswith('PASS:')
                   and ((row['opcode'] in {101,102}
                         and row.get('semantic_test')=='check_text_command_entry.py actual CoCo print handlers plus check_wbgame.py loaded literal/variable print and check_kq4_mame.py original popup/restoration'
                         and row.get('semantic_test_result','').startswith('PASS: actual CoCo print/print.v resolve literal or variable messages'))
                        or (row['opcode'] in {151,152}
                         and row.get('semantic_test')=='check_text_command_entry.py actual CoCo positioned-print handlers plus check_wbgame.py loaded print.at/print.at.v cell output'
                         and row.get('semantic_test_result','').startswith('PASS: actual CoCo print.at/print.at.v resolve literal or variable messages'))
                        or (row['opcode'] in {103,104}
                         and row.get('semantic_test')=='check_text_command_entry.py actual CoCo display handlers plus check_wbgame.py native literal/variable text pixels'
                         and row.get('semantic_test_result','').startswith('PASS: actual CoCo display/display.v format the selected message'))
                        or (row['opcode']==108
                         and row.get('semantic_test')=='check_cursor_char.py CoCo message-table handler plus check_wbgame.py native screen backend'
                         and row.get('semantic_test_result','').startswith('PASS: both owners select the first byte'))
                        or (row['opcode']==109
                         and row.get('semantic_test')=='check_text_attribute.py CoCo handler plus check_wbgame.py native screen backend'
                         and row.get('semantic_test_result','').startswith('PASS: actual CoCo set.text.attribute packs'))
                        or (row['opcode'] in {114,116}
                            and row.get('semantic_test')=='check_string_slots.py actual CoCo/native set.string and word.to.string handlers'
                            and row.get('semantic_test_result','').startswith('PASS: the actual CoCo and Wild Bits owners match set.string destination-slot writes'))
                        or (row['opcode']==117
                            and row.get('semantic_test')=='check_parse_command.py actual CoCo cmd_parse plus check_wbparser.py native dictionary and check_wbgame.py original parsed encounters'
                            and row.get('semantic_test_result','').startswith('PASS: CoCo cmd_parse selects the requested 40-byte string')))
                   for row in accepted_s05_rows)
        accepted_s06={92,93,94,95,96,97,105,112,113,115,118,119,120,121,124,131,132,137,138,139,141,156,157,158,159,160,161,169}
        accepted_s06_rows=[row for row in manifest['commands'] if row['opcode'] in accepted_s06]
        assert len(accepted_s06_rows)==len(accepted_s06)
        assert all(row['acceptance_gate']=='S06'
                   and row['equivalence_result'].startswith('PASS:')
                   and ((row['opcode'] in {92,93,94,95,96,97}
                         and row.get('semantic_test')=='check_inventory_commands.py actual CoCo/native inventory command handlers'
                         and row.get('semantic_test_result','').startswith('PASS: both owners match get/get.v/drop/put/put.v/get.room.v'))
                        or (row['opcode'] in {137,138}
                            and row.get('semantic_test')=='check_cancel_line.py actual CoCo/native cancel.line and echo.line command bodies'
                            and row.get('semantic_test_result','').startswith('PASS: CoCo cmd_cancel_line/cmd_echo_line match Wild Bits GameCancelLine/GameEchoLine'))
                        or (row['opcode']==121
                            and row.get('semantic_test')=='check_set_key.py actual CoCo CmdSetKey/RemapKeyEvent and Wild Bits SetKeyCommand/GameKeyBinding'
                            and row.get('semantic_test_result','').startswith('PASS: both owners append duplicate bindings, dispatch the first matching key'))
                        or (row['opcode']==139
                            and row.get('semantic_test')=='check_init_joy.py CoCo command plus check_wbgame_previews_mame.py --joystick Wild Bits driver path'
                            and row.get('semantic_test_result','').startswith('PASS: CoCo enable/button, Escape-cancel, disable and event-clear state pass at two code bases'))
                        or (row['opcode']==105
                            and row.get('semantic_test')=='check_text_rect.py CoCo clear.lines request and check_wbgame.py Wild Bits framebuffer colors'
                            and row.get('semantic_test_result','').startswith('PASS: CoCo cmd_clear_lines clears inclusive full-width rows'))
                        or (row['opcode'] in {119,120}
                            and row.get('semantic_test')=='check_screen_input.py actual CoCo handlers plus check_wbgame.py native screen backend'
                            and row.get('semantic_test_result','').startswith('PASS: both owners set the input-acceptance state'))
                        or (row['opcode'] in {112,113}
                            and row.get('semantic_test')=='check_status_line_commands.py CoCo entry points plus check_wbgame.py status-line pixels'
                            and row.get('semantic_test_result','').startswith('PASS: actual CoCo status.line.on/off set the enabled state'))
                        or (row['opcode']==115
                            and row.get('semantic_test')=='check_get_string.py actual CoCo cmd_get_string plus native GameGetInput modal editor'
                            and row.get('semantic_test_result','').startswith('PASS: actual CoCo cmd_get_string selects the prompt'))
                        or (row['opcode']==118
                            and row.get('semantic_test')=='check_get_number.py actual CoCo CmdObjStatus plus native opcode 118 modal input'
                            and row.get('semantic_test_result','').startswith('PASS: both real command paths store matching results'))
                        or (row['opcode']==161
                            and row.get('semantic_test')=='check_wbgame.py actual CoCo menu_input request/event loop plus loaded Wild Bits opcode 161'
                            and row.get('semantic_test_result','').startswith('PASS: CoCo menu_input and Wild Bits opcode 161 defer display'))
                        or (row['opcode']==169
                            and row.get('semantic_test')=='check_persistent_window.py actual CoCo handler plus check_coco_kq4_inventory_mame.py rendered popup dismissal and check_wbgame_mame.py Wild Bits restoration'
                            and row.get('semantic_test_result','').startswith('PASS: CoCo close.window direct handler guards and actual KQ4 look popup dismissal are checked'))
                        or (row['opcode']==141
                            and row.get('semantic_test')=='check_wbgame.py actual CoCo CmdShowAgiInfo message_box text plus loaded Wild Bits opcode 141 modal'
                            and row.get('semantic_test_result','').startswith('PASS: CoCo CmdShowAgiInfo passes the exact Adventure Game Interpreter / Version 2.072 message'))
                        or (row['opcode'] in {131,132}
                            and row.get('semantic_test')=='check_player_control.py actual CoCo/Wild Bits program.control and player.control handlers'
                            and row.get('semantic_test_result','').startswith('PASS: both owners match program.control/player.control control flags'))
                        or (row['opcode'] in {159,160}
                            and row.get('semantic_test')=='check_wbgame.py actual CoCo cmd_enable_item/cmd_disable_item plus Wild Bits MenuCommand and loaded menu selection'
                            and row.get('semantic_test_result','').startswith('PASS: both actual command handlers toggle duplicate action codes consistently'))
                        or (row['opcode'] in {156,157,158}
                            and row.get('semantic_test')=='check_wbgame.py actual CoCo and loaded Wild Bits menu construction handlers'
                            and row.get('semantic_test_result','').startswith('PASS: actual CoCo set.menu/set.menu.item/submit.menu lists'))
                        or (row['opcode']==124
                            and row.get('semantic_test')=='check_coco_kq4_inventory_mame.py and check_kq4_mame.py original KQ4 menu Inventory action'
                            and row.get('semantic_test_result','').startswith('PASS: original KQ4 Inventory opens as an opaque black/white full-page status screen')))
                   for row in accepted_s06_rows)
        game_id=next(row for row in manifest['commands'] if row['opcode']==143)
        assert game_id['acceptance_gate']=='S08'
        assert game_id.get('semantic_test')=='check_game_id.py actual CoCo cmd_set_game_id and loaded Wild Bits opcode 143'
        assert game_id.get('semantic_test_result','').startswith('PASS: actual CoCo cmd_set_game_id')
        assert all(row['equivalence_result']=='open'
                   for row in manifest['commands']
                   if row['acceptance_gate'].startswith('S')
                   and row['opcode'] not in (accepted_s01|accepted_s02|accepted_s03|accepted_s04|accepted_s05|accepted_s06|{98,99,100,136,143}))
        assert all(row['equivalence_result'].startswith('PASS:')
                   for row in manifest['commands']
                   if row['acceptance_gate'].startswith('C'))
        pause=next(row for row in manifest['commands'] if row['opcode']==136)
        assert pause['acceptance_gate']=='S07'
        assert pause.get('semantic_test')=='check_pause_command.py CoCo command plus check_wbgame.py native pause/clock behavior'
        assert pause.get('semantic_test_result','').startswith('PASS: actual CoCo pause clears queued events')
        stop_sound=next(row for row in manifest['commands'] if row['opcode']==100)
        assert stop_sound['acceptance_gate']=='S07'
        assert stop_sound.get('semantic_test')=='check_logic_executor.py opcode-100 CoCo/native no-op case plus check_native_audio.py active playback case'
        assert stop_sound.get('semantic_test_result','').startswith('PASS: actual CoCo opcode 100 consumes no operands')
        load_sound=next(row for row in manifest['commands'] if row['opcode']==98)
        assert load_sound['acceptance_gate']=='S07'
        assert load_sound.get('semantic_test')=='check_native_audio.py actual CoCo cmd_load_sound plus Wild Bits opcode 98 cache and playback comparison'
        assert load_sound.get('semantic_test_result','').startswith('PASS: actual CoCo cmd_load_sound loads the sound record')
        sound=next(row for row in manifest['commands'] if row['opcode']==99)
        assert sound['acceptance_gate']=='S07'
        assert sound.get('semantic_test')=='check_native_audio.py actual CoCo cmd_sound/PlaySound plus loaded Wild Bits opcode 99 event stream and completion flag'
        assert sound.get('semantic_test_result','').startswith('PASS: actual CoCo cmd_sound runs PlaySound over the resident note stream')
        assert all(row['candidate_regressions']
                   for row in manifest['commands']
                   if row['acceptance_gate'].startswith('S'))
        assert all(row['reference_source_files'] and row['native_source_files']
                   and row['predicate_test'] and row['predicate_test_result']
                   and row['behavior_decision']['policy'] and row['behavior_decision']['reference']
                   for row in manifest['predicates'])
        assert all(row['equivalence_result'] != 'open'
                   for row in manifest['predicates'] if row['predicate'] == 0)
        assert all(row['equivalence_result'].startswith('PASS:')
                   and row['predicate_test']=='check_coco_conditions.py direct CoCo/native handlers'
                   and row['predicate_test_result'].startswith('PASS: both real owners')
                   for row in manifest['predicates'] if 1 <= row['predicate'] <= 8)
        assert all(row['equivalence_result']=='PASS: actual CoCo/native possession and room predicates'
                   and row['predicate_test']=='check_inventory_commands.py direct CoCo/native predicate handlers'
                   and row['predicate_test_result'].startswith('PASS: both real owners')
                   for row in manifest['predicates'] if row['predicate'] in (9,10))
        assert all(row['equivalence_result']=='PASS: actual CoCo/native controller predicate'
                   and row['predicate_test']=='check_controller_predicate.py direct CoCo/native handlers'
                   and row['predicate_test_result'].startswith('PASS: both real owners')
                   for row in manifest['predicates'] if row['predicate']==12)
        assert all(row['equivalence_result']=='PASS: actual CoCo/native have.key result; cleared-key wait verified in integration'
                   and row['predicate_test']=='check_have_key_predicate.py direct handlers plus check_wbgame.py fresh-key wait'
                   and row['predicate_test_result'].startswith('PASS: actual CoCo pending-key')
                   for row in manifest['predicates'] if row['predicate']==13)
        assert all(row['equivalence_result']=='PASS: actual CoCo/native said predicate'
                   and row['predicate_test']=='check_said.py actual CoCo/native predicate handlers'
                   and row['predicate_test_result'].startswith('PASS: both real owners')
                   for row in manifest['predicates'] if row['predicate']==14)
        assert all(row['equivalence_result']=='PASS: actual CoCo/native string predicate'
                   and row['predicate_test']=='check_string_compare.py actual CoCo/native predicate handlers'
                   and row['predicate_test_result'].startswith('PASS: both real owners')
                   for row in manifest['predicates'] if row['predicate']==15)
        assert all(row['equivalence_result']=='PASS: actual CoCo/native position predicates'
                   and row['predicate_test']=='check_object_position_predicates.py direct CoCo/native handlers'
                   and row['predicate_test_result'].startswith('PASS: both real owners')
                   for row in manifest['predicates'] if row['predicate'] in (11,16,17,18))
        assert all(row['equivalence_result'] == 'open'
                   for row in manifest['predicates'] if row['predicate'] not in (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18))
        assert {row['opcode'] for row in manifest['commands'] if row['route_status']=='unsupported'}==set()
        assert [commands[n]['native_handler'] for n in (149,150)]==[
            'GameTraceOnCommand','GameTraceInfoCommand']
        assert all((ROOT/'tests'/name).exists() for row in manifest['commands'] for name in row['candidate_regressions'])
        zero_instructions,zero_predicates=analyze(bytes.fromhex('ff 00 ff 00 00 00'),commands,tests)
        assert {i['offset'] for i in zero_instructions}=={0,5} and zero_predicates==[0]
        assert manifest['predicates'][0]['native_handler']=='VmTrue'
        overlapping=bytes.fromhex('ff 01 00 00 ff 03 00 fe 05 00 ff 01 00 01 ff 08 00 84 03 fa 2a 00 00 00 00 03 fa 49 00')
        findings=[];instructions,_=analyze(overlapping,commands,tests,overlaps=findings)
        assert {i['offset'] for i in instructions}>={10,15,17,18,25}
        assert findings and {f['byte'] for f in findings}=={15,16,17}
        try:analyze(overlapping,commands,tests)
        except ValueError:pass
        else:raise AssertionError('strict mode accepted overlapping instructions')
        for bad in (b'\x03',bytes.fromhex('fe ff 7f'),bytes.fromhex('fe ff ff'),
                    bytes.fromhex('ff fc ff 00 00 00'),bytes.fromhex('ff 0e 02 01')):
            try:analyze(bad,commands,tests)
            except ValueError:pass
            else:raise AssertionError(('malformed code accepted',bad))
        print('PASS: plain/encrypted message directives, literal percent, absent messages, malformed message bounds; both branch arms, said operands, variable calls, truncation, invalid targets, explicit overlapping-bytecode findings and malformed conditions')
        if args.output is None and not args.all_games:return
    if args.all_games:
        if args.output_dir is None:parser.error('--all-games requires --output-dir')
        args.output_dir.mkdir(parents=True,exist_ok=True);rows=[]
        for words in sorted(ROOT.glob('*/words.tok')):
            try:
                report=audit(words.parent)
                (args.output_dir/(words.parent.name+'.json')).write_text(json.dumps(report,indent=2)+'\n')
                summary=report['summary']
                rows.append({'game':words.parent.name,'logics':summary['logics'],'instructions':summary['instructions'],
                    'unsupported':len(summary['unsupported']),'ignored':len(summary['ignored_operations']),
                    'formats':len(summary['unsupported_message_formats']),
                    'dynamic':len(report['unresolved_dynamic_from_direct_graph']),
                    'overlaps':len(summary['overlapping_instructions'])})
            except (ValueError,OSError) as error:rows.append({'game':words.parent.name,'error':str(error)})
        (args.output_dir/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
        (args.output_dir/'coverage.json').write_text(json.dumps(coverage_manifest(),indent=2)+'\n')
        if not rows:parser.exit(1,'No bundled words.tok directories found.\n')
        print(json.dumps(rows,indent=2))
        if any('error' in row for row in rows):parser.exit(1,'Some game audits failed; inspect summary.json.\n')
        print('PASS: all bundled titles audited; ignored/unsupported operations, formatter findings, dynamic sites and overlaps are explicitly classified.')
        print('Static reports do not establish runtime compatibility or complete-adventure progression.')
        return
    if args.output is None:parser.error('--output is required for a game audit')
    report=audit(args.game);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],indent=2))
    print('Dynamic destinations remain unresolved; this is not a complete-adventure pass.')


if __name__=='__main__':main()
