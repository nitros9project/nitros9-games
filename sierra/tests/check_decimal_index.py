#!/usr/bin/env python3
"""Run formatter index scanners and native message expansion with real handlers."""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu
from audit_game_scripts import logic_resource, message_format_samples, message_formats

ROOT = Path(__file__).resolve().parents[1]


def reference(source, strict):
    value = count = cursor = 0
    for byte in source:
        if not 48 <= byte <= 57: break
        cursor += 1
        candidate = value*10 + byte-48
        if strict and candidate > 255: return value, count, cursor, True
        value = candidate & 255
        count = (count+1) & 255
    return value, count, cursor, False


def check_formatter_parity(d,coco,cs,native,ns,original_cases):
    """Compare actual CoCo/native text, not a native-only escape oracle."""
    strings=[b'slot %v220',b'%s0!',b'%s1/%w2',b'percent%%word']+[b'']*8
    table=b''.join(text+b'\0'+bytes(39-len(text)) for text in strings)
    variables=bytearray(range(256));variables[9]=0;variables[220]=42
    cases=[b'plain',b'[%s0]',b'[%s1]',b'[%s2]',b'%s3',b'%%',b'%',b'50% done',
           b'%rabc',b'%r123',b'%s',b'%v',b'%w',b'%w0',b'%w1',b'%w2',
           b'%w3',b'%w255',b'%w256',b'%v999',b'%v7|256',b'%v7|0!',
           b'%v7|2',b'%s0|2']
    cases += [b'[%v'+str(n).encode()+b']' for n in range(256)]
    cases += [b'%' + bytes([letter])+b'123' for letter in range(1,256)
              if letter not in b'wvsmog']
    cases += [b'%v'+b'0'*n for n in (255,256,257)]
    cases += original_cases
    for text in cases:
        current_table=table
        if text==b'%s':
            # Space Quest I's original missing-operand %s selects slot zero,
            # whose game-initialized contents are empty.
            current_table=b''.join(value+b'\0'+bytes(39-len(value))
                                   for value in [b'']+strings[1:])
        outputs=[]
        for owner in ('CoCo','native'):
            d.write(0,bytes(ns['size']))
            source=b'G'+text+b'\0\0\0END'
            d.write(0x73ff,source)
            d.write(0x7ef0,b'\x7e\0\x74\0\x60\0STACK')
            if owner=='CoCo':
                d.write(0x8000,coco);d.write(0x6000,bytes(512))
                d.write(0x0158,b'\xff');d.write(0x015a,b'\x02')
                d.write(0x0431,variables);d.write(0x0251,current_table)
                d.write(0x0180,b'\x73\0\x73\x20')
                d.write(0x7300,b'red\0');d.write(0x7320,b'tree\0')
                d.regs(pc=0x8000+cs['FormatStr'],s=0x7ef0,dp=0,cc=0x50)
            else:
                d.write(0xa000,native)
                d.write(ns['resourcebase'],b'\0\0')
                d.write(ns['vmvariables'],variables);d.write(ns['vmstrings'],current_table)
                d.write(ns['parsercount'],b'\x02')
                d.write(ns['parserlastline'],b'red tree\0')
                d.write(ns['parseroffsets'],bytes([0,4])+bytes(18)+bytes([3,4])+bytes(18))
                d.write(ns['fillstack']-1,b'G');d.write(ns['fillstack']+4096,b'H')
                d.regs(pc=0xa000+ns['GameFormatMessage'],x=0x7400,s=0x7ef0,u=0,dp=0,cc=0x50)
            d.call('c');r=d.regs()
            assert (r['pc'],r['s'])==(0x7e00,0x7ef2),(owner,text,r)
            assert d.read(0x7ef6,5)==b'STACK'
            assert d.read(0x73ff,len(source))==source
            if owner=='native':
                assert not r['cc']&1 and r['b']==0,(text,r)
                assert d.read(ns['vmvariables'],256)==variables
                assert d.read(ns['vmstrings'],480)==current_table
                assert d.read(ns['fillstack']-1,1)==b'G' and d.read(ns['fillstack']+4096,1)==b'H'
                assert d.read(0xa000,len(native))==native
            outputs.append(d.read(0x6000 if owner=='CoCo' else r['x'],512).split(b'\0')[0])
        assert outputs[0]==outputs[1],(text,outputs)
    print(f'PASS: {len(cases)} actual CoCo/native formatter comparisons, including {len(original_cases)} original-resource directive samples: nested string recursion, words/bounds, all byte variables, index/count wrap, missing operands, unknown/literal percent policy and terminal percent')


def check_formatter_recursion_bounds(d,coco,cs,native,ns):
    """Measure safe nested-slot limits against the actual CoCo formatter."""
    for nested in range(7):
        slots=[b'']*12
        for index in range(nested):
            slots[index]=b'%s'+str(index+1).encode()
        slots[nested]=b'leaf'
        table=b''.join(value+b'\0'+bytes(39-len(value)) for value in slots)
        source=b'G%s0\0END'
        rendered=[]
        for owner in ('CoCo','native'):
            d.write(0,bytes(ns['size']))
            d.write(0x73ff,source)
            d.write(0x7ef0,b'\x7e\0\x74\0\x60\0STACK')
            if owner=='CoCo':
                d.write(0x8000,coco);d.write(0x6000,bytes(1024))
                d.write(0x0158,b'\xff');d.write(0x015a,b'\x02')
                d.write(0x0251,table)
                d.regs(pc=0x8000+cs['FormatStr'],s=0x7ef0,dp=0,cc=0x50)
            else:
                d.write(0xa000,native)
                d.write(ns['resourcebase'],b'\0\0')
                d.write(ns['vmstrings'],table)
                d.write(ns['fillstack']-1,b'G')
                d.write(ns['fillstack']+4096,b'H')
                d.regs(pc=0xa000+ns['GameFormatMessage'],x=0x7400,
                       s=0x7ef0,u=0,dp=0,cc=0x50)
            d.call('c');regs=d.regs()
            assert (regs['pc'],regs['s'])==(0x7e00,0x7ef2),(owner,nested,regs)
            assert d.read(0x7ef6,5)==b'STACK'
            assert d.read(0x73ff,len(source))==source
            if owner=='CoCo':
                text=d.read(0x6000,1024).split(b'\0')[0]
                assert text==b'leaf',('CoCo recursion reference',nested,text)
            else:
                assert d.read(ns['formatdepth'],1)==b'\0'
                assert d.read(ns['fillstack']-1,1)==b'G'
                assert d.read(ns['fillstack']+4096,1)==b'H'
                assert d.read(0xa000,len(native))==native
                if nested<=2:
                    assert not regs['cc']&1 and regs['b']==0,(nested,regs)
                    assert regs['x']==ns['fillstack']+2048
                    text=d.read(regs['x'],16).split(b'\0')[0]
                    assert text==b'leaf',(nested,text)
                else:
                    assert regs['cc']&1 and regs['b']==ns['E$BMode'],(nested,regs)
                    text=None
            rendered.append(text)
        if nested<=2:
            assert rendered==[b'leaf',b'leaf'],(nested,rendered)
        else:
            assert rendered==[b'leaf',None],(nested,rendered)
    print('PASS: seven actual CoCo/native recursive string chains; Wild Bits allows one top-level plus two recursive %s substitutions (four active formatter frames), rejects deeper chains with E$BMode, and unwinds depth/stack without touching guards or code')


def check_formatter_output_bound(d,coco,cs,native,ns):
    """Compare long newline-delimited text without invoking legacy auto-wrap."""
    line=b'Q'*200+b'\n'
    expected=line*11
    source=b'G'+expected+b'\0END'
    assert len(expected)>2047
    results=[]
    for owner,code,syms,basepc in (('CoCo',coco,cs,0x8000),('native',native,ns,0xa000)):
        private=0 if owner=='CoCo' else 0x1000
        d.write(0,bytes(ns['size']))
        d.write(0x73ff,source)
        d.write(0x7ef0,b'\x7e\0\x74\0\x60\0STACK')
        if owner=='CoCo':
            output=0x6000
            d.write(basepc,code);d.write(output,bytes(len(expected)+1))
            d.write(0x0155,b'\0\0');d.write(0x0157,b'\0');d.write(0x0158,b'\xff')
            d.write(0x015a,b'\x02');d.write(0x015b,b'\0')
            d.regs(pc=basepc+syms['FormatStr'],s=0x7ef0,dp=0,cc=0x50)
        else:
            output=private+syms['fillstack']+2048
            d.write(basepc,code);d.write(private,bytes(syms['size'])+b'GUARD')
            d.write(private+syms['resourcebase'],private.to_bytes(2,'big'))
            d.write(private+syms['fillstack']-1,b'G')
            d.write(private+syms['fillstack']+4096,b'H')
            d.regs(pc=basepc+syms['GameFormatMessage'],x=0x7400,s=0x7ef0,
                   u=private,dp=private>>8,cc=0x50)
        d.call('c');regs=d.regs()
        assert (regs['pc'],regs['s'])==(0x7e00,0x7ef2),(owner,regs)
        assert d.read(0x7ef6,5)==b'STACK' and d.read(0x73ff,len(source))==source
        if owner=='CoCo':
            assert d.read(output,len(expected)+1)==expected+b'\0'
            limit=len(expected)
        else:
            assert regs['cc']&1 and regs['b']==syms['E$BMode'],regs
            limit=2047
            assert d.read(output,limit)==expected[:limit]
            assert d.read(output+limit,1)==b'\0'
            assert d.read(private+syms['parserreadlength'],2)==limit.to_bytes(2,'big')
            assert d.read(private+syms['formatdepth'],1)==b'\0'
            assert d.read(private+syms['fillstack']-1,1)==b'G'
            assert d.read(private+syms['fillstack']+4096,1)==b'H'
            assert d.read(private+syms['size'],5)==b'GUARD'
            assert d.read(basepc,len(code))==code
        results.append(limit)
    assert results==[len(expected),2047]
    print(f'PASS: {len(expected)}-byte newline-delimited CoCo/native output comparison; Wild Bits returns E$BMode at byte 2048 with exact prefix, NUL, and intact depth/stack/private guards')


def original_format_cases():
    cases=[];findings=[]
    for game in sorted(ROOT.glob('*/words.tok')):
        directory=(game.parent/'logDir').read_bytes()
        for number in range(len(directory)//3):
            entry=int.from_bytes(directory[number*3:number*3+3],'big')
            if entry==0xffffff: continue
            payload,encrypted=logic_resource(game.parent,number,entry)
            findings.extend(message_formats(payload,encrypted))
            cases.extend(sample for sample in message_format_samples(payload,encrypted)
                         if sample[1:2] not in (b'w',b'v',b's',b'm',b'o',b'g'))
    assert len(findings)==18 and len(cases)==16,(len(findings),len(cases))
    return cases


def check_original_spacequest2_zero_message(d,coco,cs,native,ns,adjacent=b'\0'):
    """Compare missing-%m behavior with controlled bytes after its table."""
    game=ROOT/'spacequest2'
    directory=(game/'logDir').read_bytes()
    entry=int.from_bytes(directory[82*3:83*3],'big')
    payload,encrypted=logic_resource(game,82,entry)
    code_end=2+int.from_bytes(payload[:2],'little')
    count=payload[code_end]
    base=code_end+1
    length=int.from_bytes(payload[base:base+2],'little')
    end=base+length
    strings=bytearray(payload[base+2+2*count:end])
    if encrypted:
        key=b'Avis Durgan'
        for i,value in enumerate(strings): strings[i]=value^key[i%len(key)]
    offsets=payload[base+2:base+2+2*count]
    table=bytes([count])+payload[base:base+2]+offsets+strings
    message_number=4
    offset=int.from_bytes(offsets[(message_number-1)*2:message_number*2],'little')
    position=base+offset-(base+2+2*count)
    message=bytes(strings[position:strings.find(0,position)])
    assert message.startswith(b'%m') and message[2:].startswith(b's '), \
        'Space Quest II logic 82 message fixture changed'
    source=b'G'+message+b'\0\0\0END'
    outputs=[]; carry=[]
    for owner,code,syms,basepc in (('CoCo',coco,cs,0x8000),('native',native,ns,0xa000)):
        d.write(0,bytes(syms['size']) if owner=='native' else bytes(0x800))
        d.write(0x73ff,source)
        d.write(0x7ef0,b'\x7e\0\x74\0\x60\0STACK')
        if owner=='CoCo':
            d.write(basepc,code);d.write(0x6000,bytes(2048))
            d.write(0x0251,bytes(480));d.write(0x0431,bytes(256))
            slot=bytearray(12);slot[3]=count;slot[10:12]=(0x5000).to_bytes(2,'big')
            d.write(0x3000,slot);d.write(0x62,b'\x30\0')
            d.write(0x5000,table[1:])
            # GetMsgPtr treats a missing operand as index zero and resolves it
            # from the little-endian logic-section length. Control the actual
            # first byte after the bounded table.
            zero_target=0x5000+int.from_bytes(payload[base:base+2],'little')
            assert zero_target<0x10000,hex(zero_target)
            d.write(zero_target,adjacent)
            d.write(0x0157,b'\0');d.write(0x0158,b'\xff');d.write(0x015a,b'\x02')
            d.regs(pc=basepc+cs['FormatStr'],s=0x7ef0,dp=0,cc=0x50)
        else:
            d.write(basepc,code);private=0x1000
            resource=bytearray(payload)
            string_start=base+2+2*count
            resource[string_start:end]=strings
            d.write(private,bytes(syms['size'])+b'GUARD')
            d.write(private+syms['resourcebase'],private.to_bytes(2,'big'))
            d.write(private+syms['vmstrings'],bytes(480))
            d.write(private+syms['vmvariables'],bytes(256))
            d.write(private+syms['assetmapbase'],b'\x40\0')
            d.write(private+syms['vmend'],code_end.to_bytes(2,'big'))
            d.write(private+syms['resourcelength'],len(resource).to_bytes(2,'big'))
            d.write(private+syms['resourcestored'],len(resource).to_bytes(2,'big'))
            d.write(private+syms['assetmapped'],b'\1');d.write(0x4000,resource)
            d.regs(pc=basepc+ns['GameFormatMessage'],x=0x7400,s=0x7ef0,
                   u=private,dp=private>>8,cc=0x50)
        d.call('c');r=d.regs()
        assert (r['pc'],r['s'])==(0x7e00,0x7ef2),(owner,r)
        assert d.read(0x7ef6,5)==b'STACK',(owner,d.read(0x7ef0,16))
        rendered=d.read(0x6000 if owner=='CoCo' else r['x'],512).split(b'\0')[0]
        expected=(adjacent[:-1]+message[2:] if owner=='CoCo' and adjacent!=b'\0'
                  else message[2:])
        assert rendered==expected,(owner,rendered,expected)
        assert d.read(0x73ff,len(source))==source,(owner,'source changed')
        if owner=='CoCo':
            assert d.read(0x5000,len(table)-1)==table[1:]
            assert d.read(zero_target,len(adjacent))==adjacent
        else:
            assert d.read(0x4000,len(resource))==resource
            assert d.read(private+syms['size'],5)==b'GUARD'
        outputs.append(rendered);carry.append(bool(r['cc']&1))
    expected_coco=adjacent[:-1]+message[2:] if adjacent!=b'\0' else message[2:]
    assert outputs==[expected_coco,message[2:]]
    assert carry==[True,False],('documented legacy/native return-status distinction',carry)
    print(f'PASS: original Space Quest II logic 82 `%m` missing operand; controlled adjacent bytes {adjacent!r} verify CoCo lookup and Wild Bits bounded empty expansion')


def check_malformed_message_offset(d,coco,cs,native,ns):
    """Compare a corrupt original offset and verify bounded native recovery."""
    game=ROOT/'spacequest2'
    directory=(game/'logDir').read_bytes()
    entry=int.from_bytes(directory[82*3:83*3],'big')
    payload,encrypted=logic_resource(game,82,entry)
    code_end=2+int.from_bytes(payload[:2],'little')
    count=payload[code_end]
    base=code_end+1
    length=int.from_bytes(payload[base:base+2],'little')
    end=base+length
    message_number=1
    bad_offset=length+4
    strings=bytearray(payload[base+2+2*count:end])
    if encrypted:
        key=b'Avis Durgan'
        for i,value in enumerate(strings): strings[i]=value^key[i%len(key)]
    source=b'G%m1!\0END'
    adjacent=b'Adjacent\0'
    outputs=[]
    for owner,code,syms,basepc in (('CoCo',coco,cs,0x8000),('native',native,ns,0xa000)):
        d.write(0,bytes(syms['size']) if owner=='native' else bytes(0x800))
        d.write(0x73ff,source)
        d.write(0x7ef0,b'\x7e\0\x74\0\x60\0STACK')
        if owner=='CoCo':
            table=bytearray(bytes([count])+payload[base:base+2]+
                            payload[base+2:base+2+2*count]+strings)
            offset_at=1+2+2*(message_number-1)
            table[offset_at:offset_at+2]=bad_offset.to_bytes(2,'little')
            target=0x5000+bad_offset
            assert target+len(adjacent)<0x6000,hex(target)
            d.write(basepc,code);d.write(0x6000,bytes(2048))
            d.write(0x0251,bytes(480));d.write(0x0431,bytes(256))
            slot=bytearray(12);slot[3]=count;slot[10:12]=(0x5000).to_bytes(2,'big')
            d.write(0x3000,slot);d.write(0x62,b'\x30\0')
            d.write(0x5000,table[1:]);d.write(target,adjacent)
            d.write(0x0157,b'\0');d.write(0x0158,b'\xff');d.write(0x015a,b'\x02')
            d.regs(pc=basepc+cs['FormatStr'],s=0x7ef0,dp=0,cc=0x50)
        else:
            resource=bytearray(payload)
            resource[base+2+2*(message_number-1):base+4+2*(message_number-1)]=bad_offset.to_bytes(2,'little')
            string_start=base+2+2*count
            resource[string_start:end]=strings
            d.write(basepc,code);private=0x1000
            d.write(private,bytes(syms['size'])+b'GUARD')
            d.write(private+syms['resourcebase'],private.to_bytes(2,'big'))
            d.write(private+syms['vmstrings'],bytes(480))
            d.write(private+syms['vmvariables'],bytes(256))
            d.write(private+syms['assetmapbase'],b'\x40\0')
            d.write(private+syms['vmend'],code_end.to_bytes(2,'big'))
            d.write(private+syms['resourcelength'],len(resource).to_bytes(2,'big'))
            d.write(private+syms['resourcestored'],len(resource).to_bytes(2,'big'))
            d.write(private+syms['assetmapped'],b'\1');d.write(0x4000,resource)
            d.write(private+syms['fillstack']-1,b'G')
            d.write(private+syms['fillstack']+4096,b'H')
            d.regs(pc=basepc+ns['GameFormatMessage'],x=0x7400,s=0x7ef0,
                   u=private,dp=private>>8,cc=0x50)
        d.call('c');regs=d.regs()
        assert (regs['pc'],regs['s'])==(0x7e00,0x7ef2),(owner,regs)
        assert d.read(0x7ef6,5)==b'STACK'
        assert d.read(0x73ff,len(source))==source
        if owner=='CoCo':
            output=d.read(0x6000,32).split(b'\0')[0]
            assert output==b'Adjacent!',output
            assert d.read(target,len(adjacent))==adjacent
        else:
            assert regs['cc']&1 and regs['b']==ns['E$BMode'],regs
            assert d.read(private+syms['formatdepth'],1)==b'\0'
            assert d.read(private+syms['parserreadlength'],2)==b'\0\0'
            assert d.read(private+syms['fillstack']-1,1)==b'G'
            assert d.read(private+syms['fillstack']+4096,1)==b'H'
            assert d.read(private+syms['fillstack']+2048,1)==b'\0'
            assert d.read(0x4000,len(resource))==resource
            assert d.read(private+syms['size'],5)==b'GUARD'
            assert d.read(0xa000,len(native))==native
            output=b''
        outputs.append(output)
    assert outputs==[b'Adjacent!',b'']
    print('PASS: corrupt original Space Quest II message offset; CoCo follows it into adjacent bytes, while Wild Bits returns E$BMode with balanced formatter/stack and intact resource/private guards')


def check_truncated_message_table(d,coco,cs,native,ns):
    """Ensure a section too short for its offsets fails safely on Wild Bits."""
    game=ROOT/'spacequest2'
    directory=(game/'logDir').read_bytes()
    entry=int.from_bytes(directory[82*3:83*3],'big')
    payload,encrypted=logic_resource(game,82,entry)
    code_end=2+int.from_bytes(payload[:2],'little')
    count=payload[code_end]
    base=code_end+1
    original_length=int.from_bytes(payload[base:base+2],'little')
    end=base+original_length
    first_offset=int.from_bytes(payload[base+2:base+4],'little')
    strings=bytearray(payload[base+2+2*count:end])
    if encrypted:
        key=b'Avis Durgan'
        for i,value in enumerate(strings): strings[i]=value^key[i%len(key)]
    first_start=first_offset-(2+2*count)
    first_message=bytes(strings[first_start:strings.find(0,first_start)])
    assert first_message and b'%' not in first_message
    source=b'G%m1!\0END'
    outputs=[]
    for owner,code,syms,basepc in (('CoCo',coco,cs,0x8000),('native',native,ns,0xa000)):
        d.write(0,bytes(syms['size']) if owner=='native' else bytes(0x800))
        d.write(0x73ff,source)
        d.write(0x7ef0,b'\x7e\0\x74\0\x60\0STACK')
        if owner=='CoCo':
            table=bytes([count])+b'\x02\x00'+payload[base+2:base+2+2*count]+strings
            d.write(basepc,code);d.write(0x6000,bytes(2048))
            d.write(0x0251,bytes(480));d.write(0x0431,bytes(256))
            slot=bytearray(12);slot[3]=count;slot[10:12]=(0x5000).to_bytes(2,'big')
            d.write(0x3000,slot);d.write(0x62,b'\x30\0');d.write(0x5000,table[1:])
            d.write(0x0157,b'\0');d.write(0x0158,b'\xff');d.write(0x015a,b'\x02')
            d.regs(pc=basepc+cs['FormatStr'],s=0x7ef0,dp=0,cc=0x50)
        else:
            resource=bytearray(payload);resource[base:base+2]=b'\x02\x00'
            string_start=base+2+2*count;resource[string_start:end]=strings
            d.write(basepc,code);private=0x1000
            d.write(private,bytes(syms['size'])+b'GUARD')
            d.write(private+syms['resourcebase'],private.to_bytes(2,'big'))
            d.write(private+syms['vmstrings'],bytes(480))
            d.write(private+syms['vmvariables'],bytes(256))
            d.write(private+syms['assetmapbase'],b'\x40\0')
            d.write(private+syms['vmend'],code_end.to_bytes(2,'big'))
            d.write(private+syms['resourcelength'],len(resource).to_bytes(2,'big'))
            d.write(private+syms['resourcestored'],len(resource).to_bytes(2,'big'))
            d.write(private+syms['assetmapped'],b'\1');d.write(0x4000,resource)
            d.write(private+syms['fillstack']-1,b'G')
            d.write(private+syms['fillstack']+4096,b'H')
            d.regs(pc=basepc+ns['GameFormatMessage'],x=0x7400,s=0x7ef0,
                   u=private,dp=private>>8,cc=0x50)
        d.call('c');regs=d.regs()
        assert (regs['pc'],regs['s'])==(0x7e00,0x7ef2),(owner,regs)
        assert d.read(0x7ef6,5)==b'STACK'
        assert d.read(0x73ff,len(source))==source
        if owner=='CoCo':
            output=d.read(0x6000,512).split(b'\0')[0]
            assert output==first_message+b'!',(output,first_message)
        else:
            assert regs['cc']&1 and regs['b']==ns['E$BMode'],regs
            assert d.read(private+syms['formatdepth'],1)==b'\0'
            assert d.read(private+syms['parserreadlength'],2)==b'\0\0'
            assert d.read(private+syms['fillstack']-1,1)==b'G'
            assert d.read(private+syms['fillstack']+4096,1)==b'H'
            assert d.read(private+syms['fillstack']+2048,1)==b'\0'
            assert d.read(0x4000,len(resource))==resource
            assert d.read(private+syms['size'],5)==b'GUARD'
            assert d.read(0xa000,len(native))==native
            output=b''
        outputs.append(output)
    assert outputs==[first_message+b'!',b'']
    print('PASS: truncated original Space Quest II message table; CoCo follows the retained offset, while Wild Bits rejects the short declared section and restores stack/private state')


def check_unterminated_message(d,coco,cs,native,ns):
    """Bound an original message exactly before its NUL terminator."""
    game=ROOT/'spacequest2'
    directory=(game/'logDir').read_bytes()
    entry=int.from_bytes(directory[82*3:83*3],'big')
    payload,encrypted=logic_resource(game,82,entry)
    code_end=2+int.from_bytes(payload[:2],'little')
    count=payload[code_end]
    base=code_end+1
    original_length=int.from_bytes(payload[base:base+2],'little')
    end=base+original_length
    first_offset=int.from_bytes(payload[base+2:base+4],'little')
    strings=bytearray(payload[base+2+2*count:end])
    if encrypted:
        key=b'Avis Durgan'
        for i,value in enumerate(strings): strings[i]=value^key[i%len(key)]
    first_start=first_offset-(2+2*count)
    terminator=strings.find(0,first_start)
    first_message=bytes(strings[first_start:terminator])
    assert first_message and b'%' not in first_message and terminator>first_start
    source=b'G%m1!\0END'
    results=[]
    for owner,code,syms,basepc in (('CoCo',coco,cs,0x8000),('native',native,ns,0xa000)):
        d.write(0,bytes(syms['size']) if owner=='native' else bytes(0x800))
        d.write(0x73ff,source)
        d.write(0x7ef0,b'\x7e\0\x74\0\x60\0STACK')
        if owner=='CoCo':
            malformed=bytearray(bytes([count])+payload[base:base+2]+
                                 payload[base+2:base+2+2*count]+strings)
            table_string_start=1+2+2*count
            malformed[table_string_start+terminator]=ord('X')
            malformed[1:3]=(first_offset+len(first_message)).to_bytes(2,'little')
            adjacent=0x5000+first_offset+len(first_message)
            d.write(basepc,code);d.write(0x6000,bytes(2048))
            d.write(0x0251,bytes(480));d.write(0x0431,bytes(256))
            slot=bytearray(12);slot[3]=count;slot[10:12]=(0x5000).to_bytes(2,'big')
            d.write(0x3000,slot);d.write(0x62,b'\x30\0')
            d.write(0x5000,malformed[1:]);d.write(adjacent,b'\0')
            d.write(0x0157,b'\0');d.write(0x0158,b'\xff');d.write(0x015a,b'\x02')
            d.regs(pc=basepc+cs['FormatStr'],s=0x7ef0,dp=0,cc=0x50)
        else:
            resource=bytearray(payload)
            resource[base:base+2]=(first_offset+len(first_message)).to_bytes(2,'little')
            string_start=base+2+2*count
            resource[string_start+terminator]=ord('X')
            d.write(basepc,code);private=0x1000
            d.write(private,bytes(syms['size'])+b'GUARD')
            d.write(private+syms['resourcebase'],private.to_bytes(2,'big'))
            d.write(private+syms['vmstrings'],bytes(480))
            d.write(private+syms['vmvariables'],bytes(256))
            d.write(private+syms['assetmapbase'],b'\x40\0')
            d.write(private+syms['vmend'],code_end.to_bytes(2,'big'))
            d.write(private+syms['resourcelength'],len(resource).to_bytes(2,'big'))
            d.write(private+syms['resourcestored'],len(resource).to_bytes(2,'big'))
            d.write(private+syms['assetmapped'],b'\1');d.write(0x4000,resource)
            d.write(private+syms['fillstack']-1,b'G')
            d.write(private+syms['fillstack']+4096,b'H')
            d.regs(pc=basepc+ns['GameFormatMessage'],x=0x7400,s=0x7ef0,
                   u=private,dp=private>>8,cc=0x50)
        d.call('c');regs=d.regs()
        assert (regs['pc'],regs['s'])==(0x7e00,0x7ef2),(owner,regs)
        assert d.read(0x7ef6,5)==b'STACK' and d.read(0x73ff,len(source))==source
        if owner=='CoCo':
            output=d.read(0x6000,512).split(b'\0')[0]
            assert output==first_message+b'!',(output,first_message)
            assert d.read(adjacent,1)==b'\0'
        else:
            assert regs['cc']&1 and regs['b']==syms['E$BMode'],regs
            assert d.read(private+syms['formatdepth'],1)==b'\0'
            assert d.read(private+syms['parserreadlength'],2)==b'\0\0'
            assert d.read(private+syms['fillstack']-1,1)==b'G'
            assert d.read(private+syms['fillstack']+4096,1)==b'H'
            assert d.read(private+syms['fillstack']+2048,1)==b'\0'
            assert d.read(0x4000,len(resource))==resource
            assert d.read(private+syms['size'],5)==b'GUARD'
            assert d.read(0xa000,len(native))==native
            output=b''
        results.append(output)
    assert results==[first_message+b'!',b'']
    print('PASS: unterminated original Space Quest II message; CoCo scans the controlled adjacent NUL, while Wild Bits rejects at the declared section boundary and restores state')


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-index-') as name:
        tmp = Path(name)
        coco, cs = compile_module(ROOT/'objs/mnln.asm', tmp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame', defines=('WILDBITS=1',))
        edges = [b'', b'0', b'255', b'256', b'257', b'999', b'65535', b'999999999',
                 b'000000255', b'0000256', b'0'*255, b'0'*256, b'0'*257]
        cases = [str(n).encode()+b'!' for n in range(256)] + edges
        for byte in range(256):
            if not 48 <= byte <= 57:
                cases += [bytes([byte])+b'123', b'123'+bytes([byte])+b'4']
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=900)
        calls = 0
        try:
            d.write(0xffdf, b'\0'); d.write(0xff90, b'\x4c')
            d.write(0xff91, b'\x01'); d.write(0xffa8, bytes(range(8)))
            d.breakpoint(0x7e00)
            for owner, code, syms, bases in [('CoCo', coco, cs, (0x8000, 0x9000)),
                                            ('native', native, ns, (0x9000, 0xa000))]:
                private = 0 if owner == 'CoCo' else 0x1000
                for base in bases:
                    d.write(base, code)
                    if private:
                        d.write(private, bytes(syms['size'])+b'GUARD')
                        d.write(private+syms['resourcebase'], private.to_bytes(2, 'big'))
                    for source in cases:
                        address = 0x7400
                        data = b'G'+source+b'\0END'
                        d.write(address-1, data)
                        if private:
                            d.write(private+syms['parserwordlength'], b'\0')
                            d.write(private+syms['parserbestlength'], b'\0')
                            before = d.read(private, syms['size']) if source in edges else None
                        d.write(0x7ef0, b'\x7e\x00STACK')
                        d.regs(pc=base+syms['ParseDecStr'], s=0x7ef0, x=address,
                               y=0x7777, u=private, dp=private >> 8, cc=0x50)
                        d.call('c'); regs = d.regs()
                        value, count, cursor, rejected = reference(source, False)
                        assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                        assert regs['u'] == private and regs['y'] == 0x7777
                        assert regs['x'] == address+cursor, (owner, source, cursor, regs)
                        assert regs['b'] == (syms['E$BMode'] if rejected else value), (owner, source, regs)
                        assert d.read(address-1, len(data)) == data
                        assert d.read(0x7ef2, 5) == b'STACK'
                        if private:
                            assert bool(regs['cc'] & 1) == rejected
                            assert d.read(private+syms['parserwordlength'], 1) == b'\0'
                            assert d.read(private+syms['parserbestlength'], 1) == b'\0'
                            assert d.read(private+syms['size'], 5) == b'GUARD'
                            if before is not None:
                                expected = bytearray(before)
                                assert d.read(private, syms['size']) == expected
                        calls += 1
                    if private:
                        variables = bytes(range(256))
                        d.write(private+syms['vmvariables'], variables)
                        cases_full = [(b'[%v'+str(n).encode()+b']', ('['+str(n)+']').encode(), 0)
                                      for n in range(256)]
                        cases_full += [(b'%v000255', b'255', 0), (b'%v'+b'0'*255, b'0', 0),
                                       (b'%v'+b'0'*257, b'0', 0), (b'%%', b'', 0), (b'%v256', b'0', 0), (b'%v999', b'231', 0), (b'%v', b'0', 0), (b'%w0', b'', 0)]
                        cases_full += [(s, None, syms['E$BMode']) for s in
                                       [b'%s12']]
                        cases_full += [(b'%v0|2', b'00', 0),
                                       (b'%v117:%v116|2:%v115|2', b'117:116:115', 0),
                                       (b'%v7|2', b'07', 0), (b'%v255|1', b'255', 0),
                                       (b'%v7|0!', b'7!', 0),
                                       (b'%v7|255', b'0'*254+b'7', 0),
                                       (b'%v7|256', b'7', 0),
                                       (b'%v7|', b'7', 0),
                                       (b'%v7|002!', b'07!', 0),
                                       (b'%v7|2%v7', b'077', 0),
                                       (b'%s0|2', b'|2', 0),
                                       (b'%v7|255'*9, None, syms['E$BMode'])]
                        # Unknown two-byte escapes match the CoCo skip policy;
                        # following digits remain literal text.
                        cases_full += [(b'%' + bytes([letter]) + b'1', b'1', 0)
                                       for letter in range(1, 256) if letter not in b'wvsmog%']
                        output = private+syms['fillstack']+2048
                        for source, wanted, error in cases_full:
                            d.write(address, source+b'\0')
                            d.write(private+syms['fillstack']-1, b'G')
                            d.write(private+syms['fillstack']+4096, b'H')
                            d.write(0x7ef0, b'\x7e\x00STACK')
                            d.regs(pc=base+syms['GameFormatMessage'], s=0x7ef0,
                                   x=address, u=private, dp=private >> 8, cc=0x50)
                            d.call('c'); regs = d.regs()
                            assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                            assert bool(regs['cc'] & 1) == bool(error) and regs['b'] == error, (source, regs)
                            assert d.read(private+syms['formatdepth'], 1) == b'\0'
                            assert d.read(private+syms['vmvariables'], 256) == variables
                            assert d.read(private+syms['fillstack']-1, 1) == b'G'
                            assert d.read(private+syms['fillstack']+4096, 1) == b'H'
                            assert d.read(0x7ef2, 5) == b'STACK'
                            if wanted is not None:
                                assert regs['x'] == output
                                assert d.read(output, len(wanted)+1) == wanted+b'\0', (source, wanted)
                                assert d.read(private+syms['parserreadlength'], 2) == len(wanted).to_bytes(2, 'big')
                            calls += 1
                    assert d.read(base, len(code)) == code
            check_formatter_parity(d,coco,cs,native,ns,original_format_cases())
            check_formatter_recursion_bounds(d,coco,cs,native,ns)
            check_formatter_output_bound(d,coco,cs,native,ns)
            check_original_spacequest2_zero_message(d,coco,cs,native,ns)
            check_original_spacequest2_zero_message(d,coco,cs,native,ns,b'Adjacent\0')
            check_malformed_message_offset(d,coco,cs,native,ns)
            check_truncated_message_table(d,coco,cs,native,ns)
            check_unterminated_message(d,coco,cs,native,ns)
            print(f'PASS: {calls} actual CoCo/native index and native formatter calls; all byte values, every nondigit terminator, wrap/overflow and consumed cursor, leading zeros and count wrap, variable substitution/escape errors, frame cleanup, whole-state edges, guards/stack and immutable code')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
