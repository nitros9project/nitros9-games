#!/usr/bin/env python3
"""Establish actual CoCo trace semantics before enabling the native backend.

Executes relocated control/dispatch/display routines. Window drawing, keyboard
services and text output are intercepted; cached message lookup remains real.
This is reference evidence, not native trace support or pixel verification.
"""
from pathlib import Path
import subprocess
import tempfile
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]

def string(d,p):
    return d.read(p,128).split(b'\0')[0].decode('latin1')

def ret(d,q,**extra):
    d.regs(pc=int.from_bytes(d.read(q['s'],2),'big'),s=q['s']+2,**extra)


def check_controls():
    with tempfile.TemporaryDirectory(prefix='sierra-trace-reference-') as name:
     t=Path(name);code,s=compile_module(ROOT/'objs/mnln.asm',t/'mnln');d,e=start_cpu(idle_rom(t/'idle.rom'),timeout=900)
     try:
      d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\1');d.write(0xffa8,bytes(range(8)))
      d.breakpoint(0x1d00,False);d.breakpoint(0x7e00);d.breakpoint(0x701)
      count=0
      def call(base,label,y=0x7000):
       d.write(0x7ed0,b'GUARDLOW');d.write(0x7ef0,b'\x7e\0STACK')
       d.regs(pc=base+s[label],s=0x7ef0,y=y,dp=0,cc=0x50);windows=[]
       for _ in range(3):
        d.call('c');q=d.regs()
        if q['pc']==0x7e00:break
        assert q['pc']==0x701,q
        windows.append((d.read(0x19,1)[0],d.read(q['s']+2,6)))
        d.regs(pc=int.from_bytes(d.read(q['s'],2),'big'),s=q['s']+2)
       else:raise AssertionError('trace control did not return')
       assert q['s']==0x7ef2 and d.read(0x7ed0,8)==b'GUARDLOW' and d.read(0x7ef2,5)==b'STACK'
       return q,windows
      cases=[(v,1,15) for v in range(256)]+[(7,v,15) for v in range(256)]+[(7,1,v) for v in range(256)]
      for base in (0x8000,0x9000):
       assert base+len(code)<=0xfe00
       d.write(0,bytes(0x6000));d.write(base,code)
       for logic,line,rows in cases:
        d.write(0x7000,bytes([logic,line,rows]));q,windows=call(base,'cmd_trace_info')
        assert not windows and q['y']==0x7003
        assert d.read(0x6a,1)==bytes([logic])
        assert d.read(base+s['TraceLineOff'],2)==bytes([line,max(2,rows)])
        count+=1
       print('PASS: actual CoCo trace configuration all byte values, literal consumption and minimum two lines at',hex(base),flush=True)
       d.write(base+s['TraceLineOff'],bytes([1,15]));d.write(0x241,b'\0')
       for flags in range(256):
        for mode in (0,1,2,255):
         d.write(0x1af,bytes([flags]));d.write(0x68,bytes([mode]))
         q,windows=call(base,'cmd_trace_on')
         activate=mode==0 and bool(flags&32)
         assert d.read(0x68,1)==bytes([1 if activate else mode])
         assert len(windows)==int(activate),(flags,mode,windows)
         if activate:
          assert windows==[(12,bytes.fromhex('0385829a040f'))],windows
          assert d.read(base+s['TraceTopRow'],2)==bytes([2,16])
         count+=1
       enabled=[]
       for flag in range(32):
        d.write(0x1ae,bytes(4));d.write(0x68,b'\0');d.write(0x7000,bytes([flag]))
        call(base,'CmdSetImpl')
        _,windows=call(base,'cmd_trace_on')
        if windows:enabled.append(flag)
        count+=1
       assert enabled==[10],enabled
       print('PASS: actual CoCo trace activation requires flag 10, preserves existing modes and does not allocate twice at',hex(base),flush=True)
      print('PASS:',count,'actual CoCo trace config/permission/mode calls; byte bounds, one window creation, exact callback words, operand/stack guards')
     finally:
      d.s.close();e.terminate()
      try:e.wait(timeout=5)
      except subprocess.TimeoutExpired:e.kill();e.wait(timeout=5)


def check_steps():
    with tempfile.TemporaryDirectory(prefix='sierra-trace-steps-') as n:
     code,s=compile_module(ROOT/'objs/mnln.asm',Path(n)/'mnln')
     d,e=start_cpu(idle_rom(Path(n)/'idle.rom'),timeout=900)
     try:
      d.write(0xffdf,b'\0');d.write(0xff90,b'\x4c');d.write(0xff91,b'\1');d.write(0xffa8,bytes(range(8)))
      for base in (0x8000,0x9000):
       d.write(0,bytes(0x6000));d.write(base,code);d.write(0x2e,base.to_bytes(2,'big'))
       d.run(base+s['PatchCmdTable']);d.run(base+s['FixupEvalTbl']);d.breakpoint(0x1d00,False);d.breakpoint(0x7e00)
       dispatch=base+s['ScriptDispatch'];condition=base+s['ScriptArgDispatch']
       for point in (dispatch,condition):d.breakpoint(point)
       for mode,plus in ((0,False),(1,False),(1,True),(2,False),(255,False)):
        d.write(0x68,bytes([mode]));d.write(0x7000,bytes([240,73,3,241,74,0]))
        d.write(0x7ef0,b'\x7e\0STACK');seen=[]
        d.regs(pc=base+s['DispatchCmd'],s=0x7ef0,y=0x7000,b=3,dp=0,cc=0x50)
        for _ in range(4):
         d.call('c');q=d.regs()
         if q['pc']==0x7e00:break
         assert q['pc']==dispatch;seen.append(q['b'])
         if plus:d.write(0x68,b'\2')
         ret(d,q)
        else:raise AssertionError('command dispatch did not return')
        assert seen==([3] if plus else [3,3] if mode==1 else [])
        assert d.read(0x431+240,2)==b'IJ' and q['s']==0x7ef2
       for mode in (0,1,2,255):
        for value in (73,99):
         d.write(0x68,bytes([mode]));d.write(0x7000,bytes([1,240,value]));d.write(0x431+240,b'c')
         d.write(0x7ef0,b'\x7e\0STACK');seen=[]
         d.regs(pc=base+s['EvalExpr'],s=0x7ef0,y=0x7001,a=1,dp=0,cc=0x50)
         for _ in range(3):
          d.call('c');q=d.regs()
          if q['pc']==0x7e00:break
          assert q['pc']==condition;seen.append((q['a'],q['u']));ret(d,q)
         assert seen==([(int(value==99),0x7000)] if mode==1 else []),(mode,value,seen)
         assert q['a']==int(value==99) and q['y']==0x7003 and q['s']==0x7ef2
       for point in (dispatch,condition):d.breakpoint(point,False)
       end=base+s['ExecLogicRetState'];d.breakpoint(end)
       for mode in range(256):
        d.write(0x68,bytes([mode]));d.regs(pc=base+s['ExecLogicRun'],s=0x7ef0,dp=0,cc=0x50);d.call('c')
        assert d.regs()['pc']==end and d.read(0x68,1)==bytes([1 if mode==2 else mode])
       d.breakpoint(end,False)
       print('PASS: actual command and predicate trace gates require mode 1; plus skips both until the next logic-entry reset at',hex(base),flush=True)

       hooks={base+s[k]:k for k in ('EventPop','ScriptDisplayWaitKey','JoystickPoll','ScriptDisplayDone')}
       for point in hooks:d.breakpoint(point)
       for mode in (0,1,2):
        for key in (0,13,27,43,65,255):
         events=[None,(2,0),(1,key)];pops=polls=0
         d.write(0x68,bytes([mode]));d.write(0x7ec0,bytes(8));d.write(0x7eb0,b'LOWGUARD')
         d.regs(pc=base+s['ScriptDisplayWait'],s=0x7ec0,dp=0,cc=0x50)
         for _ in range(12):
          d.call('c');q=d.regs();kind=hooks[q['pc']]
          if kind=='ScriptDisplayDone':break
          if kind=='EventPop':
           event=events.pop(0);pops+=1
           if event is not None:d.write(0x7100,bytes(event))
           ret(d,q,x=0 if event is None else 0x7100)
          elif kind=='ScriptDisplayWaitKey':
           tick=(int.from_bytes(d.read(q['s']+2,2),'big')+1)&65535
           d.write(0x24a,tick.to_bytes(2,'big'));d.call('s')
          else:polls+=1;ret(d,q)
         else:raise AssertionError('trace input did not finish')
         assert (pops,polls)==((0,0) if mode==0 else (3,2)),(mode,key,pops,polls)
         assert d.read(0x68,1)==bytes([2 if mode and key==43 else mode])
         assert q['s']==0x7ec0 and d.read(0x7eb0,8)==b'LOWGUARD'
       for point in hooks:d.breakpoint(point,False)
       print('PASS: actual trace wait ignores non-key events, polls on timer changes, advances on every key, and only plus changes mode at',hex(base),flush=True)

       names=('PushRowCol','PopRowCol','PushTextColor','PopTextColor','text_color','TraceDrawWindow','PrintFmtStrToScr','PutCharToWindow')
       hooks={base+s[k]:k for k in names}
       for point in hooks:d.breakpoint(point)
       transcripts=[]
       cases=[('command numeric',False,3,0,b'\xf0I',True),
              ('command named',False,3,10,b'\xf0I',True),
              ('missing names numeric',False,3,11,b'\xf0I',True),
              ('condition false',True,1,0,b'\xf0I',False),
              ('condition true named',True,1,10,b'\xf0c',True),
              ('said signed words',True,14,0,b'\2\xff\xff\0\x80',True)]
       for label,is_condition,opcode,lookup,args,truth in cases:
        d.write(0x68,b'\0');d.write(0x69,b'\0');d.write(0x6a,bytes([lookup]))
        d.write(0x62,b'\x30\0');d.write(0x3000,bytes([0,0,7])+bytes(13))
        d.write(base+s['LogicTableData'],b'\x31\0')
        d.write(0x3100,bytes([0,0,10,255])+bytes(6)+b'\x32\0')
        d.write(0x3200,bytes(512));d.write(0x3200+3*2,b'\0\2');d.write(0x3200+221*2,b'\x10\2')
        d.write(0x3400,b'assign.n\0');d.write(0x3410,b'equal.n\0')
        d.write(0x431+240,b'c');d.write(0x7000,(bytes([opcode]) if is_condition else b'')+args)
        d.write(base+s['TraceBottomRow'],b'\x10');d.write(base+s['TraceWinLastCol'],b'%')
        d.write(0x7ef0,b'\x7e\0STACK');output=[]
        d.regs(pc=base+s['ScriptArgDispatch' if is_condition else 'ScriptDispatch'],s=0x7ef0,
               y=0x7000,u=0x7000,a=int(truth),b=opcode,dp=0,cc=0x50)
        for _ in range(100):
         d.call('c');q=d.regs()
         if q['pc']==0x7e00:break
         kind=hooks[q['pc']]
         if kind=='TraceDrawWindow':output.append('\n')
         elif kind=='PutCharToWindow':output.append(chr(q['a']))
         elif kind=='PrintFmtStrToScr':
          fmt=string(d,int.from_bytes(d.read(q['s']+2,2),'big'))
          words=[int.from_bytes(d.read(q['s']+4+2*i,2),'big') for i in range(2)]
          signed=lambda v:v if v<32768 else v-65536
          if fmt=='%d: %d':output.append(f'{signed(words[0])}: {signed(words[1])}')
          elif fmt=='%d: %s':output.append(f'{signed(words[0])}: {string(d,words[1])}')
          elif fmt=='%d':output.append(str(signed(words[0])))
          elif fmt==' :%c':output.append(' :'+chr(words[0]>>8))
          else:output.append(fmt)
         ret(d,q)
        else:raise AssertionError('trace display did not return')
        text=''.join(output).lstrip('\n');transcripts.append(text)
        assert d.read(0x62,2)==b'\x30\0' and q['s']==0x7ef2
        print('TRACE:',hex(base),label,repr(text),flush=True)
       assert transcripts==['7: 3(240,73)\n(99,73)','7: assign.n(240,73)\n(99,73)',
         '7: 3(240,73)\n(99,73)','7: 1(240,73)\n(99,73) :F',
         '7: equal.n(240,99)\n(99,99) :T','7: 14(-1,-32768) :T'],transcripts
       for point in hooks:d.breakpoint(point,False)
      print('PASS: reference trace gating/input/reset, actual cached name lookup/message selection, byte/word arguments, variable values and true/false labels')
     finally:
      d.s.close();e.terminate()
      try:e.wait(timeout=5)
      except subprocess.TimeoutExpired:e.kill();e.wait(timeout=5)


if __name__ == '__main__':
    check_controls()
    check_steps()
