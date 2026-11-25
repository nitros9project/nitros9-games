#!/usr/bin/env python3
"""Exercise static cel painting and persistence through real native commands."""
import argparse
from pathlib import Path
import subprocess
import tempfile
from check_wbres import exercise, idle_rom, start_cpu
from check_logic_executor import compile_module
from check_instances import symbols

ROWS=((1,1,None,2),(3,4,4,4),(5,None,None,None))

def assets(script,view,picture=b'\xff'):
    logic=len(script).to_bytes(2,'little')+script
    data=bytearray();offsets=[]
    for payload in (logic,picture,view):
        offsets.append(len(data));data+=b'\x12\x34\0'+len(payload).to_bytes(2,'little')*2+payload
    return {'/game/vol.0':bytes(data),'/game/logDir':b'\xff'*3+offsets[0].to_bytes(3,'big'),
            '/game/picDir':b'\xff'*3+offsets[1].to_bytes(3,'big'),'/game/viewDir':offsets[2].to_bytes(3,'big')}

def coco_priority_table(base):
    if base is None:
        return bytes(4 if y<48 else min(15,y//12+1) for y in range(168))
    divisor=(168-base)*168//10
    return bytes(4 if y<base else min(15,5+(y-base)*168//divisor) for y in range(168))

def render_coco_cel(d,code,syms,background,expected,viewnum,x,y,priority,control,
                    module_base=0xd000,priority_base=None):
    """Run CoCo's real shdw sprite and priority-box renderer on one cel."""
    # D000 stays beyond the picture buffer; a second low-RAM base is used only
    # after native execution is complete so it cannot overlap native scratch.
    stack=0xfdf0;stop=0xfde0;obj=0x3000;cel=0x4000
    patched=bytearray(code)
    # TwiddleMmu only swaps the view-data bank. This fixture puts the cel in
    # directly addressable RAM, so retain all renderer code and return at that
    # one memory-mapping service boundary.
    patched[syms['TwiddleMmu']]=0x39  # RTS
    d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01')
    d.write(0xffa8,bytes(range(8)))
    d.write(module_base,patched)
    top=y-2
    # Only the cel rectangle and a one-pixel guard need initialization. The
    # renderer's priority fallback scans only when a pixel priority is <= 2;
    # these fixtures use the normal background priority 4.
    for row in range(top-1,top+4):
        if 0<=row<168:
            if x>0:d.write(0x6040+row*160+x-1,bytes([background]))
            if x+4<160:d.write(0x6040+row*160+x+4,bytes([background]))
            d.write(0x6040+row*160+x,bytes([background])*4)
    record=bytearray(0x30)
    record[2]=viewnum;record[3]=x;record[4]=y
    record[8:10]=(0x5000).to_bytes(2,'big')
    record[0x10:0x12]=cel.to_bytes(2,'big')
    record[0x24]=(control<<4)|priority
    d.write(obj,record)
    # 4x3 cel: row runs are 1x2, transparent 1, 2x1; 3x1, 4x3; 5x1.
    d.write(cel,bytes([4,3,15,0x12,0xf1,0x21,0,0x31,0x43,0,0x51,0]))
    d.breakpoint(stop)
    d.write(stack,stop.to_bytes(2,'big'))
    d.write(0x05ee,b'\xff')  # force production TableInit after native fixtures
    d.regs(pc=module_base+syms['TableInit'],s=stack,dp=0,cc=0x50)
    d.call('c')
    assert d.regs()['pc']==stop,'CoCo priority table initialization did not return'
    if priority_base is not None:
        d.write(0x05ee,coco_priority_table(priority_base))
    d.write(stack,stop.to_bytes(2,'big')+obj.to_bytes(2,'big')+b'STACK')
    d.regs(pc=module_base+syms['ObjAddPicPri'],s=stack,dp=0,cc=0x50)
    d.call('c')
    regs=d.regs()
    assert regs['pc']==stop and regs['s']==stack+2,('CoCo ObjAddPicPri return',regs)
    assert d.read(stack+4,5)==b'STACK','CoCo ObjAddPicPri damaged caller stack guard'
    for row in range(top,top+3):
        at=row*160+x
        rendered=d.read(0x6040+at,4)
        wanted=expected[at:at+4]
        assert rendered==wanted,('CoCo rendered cel differs from Wild Bits pixels',row,rendered,wanted)
    for row in range(top-1,top+4):
        if not 0<=row<168:continue
        guards=[]
        if x>0:guards.append(d.read(0x6040+row*160+x-1,1))
        if x+4<160:guards.append(d.read(0x6040+row*160+x+4,1))
        assert b''.join(guards)==bytes([background])*len(guards),('CoCo cel renderer crossed its clipped pixel guard',row,guards)
    assert d.read(module_base,len(patched))==patched,'CoCo renderer modified its loaded code'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--module-root',type=Path)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='sierra-addpic-') as name:
        d,proc=start_cpu(idle_rom(Path(name)/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)))
            coco_shdw,coco_shdw_syms=compile_module(Path(__file__).resolve().parents[1]/'objs/shdw.asm',
                                                      Path(name)/'shdw-render')
            count=0
            coco_rendered=0
            coco_sample=None
            syms=symbols((args.module_root or Path(__file__).resolve().parents[1]/"objs")/"wbgame.map")
            cases=[(None,variable,priority,x,y,control) for variable in (False,True)
                   for priority in (0,3,15)
                   for x,y,control in ((20,30,4),(159,1,4),(20,48,0),(20,30,1),(20,30,2),(20,30,3))]
            cases += [(base,False,priority,20,y,control) for base,y in ((0,2),(80,80),(80,90),(167,167))
                      for priority in (0,15) for control in (0,4)]
            coco_expected={}
            for base,variable,priority,x,y,control in cases:
                operands=[0,0,0,x,y,priority,control]
                setup=([174,base] if base is not None else [])+[3,0,1,24,0,25,0,12,1]
                if variable:
                    for index,value in enumerate(operands):setup += [3,200+index,value]
                    command=[123]+list(range(200,207))
                else:command=[122]+operands
                # Force background restoration by drawing then erasing a
                # separate animated object after the static decoration.
                script=bytes(setup+command+[33,1,41,1,0,37,1,40,60,54,1,15,35,1,36,1,26,134,1,0])
                view=bytes([0,0,2,0,0,9,0,9,0,1,3,0,4,3,0x1f,0x12,0xf1,0x21,0,0x31,0x43,0,0x51,0])
                files=assets(script,view,b'\xf2\x06\xf8\0\0\xf3\xff' if base is not None else b'\xff')
                error,frame,state=exercise(d,files,module='wbgame',module_root=args.module_root,base=0xa000,
                    database=0x0000,window=0x8000,blocks=None,multiple=True,firstblock=0x10,frame_capture=True,capture=True)
                assert not error,(variable,priority,x,y,error)
                assert state['vmflags'][1]==1,'static decoration overwrote ego-hidden flag'
                expected=bytearray([1])*76800
                expected[8*320:176*320]=bytes([16])*(168*320)
                cx=min(x,156);cy=max(y,2)
                background=6 if base is not None else 4
                combined=bytearray([(background<<4)|15])*26880
                automatic=4 if cy<48 else cy//12+1
                if base is not None: automatic=4 if cy<base else min(15,5+(cy-base)*168//((168-base)*168//10))
                resolved=priority or automatic
                if resolved >= background:
                    for rownum,row in enumerate(ROWS):
                        for col,color in enumerate(row):
                            if color is not None:
                                address=(cy-2+rownum+8)*320+(cx+col)*2
                                expected[address:address+2]=bytes([color+1])*2
                                combined[(cy-2+rownum)*160+cx+col]=resolved*16+color
                assert frame==expected,(variable,priority,x,y,next((i for i,(a,b) in enumerate(zip(frame,expected)) if a!=b),None))
                if control <= 3:
                    height=min(3,cy+1 if cy<48 else (cy-48)%12+1)
                    if base is not None:
                        boundary=cy
                        def band(row):
                            return 4 if row<base else min(15,5+(row-base)*168//((168-base)*168//10))
                        while boundary and band(boundary-1)==band(cy):boundary-=1
                        height=min(3,cy-boundary+1)
                    for py in range(cy-height+1,cy+1):
                        for px in range(cx,cx+4):
                            if py in (cy-height+1,cy) or px in (cx,cx+3):
                                at=py*160+px
                                combined[at]=control*16+(combined[at]&15)
                coco_expected[(base,variable,priority,x,y,control)]=bytes(combined)
                first=int.from_bytes(d.read(0x0000+syms['picturefirst'],2),'big')
                actual=bytearray()
                for page in range(4):
                    d.write(0xffac,bytes([first+page]))
                    actual+=d.read(0x8000,8192)
                d.write(0xffac,b'\x04')
                assert actual[:26880]==combined,(variable,priority,x,y,control,'combined priority/color mismatch',[(i%160,i//160,a,b) for i,(a,b) in enumerate(zip(actual,combined)) if a!=b][:12])
                render_coco_cel(d,coco_shdw,coco_shdw_syms,background*16+15,
                                bytes(combined),0,cx,cy,priority,control,priority_base=base)
                coco_rendered+=1
                if coco_sample is None:
                    coco_sample=(background*16+15,bytes(combined),cx,cy,priority,control,base)
                count+=1
            # Compare the actual CoCo public command entry points at the
            # normalized AddToPicImpl request boundary for the same literal
            # and variable operand matrix. Below, CoCo's real ObjBlit and
            # ObjAddPicPri render the matching cel/background pixels directly.
            with tempfile.TemporaryDirectory(prefix='sierra-coco-addpic-') as refdir:
                coco, cs = compile_module(Path(__file__).resolve().parents[1]/'objs/mnln.asm',
                                          Path(refdir)/'mnln')
                refbase=0x8000
                d.write(refbase,coco)
                stop=0x7e00
                d.breakpoint(stop)
                d.breakpoint(refbase+cs['AddToPicImpl'])
                coco_calls=0
                for _,_,priority,x,y,control in cases:
                    for variable in (False,True):
                        values=[0,0,0,x,y,priority,control]
                        if variable:
                            indexes=list(range(200,207))
                            d.write(0x0431+200,bytes(values))
                            operands=indexes
                            command='cmd_add_to_pic_v'
                        else:
                            operands=values
                            command='cmd_add_to_pic'
                        d.write(0x05b2,b'\xaa'*6)
                        d.write(0x3000,bytes(operands)+b'GUARD')
                        d.write(0x7ef0,b'\x7e\x00STACK')
                        d.regs(pc=refbase+cs[command],s=0x7ef0,y=0x3000,dp=0,cc=0x50)
                        d.call('c')
                        r=d.regs()
                        # CoCo stores priority in the low nibble and the
                        # control-box value in the high nibble of its draw
                        # request, although the source operands are priority,
                        # then control.
                        expected=bytes(values[:5]+[(control<<4)|priority])
                        assert r['pc']==refbase+cs['AddToPicImpl'],(command,r)
                        assert d.read(0x05b2,6)==expected,(command,values,d.read(0x05b2,6),expected)
                        ret=int.from_bytes(d.read(r['s'],2),'big')
                        d.regs(pc=ret,s=r['s']+2)
                        d.call('c')
                        r=d.regs()
                        assert r['pc']==stop and r['s']==0x7ef2,(command,r)
                        assert r['y']==0x3007,(command,r)
                        assert d.read(0x3007,5)==b'GUARD'
                        assert d.read(0x7ef2,5)==b'STACK'
                        assert d.read(refbase,len(coco))==coco
                        coco_calls+=1
                d.breakpoint(refbase+cs['AddToPicImpl'],False)
                d.breakpoint(stop,False)
                # Run the real AddToPicImpl through view/object setup and
                # bounds/collision placement, then count calls to the range,
                # draw and page services. First pass returns from all $0701
                # calls; a later focused pass routes the draw selector into the
                # real renderer with the caller's object pointer on its stack.
                integrated=bytearray(coco)
                for helper in ('PushScript',
                               'ClearBothRanges','SwapObjRanges','SetLogicPage'):
                    counter={'PushScript':0x4011,'ClearBothRanges':0x4014,'SwapObjRanges':0x4015,
                             'SetLogicPage':0x4016}[helper]
                    address=cs[helper]
                    integrated[address:address+4]=bytes([0x7c,counter>>8,counter&255,0x39])
                # Supply a real loaded-view list node and one-loop/one-cel
                # CoCo view. SetViewForObj, view_find, SetLoopHelper and
                # SetCelHelper then execute from the actual module code.
                viewnode=0x3200;viewdata=0x5000
                integrated[cs['list_struct']:cs['list_struct']+2]=viewnode.to_bytes(2,'big')
                d.write(viewnode,bytes(2)+bytes([0])+viewdata.to_bytes(2,'big')+b'\x12\x34')
                view=bytearray(0x20)
                view[2]=1
                view[5:7]=(0x10).to_bytes(2,'little')
                view[0x10:0x13]=bytes([1,0x03,0x00])
                view[0x13:0x20]=bytes([4,3,15,0x12,0xf1,0x21,0,0x31,0x43,0,0x51,0,0])
                d.write(viewdata,view)
                d.write(refbase,integrated)
                # The real dispatcher is an OS-loaded $0701 service. Preserve
                # the two production call sites and their function selectors,
                # count each dispatch and return to AddToPicImpl.
                d.write(0x0701,bytes([0x7c,0x40,0x10,0x39]))
                d.breakpoint(stop)
                coco_impl_calls=0
                for _,_,priority,x,y,control in cases:
                    for variable in (False,True):
                        values=[0,0,0,x,y,priority,control]
                        if variable:
                            command='cmd_add_to_pic_v'
                            operands=list(range(200,207))
                            d.write(0x0431+200,bytes(values))
                        else:
                            command='cmd_add_to_pic'
                            operands=values
                        d.write(0x05b2,b'\xaa'*6)
                        d.write(0x3000,bytes(operands)+b'GUARD')
                        obj=bytearray(range(0x30))
                        obj[3:5]=b'\x41\x51'
                        obj[8:10]=b'\x04\x03'
                        obj[0x10:0x12]=b'\x41\x51'
                        d.write(0x3000+0x100,obj)
                        d.write(0x0036,(0x3100).to_bytes(2,'big'))
                        d.write(0x0030,(0x3100).to_bytes(2,'big')*2)
                        d.write(0x000a,b'\x5a\xa5')
                        d.write(0x0026,b'\x66\x00')
                        d.write(0x0028,b'\x66\x10')
                        d.write(0x01d6,b'\x00')
                        d.write(0x005c,b'\x01')
                        d.write(0x4010,bytes(7))
                        d.write(0x7ef0,b'\x7e\x00STACK')
                        d.regs(pc=refbase+cs[command],s=0x7ef0,y=0x3000,dp=0,cc=0x50)
                        d.call('c')
                        r=d.regs()
                        assert r['pc']==stop and r['s']==0x7ef2,(command,'AddToPicImpl integration return',r)
                        assert r['y']==0x3000+len(operands),(command,'operand cursor',r)
                        assert d.read(0x3000+len(operands),5)==b'GUARD'
                        assert d.read(0x7ef2,5)==b'STACK'
                        assert d.read(0x05b2,6)==bytes(values[:5]+[(control<<4)|priority])
                        updated=d.read(0x3100,0x30)
                        assert updated[3:5]==bytes([min(x,156),max(y,2)])
                        assert updated[0x1a:0x1c]==bytes([x,y])
                        assert updated[0x05]==0 and updated[0x06:0x08]==viewdata.to_bytes(2,'big')
                        assert updated[0x08:0x0a]==b'\x12\x34'
                        assert updated[0x0a:0x10]==bytes([0,1,0x50,0x10,0,1])
                        assert updated[0x10:0x12]==(viewdata+0x13).to_bytes(2,'big')
                        assert updated[0x12:0x14]==(viewdata+0x13).to_bytes(2,'big')
                        assert updated[0x14:0x16]==b'\x12\x34'
                        assert updated[0x24]==((control<<4)|priority)
                        assert updated[0x25]==2 and updated[0x26]==(8 if priority==0 else 12)
                        assert updated[0x1c:0x1e]==b'\x04\x03'
                        assert d.read(0x000a,2)==b'\x5a\xa5'
                        assert d.read(0x0021,1)==b'\x0f' and d.read(0x0019,1)==b'\x1b'
                        assert d.read(0x4010,7)==bytes([3,4,0,0,1,1,4]),(
                            command,'AddToPicImpl service call counts',d.read(0x4010,7))
                        mutable_start=cs['list_struct'];mutable_end=cs['list_clear']
                        assert d.read(refbase,mutable_start)==integrated[:mutable_start]
                        assert d.read(refbase+mutable_end,len(integrated)-mutable_end)==integrated[mutable_end:]
                        coco_impl_calls+=1
                d.breakpoint(stop,False)
                # Integrate the real CoCo draw entry with AddToPicImpl. Selector
                # A=$03 is placement (success is preseeded); A=$1B is the empty
                # priority-range-list draw. A=$0F dispatches to ObjAddPicPri.
                shdwbase=0xd000
                rendered_shdw=bytearray(coco_shdw)
                rendered_shdw[coco_shdw_syms['TwiddleMmu']]=0x39
                d.write(shdwbase,rendered_shdw)
                d.write(0x05ee,b'\xff')
                d.write(0x7ef0,stop.to_bytes(2,'big')+b'STACK')
                d.breakpoint(stop)
                d.regs(pc=shdwbase+coco_shdw_syms['TableInit'],s=0x7ef0,dp=0,cc=0x50)
                d.call('c')
                assert d.regs()['pc']==stop,'CoCo TableInit did not return before integrated renderer pass'
                draw_target=shdwbase+coco_shdw_syms['ObjAddPicPri']
                # Callback entry stack is: return address, pushed object ptr.
                # Tail-dispatching preserves precisely the layout ObjAddPicPri
                # expects (after it saves Y, the argument is at 4,s).
                dispatch=bytes([0x7c,0x40,0x10,       # count service call
                                0x81,0x03,0x27,0x07,   # placement: return
                                0x81,0x1b,0x27,0x03,   # empty priority list: return
                                0x7e,draw_target>>8,draw_target&255,
                                0x39])                 # service return
                d.write(0x0701,dispatch)
                coco_integrated_rendered=0
                for base,variable,priority,x,y,control in cases:
                    if base is not None or y>48:
                        continue
                    values=[0,0,0,x,y,priority,control]
                    if variable:
                        command='cmd_add_to_pic_v';operands=list(range(200,207))
                        d.write(0x0431+200,bytes(values))
                    else:
                        command='cmd_add_to_pic';operands=values
                    cy=max(y,2);height=cy+1
                    d.write(0x6040,bytes([0x4f])*(height*160))
                    d.write(0x05b2,b'\xaa'*6)
                    d.write(0x3000,bytes(operands)+b'GUARD')
                    obj=bytearray(range(0x30));obj[3:5]=b'\x41\x51';obj[8:10]=b'\x04\x03'
                    obj[0x10:0x12]=b'\x41\x51'
                    d.write(0x3100,obj)
                    d.write(0x0036,(0x3100).to_bytes(2,'big'))
                    d.write(0x0030,(0x3100).to_bytes(2,'big')*2)
                    d.write(0x000a,b'\x5a\xa5');d.write(0x0026,b'\x66\x00')
                    d.write(0x0028,b'\x66\x10');d.write(0x0019,b'\0')
                    d.write(0x01d6,b'\0');d.write(0x005c,b'\1')
                    d.write(0x4010,bytes(7));d.write(0x7ef0,stop.to_bytes(2,'big')+b'STACK')
                    d.regs(pc=refbase+cs[command],s=0x7ef0,y=0x3000,dp=0,cc=0x50)
                    d.call('c');r=d.regs()
                    assert (r['pc'],r['s'],r['y'])==(stop,0x7ef2,0x3000+len(operands)),(
                        command,'integrated pixel-render return',r)
                    assert d.read(0x4010,7)==bytes([3,4,0,0,1,1,4]),(
                        command,'integrated pixel-render service counts',d.read(0x4010,7))
                    expected=coco_expected[(None,variable,priority,x,y,control)]
                    actual=d.read(0x6040,height*160)
                    assert actual==expected[:height*160],(
                        command,'AddToPicImpl -> ObjAddPicPri/ObjBlit pixels',x,y,priority,control,
                        [(i%160,i//160,a,b) for i,(a,b) in enumerate(zip(
                            actual,expected[:height*160])) if a!=b][:10])
                    coco_integrated_rendered+=1
                d.breakpoint(stop,False)
            for operands in ([0,0,0,20,168,15,4],[0,0,0,20,30,16,4],
                             [0,0,0,20,30,15,16],[0,2,0,20,30,15,4],[0,0,1,20,30,15,4]):
                script=bytes([3,0,1,24,0,25,0,122]+list(operands)+[134,1,0])
                error,_=exercise(d,assets(script,view),module='wbgame',module_root=args.module_root,base=0xa000,
                    database=0x0000,window=0x8000,blocks=None,multiple=True,firstblock=0x10)
                assert error,(operands,error)
            # A bounded replay log must report overflow before painting.
            script=bytes([3,0,1,24,0,25,0,142,1,122,0,0,0,20,30,15,4,134,1,0])
            error,_=exercise(d,assets(script,view),module='wbgame',module_root=args.module_root,base=0xa000,
                database=0x0000,window=0x8000,blocks=None,multiple=True,firstblock=0x10)
            assert error==207,error
            assert coco_sample is not None
            render_coco_cel(d,coco_shdw,coco_shdw_syms,*coco_sample[:2],0,
                            *coco_sample[2:6],module_base=0x1000,
                            priority_base=coco_sample[6])
            coco_rendered+=1
            print(f'PASS: {count} immediate/variable static cel draws, default/custom/hidden/fixed priority, control-box band heights, priority-6 occlusion, clipping, persistent background and preserved ego flag; {coco_calls} actual CoCo immediate/variable commands produce the expected normalized AddToPicImpl request; {coco_impl_calls} actual CoCo immediate/variable commands execute AddToPicImpl with real view-list lookup, loop/cel resolution and bounds/collision placement plus instrumented script/range/MMU/page services; {coco_integrated_rendered} AddToPicImpl calls dispatch to real ObjAddPicPri/ObjBlit and match native pixels; {coco_rendered} actual CoCo ObjBlit/ObjAddPicPri pixel comparisons pass at two code bases')
        finally:
            d.s.close();proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)

if __name__=='__main__':main()
