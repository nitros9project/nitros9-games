#!/usr/bin/env python3
"""Run the common executor with real CoCo/native command and condition handlers."""
from pathlib import Path
import subprocess
import tempfile
from check_instances import symbols
from check_wbres import idle_rom,start_cpu

ROOT=Path(__file__).resolve().parents[1]
NESTED_LOGIC_SCRIPTS=(
    # Root: literal call 1, then call.v through v242=2, then resume.
    bytes([3,240,1,22,1,3,241,42,3,242,2,23,242,3,243,84,0]),
    # Logic 1: call.v through v245=3, then resume in its caller.
    bytes([3,245,3,23,245,3,246,33,0]),
    bytes([3,247,22,0]),
    bytes([3,248,33,0]),
)
NESTED_LOGIC_EXPECTED={240:1,241:42,242:2,243:84,245:3,246:33,247:22,248:33}
OPCODE_110_SCRIPT=bytes([3,249,73,12,221,110,255,4,250,249,0])
CASES=[
    (b'\0',{},set()),
    # Observe increment and decrement independently: the two copied results
    # prevent a net-zero final value from hiding either command's behavior.
    (bytes([3,0,7,1,0,4,250,0,2,0,4,251,0,0]),
     {0:7,250:8,251:7},set()),
    # Exercise immediate and variable assignment/add/subtract in sequence,
    # with saved checkpoints exposing each wrapped byte result.
    (bytes([3,0,250,5,0,10,4,250,0,3,1,7,6,0,1,4,251,0,
            7,0,15,4,252,0,3,2,3,8,0,2,4,253,0,0]),
     {0:249,1:7,2:3,250:4,251:11,252:252,253:249},set()),
    # Set/reset/toggle flags through literal and variable flag numbers.
    (bytes([3,0,203,3,1,204,3,2,205,12,200,12,201,13,201,
            14,202,12,204,15,0,16,1,17,2,0]),
     {0:203,1:204,2:205},{200,202,203,205}),
    # Operand bytes resemble return/branch opcodes: both must be consumed.
    *[(bytes([155,a,b,3,250,42,0]),{250:42},set())
      for a,b in ((0,0),(254,255),(255,254),(3,255),(255,3))],
    # CoCo PC-compatibility stubs and zero-operand no-ops. Operand bytes
    # deliberately resemble VM return/branch/condition markers. A command
    # after each stub proves exact consumption through both real executors.
    *[(bytes([3,249,73,12,221,opcode,*operands,4,250,249,0]),
       {249:73,250:73},{221})
      for opcode,count in ((144,1),(175,1),(179,4),(180,2))
      for operands in (bytes(count),bytes([255])*count,bytes([254])*count,
                       bytes((3+i)%256 for i in range(count)),
                       bytes((255-i)%256 for i in range(count)))],
    *[(bytes([3,249,73,12,221,opcode,4,250,249,0]),
       {249:73,250:73},{221})
      for opcode in (100,127,163,164,173,176,178,181)],
    (OPCODE_110_SCRIPT,{249:73,250:73},{221}),
    # AGI bytecode can have two legal decodings of the same bytes. This
    # models Manhunter I logic 159's jump into a condition's skip operand.
    *[(prefix+bytes.fromhex('ff 01 00 00 ff 03 00 fe 05 00 ff 01 00 01 ff 08 00 84 03 fa 2a 00 00 00 00 03 fa 49 00'),wanted,set())
      for prefix,wanted in ((b'',{250:42}),(bytes([3,0,1]),{0:1,250:42}),
                            (bytes([3,0,2]),{0:2,250:73}))],
    # Manhunter I logic 159: the IF at byte 438 reads bytes 443..444 as its
    # skip displacement, while the jump at 245 can enter byte 443 as subv.
    # Exercise both decodings with the original instruction bytes, relocated
    # into small controlled scripts (without copying game assets into tests).
    (bytes.fromhex('03 5f 00 03 20 01 ff 02 5f 20 ff 08 00 84 00 00 00 00 00 00 00 03 fa 2a 00'),
     {95:0,32:1,250:42},set()),
    (bytes.fromhex('03 00 0a 03 84 04 fe c3 00') + bytes(195) + bytes.fromhex('08 00 84 00'),
     {0:6,132:4},set()),
    # Predicate zero is CoCo's constant-true catalog entry, not return.
    (bytes.fromhex('ff 00 ff 03 00 03 fa 2a 00'),{250:42},set()),
    (bytes.fromhex('ff fd 00 ff 03 00 03 fa 2a 00'),{},set()),
    (bytes.fromhex('ff fc 00 fd 00 fc ff 03 00 03 fa 2a 00'),{250:42},set()),
    (bytes.fromhex('ff 01 00 01 00 ff 03 00 03 fa 2a 00'),{},set()),
    (bytes.fromhex('ff 01 00 00 00 ff 03 00 03 fa 2a 00'),{250:42},set()),
    (bytes([3,255,250,1,255,2,0,3,0,7,5,0,250,7,0,2,12,255,14,255,12,200,0]),{0:255,255:251},{200}),
    (bytes([254,3,0,3,0,99,3,0,42,0]),{0:42},set()),
    (bytes([3,0,0,1,0,255,3,0,3,255,3,0,254,244,255,0]),{0:3},set()),
    (bytes([3,0,7,3,1,8,12,200,255,252,1,0,8,1,0,7,252,253,1,1,9,255,3,0,3,250,99,0]),{0:7,1:8,250:99},{200}),
    (bytes([3,0,7,255,1,0,8,1,1,255,255,3,0,3,250,99,0]),{0:7},set()),
    (bytes([12,255,255,253,253,7,255,255,3,0,3,250,99,0]),{250:99},{255}),
    (bytes([3,0,7,255,252,1,0,8,1,0,9,252,255,3,0,3,250,99,0]),{0:7},set()),
    # Exercise all three AGI indirect-variable commands inside a complete
    # script. Index variables point to both edge slots (v0 and v255), and
    # each indirect write is read back through the actual command dispatcher.
    (bytes([3,250,255,3,255,42,9,250,255,10,249,250,11,250,88,
            10,248,250,3,250,0,3,0,19,10,246,250,11,250,6,
            9,250,255,0]),
     {0:88,246:19,248:88,249:42,250:0,255:88},set()),
]


def check_scan_start(d, owner, code, syms, base):
    """Compare CoCo pointers and native per-cache offsets for scan markers."""
    d.write(base, code)
    d.breakpoint(0x7e00)
    try:
        for slot_index, start in ((0, 0x5600), (1, 0x6100)):
            if owner == 'CoCo':
                slot = start + 0x100
                d.write(0x0062, slot.to_bytes(2, 'big'))
                d.write(slot + 6, start.to_bytes(2, 'big'))
                d.write(slot + 8, b'\xA5\x5A')
                scan_address = slot + 8
                start_value = start
                set_handler = 'cmd_set_scan_start'
                reset_handler = 'cmd_reset_scan_start'
                dp = 0
                database = 0
            else:
                dp = 0x10
                database = 0x1000
                d.write(database + syms['resourcebase'], database.to_bytes(2, 'big'))
                d.write(database + syms['vmcurrent'], bytes([slot_index]))
                d.write(database + syms['vmip'], bytes(2))
                entry = database + syms['vmcache'] + slot_index * 12
                d.write(entry + 10, b'\0\x02')
                scan_address = entry + 10
                start_value = 2
                set_handler = 'VmCommandScanStart'
                reset_handler = 'VmCommandScanReset'

            def invoke(handler, y):
                if owner == 'native':
                    d.write(database + syms['vmip'], y.to_bytes(2, 'big'))
                d.write(0x7ef0, b'\x7e\x00STACK')
                d.regs(pc=base + syms[handler], s=0x7ef0, dp=dp,
                       u=database, y=y, cc=0x50)
                d.call('c')
                r=d.regs()
                assert r['pc']==0x7e00 and r['s']==0x7ef2,(owner,handler,r)

            # The CoCo Y is an absolute pointer; Wild Bits stores the matching
            # offset in that logic's owned cache entry.
            mark = start + 0x12 if owner == 'CoCo' else 0x12
            invoke(set_handler, mark)
            stored = int.from_bytes(d.read(scan_address, 2), 'big')
            assert stored == mark,(owner,'set.scan.start',slot_index,stored,mark)
            invoke(reset_handler, 0)
            restored = int.from_bytes(d.read(scan_address, 2), 'big')
            assert restored == start_value,(owner,'reset.scan.start',slot_index,restored,start_value)
            if slot_index == 1:
                if owner == 'CoCo':
                    first_scan = int.from_bytes(d.read(0x5708, 2), 'big')
                    assert first_scan == 0x5600, (owner,'scan-start slot isolation',first_scan)
                else:
                    first_scan = int.from_bytes(d.read(database + syms['vmcache'] + 10, 2), 'big')
                    assert first_scan == 2, (owner,'scan-start cache isolation',first_scan)
        if owner == 'CoCo':
            assert d.read(0x0062, 2)==(0x6200).to_bytes(2,'big')
    finally:
        d.breakpoint(0x7e00,False)


def check_preloaded_nested_call(d, code, syms, base):
    """Execute the same nested call graph used by the native loader fixture."""
    d.write(base,code)
    d.write(0x002e,base.to_bytes(2,'big'))
    d.run(base+syms['PatchCmdTable'])
    d.run(base+syms['FixupEvalTbl'])
    scripts=NESTED_LOGIC_SCRIPTS
    slots=(0x3000,0x3100,0x3200,0x3300)
    starts=(0x4000,0x4100,0x4200,0x4300)
    table=base+syms['LogicTableData']
    d.write(table,slots[0].to_bytes(2,'big'))
    for index,(slot,start,script) in enumerate(zip(slots,starts,scripts)):
        following=slots[index+1] if index+1<len(slots) else 0
        entry=(following.to_bytes(2,'big')+bytes([index,0])+bytes(2)+
               start.to_bytes(2,'big')+start.to_bytes(2,'big')+bytes(2))
        d.write(slot,entry)
        d.write(start,script+b'GUARD')
    initialized=d.read(base,len(code))
    d.write(0x0062,slots[0].to_bytes(2,'big'))
    d.write(0x0431,bytes(256))
    d.write(0x01ae,bytes(32))
    d.write(0x7ef0,b'\x7e\x00STACK')
    d.breakpoint(0x7e00)
    d.breakpoint(base+syms['SetLogicPage'])
    try:
        d.regs(pc=base+syms['ExecLogicScript'],s=0x7ef0,dp=0,u=0,y=0,cc=0x50)
        for _ in range(64):
            d.call('c')
            regs=d.regs()
            if regs['pc']==0x7e00:
                break
            assert regs['pc']==base+syms['SetLogicPage'],('CoCo nested-call page transition',regs)
            ret=int.from_bytes(d.read(regs['s'],2),'big')
            d.regs(pc=ret,s=regs['s']+2)
        else:
            raise AssertionError('CoCo nested-call fixture did not return')
        assert regs['s']==0x7ef2 and d.read(0x7ef2,5)==b'STACK',regs
        assert regs['y']==starts[0]+len(scripts[0]),('CoCo root cursor not restored',regs)
        variables=d.read(0x0431,256)
        expected=NESTED_LOGIC_EXPECTED
        assert {i:variables[i] for i in expected}==expected,variables.hex()
        current=d.read(base,len(code))
        assert current==initialized,('CoCo call fixture modified executable code',
            [(i,a,b) for i,(a,b) in enumerate(zip(initialized,current)) if a!=b][:12])
        for start,script in zip(starts,scripts):
            assert d.read(start+len(script),5)==b'GUARD','nested CoCo call crossed script bound'
        return {index:variables[index] for index in expected}
    finally:
        d.breakpoint(base+syms['SetLogicPage'],False)
        d.breakpoint(0x7e00,False)


def check_native_nested_resource_calls(d,code,syms,base):
    """Run the same graph through native cache lookup and nested resource state."""
    private=0x1000
    d.write(base,code)
    d.write(private,bytes(syms['size'])+b'GUARD')
    d.write(private+syms['resourcebase'],private.to_bytes(2,'big'))
    d.write(private+syms['vmvariables'],bytes(256))
    d.write(private+syms['vmflags'],bytes(256))
    d.write(private+syms['vmcache'],bytes(32*syms['VM_CACHE_ENTRY_BYTES']))
    d.write(private+syms['vmdepth'],b'\0')
    d.write(private+syms['vmcurrent'],b'\0')
    d.write(private+syms['assetmapped'],b'\0')
    d.write(private+syms['asseterror'],b'\0')
    addresses=(0x7000,0x7100,0x7200,0x7300)
    by_first={0x30+index:address for index,address in enumerate(addresses)}
    for index,(script,address) in enumerate(zip(NESTED_LOGIC_SCRIPTS,addresses)):
        payload=len(script).to_bytes(2,'little')+script
        d.write(address,payload+b'GUARD')
        slot=private+syms['vmcache']+index*syms['VM_CACHE_ENTRY_BYTES']
        record=(bytes((index,1))+(0x30+index).to_bytes(2,'big')+
                bytes((1,0))+len(payload).to_bytes(2,'big')+
                len(payload).to_bytes(2,'big')+b'\0\2')
        assert len(record)==syms['VM_CACHE_ENTRY_BYTES']
        d.write(slot,record)
    root_payload=len(NESTED_LOGIC_SCRIPTS[0])+2
    for field,value in [('vmip',2),('vmend',root_payload),('vmsteps',0xffff)]:
        d.write(private+syms[field],value.to_bytes(2,'big'))
    d.write(private+syms['assetfirst'],(0x30).to_bytes(2,'big'))
    d.write(private+syms['assetblocks'],b'\1')
    d.write(private+syms['resourcekind'],b'\0')
    cache_size=32*syms['VM_CACHE_ENTRY_BYTES']
    cache_before=d.read(private+syms['vmcache'],cache_size)
    d.write(0x7ef0,b'\x7e\x00STACK')
    stop=0x7e00
    pointer=base+syms['AssetPointer']
    d.breakpoint(stop)
    d.breakpoint(pointer)
    d.regs(pc=base+syms['ExecuteLogic'],s=0x7ef0,dp=private>>8,
           u=private,cc=0x50)
    pointer_calls=0
    try:
        for _ in range(512):
            d.call('c')
            regs=d.regs()
            if regs['pc']==stop:
                break
            assert regs['pc']==pointer,('native nested-call unexpected service',regs)
            logical=(regs['a']<<8)|regs['b']
            first=int.from_bytes(d.read(private+syms['assetfirst'],2),'big')
            assert first in by_first,(first,logical,regs)
            return_address=int.from_bytes(d.read(regs['s'],2),'big')
            d.regs(pc=return_address,s=regs['s']+2,
                   u=by_first[first]+logical,cc=regs['cc']&~1)
            pointer_calls+=1
        else:
            raise AssertionError('native nested resource call did not return')
        assert pointer_calls>0
        assert regs['s']==0x7ef2 and d.read(0x7ef2,5)==b'STACK',regs
        assert int.from_bytes(d.read(private+syms['vmip'],2),'big')==root_payload
        assert int.from_bytes(d.read(private+syms['vmend'],2),'big')==root_payload
        assert d.read(private+syms['vmcurrent'],1)==b'\0'
        assert d.read(private+syms['assetfirst'],2)==b'\0\x30'
        variables=d.read(private+syms['vmvariables'],256)
        actual={index:variables[index] for index in NESTED_LOGIC_EXPECTED}
        assert actual==NESTED_LOGIC_EXPECTED,('native nested caller continuation',actual)
        assert d.read(private+syms['vmdepth'],1)==b'\0'
        assert d.read(private+syms['size'],5)==b'GUARD'
        assert d.read(private+syms['vmcache'],cache_size)==cache_before
        for address,script in zip(addresses,NESTED_LOGIC_SCRIPTS):
            assert d.read(address+2+len(script),5)==b'GUARD'
        return actual
    finally:
        d.breakpoint(pointer,False)
        d.breakpoint(stop,False)


def check_truncated_command_boundary(d,owner,code,syms,base,opcode,expected_value):
    """Record reference overread and bounded-EOF behavior for one command."""
    truncated=bytes((opcode,0))  # selected commands lack their final operand
    trailing=bytes((42,0))        # controlled adjacent bytes: value 42, then return
    if owner=='CoCo':
        d.write(base,code)
        d.write(0x002e,base.to_bytes(2,'big'))
        d.run(base+syms['PatchCmdTable'])
        d.run(base+syms['FixupEvalTbl'])
        expected_code=d.read(base,len(code))
        slot,start=0x3000,0x2000
        entry=(bytes(6)+start.to_bytes(2,'big')+start.to_bytes(2,'big')+
               bytes(2))
        d.write(0x0062,slot.to_bytes(2,'big'))
        d.write(slot,entry)
        d.write(0x0431,bytes(256))
        d.write(0x01ae,bytes(32))
        d.write(start,truncated+trailing+b'GUARD')
        entrypoint=base+syms['ExecLogicScript']
        page=base+syms['SetLogicPage']
        d.breakpoint(page)
        dp,u=0,0
    else:
        private,start=0x1000,0x7a00
        d.write(base,code)
        expected_code=code
        state=bytearray(syms['size'])
        state[syms['resourcebase']:syms['resourcebase']+2]=private.to_bytes(2,'big')
        state[syms['vmvariables']:syms['vmvariables']+256]=bytes(256)
        state[syms['vmflags']:syms['vmflags']+256]=bytes(256)
        state[syms['vmip']:syms['vmip']+2]=(2).to_bytes(2,'big')
        state[syms['vmend']:syms['vmend']+2]=(2+len(truncated)).to_bytes(2,'big')
        state[syms['vmsteps']:syms['vmsteps']+2]=b'\xff\xff'
        state[syms['assetmapbase']:syms['assetmapbase']+2]=start.to_bytes(2,'big')
        state[syms['assetpage']]=0
        state[syms['assetmapped']]=1
        d.write(private,state+b'GUARD')
        d.write(start,len(truncated).to_bytes(2,'little')+truncated+trailing+b'GUARD')
        entrypoint=base+syms['ExecuteLogic']
        page=None
        dp,u=private>>8,private

    stop=0x7e00
    d.write(0x7ef0,b'\x7e\x00STACK')
    d.breakpoint(stop)
    d.regs(pc=entrypoint,s=0x7ef0,dp=dp,u=u,cc=0x50)
    for _ in range(16):
        d.call('c')
        regs=d.regs()
        if regs['pc']==stop:
            break
        assert owner=='CoCo' and regs['pc']==page,(owner,'truncated command',regs)
        ret=int.from_bytes(d.read(regs['s'],2),'big')
        d.regs(pc=ret,s=regs['s']+2)
    else:
        raise AssertionError((owner,'truncated script did not return'))
    d.breakpoint(stop,False)
    if owner=='CoCo':
        d.breakpoint(page,False)
        assert d.read(0x0431,1)==bytes((expected_value,)),(
            owner,'reference did not consume controlled adjacent literal',opcode)
        assert regs['y']==start+len(truncated)+len(trailing),regs
        assert d.read(start+len(truncated)+len(trailing),5)==b'GUARD'
        outcome=('success',d.read(0x0431,1),regs['y']-start)
    else:
        assert regs['cc']&1 and regs['b']!=0,(owner,'bounded fetch did not report EOF',regs)
        assert int.from_bytes(d.read(private+syms['vmip'],2),'big')==2+len(truncated)
        assert d.read(private+syms['vmvariables'],1)==b'\0'
        assert d.read(private+syms['size'],5)==b'GUARD'
        assert d.read(start+2+len(truncated),len(trailing)+5)==trailing+b'GUARD'
        outcome=('EOF',d.read(private+syms['vmvariables'],1),
                 int.from_bytes(d.read(private+syms['vmip'],2),'big'))
    assert regs['s']==0x7ef2 and d.read(0x7ef2,5)==b'STACK',regs
    assert d.read(base,len(code))==expected_code,(owner,'truncated input modified code')
    return outcome


def original_logic159():
    """Load the exact overlapping instruction bytes from Manhunter I logic 159."""
    # Delayed import avoids check_lzw.py's existing compile_module dependency
    # on this harness during module initialization.
    from check_lzw import expand
    game=ROOT/'manhunter1';directory=(game/'logDir').read_bytes()
    entry=int.from_bytes(directory[159*3:160*3],'big')
    volume=(game/f'vol.{entry>>20}').read_bytes();offset=entry&0xfffff
    decoded=int.from_bytes(volume[offset+3:offset+5],'little')
    stored=int.from_bytes(volume[offset+5:offset+7],'little')
    packed=volume[offset+7:offset+7+stored]
    payload=packed if decoded==stored else expand(packed)
    assert len(payload)==decoded
    code=payload[2:2+int.from_bytes(payload[:2],'little')]
    assert len(code)==464
    assert code[245:248]==bytes.fromhex('fe c3 00')
    assert code[438:446]==bytes.fromhex('ff 02 5f 20 ff 08 00 84')
    return code


def check_original_logic159_overlap(d,owner,code,syms,base,original):
    """Execute original resource entry paths, changing only a post-path terminator."""
    cases=[]
    positions=[]
    # The real jump at 245 lands at 443 and decodes the original bytes
    # 08 00 84 as `subv v0,v132`; terminate at 446 after it returns.
    jump=bytearray(original);jump[446]=0
    values=bytearray(256);values[0]=10;values[132]=3
    expected=bytearray(values);expected[0]=7
    cases.append(('jump-to-subv',bytes(jump),245,values,expected))
    # The IF at 438 reads the original 08 00 displacement at 443..444. Its
    # true arm lands on 445; its false arm skips eight bytes to 453. Place a
    # return sentinel only at the selected arm's next opcode.
    take=bytearray(original);take[445]=0
    values=bytearray(256);values[95]=32;values[32]=32
    cases.append(('if-true',bytes(take),438,values,values))
    skip=bytearray(original);skip[453]=0
    values=bytearray(256);values[95]=31
    cases.append(('if-false',bytes(skip),438,values,values))

    for name,script,start,variables,expected in cases:
        initialized=d.read(base,len(code))
        if owner=='CoCo':
            d.write(0x0431,variables);d.write(0x01ae,bytes(32))
            d.write(0x0062,b'\x30\x00');d.write(0x3000,bytes(10))
            d.write(0x3008,(0x2000+start).to_bytes(2,'big'))
            d.write(0x2000,script+b'GUARD')
            entry=base+syms['ExecLogicScript'];private=0
            page_callback=base+syms['SetLogicPage'];d.breakpoint(page_callback)
            d.regs(pc=entry,s=0x7ef0,dp=0,u=0,y=0x2000+start,cc=0x50)
        else:
            private=0x1000;d.write(private,bytes(syms['size'])+b'GUARD')
            d.write(private+syms['vmvariables'],variables)
            d.write(0x8000,b'\0\0'+script+b'GUARD')
            for field,value in [('resourcebase',private),('assetmapbase',0x8000),
                                ('vmip',start+2),('vmend',len(script)+2)]:
                d.write(private+syms[field],value.to_bytes(2,'big'))
            d.write(private+syms['assetpage'],b'\0')
            d.write(private+syms['assetmapped'],b'\1')
            entry=base+syms['ExecuteLogic'];page_callback=0
            d.regs(pc=entry,s=0x7ef0,dp=private>>8,u=private,y=0,cc=0x50)
        d.write(0x7ef0,b'\x7e\x00STACK');d.breakpoint(0x7e00)
        for _ in range(12):
            d.call('c');r=d.regs()
            if r['pc']==0x7e00:break
            assert owner=='CoCo' and r['pc']==page_callback,(owner,name,r)
            ret=int.from_bytes(d.read(r['s'],2),'big')
            d.regs(pc=ret,s=r['s']+2)
        else:raise AssertionError((owner,name,'executor failed to return'))
        d.breakpoint(0x7e00,False)
        if owner=='CoCo':
            d.breakpoint(page_callback,False)
            actual=d.read(0x0431,256)
            cursor=r['y']-0x2000
            assert d.read(0x2000+len(script),5)==b'GUARD'
        else:
            assert not r['cc']&1 and r['b']==0,(owner,name,r)
            actual=d.read(private+syms['vmvariables'],256)
            ip=int.from_bytes(d.read(private+syms['vmip'],2),'big')
            cursor=ip-2
            assert d.read(private+syms['size'],5)==b'GUARD'
            assert d.read(0x8002+len(script),5)==b'GUARD'
        assert start<=cursor<=len(script),(owner,name,cursor)
        positions.append(cursor)
        assert actual==expected,(owner,name,cursor,
            [(i,actual[i],expected[i]) for i in range(256) if actual[i]!=expected[i]][:8])
        assert d.read(base,len(code))==initialized
    return positions


def compile_module(source,target,defines=(),listing=False):
    subprocess.run(['lwasm.orig','--6809','--format=os9','--no-warn=ifp1',
        '--pragma=pcaspcr,nosymbolcase,condundefzero','-I'+str(ROOT/'kingsquest1'),
        '-I'+str(ROOT/'objs'),'-I'+str(ROOT.parent.parent/'nitros9/defs'),
        '--map='+str(target)+'.map',*(['--list='+str(target)+'.list'] if listing else []),'-o'+str(target),*['-D'+value for value in defines],str(source)],check=True)
    return target.read_bytes(),symbols(Path(str(target)+'.map'))


def check_coco_shake_stub(d, code, syms, base):
    """Call CoCo's opcode-110 target directly to verify operand consumption."""
    d.write(base,code)
    d.write(0x5000,b'\xffGUARD')
    d.write(0x7ef0,b'\x7e\x00STACK')
    d.breakpoint(0x7e00)
    d.regs(pc=base+syms['cmd_shake_screen'],s=0x7ef0,y=0x5000,cc=0x50)
    d.call('c');r=d.regs()
    assert r['pc']==0x7e00 and r['s']==0x7ef2 and r['y']==0x5001,r
    assert d.read(0x5000,6)==b'\xffGUARD'
    assert d.read(0x7ef2,5)==b'STACK'
    d.breakpoint(0x7e00,False)


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-executor-') as tmp:
        tmp=Path(tmp);coco,cs=compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
        native,ns=compile_module(ROOT/'objs/sierra.asm',tmp/'native',defines=('WILDBITS=1',))
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            overlap_positions={}
            nested_states={}
            for owner,code,syms,bases in [('CoCo',coco,cs,(0x8000,0x9000)),('native',native,ns,(0x9000,0xa000))]:
                for base_index,base in enumerate(bases):
                    d.write(base,code)
                    if owner=='CoCo':
                        d.write(0x2e,base.to_bytes(2,'big'))
                        d.run(base+syms['PatchCmdTable']);d.run(base+syms['FixupEvalTbl'])
                    initialized_code=d.read(base,len(code))
                    for script,wanted,flagset in CASES:
                        if owner=='CoCo' and script==OPCODE_110_SCRIPT:
                            continue
                        variables=bytearray(256)
                        for index,value in wanted.items():variables[index]=value
                        if owner=='CoCo':
                            d.write(0x0431,bytes(256));d.write(0x01ae,bytes(32));d.write(0x68,b'\0')
                            d.write(0x62,b'\x30\x00');d.write(0x3000,bytes(10));d.write(0x3008,b'\x20\x00')
                            d.write(0x2000,script+b'GUARD')
                            entry=base+syms['ExecLogicScript'];private=0
                            page_callback=base+syms['SetLogicPage'];d.breakpoint(page_callback)
                        else:
                            private=0x1000;d.write(private,bytes(syms['size'])+b'GUARD')
                            for field,value in [('resourcebase',private),('assetmapbase',0x7a00),('vmip',2),('vmend',len(script)+2)]:
                                d.write(private+syms[field],value.to_bytes(2,'big'))
                            d.write(private+syms['assetmapped'],b'\1')
                            d.write(0x7a00,b'\0\0'+script+b'GUARD');entry=base+syms['ExecuteLogic']
                        d.write(0x7ef0,b'\x7e\x00STACK');d.breakpoint(0x7e00)
                        d.regs(pc=entry,s=0x7ef0,dp=private>>8,u=private,cc=0x50)
                        pages=0
                        for _ in range(10):
                            d.call('c');r=d.regs()
                            if r['pc']==0x7e00:break
                            assert owner=='CoCo' and r['pc']==page_callback,(owner,script.hex(),hex(page_callback),r)
                            # Only the physical page service is substituted;
                            # table dispatch, argument reads and handlers run.
                            pages+=1;ret=int.from_bytes(d.read(r['s'],2),'big')
                            d.regs(pc=ret,s=r['s']+2)
                        else:raise AssertionError('executor did not return')
                        d.breakpoint(0x7e00,False)
                        assert r['s']==0x7ef2 and d.read(0x7ef2,5)==b'STACK'
                        if owner=='CoCo':
                            d.breakpoint(page_callback,False);assert pages==1
                            actual=d.read(0x0431,256);packed=d.read(0x01ae,32)
                            flags={index for index in range(256) if packed[index>>3]&(128>>(index&7))}
                            assert d.read(0x2000+len(script),5)==b'GUARD'
                        else:
                            assert not r['cc']&1 and r['b']==0,(script.hex(),r,d.read(private+syms['vmip'],2).hex())
                            actual=d.read(private+syms['vmvariables'],256)
                            flags={index for index,value in enumerate(d.read(private+syms['vmflags'],256)) if value}
                            assert d.read(private+syms['size'],5)==b'GUARD'
                            assert d.read(0x7a02+len(script),5)==b'GUARD'
                        assert actual==variables,(owner,script,[(i,actual[i],variables[i]) for i in range(256) if actual[i]!=variables[i]][:8])
                        assert flags==flagset,(owner,script,flags,flagset)
                        assert d.read(base,len(code))==initialized_code
                    overlap_positions[(owner,base_index)]=check_original_logic159_overlap(
                        d,owner,code,syms,base,original_logic159())
                    check_scan_start(d,owner,code,syms,base)
                    malformed=[check_truncated_command_boundary(
                        d,owner,code,syms,base,opcode,value)
                        for opcode,value in ((3,42),(5,42),(7,214),
                                             (4,0),(6,0),(8,0))]
                    if owner=='CoCo':
                        assert malformed==[('success',bytes((value,)),4)
                                           for value in (42,42,214,0,0,0)],malformed
                    else:
                        assert malformed==[('EOF',b'\0',4)]*6,malformed
                    if owner=='CoCo':
                        nested_states[(owner,base_index)]=check_preloaded_nested_call(
                            d,code,syms,base)
                    else:
                        nested_states[(owner,base_index)]=check_native_nested_resource_calls(
                            d,code,syms,base)
            for base_index in range(2):
                coco_positions=overlap_positions[('CoCo',base_index)]
                native_positions=overlap_positions[('native',base_index)]
                assert coco_positions==native_positions,('logic 159 normalized cursor',base_index,coco_positions,native_positions)
                assert nested_states[('CoCo',base_index)]==nested_states[('native',base_index)],('nested resource caller state',base_index,nested_states[('CoCo',base_index)],nested_states[('native',base_index)])
            check_coco_shake_stub(d,coco,cs,0x8000)
            print(f'PASS: {len(CASES)} controlled scripts (opcode 110 through the native table; CoCo opcode-110 target directly) at two code bases; actual command/test table dispatch and mapped native byte fetch, indirect variable reads/writes through v0/v255, CoCo/native nested-resource caller restoration at both bases, direct scan-start/reset equivalence and cache isolation, CoCo adjacent-read vs bounded-native-EOF behavior for truncated assignn/addn/subn/assignv/addv/subv, all CoCo PC stubs/zero-operand no-ops, original Manhunter I logic 159 jump/IF true/IF false overlap entries, fixed-origin set.upper.left operand consumption, saturating/wrapping arithmetic, packed/byte flags, forward/backward jumps, bounded loop, mixed condition groups, return/frame guards and post-initialization code immutability')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
