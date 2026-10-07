#!/usr/bin/env python3
"""Probe cold-code execution at the production game's memory footprint.

Diagnostic only: no save/restore support is installed in the game.
Uses public OS-9 module/RAM services and a disposable MAME image.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]

OWNER = r"""
Level               equ 2
                    use os9.d
                    org 0
header              rmb 2
entry               rmb 2
physical            rmb 2
window              rmb 2
loops               rmb 1
scratch             rmb 64
                    rmb PRIVATE_BYTES-.
size                equ .
                    mod eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs /wbcoldprobe/
start               lda #2
                    sta <loops
again               leax helper,pcr
                    lda #Sbrtn+Objct
                    os9 F$Load
                    lbcs exit
                    stu <header
                    sty <entry
                    cmpu #$8000
                    lblo bad
                    cmpu #$A000
                    lbhs bad
                    leax ,u
                    ldd M$Size,u
                    cmpd #64
                    lbhi bad
                    tfr d,y
                    ldu <header
                    ldd <entry
                    subd <header
                    pshs d
* Restore private base through DP, not the linked module address.
                    tfr dp,a
                    clrb
                    tfr d,u
                    leau scratch,u
copy                lda ,x+
                    sta ,u+
                    leay -1,y
                    bne copy
                    ldu <header
                    os9 F$UnLink
                    lbcs poperror
                    tfr dp,a
                    clrb
                    tfr d,u
                    leau scratch,u
                    puls d
                    leau d,u
                    jsr ,u
                    cmpd #$1234
                    lbne bad
                    ldb #1
                    os9 F$AllRAM
                    lbcs exit
                    std <physical
                    tfr d,x
                    ldb #1
                    os9 F$MapBlk
                    lbcs exit
                    stu <window
                    cmpu #$8000
                    lbne bad
                    ldd #$5678
                    std ,u
                    ldb #1
                    os9 F$ClrBlk
                    lbcs exit
                    ldx <physical
                    ldb #1
                    os9 F$DelRAM
                    lbcs exit
                    dec <loops
                    lbne again
                    leax good,pcr
                    ldy #32
                    lda #1
                    os9 I$WritLn
                    lbcs exit
                    clrb
exit                os9 F$Exit
poperror            leas 2,s
                    bra exit
bad                 ldb #E$BMode
                    bra exit
helper              fcc +/s0/CMDS/wbcold+
                    fcb 13
good                fcc /COLD-COPY-OK/
                    fcb 13
                    zmb CODE_BYTES-3-*
                    emod
eom                 equ *
"""
HELPER = r"""
                    use os9.d
                    mod eom,name,Sbrtn+Objct,ReEnt+1,start,0
name                fcs /wbcold/
start               leax message,pcr
                    ldd ,x
                    rts
message             fdb $1234
                    emod
eom                 equ *
"""

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('mame', 'disk', 'firmware', 'output'):
        ap.add_argument('--'+name, type=Path, required=True)
    ap.add_argument('--lwasm', default='lwasm.orig')
    ap.add_argument('--os9', default='os9')
    a = ap.parse_args()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    production = (ROOT/'objs/wbgame').read_bytes()
    code = len(production)
    private = int.from_bytes(production[11:13], 'big')
    assert production[:2] == b'\x87\xcd' and code == int.from_bytes(production[2:4], 'big')
    assert 16384 < code <= 23808 and 16384 < private <= 24576
    for name, source in [('wbcoldprobe', OWNER), ('wbcold', HELPER)]:
        asm = out/(name+'.asm')
        asm.write_text(source)
        command = [a.lwasm, '--6809', '--format=os9',
                   '--pragma=pcaspcr,nosymbolcase,condundefzero',
                   '-I'+str(ROOT.parent.parent/'nitros9/defs'),
                   '-DPRIVATE_BYTES='+str(private), '-DCODE_BYTES='+str(code),
                   '-o', str(out/name), str(asm)]
        subprocess.run(command, check=True)
        b = (out/name).read_bytes()
        assert len(b) == int.from_bytes(b[2:4], 'big')
        if name == 'wbcoldprobe':
            assert len(b) == code and int.from_bytes(b[11:13], 'big') == private
    disk = out/'test.dsk'
    shutil.copyfile(a.disk, disk)
    rom = out/'roms/wbjr2'
    rom.mkdir(parents=True)
    for name in ('booter', 'f0.dsk'):
        shutil.copyfile(a.firmware/name, rom/name)
    def os9(*args):
        return subprocess.check_output([a.os9, *map(str, args)], stderr=subprocess.STDOUT)
    for name in ('wbcold', 'wbcoldprobe'):
        os9('copy', '-r', out/name, f'{disk},CMDS/{name}')
        os9('attr', f'{disk},CMDS/{name}', '-e', '-pe')
    for name, target, content in [
            ('startup', 'startup', 'load utilpak1\nlink shell\n'),
            ('feu.startup', 'FEU/startup', 'bootos9 /s0/OS9Boot\n')]:
        (out/name).write_text(content)
        os9('copy', '-r', '-l', out/name, f'{disk},{target}')
    with disk.open('ab') as f:
        f.truncate(1 << (disk.stat().st_size-1).bit_length())
    commands = {600: 'mfree >/s0/free-before\n',
                800: 'wbcoldprobe >/s0/result\n',
                1100: 'mfree >/s0/free-after\n',
                1300: 'echo COLD-DONE >/s0/done\n'}
    lua = out/'drive.lua'
    lua.write_text('frames=0\nlocal commands={'+','.join(
        '['+str(k)+']='+json.dumps(v) for k,v in commands.items())+
        '}\nsub=emu.add_machine_frame_notifier(function()\n'
        'frames=frames+1\n'
        'if commands[frames] then manager.machine.natkeyboard:post(commands[frames]) end\n'
        'if frames==1700 then manager.machine:exit() end\nend)\n')
    command = [str(a.mame.resolve()), 'wbjr2', '-bios', 'turbo',
               '-rompath', str(rom.parent), '-hard', str(disk), '-skip_gameinfo',
               '-video', 'none', '-sound', 'none', '-nothrottle',
               '-autoboot_script', str(lua), '-seconds_to_run', '50',
               '-nvram_directory', str(out/'nvram'), '-cfg_directory', str(out/'cfg')]
    (out/'command.json').write_text(json.dumps(command, indent=2)+'\n')
    with (out/'mame.log').open('w') as log:
        subprocess.run(command, cwd=out, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=100)
    result = {name: os9('list', f'{disk},{name}').decode()
              for name in ('result','done','free-before','free-after')}
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    assert result['result'].strip() == 'COLD-COPY-OK', result
    assert result['done'].strip() == 'COLD-DONE', result
    assert result['free-before'] == result['free-after'], result
    print(f'PASS: {code}-byte owner/{private}-byte private area, two load/copy/unlink/execute cycles, $8000 mapping reuse and unchanged free memory')


if __name__ == '__main__':
    main()
