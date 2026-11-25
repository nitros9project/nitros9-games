#!/usr/bin/env python3
"""Compare config.screen layout writes and guard Wild Bits updates.

Wild Bits stores its picture top, input row and status row separately, and
packs the validated CoCo horizontal text offset into unused high bits of the
status-enabled byte.
"""
from pathlib import Path
import tempfile
from check_instances import symbols
from check_logic_executor import compile_module, ROOT
from check_wbres import idle_rom, start_cpu


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-screen-config-') as name:
        tmp=Path(name)
        coco,cs=compile_module(ROOT/'objs/mnln.asm',tmp/'mnln')
        us=symbols(ROOT/'objs/sierraui.map');ui=(ROOT/'objs/sierraui').read_bytes()
        gs=symbols(ROOT/'objs/wbgame.map')
        d,emulator=start_cpu(idle_rom(tmp/'idle.rom'),timeout=900)
        try:
            d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01')
            d.write(0xffa8,bytes(range(8)));d.breakpoint(0x7e00)
            calls=0;reference_layouts={}
            for base in (0x8000,0x9000):
                d.write(base,coco)
                for picturetop,inputrow,statusrow in (
                        (0,0,0),(1,22,0),(1,23,0),(1,23,7),
                        (4,0,24),(4,24,0),(0,24,24)):
                    d.write(0x0241,b'\xaa');d.write(0x023f,b'\xbb')
                    d.write(0x002c,b'\xcc\xdd');d.write(0x01d7,b'\xee');d.write(0x0247,b'\xff')
                    d.write(0x3000,bytes([picturetop,inputrow,statusrow])+b'GUARD')
                    d.write(0x7ef0,b'\x7e\0STACK')
                    d.regs(pc=base+cs['cmd_config_screen'],s=0x7ef0,y=0x3000,u=0,dp=0,cc=0x50)
                    d.call('c');r=d.regs()
                    stride=(picturetop*8*160).to_bytes(2,'big')
                    assert r['pc']==0x7e00 and r['s']==0x7ef2 and r['y']==0x3003
                    assert d.read(0x0241,1)==bytes([picturetop])
                    assert d.read(0x023f,1)==bytes([(picturetop+21)&255])
                    assert d.read(0x002c,2)==stride
                    assert d.read(0x01d7,1)==bytes([inputrow])
                    assert d.read(0x0247,1)==bytes([statusrow])
                    assert d.read(0x3003,5)==b'GUARD' and d.read(0x7ef2,5)==b'STACK'
                    logical=(d.read(0x0241,1)+d.read(0x01d7,1)+d.read(0x0247,1))
                    assert logical==bytes([picturetop,inputrow,statusrow])
                    reference_layouts[(picturetop,inputrow,statusrow)]=logical
                    calls+=1
                # Execute the real CoCo message-box column adjustment after
                # config.screen has set PicNum. The following STA stores the
                # computed left edge; stop immediately afterward so unrelated
                # MMU drawing and keyboard services remain outside this probe.
                draw_column=base+cs['MsgBoxColCalc']+6
                d.breakpoint(draw_column)
                try:
                    for offset in range(5):
                        d.write(0x0241,bytes([offset]))
                        d.write(0x015b,b'\x08')
                        d.write(0x0175,b'\xcc')
                        d.write(0x7ef0,b'\x7e\0STACK')
                        d.regs(pc=base+cs['MsgBoxColCalc'],s=0x7ef0,a=6,dp=0,cc=0x50)
                        d.call('c');r=d.regs()
                        assert r['pc']==draw_column and r['s']==0x7ef0,r
                        assert r['a']==6+offset and d.read(0x0175,1)==bytes([6+offset]),(
                            'CoCo message-box horizontal offset',offset,r,d.read(0x0175,1))
                        calls+=1
                finally:d.breakpoint(draw_column,False)
                # CoCo's dropdown height depends on both the submitted
                # visible-item count and PicNum. Execute the real geometry
                # routine with only SetLogicPage intercepted; StrLen and all
                # geometry arithmetic remain production code.
                menu,item,text=0x3000,0x3100,0x3200
                page_service=base+cs['SetLogicPage']
                d.breakpoint(page_service)
                try:
                    for visible_items in (1,4,8,21):
                        for offset in range(5):
                            d.write(0x0241,bytes([offset]))
                            record=bytearray(16);record[11:13]=item.to_bytes(2,'big')
                            record[15]=visible_items;d.write(menu,record)
                            first_item=bytearray(16);first_item[4:6]=text.to_bytes(2,'big')
                            first_item[9]=5
                            d.write(item,first_item);d.write(text,b'Item\0')
                            d.write(0x7ef0,b'\x7e\0STACK')
                            d.regs(pc=base+cs['CalcMenuItemGeometry'],s=0x7ef0,
                                   u=menu,dp=0,cc=0x50)
                            for _ in range(8):
                                d.call('c');r=d.regs()
                                if r['pc']==0x7e00:break
                                assert r['pc']==page_service,('CoCo menu geometry service',r)
                                ret=int.from_bytes(d.read(r['s'],2),'big')
                                d.regs(pc=ret,s=r['s']+2)
                            else:raise AssertionError('CoCo menu geometry did not return')
                            expected_height=((visible_items+2-offset)*8+7)&255
                            got=(d.read(base+cs['MenuItemRow'],1)[0],
                                 d.read(base+cs['MenuItemWidth'],1)[0],
                                 d.read(base+cs['MenuItemCol'],1)[0],
                                 d.read(base+cs['MenuItemHeight'],1)[0])
                            expected=(visible_items*8+16,24,16,expected_height)
                            assert got==expected,('CoCo menu geometry',visible_items,offset,got,expected)
                            assert r['s']==0x7ef2 and d.read(0x7ef2,5)==b'STACK',r
                            calls+=1
                finally:d.breakpoint(page_service,False)
                # The CoCo handler does not range-check these bytes. Record
                # that compatibility difference against Wild Bits' atomic
                # E$IllArg rejection for offsets/rows outside the legal UI.
                for picturetop,inputrow,statusrow in (
                        (5,0,0),(255,255,255),(1,25,25)):
                    d.write(0x3000,bytes([picturetop,inputrow,statusrow])+b'GUARD')
                    d.write(0x7ef0,b'\x7e\0STACK')
                    d.regs(pc=base+cs['cmd_config_screen'],s=0x7ef0,y=0x3000,u=0,dp=0,cc=0x50)
                    d.call('c');r=d.regs()
                    stride=((picturetop*8&255)*160).to_bytes(2,'big')
                    assert r['pc']==0x7e00 and r['s']==0x7ef2 and r['y']==0x3003,r
                    assert d.read(0x0241,1)==bytes([picturetop])
                    assert d.read(0x023f,1)==bytes([(picturetop+21)&255])
                    assert d.read(0x002c,2)==stride
                    assert d.read(0x01d7,1)==bytes([inputrow])
                    assert d.read(0x0247,1)==bytes([statusrow])
                    assert d.read(0x3003,5)==b'GUARD' and d.read(0x7ef2,5)==b'STACK'
                    calls+=1
            private=0x1000;base=0xa000
            d.write(base,ui);d.write(0,bytes(gs['size']))
            d.write(us['resourcebase'],private.to_bytes(2,'big'))
            d.write(0x7ef0,b'\x7e\0STACK')
            layout=us['vmpicturetop']
            for picturetop,inputrow,statusrow in reference_layouts:
                before=bytes([9,8,7]);d.write(layout,before)
                d.write(private+gs['vmarguments'],bytes([picturetop,inputrow,statusrow]))
                d.regs(pc=base+us['ScreenConfigure'],s=0x7ef0,u=private,dp=0,cc=0x50)
                d.call('c');r=d.regs()
                assert r['pc']==0x7e00 and r['s']==0x7ef2 and not(r['cc']&1),r
                assert d.read(layout,1)==bytes([picturetop])
                assert d.read(layout+1,1)==bytes([inputrow])
                assert d.read(layout+2,1)==bytes([statusrow])
                packedenable=d.read(layout+3,1)[0]
                assert (packedenable&7,packedenable>>3)==(0,picturetop)
                assert d.read(private+gs['vmarguments'],3)==bytes([picturetop,inputrow,statusrow])
                d.regs(pc=base+us['ScreenStatusOn'],s=0x7ef0,u=private,dp=0,cc=0x50)
                d.call('c')
                assert d.read(layout+3,1)==bytes([packedenable|1])
                d.regs(pc=base+us['ScreenStatusOff'],s=0x7ef0,u=private,dp=0,cc=0x50)
                d.call('c')
                assert d.read(layout+3,1)==bytes([packedenable])
                calls+=1
            for invalid in ((5,10,10),(1,25,10),(1,10,25)):
                before=bytes([3,4,5]);d.write(layout,before)
                d.write(private+gs['vmarguments'],bytes(invalid))
                d.regs(pc=base+us['ScreenConfigure'],s=0x7ef0,u=private,dp=0,cc=0x50)
                d.call('c');r=d.regs()
                assert r['pc']==0x7e00 and r['s']==0x7ef2 and r['cc']&1
                assert r['b']==us['E$IllArg'] and d.read(layout,3)==before,(invalid,r)
                calls+=1
            assert d.read(base,len(ui))==ui
            # Exercise the packed offset in two independently switched
            # direct-page/process maps, including status on/off operations.
            savedmap=d.read(0xffa8,3)
            banks={0:bytes([0x20,0x21,0x22]),1:bytes([0x23,0x24,0x25])}
            layouts={0:bytes([1,23,0]),1:bytes([4,22,24])}
            def select(owner):d.write(0xffa8,banks[owner])
            try:
                for owner in banks:
                    select(owner)
                    d.write(0,bytes(gs['size']))
                    d.write(us['resourcebase'],private.to_bytes(2,'big'))
                    d.write(private+gs['vmarguments'],layouts[owner])
                for owner in (0,1):
                    select(owner)
                    d.regs(pc=base+us['ScreenConfigure'],s=0x7ef0,u=private,dp=0,cc=0x50)
                    d.call('c')
                for owner in (0,1,0):
                    select(owner)
                    offset=layouts[owner][0]
                    assert d.read(us['vmstatusenabled'],1)==bytes([offset<<3])
                    assert d.read(us['vmstatusrow'],1)==bytes([layouts[owner][2]])
                    d.regs(pc=base+us['ScreenStatusOn'],s=0x7ef0,u=private,dp=0,cc=0x50)
                    d.call('c')
                    assert d.read(us['vmstatusenabled'],1)==bytes([(offset<<3)|1])
                    d.regs(pc=base+us['ScreenStatusOff'],s=0x7ef0,u=private,dp=0,cc=0x50)
                    d.call('c')
                    assert d.read(us['vmstatusenabled'],1)==bytes([offset<<3])
                    for other in banks:
                        select(other)
                        expected=layouts[other][0]<<3
                        assert d.read(us['vmstatusenabled'],1)==bytes([expected]),(owner,other)
                calls+=8
            finally:
                d.write(0xffa8,savedmap)
            # CoCo has no range check: record its actual invalid-value result
            # so it cannot be mistaken for the Wild Bits rejection policy.
            for base in (0x8000,0x9000):
                d.write(base,coco)
                for invalid in ((5,10,10),(1,25,10),(1,10,25)):
                    d.write(0x3000,bytes(invalid)+b'GUARD')
                    d.write(0x7ef0,b'\x7e\0STACK')
                    d.regs(pc=base+cs['cmd_config_screen'],s=0x7ef0,y=0x3000,u=0,dp=0,cc=0x50)
                    d.call('c');r=d.regs()
                    assert r['pc']==0x7e00 and r['s']==0x7ef2 and not(r['cc']&1),r
                    assert d.read(0x0241,1)==bytes([invalid[0]])
                    assert d.read(0x01d7,1)==bytes([invalid[1]])
                    assert d.read(0x0247,1)==bytes([invalid[2]])
                    calls+=1
            print(f'PASS: {calls} actual config.screen, dialog-column and menu-geometry calls; CoCo legal and permissive malformed operands, stride, right edge and dialog-column offset plus both owners\' input/status rows are checked; Wild Bits picture top, input/status rows and packed text-X offset are verified; invalid-range policy remains different')
        finally:
            d.s.close();emulator.terminate()
            try:emulator.wait(timeout=5)
            except Exception:emulator.kill();emulator.wait(timeout=5)


if __name__=='__main__':main()
