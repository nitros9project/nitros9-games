from pathlib import Path
import subprocess,shutil,json,argparse
parser=argparse.ArgumentParser(description='Boot and exercise the actual Wildbits OS and game in MAME')
parser.add_argument('--mame',required=True,type=Path)
parser.add_argument('--disk',required=True,type=Path)
parser.add_argument('--firmware',required=True,type=Path)
parser.add_argument('--output',required=True,type=Path)
parser.add_argument('--activity',choices=['railroad','stores','playground','airport','produce','toystore'])
parser.add_argument('--installed',action='store_true',help='test an already-installed release image')
parser.add_argument('--record-audio',action='store_true')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1];out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
disk=out/'test.dsk'
shutil.copyfile(args.disk,disk)
def os9(*a):subprocess.run(['os9',*map(str,a)],check=True,stdout=subprocess.DEVNULL)
if not args.installed:
 os9('makdir',str(disk)+',ddp');os9('makdir',str(disk)+',ddp/CMDS');os9('makdir',str(disk)+',ddp/PIC')
 for p in (root/'build/game').rglob('*'):
  if p.is_file():
   relative=str(p.relative_to(root/'build/game'))
   target=str(disk)+','+('' if relative.startswith('CMDS/') else 'ddp/')+relative
   if args.activity and p.name=='DONALD':
    import sys
    sys.path.insert(0,str(root/'tools'))
    from build import crc
    data=bytearray(p.read_bytes()[:-3])
    destinations={'railroad':0xcd4,'stores':0xd02,'playground':0xce6,'airport':0xcec,'produce':0xcda,'toystore':0xce0}
    assert data[0xb1:0xb4]==bytes.fromhex('170738')
    data[0xb1:0xb4]=b'\x12'*3
    assert data[0xb4:0xb7]==bytes.fromhex('170522')
    data[0xb4:0xb7]=b'\x16'+((destinations[args.activity]-0xb7)&65535).to_bytes(2,'big')
    data.extend((crc(data)^0xffffff).to_bytes(3,'big'))
    diagnostic=out/'DONALD';diagnostic.write_bytes(data)
    os9('copy',diagnostic,target)
   else:os9('copy',p,target)
   if p.parent.name=='CMDS':os9('attr',target,'-e','-pe')
 for name,data,target in [('startup',b'load utilpak1\rload vt\rlink shell\rload grfdrv256\r','startup'),('feustartup',b'bootos9 /s0/OS9Boot\r','FEU/startup')]:
  p=out/name;p.write_bytes(data);os9('copy','-r',p,str(disk)+','+target)
with disk.open('ab') as f:f.truncate(1<<(disk.stat().st_size-1).bit_length())
rom=out/'roms/wbjr2';rom.mkdir(parents=True,exist_ok=True)
for name in ['booter','f0.dsk']:shutil.copyfile(args.firmware/name,rom/name)
commands={900:'iniz /vt1\n',1150:'shell i=/vt1&\n',1500:'chd /s0/ddp\n',1800:'mfree >/s0/free-before\n',2200:'donald\n',11800:'echo DDP-DONE >/s0/ddp-done\n',12000:'mfree >/s0/free-after\n'}
shots={2000:'before',3500:'logo',5200:'title',6800:'menu',8500:'town',9700:'activity',11000:'quit',12300:'shell'}
lua=out/'drive.lua';lua.write_text('''frames=0
local commands=%s
local shots=%s
local fields=manager.machine.ioport.ports[":KEY2"].fields
local qfields=manager.machine.ioport.ports[":KEY1"].fields
local arrows=manager.machine.ioport.ports[":KEY3"].fields
sub=emu.add_machine_frame_notifier(function()
frames=frames+1

if frames==4200 or frames==6800 or frames==8100 then fields["Return"]:set_value(1) end
if frames==4280 or frames==6880 or frames==8180 then fields["Return"]:clear_value() end
if frames==6000 or frames==8800 then fields["Space"]:set_value(1) end
if frames==6080 or frames==8880 then fields["Space"]:clear_value() end
if frames==10500 then qfields["q  Q"]:set_value(1) end
if frames==10700 then qfields["q  Q"]:clear_value() end
if commands[frames] then manager.machine.natkeyboard:post(commands[frames]) end
if shots[frames] then manager.machine.screens[":screen"]:snapshot(%s .. shots[frames] .. ".png") end
if frames==8500 and %s then
 local visible=0
 for y=240,280 do
  for x=308,336 do
   if (manager.machine.screens[":screen"]:pixel(x,y) & 0xffffff) ~= 0 then
    visible=visible+1
   end
  end
 end
 assert(visible>80, "Donald missing from initial town screen")
end
if frames==12500 then manager.machine:exit() end
end)
'''%('{' + ','.join('[%d]=%s'%(k,json.dumps(v).replace("\\u0005", "\\005")) for k,v in commands.items())+'}','{'+','.join('[%d]=%s'%(k,json.dumps(v).replace("\\u0005", "\\005")) for k,v in shots.items())+'}',json.dumps(str(out)+'/'), 'false' if args.activity else 'true'))
cmd=[str(args.mame.resolve()),'wbjr2','-bios','turbo','-rompath',str(rom.parent),'-hard',str(disk),'-skip_gameinfo','-video','none','-sound','none','-nothrottle','-autoboot_script',str(lua),'-seconds_to_run','240','-nvram_directory',str(out/'nvram'),'-cfg_directory',str(out/'cfg')]
if args.record_audio:cmd+=['-wavwrite',str(out/'game.wav')]
with (out/'mame.log').open('w') as f:subprocess.run(cmd,cwd=out,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=240)
assert b'DDP-DONE' in subprocess.check_output(['os9','list',str(disk)+',ddp-done']), 'shell failed to resume'
assert '[LUA ERROR]' not in (out/'mame.log').read_text()
before=subprocess.check_output(['os9','list',str(disk)+',free-before'])
after=subprocess.check_output(['os9','list',str(disk)+',free-after'])
assert before==after,(before,after)
print('PASS Wildbits MAME:',args.activity or 'town',out)
