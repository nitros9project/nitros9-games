#!/usr/bin/env python3
"""Verify the OS frame-clock service required by concurrent Wild Bits games."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from check_instances import symbols
from check_wbres import start_cpu,idle_rom


def check_cpu(tmp):
    code=(tmp/'SOLdrv').read_bytes();sy=symbols(tmp/'SOLdrv.map');base=0x9000;private=0x1000;stack=0x7000;finish=0x7100
    calls={base+int(m[1],16):int(m[2],16) for m in re.finditer(r'^([0-9A-F]{4}) 103F([0-9A-F]{2}).*os9',(tmp/'SOLdrv.list').read_text(),re.M)}
    d,p=start_cpu(idle_rom(Path(tmp)/'idle.rom'))
    try:
        d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\x01');d.write(0xffa8,bytes(range(8)));d.write(base,code)
        for a in calls:d.breakpoint(a)
        d.breakpoint(finish)
        def table(rows,curr=None):
            data=bytearray([0xcc])*sy['size'];data[sy['V.SOLMax']]=(len(rows)-1)*5 if rows else 255;data[sy['V.SOLCurr']]=(len(rows)-1)*5 if curr is None and rows else (curr or 0)
            for i,(pid,sig,line,mute) in enumerate(rows):
                at=sy['V.SOLTable']+i*5;data[at:at+5]=bytes([pid,sig])+line.to_bytes(2,'big')+bytes([mute])
            d.write(private,data+b'GUARD');return data
        def run(entry,**regs):
            sent=[];d.write(stack,finish.to_bytes(2,'big')+b'STACK');d.regs(pc=base+sy[entry],u=private,s=stack,dp=0,cc=regs.pop('cc',0x50),**regs)
            for _ in range(50):
                d.call('c');r=d.regs()
                if r['pc']==finish:
                    assert r['s']==stack+2 and d.read(stack+2,5)==b'STACK';assert d.read(private+sy['size'],5)==b'GUARD';return sent,r
                service=calls[r['pc']]
                if service==sy['F$Send']:sent.append((r['a'],r['b']))
                else:assert service==sy['F$IRQ'],service
                d.regs(pc=r['pc']+3,cc=r['cc']&~1,b=0)
            raise AssertionError('unbounded IRQ')
        count=0
        for n in range(1,9):
            for muted in (False,True):
                rows=[(i+1,0x82,0,int(muted and i%2)) for i in range(n)];table(rows)
                sent,_=run('SOL_IRQSvc');assert sorted(sent)==[(pid,sig) for pid,sig,line,mute in rows if not mute],(rows,sent);count+=1
        rows=[(1,130,200,0),(2,131,200,0),(3,132,100,0),(4,133,100,0),(5,134,0,0),(6,135,0,0)];table(rows)
        for expected in ([(5,134),(6,135)],[(3,132),(4,133)],[(1,130),(2,131)]):
            sent,_=run('SOL_IRQSvc');assert sorted(sent)==expected,(sent,expected);count+=1
        d.write(sy['D.Proc'],b'\x40\x00');d.write(0x4000,b'\x02');shadow=bytearray(20);shadow[sy['R$X']:sy['R$X']+2]=b'\0\0';d.write(0x3000,shadow)
        rows=[(3,130,0,0),(2,130,0,0),(1,130,0,0)];table(rows);run('SOLremoveval',x=0x3000)
        assert d.read(private+sy['V.SOLTable'],10)==bytes([3,130,0,0,0,1,130,0,0,0]);assert d.read(private+sy['V.SOLMax'],1)==b'\x05';count+=1
        rows=[(1,130,0,0),(2,130,0,0),(2,130,100,0),(3,130,200,0)];table(rows);shadow[sy['R$X']:sy['R$X']+2]=b'\0\x01';d.write(0x3000,shadow);run('SSOLMUTE',x=0x3000)
        assert [d.read(private+sy['V.SOLTable']+i*5+4,1)[0] for i in range(4)]==[0,1,1,0];count+=1
        for entry in ('SOLremoveval','SSOLMUTE'):
            table([]);before=d.read(private,sy['size']);sent,r=run(entry,x=0x3000)
            assert not sent and not r['cc']&1 and r['b']==0
            assert d.read(private,sy['size'])==before;count+=1
        d.write(0x5000+sy['PD.RGS'],b'\x30\x00')
        sent,r=run('GetSta',a=sy['SS.SOLIRQ'],y=0x5000)
        assert not sent and not r['cc']&1
        assert d.read(0x3000+sy['R$X'],2)==b'\0\x07'
        assert d.read(0x3000+sy['R$Y'],2)==d.read(private+sy['V.SOLTicks'],2)
        count+=1
        # Shared clients count one raster frame, including wrap and mute.
        for ticks,line,muted in ((0,0,0),(65535,0,0),(123,100,0),(123,0,1)):
            table([(1,1,line,muted),(2,1,line,muted)])
            d.write(private+sy['V.SOLTicks'],ticks.to_bytes(2,'big'))
            sent,_=run('SOL_IRQSvc')
            assert d.read(private+sy['V.SOLTicks'],2)==((ticks+(line==0))&65535).to_bytes(2,'big')
            assert sorted(sent)==([] if muted else [(1,1),(2,1)])
            count+=1
        table([])
        shadow[sy['R$X']:sy['R$X']+2]=b'\0\0'
        shadow[sy['R$Y']:sy['R$Y']+2]=b'\0\x83'
        d.write(0x3000,shadow)
        for pid in range(1,9):
            d.write(0x4000,bytes([pid]))
            sent,r=run('SOLIRQAtomic',x=0x3000,cc=0)
            assert not sent and not r['cc']&0x51,r
            assert d.read(private+sy['V.SOLMax'],1)==bytes([(pid-1)*5])
            count+=1
        before=d.read(private,sy['size'])
        sent,r=run('SOLIRQAtomic',x=0x3000,cc=0)
        assert not sent and r['cc']&1 and not r['cc']&0x50 and r['b']==sy['E$DevOvf'],r
        assert d.read(private,sy['size'])==before
        count+=1
        assert d.read(base,len(code))==code
        print('PASS:',count,'actual driver cases: one/eight shared-line owners, muted owners, distinct-line scheduling, PID-scoped removal, multi-entry mute, immutable code and guards')
    finally:
        d.s.close();p.terminate()
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)

def check_mame(args, tmp):
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    disk=out/'test.dsk';shutil.copyfile(args.disk,disk)
    roms=out/'roms/wbjr2';roms.mkdir(parents=True)
    for name in ('booter','f0.dsk'):shutil.copyfile(args.firmware/name,roms/name)
    def os9(*items):
        return subprocess.check_output(['os9',*map(str,items)],stderr=subprocess.STDOUT)
    def install(source,target,text=False):
        os9('copy','-r',*(['-l'] if text else []),source,f'{disk},{target}')
    os9('copy',f'{disk},OS9Boot',out/'original-boot')
    boot=(out/'original-boot').read_bytes();first=boot.index(b'\x87\xcd')
    assert boot[:first]==b'\xff'*first
    boot=boot[first:];cursor=0
    while cursor<len(boot):
        assert boot[cursor:cursor+2]==b'\x87\xcd'
        size=int.from_bytes(boot[cursor+2:cursor+4],'big')
        assert size>=12 and cursor+size<=len(boot)
        module=boot[cursor:cursor+size];at=int.from_bytes(module[4:6],'big');name=''
        for value in module[at:]:
            name+=chr(value&127)
            if value&128:break
        if name.lower()=='soldrv':
            boot=boot[:cursor]+(tmp/'SOLdrv').read_bytes()+boot[cursor+size:];break
        cursor+=size
    else:raise AssertionError('SOLdrv absent from bootfile')
    boot=b'\xff'*((-len(boot))%256)+boot
    assert len(boot)<=32256
    (out/'fixed-boot').write_bytes(boot);install(out/'fixed-boot','OS9Boot')
    root=Path(__file__).resolve().parents[1]/'objs'
    subprocess.run(['lwasm.orig','--6809','--format=os9',
        '--pragma=pcaspcr,nosymbolcase,condundefzero','-I'+str(root),
        '-I'+str(args.os_root/'defs'),'-o',str(out/'wbsol'),
        str(Path(__file__).parent/'probes/wbsol.asm')],check=True)
    install(out/'wbsol','CMDS/wbsol');os9('attr',f'{disk},CMDS/wbsol','-e','-pe')
    (out/'startup').write_bytes(b'load utilpak1\nlink shell\n')
    install(out/'startup','startup',True)
    (out/'feu.startup').write_bytes(b'bootos9 /s0/OS9Boot\n')
    install(out/'feu.startup','FEU/startup',True)
    lua=out/'drive.lua'
    lua.write_text('''local frames=0
local function post(s) manager.machine.natkeyboard:post(s) end
sub=emu.add_machine_frame_notifier(function()
 frames=frames+1
 if frames==800 then post("mfree >/s0/free-before\\r") end
 if frames==1000 then post("wbsol >/s0/sol-single\\r") end
 if frames==1600 then post("wbsol >/s0/sol-a & wbsol 6 >/s0/sol-b\\r") end
 if frames==2300 then post("mfree >/s0/free-after\\r") end
 if frames==2700 then manager.machine:exit() end
end)
''')
    with disk.open('ab') as stream:stream.truncate(1<<(disk.stat().st_size-1).bit_length())
    command=[str(args.mame.resolve()),'wbjr2','-bios','turbo','-rompath',str(roms.parent),
        '-hard',str(disk),'-skip_gameinfo','-noui_mouse','-mouseprovider','none',
        '-video','none','-sound','none','-nothrottle','-autoboot_script',str(lua),
        '-seconds_to_run','50','-nvram_directory',str(out/'nvram'),'-cfg_directory',str(out/'cfg')]
    with (out/'mame.log').open('w') as log:
        subprocess.run(command,cwd=out,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
    counts={}
    for name,minimum,maximum in (('sol-single',120,181),('sol-a',120,181),('sol-b',300,361)):
        os9('copy',f'{disk},{name}',out/(name+'.bin'))
        data=(out/(name+'.bin')).read_bytes();assert len(data)==2,(name,data)
        counts[name]=int.from_bytes(data,'big')
        assert minimum<=counts[name]<=maximum,(name,counts[name],minimum,maximum)
    assert os9('list',f'{disk},free-before')==os9('list',f'{disk},free-after'),'clock clients leaked memory'
    (out/'clock.json').write_text(json.dumps(counts,indent=2)+'\n')
    print('PASS: real SOL signals, concurrent frame delivery, surviving owner after peer exit, memory restored',counts)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',type=Path,required=True,help='SOLdrv.asm to test')
    ap.add_argument('--os-root',type=Path,default=Path(__file__).resolve().parents[3]/'nitros9')
    for name in ('mame','disk','firmware','output'):ap.add_argument('--'+name,type=Path)
    args=ap.parse_args()
    if any((args.mame,args.disk,args.firmware,args.output)) and not all((args.mame,args.disk,args.firmware,args.output)):
        ap.error('MAME verification requires --mame, --disk, --firmware and --output')
    with tempfile.TemporaryDirectory(prefix='sierra-sol-driver-') as name:
        tmp=Path(name)
        subprocess.run(['lwasm.orig','--6809','--format=os9',
            '--pragma=pcaspcr,nosymbolcase,condundefzero','-Dwildbits=1','-Djr2=1',
            '-I'+str(args.os_root/'level2/wildbits'),'-I'+str(args.os_root/'defs'),
            '--map='+str(tmp/'SOLdrv.map'),'--list='+str(tmp/'SOLdrv.list'),
            '-o',str(tmp/'SOLdrv'),str(args.source)],check=True)
        check_cpu(tmp)
        if args.mame:check_mame(args,tmp)


if __name__=='__main__':main()
