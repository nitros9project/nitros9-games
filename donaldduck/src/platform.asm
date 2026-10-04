* Appended PIC platform adapter. Labels are module-relative patch destinations.
        use defsfile
syscall macro
        fcb $10,$3f,\1
        endm
        org $196d
Screen0 equ $3900
Screen1 equ $5100
RowBuf equ $6900
Owned equ $6a40
First equ $6a41
Window equ $6a43
Dest equ $6a45
Space equ $6a47
Source equ $6a49
Row equ $6a4b
Index equ $6a4d
Hidden equ $6a4e
Regd equ $6a4f
Error equ $6a50
Chunk equ $6a51
Guard equ $6a55
Aborted equ $6a57
OriginalTerm equ $0f00

NativeStart
* The CoCo binary assumes freshly zeroed process RAM; Level 2 may recycle it.
        pshs x,y
        leax ,u
        ldy #$3815
StartClear
        clr ,x+
        leay -1,y
        bne StartClear
        puls x,y
        stu <8
        leau $374c,u
        lbra $0019

NativeInit
        pshs u
        ldu <8
        leax Screen0,u
        stx <14
        leax Screen1,u
        stx <16
        leax RowBuf,u
        ldy #$160
ni0     clr ,x+
        leay -1,y
        bne ni0
        leax Screen0,u
        ldy #$3000
ni1     clr ,x+
        leay -1,y
        bne ni1
        lda #1
        ldb #SS.AScrn
        ldx #0
        ldy #0
        syscall I$SetStt
        lbcs InitError
        ldu <8
        inc Owned,u
        lda #1
        ldb #SS.BmBlk
        ldy #0
        syscall I$GetStt
        lbcs InitError
        ldu <8
        stx First,u
* Reserve the highest free logical window. If it is $E000, its last
* $300 bytes are fixed I/O, so it cannot carry a complete bitmap block.
* Keep it mapped without touching its bytes; use a lower service window.
        ldb #1
        syscall F$MapBlk
        lbcs InitError
        tfr u,d
        ldu <8
        std Guard,u
        lda #1
        ldb #SS.ClutWrite
        leax Palette,pcr
        ldy #0
        ldu #5
        syscall I$SetStt
        lbcs InitError
        lda #1
        ldb #SS.Palet
        ldx #0
        ldy #0
        syscall I$SetStt
        lbcs InitError
        lda #1
        ldb #SS.PScrn
        ldx #0
        ldy #0
        syscall I$SetStt
        lbcs InitError
        lda #0
        ldb #SS.WSig
        ldx #$8182
        syscall I$SetStt
        lbcs InitError
        ldu <8
        inc Regd,u
        puls u
        andcc #$fe
        rts
InitError
        puls u
        lbsr CleanGraphics
        orcc #1
        rts

NativeSignal
        leau -$374c,u
        cmpb #$81
        beq SignalBg
        cmpb #$82
        beq SignalFg
        stb Aborted,u
        rti
SignalBg
        inc Hidden,u
        rti
SignalFg
        clr Hidden,u
        rti

NativeFlip
        pshs cc,d,x,y,u
        lbsr PollQuit
        lbsr Present
        puls cc,d,x,y,u
        ldx #3
        syscall F$Sleep
        rts

Present
        ldu <8
        tst Owned,u
        lbeq PresentDone
WaitVisible
        lda Aborted,u
        cmpa #2
        lbeq AbortGame
        cmpa #3
        lbeq AbortGame
        tst Hidden,u
        beq Visible
        ldx #2
        syscall F$Sleep
        ldu <8
        bra WaitVisible
Visible
        lda Aborted,u
        cmpa #2
        lbeq AbortGame
        cmpa #3
        lbeq AbortGame
        ldx <14
        tst <119
        beq psel
        ldx <16
psel    stx Source,u
        clr Row,u
        clr Row+1,u
        clr Index,u
        ldd #0
        std Window,u
        lbsr MapNext
        lbcs RuntimeError
NextRow
        ldu <8
        leax RowBuf,u
        ldy #40
        ldd #$0101
ClearRow
        std ,x++
        std ,x++
        std ,x++
        std ,x++
        leay -1,y
        bne ClearRow
        ldd Row,u
        cmpd #24
        blo CopyRow
        cmpd #216
        bhs CopyRow
        leay RowBuf+32,u
        ldx Source,u
        ldb #32
Unpack
        pshs b
        lda ,x+
        pshs a
        lsra
        lsra
        lsra
        lsra
        lsra
        lsra
        inca
        tfr a,b
        std ,y++
        lda ,s
        lsra
        lsra
        lsra
        lsra
        anda #3
        inca
        tfr a,b
        std ,y++
        lda ,s
        lsra
        lsra
        anda #3
        inca
        tfr a,b
        std ,y++
        lda ,s+
        anda #3
        inca
        tfr a,b
        std ,y++
        puls b
        decb
        bne Unpack
        stx Source,u
CopyRow
        leax RowBuf,u
        ldy #320
CopySpan
        pshs x,y
        ldu <8
        ldd Space,u
        bne HaveRoom
        lbsr Unmap
        lbcs RuntimeError
        ldu <8
        inc Index,u
        lbsr MapNext
        lbcs RuntimeError
        ldu <8
        ldd Space,u
HaveRoom
        cmpd 2,s
        bls UseCount
        ldd 2,s
UseCount
        std Chunk,u
        ldd Space,u
        subd Chunk,u
        std Space,u
        ldd 2,s
        subd Chunk,u
        std 2,s
        ldy Chunk,u
        ldu Dest,u
        ldx ,s
CopyPixel
* Row lengths and 8 KB boundaries are multiples of eight.
        ldd ,x++
        std ,u++
        ldd ,x++
        std ,u++
        ldd ,x++
        std ,u++
        ldd ,x++
        std ,u++
        leay -8,y
        bne CopyPixel
        tfr u,d
        ldu <8
        std Dest,u
        stx ,s
        puls x,y
        cmpy #0
        bne CopySpan
        ldd Row,u
        addd #1
        std Row,u
        cmpd #240
        lblo NextRow
        lbsr Unmap
        lbcs RuntimeError
        lda #1
        ldb #SS.DScrn
        ldx #FX_BM+FX_GRF
        ldy #FT_OMIT
        syscall I$SetStt
        lbcs RuntimeError
PresentDone
        rts

MapNext
        ldu <8
        ldx First,u
        ldb Index,u
        abx
        ldb #1
        syscall F$MapBlk
        bcs MapDone
        cmpu #$e000
        blo SafeWindow
        ldb #1
        syscall F$ClrBlk
        ldb #207
        orcc #1
        rts
SafeWindow
        tfr u,d
        ldu <8
        std Window,u
        std Dest,u
        ldd #$2000
        std Space,u
        andcc #$fe
MapDone rts
Unmap
        ldu <8
        ldu Window,u
        ldb #1
        syscall F$ClrBlk
        bcs UnmapDone
        ldu <8
        ldd #0
        std Window,u
        andcc #$fe
UnmapDone rts
RuntimeError
        ldu <8
        stb Error,u
        lbsr CleanGraphics
        lda #1
        sta <52
        lbsr OriginalTerm
        ldu <8
        ldb Error,u
        syscall F$Exit
NativeCleanup
        lbsr CleanGraphics
        lbra OriginalTerm
CleanGraphics
        pshs d,x,y,u
        ldu <8
        tst Regd,u
        beq c0
        lda #0
        ldb #SS.WSig
        ldx #0
        syscall I$SetStt
        ldu <8
        clr Regd,u
c0      ldd Window,u
        beq c1
        lbsr Unmap
c1      ldu <8
        ldd Guard,u
        beq c2
        tfr d,u
        ldb #1
        syscall F$ClrBlk
        ldu <8
        ldd #0
        std Guard,u
c2      tst Owned,u
        beq cdone
        lda #$9f
        sta >$ff92
        lda #1
        ldb #SS.DScrn
        ldx #FX_TXT
        ldy #FT_OMIT
        syscall I$SetStt
        lda #1
        ldb #SS.FScrn
        ldy #0
        syscall I$SetStt
        ldu <8
        clr Owned,u
cdone   puls d,x,y,u,pc

* Legacy CoCo joystick range 0..63, fire=$FF; native range 0..255.
NativeJoy
        pshs d,x,y,u
        lbsr Present
        puls d,x,y,u
        syscall I$GetStt
        bcs joydone
        pshs a
        tfr x,d
        lsrb
        lsrb
        clra
        tfr d,x
        tfr y,d
        lsrb
        lsrb
        clra
        tfr d,y
        puls a
        pshs a,x,y,u
        lda #0
        ldb #$c6
        syscall I$GetStt
        bcs NoKeys
* Q is also available in modal joystick-only loops.
        pshs a
        pshs x,y,u
        ldb #6
KeyScan
        lda ,s+
        cmpa #'q
        lbeq QuitGame
        cmpa #32
        bne NotSpace
* K2 can report space only in the ordinary held-key slots.
        leay -1,s
        lda b,y
        ora #$80
        sta b,y
NotSpace
        decb
        bne KeyScan
        puls a
        puls u,y,x,b
        pshs b
        bita #$20
        beq kright
        ldx #0
kright  bita #$40
        beq kup
        ldx #63
kup     bita #$08
        beq kdown
        ldy #0
kdown   bita #$10
        beq kfire
        ldy #63
kfire   bita #$80
        beq kdone
        lda #$ff
        leas 1,s
        rts
kdone   puls a
        bra jbutton
NoKeys  puls u,y,x,a
jbutton anda #7
        beq joydone
        lda #$ff
joydone rts
AbortGame
        ldb #$e4
        lbra RuntimeError
QuitGame
* Wait for Q release, draining typematic bytes before the shell resumes.
        lda #0
        ldb #$c6
        syscall I$GetStt
        lbcs $01f0
        pshs x,y,u
        leau ,s
        ldb #6
QuitScan
        lda ,u+
        cmpa #'q
        beq QuitHeld
        decb
        bne QuitScan
        leas 6,s
        lbra $01f0
QuitHeld
        leas 6,s
        ldx #2
        syscall F$Sleep
        bra QuitGame
PollQuit
        pshs d,x,y,u
        lda #0
        ldb #$c6
        syscall I$GetStt
        bcs pqdone
        pshs x,y,u
        leau ,s
        ldb #6
pqscan
        lda ,u+
        cmpa #'q
        lbeq QuitGame
        decb
        bne pqscan
        leas 6,s
pqdone  puls d,x,y,u,pc
ReadKey
        pshs d,x,y,u
        lbsr Present
        puls d,x,y,u
        syscall $89
        rts

* Original duration/pitch scripts, played by PSG channel zero.
* Fixed sound decode requires the modern Wildbits core described in the guide.
NativeSound
        tst <78
        lbeq SoundDone
        cmpa #1
        lblo SoundDone
        cmpa #21
        lbhs SoundDone
        pshs d,x,y,u
        lsla
        leax SoundTable,pcr
        ldd a,x
        leax d,x
SoundNote
        pshs x
SoundVisible
        ldu <8
        lda Aborted,u
        cmpa #2
        lbeq AbortGame
        cmpa #3
        lbeq AbortGame
        tst Hidden,u
        beq SoundContinue
        lda #$9f
        sta >$ff92
        ldx #2
        syscall F$Sleep
        bra SoundVisible
SoundContinue
        lbsr PollQuit
        puls x
        lda ,x+
        beq SoundEnd
        pshs x,a
        ldb ,x+
        beq RestNote
        clra
        lslb
        rola
        lslb
        rola
        addd #12
        cmpd #1023
        bls PitchOK
        ldd #1023
PitchOK
        pshs d
        andb #15
        orb #$80
        stb >$ff92
        puls d
        lsra
        rorb
        lsra
        rorb
        lsra
        rorb
        lsra
        rorb
        stb >$ff92
        lda #$94
        bra Volume
RestNote
        lda #$9f
Volume
        sta >$ff92
        lda ,s
        clrb
Duration
        cmpa #5
        blo SleepNote
        suba #5
        incb
        bra Duration
SleepNote
        clra
        addd #2
        tfr d,x
        syscall F$Sleep
        puls a,x
        leax 1,x
        lbra SoundNote
SoundEnd
        lda #$9f
        sta >$ff92
        puls d,x,y,u
SoundDone
        rts
SoundTable equ $0fbe
NoSoundLoad
        ldd #0
        std <79
        std <81
        rts
NoSound
        rts
Palette
        fcb 0,0,0,0
        fcb 0,0,0,0
        fcb 255,100,0,0
        fcb 0,100,255,0
        fcb 255,255,255,0
