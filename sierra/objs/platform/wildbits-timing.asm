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
* removal and a public frame counter before registering wake signals.
* Older drivers retain the sleep-based gate without consuming user signals.
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
                    andb      #7
                    cmpb      #7
                    bne       GameClockOpenClose
                    ldu       <resourcebase
                    tfr       y,d
                    stb       gameclockticks,u
                    stb       gameclockseen,u
                    clr       gameclockcredit,u
                    clr       gameclockcredit+1,u
                    lda       ,s
                    ldb       #SS.SOLIRQ
                    ldx       #0
                    ldy       #S$Wake                distinct from background/foreground
                    os9       I$SetStt
                    bcs       GameClockOpenClose
                    puls      a
                    ldu       <resourcebase
                    sta       gameclockpath,u
                    clrb
                    rts
GameClockOpenClose  puls      a
                    os9       I$Close
                    bcs      GameClockReturn
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
                    bcs      GameClockReturn
                    ldu       <resourcebase
                    lda       gameclockpath,u
                    os9       I$Close
                    bcs      GameClockReturn
                    ldu       <resourcebase
                    lda       #$FF
                    sta       gameclockpath,u
                    clrb
GameClockReturn     rts

* Sample the public modulo-256 frame counter; wake signals occupy only the
* replaceable wake slot, allowing keyboard abort/interrupt signals to win.
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
GameClockSleep      os9       F$Sleep
                    rts
GameClockSignalGate ldb       vmvariables+10,u
                    lda       #3
                    mul
                    beq       GameClockYield
                    pshs      d
GameClockCollect    ldu       <resourcebase
                    tst       gameclockreset,u
                    beq       GameClockCollectDelta
                    bsr      GameClockRebase
                    bcs       GameClockGateReturn
                    lbsr      GameReadClock
                    bcs       GameClockGateReturn
GameClockCollectDelta bsr    GameClockSample
                    bcs       GameClockGateReturn
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
                    bra       GameClockSleep
GameClockSample     ldu       <resourcebase
                    lda       gameclockpath,u
                    ldb       #SS.SOLIRQ
                    ldx       #0
                    os9       I$GetStt
                    lbcs      GameClockReturn
                    ldu       <resourcebase
                    tfr       y,d
                    stb       gameclockticks,u
                    tfr       b,a
                    rts
GameClockRebase     bsr      GameClockSample
                    lbcs      GameClockReturn
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
                    bsr      GameClockRebase
                    lbcs      GameClockReturn
                    clrb
                    rts
                    endc
