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
    """Complete catalog inventory; candidate tests do not assert equivalence."""
    commands,tests,supported=catalogs()
    candidates={
        'C01':['check_priority_view.py','check_priority_mame.py','check_native_dispatch.py'],
        'C02':['check_decimal_output.py','check_wbgame.py','check_priority_mame.py','check_native_dispatch.py'],
        'C03':['check_decimal_output.py','check_wbgame.py','check_priority_mame.py','check_native_dispatch.py'],
        'C06':['check_wbgame.py','check_priority_mame.py','check_native_dispatch.py'],
        'C07':['check_wbgame.py','check_priority_mame.py','check_native_dispatch.py'],
        'S01':['check_logic_executor.py','check_condition_flow.py','check_math_commands.py','check_random_command.py','check_coco_conditions.py'],
        'S02':['check_resource_lifetime.py','check_resource_format.py','check_wbasset.py','check_packed_pictures.py','check_lzw.py','check_wbgame.py'],
        'S03':['check_object_flags.py','check_object_scalar_commands.py','check_object_bounds.py','check_object_terrain.py','check_motion_setup.py','check_wbgame.py'],
        'S04':['check_wbdecode.py','check_add_to_picture.py','check_priority_bands.py','check_wbgame.py'],
        'S05':['check_decimal_index.py','check_text_helpers.py','check_string_compare.py','check_tokenizer.py','check_wbparser.py','check_wbplay.py'],
        'S06':['check_wbgame.py','check_wbparser.py','check_inventory_commands.py','check_wbplay.py'],
        'S07':['check_game_clock.py','check_native_audio.py','check_wbgame.py'],
        'S08':['check_wbgame.py','check_original_kq3.py','check_kq3_mame.py']}
    gates={i:'S01' for i in range(182)}
    for gate,ranges in {'S02':[(18,23),(30,32),(142,142),(153,153),(171,172)],
                        'S03':[(33,91),(131,132),(147,148)],
                        'S04':[(24,28),(106,107),(110,110),(122,123),(140,140),(154,154),(174,174)],
                        'S05':[(101,104),(108,109),(114,114),(116,117),(151,152)],
                        'S06':[(92,97),(111,113),(115,115),(118,121),(124,124),(129,129),(137,139),(141,141),(156,162),(169,169)],
                        'S07':[(98,100),(136,136)],'S08':[(125,126),(128,128),(134,134),(143,143)]}.items():
        for lo,hi in ranges:
            for i in range(lo,hi+1):gates[i]=gate
    for i,gate in {29:'C01',133:'C02',135:'C03',149:'C04',150:'C05',170:'C06',177:'C07',
                   144:'C08',175:'C09',179:'C10',180:'C11',
                   **{i:'C12' for i in (127,155,163,164,173,176,178,181)}}.items():gates[i]=gate
    rows=[]
    for i,command in enumerate(commands):
        gate=gates[i];status='unsupported' if i not in supported else 'CoCo ignored operation' if command['native_handler']=='VmSuccess' else 'routed'
        rows.append({'opcode':i,**command,'effective_native_handler':'ExecuteLogic core' if i<18 else command['native_handler'],
            'route_status':status,'acceptance_gate':gate,
            'candidate_regressions':candidates.get(gate,['check_logic_executor.py','check_native_dispatch.py'] if gate in ('C08','C09','C10','C11','C12') else []),
            'equivalence_result':'see recorded stub evidence' if gate in ('C08','C09','C10','C11','C12') else 'open'})
    names=re.findall(r'^\s*AGI_TEST\s+([^,]+),', (ROOT/'objs/shared/agi-test-table.asm').read_text(),re.M)
    predicates=[{'predicate':i,'coco_handler':name.strip(),'operands':tests[i],
                 'acceptance_gate':'S01' if i<=8 else 'S05' if i in (14,15) else 'S03' if i in (11,16,17,18) else 'S06',
                 'native_handler': 'VmTrue' if i==0 else name.strip() if i<=8 else 'InventoryTest' if i in (9,10) else 'ObjectPositionTest' if i in (11,16,17,18) else {12:'InputControllerTest',13:'InputHaveKeyTest',14:'InputSaidTest',15:'StringCompareTest'}[i],
                 'candidate_regressions':['check_logic_executor.py'] if i==0 else candidates['S01' if i<=8 else 'S05' if i in (14,15) else 'S03' if i in (11,16,17,18) else 'S06'],
                 'equivalence_result':'constant-true/NOT/OR/AND/skip full-executor comparison' if i==0 else 'open'} for i,name in enumerate(names)]
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
        key = b"Avis Durgan"
        encrypted = bytes(value ^ key[i % len(key)] for i,value in enumerate(message))
        assert message_formats(header+encrypted, True) == expected
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
        assert ignored=={127,144,155,163,164,173,175,176,178,179,180,181}
        assert {commands[n]['coco_handler'] for n in ignored}<={'NoopCmdsRet','cmd_shake_screen','cmd_set_upper_left','cmd_hide_mouse'}
        manifest=coverage_manifest()
        assert len(manifest['commands'])==182 and len(manifest['predicates'])==19
        assert {row['opcode'] for row in manifest['commands'] if row['route_status']=='unsupported'}=={149,150}
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
