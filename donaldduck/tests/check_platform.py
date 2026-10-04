#!/usr/bin/env python3
"""Execute actual adapter code on a 6809. Services are mocked, no hardware claims."""
from pathlib import Path
import re,subprocess,socket,time,argparse,shutil
parser=argparse.ArgumentParser();parser.add_argument("--xroar",default=shutil.which("xroar") or "xroar");args=parser.parse_args()
from cpu_debugger import Debugger,symbols
ROOT=Path(__file__).resolve().parents[1]
syms=symbols(ROOT/'build/platform.map')
code=(ROOT/'build/game/CMDS/DONALD').read_bytes()
calls={i:code[i+2] for i in range(0x196d,len(code)-2) if code[i:i+2]==b'\x10\x3f'}
with socket.socket() as reservation:
 reservation.bind(('127.0.0.1',0));port=reservation.getsockname()[1]
calls.update({0xf0b:0x8d,0xf1d:0x8e})
p=subprocess.Popen([args.xroar,'-machine','coco3','-ui','null','-ao','null','-no-bas','-no-extbas','-no-altbas','-ram','512','-gdb','-gdb-port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 for _ in range(80):
  try:d=Debugger(port);break
  except OSError:time.sleep(.1)
 else:raise RuntimeError("XRoar debugger did not start")
 d.write(0xffdf,b"\0");d.write(0xff90,b"\x4c");d.write(0xff91,b"\x01");d.write(0xffa8,bytes(range(8)))
 for address in (0xff92,0xff93,0xff01,0xff03,0xff21,0xff23):d.write(address,b"\0")
 def run(base,db,screen,error=0):
  d.write(base,code);d.write(db,bytes(0x6c00));d.write(db+8,db.to_bytes(2,'big'))
  d.write(db+14,(db+0x3900).to_bytes(2,'big')+(db+0x5100).to_bytes(2,'big'))
  payload=bytes((i*37+i//32)&255 for i in range(6144));d.write(db+0x3900,payload);d.write(db+0x5100,bytes(v^255 for v in payload))
  d.write(db+119,bytes([screen]));d.write(db+0x6a40,b'\x01\x00\x30')
  frame=bytearray(81920);mapped=None;maps=0;stop=0x2100;stack=0xbff0;d.write(stack,stop.to_bytes(2,'big'));d.breakpoint(stop)
  for i in calls:d.breakpoint(base+i)
  d.regs(pc=base+syms['Present'],u=db+0x374c,dp=db>>8,s=stack,cc=0x50)
  for _ in range(100):
   d.call('c');r=d.regs()
   if r['pc']==stop:break
   service=calls[r['pc']-base];u={'cc':r['cc']&~1,'pc':r['pc']+3}
   if service==0x4f:
    assert mapped is None and r['b']==1;maps+=1
    if maps==error:u.update(cc=r['cc']|1,b=207)
    else:
     mapped=r['x']-0x30;assert 0<=mapped<10
     d.write(0xc000,frame[mapped*8192:(mapped+1)*8192]);u['u']=0xc000
   elif service==0x50:
    assert mapped is not None and r['u']==0xc000
    frame[mapped*8192:(mapped+1)*8192]=d.read(0xc000,8192);mapped=None
   elif service==0x8e:pass
   elif service==0x8d and r['b']==0:d.write(r['x'],bytes(32))
   elif service==6:
    assert error and r['b']==207 and mapped is None;break
   else:raise AssertionError((service,r))
   d.regs(**u)
  else:raise AssertionError('did not return')
  for i in calls:d.breakpoint(base+i,False)
  d.breakpoint(stop,False)
  if not error:
   assert maps==10 and mapped is None
   expected=bytearray([1])*76800
   source=payload if not screen else bytes(v^255 for v in payload)
   for y in range(192):
    pixels=bytes(c for v in source[y*32:(y+1)*32] for shift in (6,4,2,0) for c in [1+((v>>shift)&3)]*2)
    expected[(y+24)*320+32:(y+24)*320+288]=pixels
   assert frame[:76800]==expected,'bitmap mismatch'
  print('PASS',hex(base),hex(db),'screen',screen,'map failure',error)
 def initialize(refused=False):
  base=0x100;db=0x2200;stop=0x2100;stack=0xbff0
  d.write(base,code);d.write(db,bytes(0x6c00));d.write(db+8,db.to_bytes(2,'big'));d.write(stack,stop.to_bytes(2,'big'))
  for i in calls:d.breakpoint(base+i)
  d.breakpoint(stop);d.regs(pc=base+syms['NativeInit'],u=db+0x374c,dp=db>>8,s=stack,cc=0x50)
  frees=0;allocated=False
  for _ in range(40):
   d.call('c');r=d.regs()
   if r['pc']==stop:break
   service=calls[r['pc']-base];u={'pc':r['pc']+3,'cc':r['cc']&~1}
   if service==0x8e:
    if r['b']==0x8b:
     if refused:u.update(cc=r['cc']|1,b=183)
     else:allocated=True;u['x']=99
    elif r['b']==0x8d:frees+=1
   elif service==0x8d:
    assert r['b']==0xe4;u['x']=48
   elif service==0x4f:assert r['x']==48 and r['b']==1;u['u']=0xe000
   else:raise AssertionError((service,r))
   d.regs(**u)
  else:raise AssertionError('init did not return')
  assert r['u']==db+0x374c and bool(r['cc']&1)==refused
  assert frees==0
  if allocated:assert d.read(db+syms['Guard'],2)==b'\xe0\0'
  for i in calls:d.breakpoint(base+i,False)
  d.breakpoint(stop,False)
 initialize();initialize(True)
 print('PASS initialization, upper guard window, existing-bitmap refusal')
 def signals():
  base=0x100;db=0x2200;stop=0x2100;stack=0xbff0
  d.write(base,code);d.write(db,bytes(0x6c00));d.write(db+10,b'\x77');d.breakpoint(stop)
  for signal,value in [(129,1),(130,0),(2,2)]:
   frame=bytes([0xd0,1,2,db>>8])+bytes(6)+stop.to_bytes(2,'big')
   d.write(stack,frame);d.regs(pc=base+syms['NativeSignal'],s=stack,u=db+0x374c,b=signal,dp=0x11,cc=0xd0)
   d.call('c');assert d.regs()['pc']==stop
   address=syms['Aborted'] if signal==2 else syms['Hidden']
   assert d.read(db+address,1)==bytes([value]);assert d.read(db+10,1)==b'\x77'
  d.breakpoint(stop,False)
 signals();print('PASS intercept U rebasing, arbitrary DP, private signal state')
 def joystick(sense,slots=b'\0'*6,button=0):
  base=0x100;db=0x2200;stop=0x2100;stack=0xbff0
  d.write(base,code);d.write(db,bytes(0x6c00));d.write(db+8,db.to_bytes(2,'big'));d.write(stack,stop.to_bytes(2,'big'))
  for i in calls:d.breakpoint(base+i)
  d.breakpoint(stop);d.regs(pc=base+syms['NativeJoy'],u=db+0x374c,dp=db>>8,s=stack,a=1,b=0x13,x=0,y=0,cc=0x50)
  for _ in range(15):
   d.call('c');r=d.regs()
   if r['pc']==stop:break
   assert calls[r['pc']-base]==0x8d
   u={'pc':r['pc']+3,'cc':r['cc']&~1}
   if r['b']==0x13:u.update(a=button,x=128,y=128)
   else:
    assert r['b']==0xc6
    u.update(a=sense,x=int.from_bytes(slots[:2],'big'),y=int.from_bytes(slots[2:4],'big'),u=int.from_bytes(slots[4:],'big'))
   d.regs(**u)
  else:raise AssertionError('joystick did not return')
  assert r['u']==db+0x374c
  for i in calls:d.breakpoint(base+i,False)
  d.breakpoint(stop,False)
  return r['a'],r['x'],r['y']
 assert joystick(0)==(0,32,32)
 assert joystick(0x28)==(0,0,0)
 assert joystick(0x50)==(0,63,63)
 assert joystick(0x80)==(255,32,32)
 assert joystick(0,b' '+b'\0'*5)==(255,32,32)
 assert joystick(0,b'\0'*5+b' ')==(255,32,32)
 assert joystick(0,button=1)==(255,32,32)
 print('PASS joystick, held arrows, both space representations, original U')
 def sound():
  base=0x100;db=0x2200;stop=0x2100;stack=0xbff0
  d.write(base,code);d.write(db+8,db.to_bytes(2,'big'));d.write(db+78,b'\x01');d.write(stack,stop.to_bytes(2,'big'))
  points={base+i:('call',calls[i]) for i in calls}
  points.update({base+i:('psg',0) for i in range(0x196d,len(code)-2) if code[i:i+3] in (b'\xb7\xff\x92',b'\xf7\xff\x92')})
  for address in points:d.breakpoint(address)
  d.breakpoint(stop);d.regs(pc=base+syms['NativeSound'],u=db+0x374c,dp=db>>8,s=stack,a=1,b=99,x=123,y=456,cc=0x50)
  writes=[];sleeps=[]
  for _ in range(2000):
   d.call('c');r=d.regs()
   if r['pc']==stop:break
   kind,service=points[r['pc']]
   if kind=='psg':writes.append(r['a'] if code[r['pc']-base]==0xb7 else r['b'])
   else:
    if service==10:sleeps.append(r['x'])
    else:
     assert service==0x8d and r['b']==0xc6,(service,r)
     d.regs(a=0,x=0,y=0,u=0)
   d.regs(pc=r['pc']+3,cc=r['cc']&~1)
  else:raise AssertionError('sound did not finish')
  assert (r['a'],r['b'],r['x'],r['y'],r['u'])==(1,99,123,456,db+0x374c),r
  for address in points:d.breakpoint(address,False)
  d.breakpoint(stop,False)
  print('PASS sound',len(sleeps),'notes',len(writes),'PSG writes')
 sound()
 run(0x100,0x2200,0)
 run(0xa000,0x2000,1)
 run(0x100,0x2200,0,4)
finally:
 p.terminate()
 try:p.wait(timeout=5)
 except subprocess.TimeoutExpired:
  p.kill();p.wait(timeout=5)
