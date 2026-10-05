GameInitialize      lbsr      ParserInitialize
                    ldu       <resourcebase
                    ldd       #$ACE1
                    std       gamerandom,u
                    clr       gamesoundwarned,u
                    clr       inventoryloaded,u
                    clr       gameblockenabled,u
                    clr       gamequit,u
                    clr       gameclockreset,u
                    lda       #$FF
                    sta       gameclocklast,u
                    lda       #1
                    sta       vmflags+5,u
                    clr       vmflags+9,u     no owned multi-terminal audio service yet
                    sta       vmflags+11,u
                    sta       vmvariables+22,u     three-channel sound model
                    lda       #3
                    sta       vmvariables+26,u     EGA-compatible palette
                    lda       #38
                    sta       vmvariables+24,u
                    lda       #1
                    sta       <vmplayercontrol
                    lbra      GameReadClock

* A completed logic cycle: clear transient state, wait without mappings,
* poll stdin without blocking, then resume root logic at its scan start.
GameNextCycle       lbsr      AssetUnmap
                    lbcs      GameCycleReturn
                    lbsr      PictureUnmap
                    lbcs      GameCycleReturn
                    ldu       <resourcebase
                    tst       gamequit,u
                    lbne      GameCycleSuccess
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
                    ldy       #32
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
                    lbsr      GameUpdateObjects
                    lbcs      GameCycleReturn
                    ldu       <resourcebase
                    lda       #40
                    sta       gamekeybudget,u
GameDrainKeyboard   lbsr      GamePollKeyboard
                    lbcs      GameCycleReturn
                    ldu       <resourcebase
                    tst       gamekeypending,u
                    beq       GameKeyboardDone
                    tst       vmflags+2,u
                    bne       GameKeyboardDone
                    dec       gamekeybudget,u
                    bne       GameDrainKeyboard
GameKeyboardDone    tst       <bitmapowned
                    beq       GameCycleSuccess
                    lbsr      ParserDrawInput
                    lbsr      GameComposeScene
                    lbcs      GameCycleReturn
                    lbsr      PresentPicture
GameCycleReturn     rts
GameCycleSuccess    clrb
                    rts

* Returns B=0/C clear or an OS/validation error; A/X/D are scratch.
* Acquisition and modal reset policy stay here; rollover is common.
GameReadClock       ldu       <resourcebase
                    leax      gametime,u
GameClockTimeCall   os9       F$Time
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
                    use       platform/game-clock-operands.asm
                    use       shared/game-clock-tick.asm
                    AGI_CLOCK_TICK GameClockTick
                    bra       GameClockTick
GameClockStoreCurrent ldb     gametime+5,u
GameClockStore      stb       gameclocklast,u
                    clr       gameclockreset,u
                    clrb
                    rts
GameClockInvalid    ldb       #E$BMode
                    orcc      #1
                    rts

GamePollKeyboard    ldu       <resourcebase
                    clr       gamekeypending,u
                    clra
                    ldb       #SS.Ready
                    os9       I$GetStt
                    bcc       GameReadKey
                    cmpb      #E$NotRdy
                    lbne      GameCycleReturn
                    clrb
                    rts
GameReadKey         ldu       <resourcebase
                    inc       gamekeypending,u
                    leax      vmkeybyte,u
                    ldy       #1
                    clra
                    os9       I$Read
                    lbcs      GameCycleReturn
                    cmpy      #1
                    bne       GameClockInvalid
                    ifne      GAME_TRACE
                    ldu       <resourcebase
                    lda       <vmkeybyte
                    sta       gametracekeybyte,u
                    endc
                    clra
                    ldb       #SS.KySns
                    os9       I$GetStt
                    lbcs      GameCycleReturn
                    ldu       <resourcebase
                    sta       gamekeysense,u
                    clr       gamekeyscan,u
                    lda       #1
                    sta       <vmhavekey
                    lbsr      GameDirectionalKey
                    ldu       <resourcebase
                    ldb       <vmkeybyte
                    stb       vmvariables+19,u
                    leax      vmkeys,u
                    ldy       #0
GameKeyBinding      tfr       y,d
                    cmpb      <vmkeycount
                    lbhs      ParserKey
                    ldb       <vmkeybyte
                    cmpb      ,x
                    bne       GameNextBinding
                    lda       gamekeyscan,u
                    cmpa      1,x
                    bne       GameNextBinding
                    ldb       2,x
                    lbsr      InputControllerAddress
                    ora       ,x
                    sta       ,x
                    clr       vmvariables+19,u
                    clrb
                    rts
* Arrow codes overlap ordinary SCF control characters. Use the buffered
* key-sense byte from the character just read to distinguish them.
GameDirectionalKey  ldb       <vmkeybyte
                    cmpb      #5             CoCo-style Break key from Wild Bits K keyboard
                    bne       GameFunctionKey
                    ldb       #27
                    stb       <vmkeybyte
GameFunctionKey
                    cmpb      #$B1
                    blo       GameArrowKey
                    cmpb      #$B4
                    bhi       GameArrowKey
                    subb      #$76                 F1..Shift-F2 -> scans 3B..3E
                    stb       gamekeyscan,u
                    clr       <vmkeybyte
                    clrb
                    rts
GameArrowKey        leax      GameArrowTable,pcr
GameArrowFind       lda       ,x
                    beq       GameDirectionDone
                    cmpa      <vmkeybyte
                    bne       GameArrowNext
                    lda       gamekeysense,u
                    bita      1,x
                    beq       GameDirectionDone
                    clr       <vmkeybyte          arrows never become ASCII Tab/backspace controllers
                    tst       <vmplayercontrol
                    beq       GameDirectionDone
                    lda       2,x
                    sta       vmvariables+6,u
                    clrb
                    rts
GameArrowNext       leax      3,x
                    bra       GameArrowFind
GameDirectionDone   clrb
                    rts
GameArrowTable      fcb       $0C,$08,1,$0A,$10,5,$08,$20,7,$09,$40,3,0
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
GameQuitNeedsDialog clr       dialoginputmode,u
                    leax      GameQuitPrompt,pcr
                    lbsr      GamePrintText
                    lbcs      GameCycleReturn
                    ldu       <resourcebase
                    lda       parsercharacter,u
                    cmpa      #13
                    lbne      GameCycleSuccess
                    lda       #1
                    sta       gamequit,u
                    clrb
                    rts
GameQuitPrompt      fcc       /Quit the game?/
                    fcb       10
                    fcc       /ENTER quits; ESC cancels./
                    fcb       0

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
