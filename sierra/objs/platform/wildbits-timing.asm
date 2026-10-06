                    ifndef PLATFORM_WILDBITS_TIMING_BINDINGS
* wildbits-timing-bindings feature bindings. Included once; emits no code.
PLATFORM_WILDBITS_TIMING_BINDINGS equ 1

* ===== wildbits-game-clock-operands =====
* Private native AGI clock variables 11..14.
GAME_CLOCK_ADDRESS  macro
                    leax      vmvariables+11,u
                    endm
                    endc

                    ifdef PLATFORM_WILDBITS_TIMING_CODE
* The public raster service is optional. Require broadcast and PID-scoped
* removal before registering; an old driver retains the sleep-based gate.
GameClockOpen       leax      GameClockDevice,pcr
                    lda       #UPDAT.             SHARE. would request exclusive access
                    os9       I$Open
                    bcs       GameClockSuccess
                    pshs      a
                    ldb       #SS.SOLIRQ
                    ldx       #0
                    os9       I$GetStt
                    bcs       GameClockOpenClose
                    tfr       x,d
                    andb      #3
                    cmpb      #3
                    bne       GameClockOpenClose
                    ldu       <resourcebase
                    clr       gameclockticks,u
                    clr       gameclockseen,u
                    clr       gameclockcredit,u
                    clr       gameclockcredit+1,u
                    lda       ,s
                    ldb       #SS.SOLIRQ
                    ldx       #0
                    ldy       #$83                distinct from background/foreground
                    os9       I$SetStt
                    bcs       GameClockOpenClose
                    puls      a
                    ldu       <resourcebase
                    sta       gameclockpath,u
                    clrb
                    rts
GameClockOpenClose  puls      a
                    os9       I$Close
                    bcs       GameClockReturn
GameClockSuccess    clrb
                    rts
GameClockDevice     fcc       |/fSOL|
                    fcb       C$CR

GameClockClose      ldu       <resourcebase
                    lda       gameclockpath,u
                    cmpa      #$FF
                    beq       GameClockSuccess
                    ldb       #SS.SOLIRQ
                    ldx       #0
                    ldy       #0
                    os9       I$SetStt
                    bcs       GameClockReturn
                    ldu       <resourcebase
                    lda       gameclockpath,u
                    os9       I$Close
                    bcs       GameClockReturn
                    ldu       <resourcebase
                    lda       #$FF
                    sta       gameclockpath,u
                    clrb
GameClockReturn     rts

* A modulo-256 snapshot avoids read/clear races with the signal intercept.
* Preserve at most one extra cycle's credit; long frames do not add a full
* delay afterward and long stalls do not create an unbounded catch-up burst.
GameClockGate       ldu       <resourcebase
                    lda       gameclockpath,u
                    cmpa      #$FF
                    bne       GameClockSignalGate
                    ldb       vmvariables+10,u
                    lda       #3
                    mul
                    addd      #1
                    tfr       d,x
                    os9       F$Sleep
                    rts
GameClockSignalGate ldb       vmvariables+10,u
                    lda       #3
                    mul
                    beq       GameClockYield
                    pshs      d
GameClockCollect    ldu       <resourcebase
                    tst       gameclockreset,u
                    beq       GameClockCollectDelta
                    lbsr      GameClockRebase
                    lbsr      GameReadClock
                    bcs       GameClockGateReturn
GameClockCollectDelta      lda       gameclockticks,u
                    tfr       a,b
                    subb      gameclockseen,u
                    sta       gameclockseen,u
                    clra
                    addd      gameclockcredit,u
                    std       gameclockcredit,u
                    cmpd      ,s
                    bhs       GameClockConsume
                    ldx       #0
                    os9       F$Sleep
                    lbsr      foreground
                    bcs       GameClockGateReturn
                    bra       GameClockCollect
GameClockConsume    subd      ,s
                    cmpd      ,s
                    bls       GameClockKeepCredit
                    ldd       ,s
GameClockKeepCredit std       gameclockcredit,u
                    clrb
GameClockGateReturn leas      2,s
                    rts
GameClockYield      ldx       #1
                    os9       F$Sleep
                    rts
GameClockRebase     lda       gameclockticks,u
                    sta       gameclockseen,u
                    clr       gameclockcredit,u
                    clr       gameclockcredit+1,u
                    rts

GameClockMute       ldu       <resourcebase
                    tst       gameclockmuted,u
                    lbne      GameClockSuccess
                    lda       gameclockpath,u
                    cmpa      #$FF
                    lbeq      GameClockSuccess
                    ldb       #SS.SOLMUTE
                    ldx       #1
                    os9       I$SetStt
                    lbcs      GameClockReturn
                    ldu       <resourcebase
                    inc       gameclockmuted,u
                    lbra      GameClockSuccess
GameClockUnmute     ldu       <resourcebase
                    tst       gameclockmuted,u
                    lbeq      GameClockSuccess
                    lda       gameclockpath,u
                    ldb       #SS.SOLMUTE
                    ldx       #0
                    os9       I$SetStt
                    lbcs      GameClockReturn
                    ldu       <resourcebase
                    clr       gameclockmuted,u
                    lbsr      GameClockRebase
                    clrb
                    rts
                    endc
