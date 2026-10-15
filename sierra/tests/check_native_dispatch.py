#!/usr/bin/env python3
"""Check every native platform-command destination before its body executes."""
from pathlib import Path
import tempfile
import re
from check_logic_executor import compile_module
from check_wbres import idle_rom, start_cpu

ROOT = Path(__file__).resolve().parents[1]

# Independent behavioral contract for game-only and shared probe commands.
# Unsupported opcodes must retain the explicit error handler.
GAME = {
    'GamePriorityBaseCommand': (174,),
    'GameStateCommand': (125,126),
    'GameForceUpdate': (60,), 'GameCloseWindow': (169,), 'GameAddToPicture': (122,123), 'GameCancelLine': (138,), 'GameEchoLine': (137,),
    'GameMenuInput': (161,), 'GameReposition': (40,147,148),
    'GameRandomCommand': (130,), 'GameMathCommand': tuple(range(165,169)),
    'InventoryStatus': (124,), 'InventoryCommand': tuple(range(92,98)),
    'GameFollowCommand': (83,), 'GameWanderCommand': (84,),
    'GameSoundCommand': (99,100), 'GameBlockCommand': (90,91),
    'GameMoveCommand': (81,82), 'GameClearLines': (105,), 'GameClearTextRect': (154,),
    'GameDisplayCommand': (103,104), 'GameQuitCommand': (134,),
    'GameMonitorCommand': (140,), 'GameJoystickCommand': (139,), 'GameVersionCommand': (141,), 'GameShakeCommand': (110,), 'GameShowObjectCommand': (129,162), 'GameRestartCommand': (128,), 'GamePauseCommand': (136,), 'GameObjectVisibility': (35,36),
    'GameTextScreen': (106,), 'GameGraphicsMode': (107,),
    'GameLoadPicture': (24,), 'GameDrawPicture': (25,28),
    'GameShowPicture': (26,), 'GameDiscardPicture': (27,),
    'GameGetInput': (115,118), 'GameWordToString': (116,),
    'GamePrintCommand': (101,102,151,152), 'ParserCommand': (117,),
}
COMMON = {
    'VmSuccess': (127,144,155,163,164,173,175,176,178,179,180,181),
    'ScreenCommand': (108,109,111,112,113,119,120), 'SetKeyCommand': (121,),
    'SetStringCommand': (114,), 'VmCommandNewRoom': (18,),
    'VmCommandNewRoomVariable': (19,), 'MenuCommand': tuple(range(156,161)),
    'ObjectFlagCommand': tuple(range(61,69))+(88,89),
    'ObjectDistanceCommand': (69,), 'ObjectCycleCommand': tuple(range(70,81))+(85,),
    'VmProgramControl': (131,), 'VmSetPlayerControl': (132,),
    'ViewCommand': tuple(range(41,45))+tuple(range(47,54)),
    'ObjectCommand': (33,34,37,38,39,45,46,54,55,56,57,58,59,86,87),
    'ReplayInitialize': (142,), 'ReplaySaveCheckpoint': (171,), 'ReplayRestore': (172,),
    'VmCommandLoadView': (30,), 'VmCommandLoadViewVariable': (31,),
    'VmCommandDiscardView': (32,), 'VmCommandDiscardViewVariable': (153,),
    'VmCommandLoadSound': (98,), 'VmCommandLoadLogic': (20,),
    'VmCommandLoadLogicVariable': (21,), 'VmCommandCallLogic': (22,),
    'VmCommandCallLogicVariable': (23,), 'VmCommandScanStart': (145,),
    'VmCommandScanReset': (146,), 'VmCommandGameId': (143,),
}


def main():
    with tempfile.TemporaryDirectory(prefix='sierra-dispatch-') as name:
        tmp = Path(name)
        game, gs = compile_module(ROOT/'objs/sierra.asm', tmp/'wbgame',
                                  defines=('WILDBITS=1',),listing=True)
        # Forced direct-page addressing truncates silently in the assembler.
        # Audit the emitted native instructions against resolved private offsets.
        direct=set()
        for line in (tmp/'wbgame.list').read_text().splitlines():
            if re.match(r'^[0-9A-F]{4} [0-9A-F]+\s+\(',line):
                source=re.split(r'\):\d+\s',line,maxsplit=1)[1]
                tokens=source.split()
                for operand in tokens[:3]:
                    if operand.startswith('<'):
                        direct.update(re.findall(r'^<([A-Za-z_][A-Za-z0-9_]*)',operand))
        for field in direct:
            assert field in gs and gs[field]<=255, ('forced direct-page field',field,gs.get(field))
        probe, ps = compile_module(ROOT/'tests/probes/wbexec.asm', tmp/'wbexec')
        counts = [int(value[1:],16)//256 for value in re.findall(
            r'^\s*AGI_COMMAND\s+[^,]+,(\$[0-9A-Fa-f]+),',
            (ROOT/'objs/shared/agi-command-table.asm').read_text(),re.M)]
        assert len(counts)==182
        for owner,code,syms in [('game',game,gs),('probe',probe,ps)]:
            offset=syms['VmArgumentCounts'];packed=code[offset:offset+91]
            assert [(packed[i//2]>>(4 if i%2==0 else 0))&15
                    for i in range(182)] == counts, owner
        d, emulator = start_cpu(idle_rom(tmp/'idle.rom'), timeout=900)
        calls = 0
        try:
            d.write(0xffdf,b'\0'); d.write(0xff90,b'\x4c')
            d.write(0xff91,b'\x01'); d.write(0xffa8,bytes(range(8)))
            for owner,code,syms,groups in (
                    ('game',game,gs,{**COMMON,**GAME}),
                    ('probe',probe,ps,COMMON)):
                routes = {opcode:label for label,opcodes in groups.items() for opcode in opcodes}
                assert len(routes) == sum(map(len,groups.values()))
                for base in (0x9000,0xa000):
                    d.write(base,code)
                    state = bytearray(syms['size'])
                    state[syms['resourcebase']:syms['resourcebase']+2] = b'\x10\x00'
                    d.write(0x1000,state+b'GUARD')
                    destinations = {base+syms[label] for label in groups}
                    destinations.add(base+syms['VmPlatformUnsupported'])
                    for address in destinations: d.breakpoint(address)
                    for opcode in range(256):
                        state[syms['vmopcode']] = opcode
                        d.write(0x1000+syms['vmopcode'],bytes((opcode,)))
                        d.write(0x7ee0,b'GUARD')
                        d.write(0x7ef0,b'\x7e\x00STACK')
                        d.regs(pc=base+syms['VmPlatformCommand'],s=0x7ef0,
                               a=0x12,b=0x34,x=0x4567,y=0x5678,u=0x6789,dp=0x10,cc=0x50)
                        d.call('c'); regs = d.regs()
                        label = routes.get(opcode,'VmPlatformUnsupported')
                        assert regs['pc'] == base+syms[label], (owner,opcode,label,regs)
                        assert regs['s'] == 0x7ef0 and regs['a'] == 0x12 and regs['b'] == opcode
                        assert (regs['x'],regs['y'],regs['u']) == (0x4567,0x5678,0x6789)
                        assert d.read(0x7ef0,7) == b'\x7e\x00STACK'
                        assert d.read(0x7ee0,5) == b'GUARD'
                        assert d.read(0x1000,len(state)) == state
                        assert d.read(0x1000+len(state),5) == b'GUARD'
                        if opcode == 255:
                            # Also execute the unsupported return, rather
                            # than checking only its selected destination.
                            error = base+syms['VmPlatformUnsupported']
                            d.breakpoint(error,False); d.breakpoint(0x7e00)
                            d.call('c'); result = d.regs()
                            assert result['pc'] == 0x7e00 and result['s'] == 0x7ef2
                            assert result['b'] == syms['E$UnkSvc'] and result['cc'] & 1
                            d.breakpoint(0x7e00,False); d.breakpoint(error)
                        calls += 1
                    for address in destinations: d.breakpoint(address,False)
                    assert d.read(base,len(code)) == code
            print(f'PASS: {calls} native platform dispatches; all 256 opcodes in '
                  'game/probe at two addresses, exact destinations, unsupported '
                  'and presentation-only policy, preserved registers/stack, '
                  'private guards and immutable code')
        finally:
            d.s.close(); emulator.terminate()
            try: emulator.wait(timeout=5)
            except Exception: emulator.kill(); emulator.wait(timeout=5)


if __name__ == '__main__': main()
