#!/usr/bin/env python3
"""Conservatively audit original AGI script control flow and native support.

No game assets are copied to the report. Both arms of every condition are
visited; variable calls/rooms remain unresolved rather than guessed.
"""
import argparse
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
            commands.append({'coco_handler': match[1], 'operands': int(match[2],16)//256})
    tests = [int(m[1],16)//256 for m in re.finditer(
        r'^\s*AGI_TEST\s+[^,]+,\$([0-9a-f]+)',
        (ROOT/'objs/shared/agi-test-table.asm').read_text(), re.M|re.I)]
    assert len(commands)==182 and len(tests)==19
    supported = set(range(18))
    for routes in (COMMON,GAME):
        for opcodes in routes.values(): supported.update(opcodes)
    return commands, tests, supported


def script(game, number, entry):
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
    return payload[2:length+2]


def analyze(code, commands, tests):
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
                if not 1<=test<len(tests):raise ValueError(f'invalid predicate {test} at {at-1}')
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
                raise ValueError(f'instruction overlap at {byte}')
            occupied[byte]=start
        instructions[start]={'offset':start,'opcode':opcode,'arguments':arguments}
        queue.extend(targets)
    return list(instructions.values()), sorted(predicates)


def audit(game):
    commands,tests,supported=catalogs();directory=(game/'logDir').read_bytes()
    if len(directory)%3:raise ValueError('partial logDir entry')
    report={'game':game.name,'method':'Both branch arms; local control flow from entry; variable destinations unresolved.',
            'limits':['Static reachability does not establish puzzle solvability or correct command semantics.',
                      'Dynamic calls/rooms and saved scan starts require runtime coverage.'], 'logics':[]}
    for number in range(len(directory)//3):
        entry=int.from_bytes(directory[number*3:number*3+3],'big')
        if entry==0xffffff:continue
        code=script(game,number,entry)
        try:instructions,predicates=analyze(code,commands,tests)
        except ValueError as error:raise ValueError(f'logic {number}: {error}') from error
        operations=[i for i in instructions if i['opcode']<182]
        unsupported=[dict(i,coco_handler=commands[i['opcode']]['coco_handler']) for i in operations if i['opcode'] not in supported]
        direct=[{'offset':i['offset'],'kind':'room' if i['opcode']==18 else 'call','target':i['arguments'][0]}
                for i in operations if i['opcode'] in (18,22)]
        dynamic=[{'offset':i['offset'],'kind':'room' if i['opcode']==19 else 'call','variable':i['arguments'][0]}
                 for i in operations if i['opcode'] in (19,23)]
        report['logics'].append({'logic':number,'code_bytes':len(code),'instructions':len(instructions),
            'commands':sorted({i['opcode'] for i in operations}),'predicates':predicates,
            'direct_destinations':direct,'dynamic_destinations':dynamic,'unsupported':unsupported})
    by_number={item['logic']:item for item in report['logics']};reachable=set();queue=deque([0])
    while queue:
        number=queue.popleft()
        if number in reachable or number not in by_number:continue
        reachable.add(number);queue.extend(d['target'] for d in by_number[number]['direct_destinations'])
    report['direct_graph_from_root']=sorted(reachable)
    report['unresolved_dynamic_from_direct_graph']=[{'logic':n,**d} for n in sorted(reachable)
                                                   for d in by_number[n]['dynamic_destinations']]
    report['summary']={'logics':len(by_number),'instructions':sum(i['instructions'] for i in by_number.values()),
        'unsupported':[{'logic':i['logic'],**op} for i in by_number.values() for op in i['unsupported']]}
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,default=ROOT/'kingsquest1')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:
        commands,tests,_=catalogs()
        instructions,predicates=analyze(bytes([255,1,0,0,255,3,0,3,0,7,0]),commands,tests)
        assert {i['offset'] for i in instructions}=={0,7,10} and predicates==[1]
        instructions,predicates=analyze(bytes.fromhex('ff 0e 02 01 00 02 00 ff 00 00 00'),commands,tests)
        assert predicates==[14] and len(instructions)==2
        instructions,_=analyze(bytes([23,0,0]),commands,tests)
        assert instructions[0]['arguments']==[0]
        instructions,_=analyze(bytes([128,134,0,0]),commands,tests)
        assert {i['offset'] for i in instructions}=={0,1,3}
        for bad in (b'\x03',bytes.fromhex('fe ff 7f'),bytes.fromhex('fe ff ff'),
                    bytes.fromhex('ff fc ff 00 00 00'),bytes.fromhex('ff 0e 02 01')):
            try:analyze(bad,commands,tests)
            except ValueError:pass
            else:raise AssertionError(('malformed code accepted',bad))
        print('PASS: both branch arms, said operands, variable calls, truncation, invalid targets and malformed conditions')
        if args.output is None:return
    if args.output is None:parser.error('--output is required for a game audit')
    report=audit(args.game);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],indent=2))
    print('Dynamic destinations remain unresolved; this is not a complete-adventure pass.')


if __name__=='__main__':main()
