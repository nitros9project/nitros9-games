GameInitialize      ldu       <resourcebase
                    clr       gamequit,u
                    clr       gameclockreset,u
                    lda       #$FF
                    sta       gameclocklast,u
                    lda       #1
                    sta       vmflags+5,u
                    sta       vmflags+9,u
                    sta       vmflags+11,u
                    sta       vmvariables+22,u     three-channel sound model
                    lda       #3
                    sta       vmvariables+26,u     EGA-compatible palette
                    lda       #38
                    sta       vmvariables+24,u
                    clr       <vmplayercontrol
                    lbra      GameReadClock

* A completed logic cycle: clear transient state, wait without mappings,
* poll stdin without blocking, then resume root logic at its scan start.
GameNextCycle       lbsr      AssetUnmap
                    lbcs      GameCycleReturn
                    lbsr      PictureUnmap
                    lbcs      GameCycleReturn
                    ldu       <resourcebase
                    tst       gamequit,u
                    bne       GameCycleSuccess
                    lbsr      foreground
                    lbcs      GameCycleReturn
                    ldu       <resourcebase
                    clr       vmflags+2,u
                    clr       vmflags+4,u
                    clr       vmflags+5,u
                    clr       vmflags+6,u
                    clr       vmflags+11,u
                    clr       vmflags+12,u
                    clr       vmvariables+9,u
                    clr       vmvariables+19,u
                    clr       <vmhavekey
                    leax      vmcontrollers,u
                    ldy       #256
GameResetControllers clr     ,x+
                    leay      -1,y
                    bne       GameResetControllers
                    ldb       vmvariables+10,u     AGI delay in 50-ms units
                    lda       #3                  three 60-Hz ticks per unit
                    mul
                    addd      #1                  F$Sleep sleeps X-1 ticks
                    tfr       d,x
                    os9       F$Sleep
                    lbsr      foreground
                    lbcs      GameCycleReturn
                    lbsr      GameReadClock
                    lbcs      GameCycleReturn
                    lbsr      GamePollKeyboard
                    lbcs      GameCycleReturn
                    tst       <bitmapowned
                    beq       GameCycleSuccess
                    lbsr      GameComposeScene
                    lbcs      GameCycleReturn
                    lbsr      PresentPicture
GameCycleReturn     rts
GameCycleSuccess    clrb
                    rts

GameReadClock       ldu       <resourcebase
                    leax      gametime,u
                    os9       F$Time
                    lbcs      GameCycleReturn
                    ldu       <resourcebase
                    ldb       gametime+5,u
                    cmpb      #60
                    bhs       GameClockInvalid
                    lda       gameclocklast,u
                    cmpa      #$FF
                    beq       GameClockStore
                    tst       gameclockreset,u
                    bne       GameClockStore
                    subb      gameclocklast,u
                    bcc       GameClockComputeDelta
                    addb      #60
GameClockComputeDelta stb       gameclockdelta,u
GameClockTick       tst       gameclockdelta,u
                    beq       GameClockStoreCurrent
                    dec       gameclockdelta,u
                    inc       vmvariables+11,u
                    lda       vmvariables+11,u
                    cmpa      #60
                    blo       GameClockTick
                    clr       vmvariables+11,u
                    inc       vmvariables+12,u
                    lda       vmvariables+12,u
                    cmpa      #60
                    blo       GameClockTick
                    clr       vmvariables+12,u
                    inc       vmvariables+13,u
                    lda       vmvariables+13,u
                    cmpa      #24
                    blo       GameClockTick
                    clr       vmvariables+13,u
                    inc       vmvariables+14,u
                    bra       GameClockTick
GameClockStoreCurrent ldb     gametime+5,u
GameClockStore      stb       gameclocklast,u
                    clr       gameclockreset,u
                    clrb
                    rts
GameClockInvalid    ldb       #E$BMode
                    orcc      #1
                    rts

GamePollKeyboard    clra
                    ldb       #SS.Ready
                    os9       I$GetStt
                    bcc       GameReadKey
                    cmpb      #E$NotRdy
                    lbne      GameCycleReturn
                    clrb
                    rts
GameReadKey         ldu       <resourcebase
                    leax      vmkeybyte,u
                    ldy       #1
                    clra
                    os9       I$Read
                    lbcs      GameCycleReturn
                    cmpy      #1
                    bne       GameClockInvalid
                    lda       #1
                    sta       <vmhavekey
                    ldu       <resourcebase
                    ldb       <vmkeybyte
                    stb       vmvariables+19,u
                    leax      vmkeys,u
                    ldy       #0
GameKeyBinding      tfr       y,d
                    cmpb      <vmkeycount
                    lbhs      GameCycleSuccess
                    ldb       <vmkeybyte
                    cmpb      ,x
                    bne       GameNextBinding
                    tst       1,x       ASCII binding, scan bindings separate
                    bne       GameNextBinding
                    ldb       2,x
                    leay      vmcontrollers,u
                    clra
                    leay      d,y
                    lda       #1
                    sta       ,y
                    clr       vmvariables+19,u
                    clrb
                    rts
GameNextBinding     leax      3,x
                    leay      1,y
                    bra       GameKeyBinding

GameQuitCommand     ldu       <resourcebase
                    lda       vmarguments,u
                    cmpa      #1
                    bne       GameQuitNeedsDialog
                    sta       gamequit,u
                    clrb
                    rts
GameQuitNeedsDialog ldb       #E$UnkSvc
                    orcc      #1
                    rts

* Remove any renderer mapping before freeing cache slabs. A transient error
* is retried, while the first error remains the process's exit status.
GameUnmapForExit    ldu       <resourcebase
                    clr       gamecleanup,u
                    lbsr      PictureUnmap
                    bcc       GameExitFrame
                    ldu       <resourcebase
                    stb       gamecleanup,u
                    lbsr      PictureUnmap
GameExitFrame       tst       <mapped
                    beq       GameExitAsset
                    lbsr      unmap
                    bcc       GameExitAsset
                    ldu       <resourcebase
                    tst       gamecleanup,u
                    bne       GameExitFrameRetry
                    stb       gamecleanup,u
GameExitFrameRetry  lbsr      unmap
GameExitAsset       lbsr      AssetUnmap
                    bcc       GameExitUnmapped
                    ldu       <resourcebase
                    tst       gamecleanup,u
                    bne       GameExitAssetRetry
                    stb       gamecleanup,u
GameExitAssetRetry  lbsr      AssetUnmap
GameExitUnmapped    ldu       <resourcebase
                    ldb       gamecleanup,u
                    beq       GameExitUnmapSuccess
                    orcc      #1
                    rts
GameExitUnmapSuccess andcc    #$FE
                    rts
