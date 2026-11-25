#!/usr/bin/env python3
"""Execute owner cache discard paths; mock only platform/service boundaries."""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom, start_cpu


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-cache-lifetime-') as name:
        tmp=Path(name)
        coco,cs=compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
        native,ns=compile_module(ROOT/'objs/sierra.asm',tmp/'native',defines=('WILDBITS=1',))
        slot_bytes=ns['VM_CACHE_ENTRY_BYTES']; cache_bytes=32*slot_bytes
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=900)
        calls=0
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            d.breakpoint(0x7e00)
            def return_to_caller(regs,**updates):
                address=int.from_bytes(d.read(regs['s'],2),'big')
                d.regs(pc=address,s=regs['s']+2,**updates)
            for base in (0x8000,0x9000):
                d.write(base,coco)
                # Picture-list initialization must touch its relocated list
                # head only. A stale numeric address once erased an LBSR
                # operand in AddToPicImpl and crashed the KQ3 introduction.
                head=base+cs['PicListBuf']
                d.write(head,b'\x45\x67PICTS')
                expected=bytearray(d.read(base,len(coco)))
                expected[cs['PicListBuf']:cs['PicListBuf']+2]=b'\0\0'
                d.write(0x7ef0,b'\x7e\x00STACK')
                d.regs(pc=base+cs['PicListClear'],s=0x7ef0,dp=0,cc=0x50)
                d.call('c');regs=d.regs()
                assert regs['pc']==0x7e00 and regs['s']==0x7ef2,regs
                assert d.read(0x7ef2,5)==b'STACK'
                assert d.read(base,len(coco))==expected,'picture-list clear modified code or adjacent data'
                d.write(base,coco)
                hooks={base+cs[n]:n for n in ('PushScript','ClearBothRanges','CalcPriAddr','SwapObjRanges','SetLogicPage','ReportError')}
                for address in hooks:d.breakpoint(address)
                for target in range(3):
                    nodes=(0x7000,0x7010,0x7020)
                    records=bytearray(0x30)
                    for index,address in enumerate(nodes):
                        offset=index*16
                        records[offset:offset+2]=(nodes[index+1] if index<2 else 0).to_bytes(2,'big')
                        records[offset+2]=11+index
                        records[offset+3:offset+5]=(0x5000+index*0x100).to_bytes(2,'big')
                        records[offset+5]=3+index
                    d.write(0x6fff,b'G'+records+b'H')
                    d.write(base+cs['list_struct'],nodes[0].to_bytes(2,'big'))
                    d.write(base+cs['ListLastNode'],b'\x55\x55')
                    d.write(0xa,b'\x12\x34')
                    d.write(0x7ef0,b'\x7e\x00STACK')
                    d.regs(pc=base+cs['DiscardViewHelper'],s=0x7ef0,b=11+target,dp=0,cc=0x50)
                    trace=[]
                    for _ in range(20):
                        d.call('c');regs=d.regs()
                        if regs['pc']==0x7e00:break
                        hook=hooks[regs['pc']];trace.append(hook)
                        assert hook!='ReportError'
                        updates={'cc':regs['cc']&~1}
                        if hook=='CalcPriAddr':updates['u']=0x6000+target*0x100
                        if hook=='SetLogicPage':assert (regs['a']<<8|regs['b'])==0x1234
                        return_to_caller(regs,**updates)
                    else:raise AssertionError('CoCo discard did not return')
                    assert regs['s']==0x7ef2 and d.read(0x7ef2,5)==b'STACK'
                    predecessor=base+cs['list_struct'] if not target else nodes[target-1]
                    successor=nodes[target+1] if target<2 else 0
                    expected=bytearray(records)
                    if target:expected[(target-1)*16:(target-1)*16+2]=successor.to_bytes(2,'big')
                    assert d.read(0x7000,len(records))==expected
                    assert d.read(predecessor,2)==successor.to_bytes(2,'big')
                    assert d.read(0x55,2)==nodes[target].to_bytes(2,'big')
                    assert d.read(0x4f,2)==(0x6000+target*0x100).to_bytes(2,'big')
                    assert trace==['PushScript','ClearBothRanges','CalcPriAddr','SwapObjRanges','SetLogicPage']
                    assert d.read(0x6fff,1)==b'G' and d.read(0x7030,1)==b'H'
                    expected_head=successor if not target else nodes[0]
                    assert d.read(base+cs['list_struct'],2)==expected_head.to_bytes(2,'big')
                    assert d.read(base+cs['ListLastNode'],2)==predecessor.to_bytes(2,'big')
                    calls+=1
                for address in hooks:d.breakpoint(address,False)
                picture_hooks={base+cs[n]:n for n in
                               ('PushScript','ClearBothRanges','CalcPriAddr',
                                'SwapObjRanges','UpdateFreeSpace','ReportError')}
                for address in picture_hooks:d.breakpoint(address)
                picture_nodes=(0x7000,0x7007,0x700e)
                for target in range(3):
                    picture_records=bytearray(21)
                    for index,node in enumerate(picture_nodes):
                        offset=index*7
                        picture_records[offset:offset+2]=(picture_nodes[index+1]
                            if index<2 else 0).to_bytes(2,'big')
                        picture_records[offset+2]=11+index
                        picture_records[offset+3:offset+5]=(0x5000+index*0x100).to_bytes(2,'big')
                        picture_records[offset+5:offset+7]=(100+index).to_bytes(2,'big')
                    d.write(0x6fff,b'G'+picture_records+b'H')
                    d.write(base+cs['PicListBuf'],picture_nodes[0].to_bytes(2,'big'))
                    d.write(0x0431+250,bytes([11+target]))
                    d.write(0x2000,b'\xfaARGS')
                    d.write(0x7ef0,b'\x7e\x00STACK')
                    d.regs(pc=base+cs['cmd_discard_pic'],s=0x7ef0,y=0x2000,dp=0,cc=0x50)
                    trace=[]
                    for _ in range(20):
                        d.call('c');regs=d.regs()
                        if regs['pc']==0x7e00:break
                        hook=picture_hooks.get(regs['pc'])
                        assert hook and hook!='ReportError',('CoCo discard.pic',target,regs)
                        trace.append(hook);updates={'cc':regs['cc']&~1}
                        if hook=='CalcPriAddr':updates['u']=0x6000+target*0x100
                        ret=int.from_bytes(d.read(regs['s'],2),'big')
                        d.regs(pc=ret,s=regs['s']+2,**updates)
                    else:raise AssertionError('CoCo discard.pic did not return')
                    predecessor=base+cs['PicListBuf'] if target==0 else picture_nodes[target-1]
                    successor=picture_nodes[target+1] if target<2 else 0
                    expected_records=bytearray(picture_records)
                    if target:
                        expected_records[(target-1)*7:(target-1)*7+2]=successor.to_bytes(2,'big')
                    assert d.read(0x7000,21)==expected_records,('CoCo picture links',target)
                    assert d.read(predecessor,2)==successor.to_bytes(2,'big')
                    assert regs['s']==0x7ef2 and d.read(0x7ef2,5)==b'STACK'
                    assert regs['y']==0x2001 and d.read(0x2001,4)==b'ARGS'
                    assert trace==['PushScript','ClearBothRanges','CalcPriAddr',
                                   'SwapObjRanges','UpdateFreeSpace']
                    expected_head=successor if target==0 else picture_nodes[0]
                    assert d.read(base+cs['PicListBuf'],2)==expected_head.to_bytes(2,'big')
                    assert d.read(base+cs['PicListPtr'],2)==predecessor.to_bytes(2,'big')
                    assert d.read(0x6fff,1)==b'G' and d.read(0x7015,1)==b'H'
                    calls+=1
                for address in picture_hooks:d.breakpoint(address,False)
            for base in (0x9000,0xa000):
                d.write(base,native)
                hooks={base+ns[n]:n for n in ('AssetUnmap','AssetRelease')}
                for address in hooks:d.breakpoint(address)
                for target,fail in [(11,False),(12,False),(13,False),(99,False),(12,True)]:
                    private=0x1000;state=bytearray(ns['size'])
                    state[ns['resourcebase']:ns['resourcebase']+2]=private.to_bytes(2,'big')
                    state[ns['vmcurrent']]=0
                    for index,(kind,number) in enumerate([(0,10),(2,11),(2,12),(2,13),(3,12)]):
                        offset=ns['vmcache']+slot_bytes*index
                        state[offset:offset+10]=bytes([number,1,0,0x30+index,2,kind,0,50,0,50])
                    cache=bytes(state[ns['vmcache']:ns['vmcache']+cache_bytes])
                    d.write(private,state+b'GUARD')
                    d.write(0x7ef0,b'\x7e\x00STACK')
                    d.regs(pc=base+ns['VmDiscardResource'],s=0x7ef0,a=2,b=target,dp=private>>8,cc=0x50)
                    released=[]
                    for _ in range(12):
                        d.call('c');regs=d.regs()
                        if regs['pc']==0x7e00:break
                        hook=hooks[regs['pc']]
                        updates={'cc':regs['cc']&~1,'b':0}
                        if hook=='AssetRelease':
                            released.append(int.from_bytes(d.read(private+ns['assetfirst'],2),'big'))
                            assert d.read(private+ns['assetowned'],1)==b'\x01'
                            if fail:updates.update(cc=regs['cc']|1,b=0xd3)
                            else:d.write(private+ns['assetowned'],b'\0')
                        return_to_caller(regs,**updates)
                    else:raise AssertionError('native discard did not return')
                    expected=bytearray(cache)
                    if target!=99 and not fail:expected[slot_bytes*(target-10)+1]=0
                    assert d.read(private+ns['vmcache'],cache_bytes)==expected
                    assert released==([] if target==99 else [0x30+target-10])
                    assert bool(regs['cc']&1)==fail,(base,target,fail,regs)
                    assert regs['b']==(0xd3 if fail else 0)
                    if not fail:
                        assert d.read(private+ns['assetfirst'],2)==b'\0\x30'
                        assert d.read(private+ns['resourcekind'],1)==b'\0'
                    assert d.read(private+ns['assetowned'],1)==b'\0'
                    assert regs['s']==0x7ef2 and d.read(0x7ef2,5)==b'STACK'
                    assert d.read(private+ns['size'],5)==b'GUARD'
                    assert d.read(base,len(native))==native
                    calls+=1
                    if fail:
                        d.write(0x7ef0,b'\x7e\x00STACK')
                        d.regs(pc=base+ns['VmDiscardResource'],s=0x7ef0,a=2,b=target,dp=private>>8,cc=0x50)
                        retry_releases=[]
                        for _ in range(12):
                            d.call('c');regs=d.regs()
                            if regs['pc']==0x7e00:break
                            hook=hooks[regs['pc']]
                            if hook=='AssetRelease':
                                retry_releases.append(int.from_bytes(d.read(private+ns['assetfirst'],2),'big'))
                                assert d.read(private+ns['assetowned'],1)==b'\x01'
                                d.write(private+ns['assetowned'],b'\0')
                            return_to_caller(regs,cc=regs['cc']&~1,b=0)
                        else:raise AssertionError('discard retry did not return')
                        expected[slot_bytes*(target-10)+1]=0
                        assert retry_releases==[0x30+target-10]
                        assert d.read(private+ns['vmcache'],cache_bytes)==expected
                        assert not regs['cc']&1 and regs['b']==0
                        assert d.read(private+ns['assetfirst'],2)==b'\0\x30'
                        assert d.read(private+ns['assetowned'],1)==b'\0'
                        assert regs['s']==0x7ef2 and d.read(0x7ef2,5)==b'STACK'
                        assert d.read(base,len(native))==native
                        calls+=1
                for target in (11,12,13):
                    private=0x1000;state=bytearray(ns['size'])
                    state[ns['resourcebase']:ns['resourcebase']+2]=private.to_bytes(2,'big')
                    state[ns['vmcurrent']]=0;state[ns['vmopcode']]=27
                    state[ns['vmarguments']]=250;state[ns['replaylimit']]=0
                    state[ns['vmvariables']+250]=target
                    for index,(kind,number) in enumerate([(0,10),(1,11),(1,12),(1,13)]):
                        offset=ns['vmcache']+slot_bytes*index
                        state[offset:offset+12]=bytes([number,1,0,0x30+index,2,kind,0,50,0,50,0,0])
                    cache=bytes(state[ns['vmcache']:ns['vmcache']+cache_bytes])
                    d.write(private,state+b'GUARD')
                    d.write(0x7ef0,b'\x7e\x00STACK')
                    d.regs(pc=base+ns['GameDiscardPicture'],s=0x7ef0,
                           dp=private>>8,u=private,cc=0x50)
                    released=[]
                    for _ in range(12):
                        d.call('c');regs=d.regs()
                        if regs['pc']==0x7e00:break
                        hook=hooks.get(regs['pc']);assert hook,('native discard.pic',target,regs)
                        updates={'cc':regs['cc']&~1,'b':0}
                        if hook=='AssetRelease':
                            released.append(int.from_bytes(d.read(private+ns['assetfirst'],2),'big'))
                            assert d.read(private+ns['assetowned'],1)==b'\x01'
                            d.write(private+ns['assetowned'],b'\0')
                        ret=int.from_bytes(d.read(regs['s'],2),'big')
                        d.regs(pc=ret,s=regs['s']+2,**updates)
                    else:raise AssertionError('native discard.pic did not return')
                    expected=bytearray(cache);slot=target-10
                    expected[slot*slot_bytes+1]=0
                    assert d.read(private+ns['vmcache'],cache_bytes)==expected
                    assert released==[0x30+slot]
                    assert d.read(private+ns['replayused'],2)==b'\0\0'
                    assert d.read(private+ns['assetfirst'],2)==b'\0\x30'
                    assert not d.read(private+ns['assetowned'],1)[0]
                    assert regs['s']==0x7ef2 and d.read(0x7ef2,5)==b'STACK'
                    assert d.read(private+ns['size'],5)==b'GUARD'
                    assert d.read(base,len(native))==native
                    calls+=1
                for address in hooks:d.breakpoint(address,False)
            print(f'PASS: relocated picture-list initialization preserves code; {calls} actual discard calls at two load addresses; CoCo successor-link preservation, '
                  'native typed single-slot release/absent/release failure, ownership, stack and code guards')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
