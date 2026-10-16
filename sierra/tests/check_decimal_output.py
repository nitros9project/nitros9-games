#!/usr/bin/env python3
"""Run both real decimal converters and native expansion/overflow stack cleanup."""
from pathlib import Path
import subprocess
import itertools
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]
WIDE = [256, 257, 999, 1000, 9999, 10000, 32767, 32768, 65534, 65535]


def check_object_status(d, c, cs, tmp):
    """Compare the shared diagnostic's actual output before either modal backend."""
    n, ns = compile_module(ROOT/'objs/wbui.asm', tmp/'wbui-status')
    d.breakpoint(0x7e00, False)
    d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\1');d.write(0xffa8,bytes(range(8)));d.write(0x7e00,b'\x39');d.write(0x7e04,b'\x5f\x39');d.breakpoint(0x7e02)
    results={};calls=0
    for owner,code,syms,bases in [('CoCo',c,cs,(0x8000,0x9000)),('native',n,ns,(0x8000,0xa000))]:
     for base in bases:
      d.write(base,code)
      hook=base+cs['message_box'] if owner=='CoCo' else 0x7e00;d.breakpoint(hook)
      for obj,var,cycle,motion in itertools.product((0,63),(0,255),(0,1,2,3,255),(0,1,2,3,255)):
       d.write(0,bytes(0x6000));d.write(0x7000,bytes([var]));d.write(0x7df0,b'\x7e\x02STACK');d.write(0x7b00,b'LOWGUARD')
       record=bytearray(43);record[2:5]=bytes([obj,255,167]);record[0x1c:0x20]=bytes([160,168,255,1]);record[0x22:0x29]=bytes([motion,cycle,15,255,255,255,167])
       if owner=='CoCo':
        d.write(0x30,b'\x30\0');d.write(0x431+var,bytes([obj]));d.write(0x3000+43*obj,record)
       else:
        d.write(syms['resourcebase'],b'\0\0');d.write(syms['vmvariables']+var,bytes([obj]));d.write(syms['vmarguments'],bytes([var]));d.write(syms['vmobjects']+43*obj,record);d.write(syms['coldapi'],b'\x72\0');d.write(0x7210,(0x7e00-0x7200).to_bytes(2,'big'));d.write(0x721a,(0x7e04-0x7200).to_bytes(2,'big'));d.write(0x7212,(0x7e04-0x7200).to_bytes(2,'big'))
       d.regs(pc=base+syms['CmdObjStatusV'],s=0x7df0,y=0x7000,u=0,dp=0,cc=0x50);d.call('c');regs=d.regs();assert regs['pc']==hook,(owner,regs)
       ptr=regs['u'] if owner=='CoCo' else regs['x'];text=d.read(ptr,300).split(b'\0')[0];key=(obj,var,cycle,motion)
       if owner=='CoCo':
        if key in results:assert text==results[key]
        results[key]=text
       else:assert text==results[key],(key,text,results[key])
       d.breakpoint(hook,False);d.regs(pc=0x7e00);d.call('c');regs=d.regs();assert regs['pc']==0x7e02 and regs['s']==0x7df2,(owner,regs);assert d.read(0x7b00,8)==b'LOWGUARD';assert d.read(0x7df2,5)==b'STACK';d.breakpoint(hook)
       if owner=='native':assert d.read(base,len(code))==code
       calls+=1
      d.breakpoint(hook,False)
    print('PASS:',calls,'actual shared object-status calls, two bases, all cycle/motion classes, object/variable edges, exact reference text and stack/code guards')
    wide_calls=0
    values=sorted(set([0,1,9,10,15,16,99,100,255,256,4095,4096]+WIDE))
    for base in (0x8000,0xa000):
        d.write(base,n)
        for routine in ('WordUIntToDecStr','UIntToHexStr'):
            for value in values:
                d.write(0,bytes(ns['size']))
                d.write(ns['messagebuffer'],b'\xa5'*512)
                d.write(0x7df0,b'\x7e\x02STACK')
                d.write(0x7b00,b'LOWGUARD')
                d.regs(pc=base+ns[routine],s=0x7df0,x=0x7777,y=0x6666,u=0,dp=0,
                       a=value>>8,b=value&255,cc=0x50)
                d.call('c');regs=d.regs()
                expected=(str(value) if routine=='WordUIntToDecStr' else format(value,'X')).encode()
                start=ns['messagebuffer']+511-len(expected)
                assert regs['pc']==0x7e02 and regs['s']==0x7df2 and regs['x']==start
                assert regs['y']==0x6666 and regs['u']==0 and regs['a']==regs['b']==0
                assert d.read(start,len(expected)+1)==expected+b'\0',(routine,value,regs)
                assert d.read(ns['messagebuffer'],start-ns['messagebuffer'])==b'\xa5'*(start-ns['messagebuffer'])
                assert d.read(0x7b00,8)==b'LOWGUARD' and d.read(0x7df2,5)==b'STACK'
                assert d.read(base,len(n))==n
                wide_calls+=1
    print(f'PASS: {wide_calls} native diagnostic word decimal/hex conversions through 65535, two bases, bounded private buffers, exact registers/stack and immutable code')
    error_calls=0
    d.write(0x7e08,b'\xc6\xcb\x1a\x01\x39')
    for base in (0x8000,0xa000):
        d.write(base,n)
        for label,object_number,failed_callback,error in [
                ('unmap',0,18,203),('canvas',63,26,203),
                ('object64',64,None,187),('object255',255,None,187)]:
            d.write(0,bytes(ns['size']))
            d.write(ns['messagebuffer'],b'\xa5'*512)
            d.write(ns['vmarguments'],b'\xff')
            d.write(ns['vmvariables']+255,bytes([object_number]))
            d.write(ns['coldapi'],b'\x72\0')
            for callback in (18,26):
                target=0x7e08 if callback==failed_callback else 0x7e04
                d.write(0x7200+callback,(target-0x7200).to_bytes(2,'big'))
            before=d.read(0,ns['size'])
            d.write(0x7df0,b'\x7e\x02STACK');d.write(0x7b00,b'LOWGUARD')
            d.regs(pc=base+ns['CmdObjStatusV'],s=0x7df0,x=0x7777,y=0x6666,u=0,dp=0,cc=0x50)
            d.call('c');regs=d.regs()
            assert regs['pc']==0x7e02 and regs['s']==0x7df2 and regs['u']==0
            assert regs['cc']&1 and regs['b']==error,(label,regs)
            assert d.read(0,ns['size'])==before,(label,'private state changed')
            assert d.read(base,len(n))==n and d.read(0x7b00,8)==b'LOWGUARD'
            assert d.read(0x7df2,5)==b'STACK'
            error_calls+=1
    print(f'PASS: {error_calls} diagnostic unmap/canvas/index failures, unchanged private state and exact stack/private-base/error recovery')
    d.breakpoint(0x7e02, False)
    d.breakpoint(0x7e00)


def check_memory_info(d, coco, cs, tmp):
    """Verify actual reference formatting and native owned-memory categories."""
    code, syms = compile_module(ROOT/'objs/wbui.asm', tmp/'wbui-memory')
    d.breakpoint(0x7e00,False);d.breakpoint(0x7e02)
    d.write(0x7e00,b'\x39');d.write(0x7e04,b'\x5f\x39')
    for base in (0x8000,0x9000):
        d.write(0,bytes(0x6000));d.write(base,coco)
        heap=cs['SierraHeapBase']
        for address,value in [(0,heap+5000),(0x4b,2345),(0x4d,6789),(0x4f,12345),
                              (0x51,heap+1000),(0x53,heap+200),(0x55,heap+300),(0x57,65535)]:
            d.write(address,value.to_bytes(2,'big'))
        d.write(0x431,b'\xff');before=d.read(0,0x6000)
        d.write(0x7df0,b'\x7e\x02STACK');d.write(0x7b00,b'LOWGUARD')
        hook=base+cs['message_box'];d.breakpoint(hook)
        d.regs(pc=base+cs['CmdShowMemInfo'],s=0x7df0,u=0,y=0x7000,dp=0,cc=0x50)
        d.call('c');regs=d.regs();assert regs['pc']==hook
        text=d.read(regs['u'],200).split(b'\0')[0]
        # Preserve the actual legacy argument order, including the FFFF word.
        # Do not infer meanings from the decompiled heap-variable comments.
        expected=(b'room: 255\nheap size: 65535\nnow: 12345  max: 2345\nrm.0, etc.: 6789\n'
                  b'common size: 5000\nnow: 100  max: 800\ntables, etc.: 200\nmax script: 65535')
        assert text==expected,(text,expected)
        d.breakpoint(hook,False);d.regs(pc=0x7e00);d.call('c');regs=d.regs()
        assert regs['pc']==0x7e02 and regs['s']==0x7df2 and d.read(0,0x6000)==before
        assert d.read(0x7b00,8)==b'LOWGUARD' and d.read(0x7df2,5)==b'STACK'
    models=[[],[(0,1,1,0,512),(10,1,8,2,65535),(31,1,3,0,65535)],
            [(i,1,8,i%3,65535 if i==0 else (i*2111)&65535) for i in range(32)],
            [(i,255,255,0,65535) for i in range(32)]]
    count=0
    for base,header,room,model in itertools.product((0x8000,0xa000),(0x7100,0x7600),(0,255),models):
        d.write(base,code);d.write(0,bytes(syms['size']))
        d.write(syms['messagebuffer'],b'\xa5'*512)
        d.write(syms['coldapi'],b'\x72\0');d.write(syms['vmvariables'],bytes([room]))
        for callback in (18,26):d.write(0x7200+callback,(0x7e04-0x7200).to_bytes(2,'big'))
        d.write(0x7210,(0x7e00-0x7200).to_bytes(2,'big'))
        d.write(0x722c,((header-0x7200)&65535).to_bytes(2,'big'))
        d.write(header+2,(11111).to_bytes(2,'big'))
        for name in ('pictureowned','bitmapowned','gamebackgroundowned'):
            d.write(syms[name],bytes([room]))
        # Inactive slots deliberately contain stale counts/lengths; skip them.
        for i in range(32):
            p=syms['vmcache']+i*syms['VM_CACHE_ENTRY_BYTES']
            d.write(p+4,b'\xff\0\xff\xff')
        for index,owned,pages,kind,length in model:
            p=syms['vmcache']+index*syms['VM_CACHE_ENTRY_BYTES']
            d.write(p+1,bytes([owned]));d.write(p+4,bytes([pages,kind])+length.to_bytes(2,'big'))
        before=d.read(0,syms['size'])
        d.write(0x7df0,b'\x7e\x02STACK');d.write(0x7b00,b'LOWGUARD')
        d.breakpoint(0x7e00)
        d.regs(pc=base+syms['AuxMemoryInfo'],s=0x7df0,u=0,y=0x7200,dp=0,cc=0x50)
        d.call('c');regs=d.regs();assert regs['pc']==0x7e00,regs
        text=d.read(regs['x'],300).split(b'\0')[0]
        pages=sum(item[2] for item in model if item[1])
        largest=max([item[4] for item in model if item[1] and item[3]==0],default=0)
        expected=(f'room: {room}\ncode bytes: 11111\nprivate bytes: {syms["size"]}\nUI bytes: {len(code)}\n'
                  f'owned 8K pages:\ncache: {pages}  picture: {4 if room else 0}\n'
                  f'background: {4 if room else 0}  bitmap: {10 if room else 0}\nmax logic bytes: {largest}').encode()
        assert text==expected,(base,header,room,model,text,expected)
        d.breakpoint(0x7e00,False);d.call('c');regs=d.regs()
        assert regs['pc']==0x7e02 and regs['s']==0x7df2 and regs['u']==0
        after=bytearray(d.read(0,syms['size']))
        for start,length in [(syms['messagebuffer'],512),(syms['textpointer'],2)]:
            after[start:start+length]=before[start:start+length]
        assert after==before,'memory diagnostic altered caller state'
        assert d.read(base,len(code))==code and d.read(0x7b00,8)==b'LOWGUARD'
        assert d.read(0x7df2,5)==b'STACK'
        count+=1
    d.write(0x7e08,b'\xc6\xcb\x1a\x01\x39')
    for base,failed in itertools.product((0x8000,0xa000),(18,26)):
        d.write(base,code);d.write(0,bytes(syms['size']))
        d.write(syms['messagebuffer'],b'\xa5'*512)
        d.write(syms['coldapi'],b'\x72\0')
        for callback in (18,26):
            target=0x7e08 if callback==failed else 0x7e04
            d.write(0x7200+callback,(target-0x7200).to_bytes(2,'big'))
        before=d.read(0,syms['size'])
        d.write(0x7df0,b'\x7e\x02STACK');d.write(0x7b00,b'LOWGUARD')
        d.regs(pc=base+syms['AuxMemoryInfo'],s=0x7df0,u=0,dp=0,cc=0x50)
        d.call('c');regs=d.regs()
        assert regs['pc']==0x7e02 and regs['s']==0x7df2 and regs['u']==0
        assert regs['cc']&1 and regs['b']==203 and d.read(0,syms['size'])==before
        assert d.read(base,len(code))==code and d.read(0x7b00,8)==b'LOWGUARD'
        assert d.read(0x7df2,5)==b'STACK'
    print('PASS: four memory-report unmap/canvas failures, exact error/stack/private-base recovery and unchanged caller state')
    d.breakpoint(0x7e02,False);d.breakpoint(0x7e00)
    print(f'PASS: actual CoCo memory report and {count} native reports; dynamic header offsets, owned-only page totals, byte extents, largest logic, wide values, stack/private/code guards')


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-decimal-output-') as name:
        tmp = Path(name)
        coco, cs = compile_module(ROOT/'objs/mnln.asm', tmp/'mnln')
        native, ns = compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame', defines=('WILDBITS=1',))
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
                        start, end = 0x7400, 0x7403
                    else:
                        start, end = base+syms['NumConvBuf'], base+syms['NumConvEnd']
                    guards = d.read(start-1, 1), d.read(end+1, 1)
                    for value in list(range(256))+(WIDE if not private else []):
                        d.write(start, b'\xa5'*(end-start+1))
                        before = d.read(private, syms['size']) if private and value in (0, 9, 10, 99, 100, 255) else None
                        d.write(0x7ef0, b'\x7e\x00STACK')
                        d.regs(pc=base+syms['UIntToDecStr'], s=0x7ef0, x=end,
                               y=0x7777, u=private, a=value >> 8, b=value & 255,
                               dp=private >> 8, cc=0x50)
                        try:
                            d.call('c'); regs = d.regs()
                        except Exception:
                            print('Converter failure:', owner, hex(base), value, flush=True)
                            d.s.sendall(b'\x03')
                            try:
                                d.receive()
                                print('Stopped registers:', d.regs(), flush=True)
                            except Exception as diagnostic:
                                print('Stop diagnostic:', diagnostic, flush=True)
                            raise
                        wanted = str(value).encode()
                        assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                        assert regs['x'] == end-len(wanted) and regs['y'] == 0x7777
                        assert regs['u'] == 0 and regs['a'] == 0 and regs['b'] == 0
                        expected = b'\xa5'*(end-start-len(wanted))+wanted+b'\0'
                        assert d.read(start, end-start+1) == expected, (owner, value)
                        assert (d.read(start-1, 1), d.read(end+1, 1)) == guards
                        assert d.read(0x7ef2, 5) == b'STACK'
                        if private:
                            assert d.read(private+syms['size'], 5) == b'GUARD'
                            if before is not None:
                                expected_private = bytearray(before)
                                expected_private[syms['DivideDivisor']] = 10
                                expected_private[syms['DivideBits']] = 0
                                assert d.read(private, syms['size']) == expected_private
                        calls += 1
                    if private:
                        variables = bytes(range(256))
                        d.write(private+syms['vmvariables'], variables)
                        d.write(private+syms['vmstrings'], b'Z'*39+b'\0')
                        sourceaddr = private+syms['assetinput']
                        output = private+syms['fillstack']+2048
                        cases = [(b'[%v'+str(n).encode()+b']', ('['+str(n)+']').encode(), 0)
                                 for n in range(256)]
                        cases += [(b'%v0/%v9/%v10/%v99/%v100/%v255', b'0/9/10/99/100/255', 0)]
                        # Reach the output limit through bounded string substitution,
                        # then fail inside numeric output while its stack buffer is live.
                        cases += [(b'%s0'*52+b'A'*19+b'%v255', None, syms['E$BMode'])]
                        for source, wanted, error in cases:
                            # assetinput ends immediately before fillstack; its last
                            # byte is also the left guard of the source-frame area.
                            input_bytes = source+b'\0'+b'Q'*(510-len(source))+b'G'
                            d.write(sourceaddr, input_bytes)
                            d.write(private+syms['fillstack']-1, b'G')
                            d.write(private+syms['fillstack']+4096, b'H')
                            d.write(0x7ef0, b'\x7e\x00STACK')
                            d.regs(pc=base+syms['GameFormatMessage'], s=0x7ef0,
                                   x=sourceaddr, u=private, dp=private >> 8, cc=0x50)
                            d.call('c'); regs = d.regs()
                            assert regs['pc'] == 0x7e00 and regs['s'] == 0x7ef2
                            assert regs['u'] == private and regs['b'] == error
                            assert bool(regs['cc'] & 1) == bool(error)
                            assert d.read(sourceaddr, 512) == input_bytes
                            assert d.read(private+syms['vmvariables'], 256) == variables
                            assert d.read(private+syms['vmstrings'], 40) == b'Z'*39+b'\0'
                            assert d.read(private+syms['formatdepth'], 1) == b'\0'
                            assert d.read(private+syms['fillstack']-1, 1) == b'G'
                            assert d.read(private+syms['fillstack']+4096, 1) == b'H'
                            assert d.read(0x7ef2, 5) == b'STACK'
                            if wanted is not None:
                                assert regs['x'] == output
                                assert d.read(output, len(wanted)+1) == wanted+b'\0'
                            else:
                                assert d.read(private+syms['parserreadlength'], 2) == (2047).to_bytes(2, 'big')
                                assert d.read(output, 2048) == b'Z'*(52*39)+b'A'*19+b'\0'
                            calls += 1
                    current = bytearray(d.read(base, len(code)))
                    if not private:
                        # The legacy CoCo converter intentionally writes its private
                        # engine conversion buffer; all instruction bytes stay intact.
                        current[syms['NumConvBuf']:syms['NumConvEnd']+1] = code[syms['NumConvBuf']:syms['NumConvEnd']+1]
                    assert current == code
            check_object_status(d, coco, cs, tmp)
            check_memory_info(d, coco, cs, tmp)
            print(f'PASS: {calls} real decimal converter/formatter calls; all bytes, CoCo wide values through 65535, exact digits/termination, native message preservation, numeric output-limit failure/frame unwinding, two load addresses, state/buffer/stack guards and instruction immutability')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except subprocess.TimeoutExpired:
                emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__':
    main()
