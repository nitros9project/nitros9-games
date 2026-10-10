* wildbits-objects feature: code and related private state.
* Named layout sections preserve existing module and private-data addresses.

                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_BLOCK_CODE
* ===== wildbits-game-block-code =====
GameBlockCommand    ldx       <resourcebase
                    ldb       <vmopcode
                    cmpb      #91
                    beq       GameBlockClear
                    ldd       vmarguments,x
                    std       BlockLeft,x
                    ldd       vmarguments+2,x
                    std       BlockRight,x
                    lda       #1
                    sta       gameblockenabled,x
                    clrb
                    rts
GameBlockClear      clr       gameblockenabled,x
                    clrb
                    rts
BLOCK_PRIVATE_STATE equ       1
                    use       shared/object-block-test.asm
                    ifndef SHARED_OBJECT_COMMANDS_DEFINED
                    use shared/object-commands.asm
                    endc
GameCheckBlock      OBJECT_BLOCK_CLEAR u
                    bita      #2
                    bne       GameBlockAllowed
                    tst       gameblockenabled,x
                    beq       GameBlockAllowed
                    ldd       motionoldposition,x
                    bsr      InBlockRect
                    sta       motioncollision,x
                    lda       motionx+1,x
                    ldb       motiony+1,x
                    bsr      InBlockRect
                    cmpa      motioncollision,x
                    beq       GameBlockAllowed
GameBlockCrossing   OBJECT_BLOCK_STOP u,GameBlockStopped
GameBlockStopped    ldb       #1
                    rts
GameBlockAllowed    clrb
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_BLOCK_DATA
* ===== wildbits-game-block-data =====
gameblockenabled    rmb       1
BlockLeft           rmb       1
BlockTop            rmb       1
BlockRight          rmb       1
BlockBottom         rmb       1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_CYCLE_CODE
* ===== wildbits-game-cycle-code =====
GameInitialize      lbsr      ParserInitialize
                    ldu       <resourcebase
                    ldd       #$ACE1
                    std       gamerandom,u
                    clr       soundinstalled,u
                    clr       inventoryloaded,u
                    clr       gameblockenabled,u
                    clr       monitorprofile,u
                    clr       joystickenabled,u
                    clr       joysticklast,u
                    clr       joystickbuttons,u
                    clr       joystickpressed,u
                    clr       gamequit,u
                    clr       gameclockreset,u
                    lda       #$FF
                    sta       gameclocklast,u
                    lda       #1
                    sta       vmflags+5,u
                    sta       vmflags+9,u     owned queued audio; unavailable service disables it
                    sta       vmflags+11,u
                    ldb       <vmroompending
                    cmpb      #3
                    bne       GameInitialFlags
                    sta       vmflags+6,u
                    clr       <vmroompending
GameInitialFlags    equ       *
                    sta       vmvariables+22,u     three-channel sound model
                    lda       #3
                    sta       vmvariables+26,u     EGA-compatible palette
                    lda       #38
                    sta       vmvariables+24,u
                    lda       #1
                    sta       <vmplayercontrol
                    lbsr      GameClockOpen
                    lbra      GameReadClock

* A completed logic cycle: clear transient state, wait without mappings,
* poll stdin without blocking, then resume root logic at its scan start.
                    use shared/game-cycle.asm
GameNextCycle       lbsr      AssetUnmap
                    lbcs      GameCycleReturn
                    lbsr      PictureUnmap
                    lbcs      GameCycleReturn
                    lbsr      GameSoundTick
                    lbcs      GameCycleReturn
                    ldu       <resourcebase
                    tst       gamequit,u
                    lbne      GameCycleSuccess
                    lbsr      foreground
                    lbcs     GameCycleReturn
                    ldu       <resourcebase
GameCycleInputReset AGI_CYCLE_INPUT_RESET
GameCycleRoomReset  AGI_CYCLE_ROOM_RESET
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
                    lbsr      GameClockGate
                    lbcs     GameCycleReturn
                    lbsr      foreground
                    lbcs     GameCycleReturn
                    bsr      GameReadClock
                    lbcs     GameCycleReturn
                    lbsr      GamePollJoystick
                    bcs       GameCycleReturn
                    lbsr      GameUpdateObjects
                    bcs       GameCycleReturn
                    ldu       <resourcebase
                    lda       #40
                    sta       gamekeybudget,u
GameDrainKeyboard   lbsr      GamePollKeyboard
                    lbcs     GameCycleReturn
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
                    bcs       GameCycleReturn
                    tst       <vmgraphics
                    bne       GameCycleGraphics
                    lbra      GameDrawText
GameCycleGraphics   lbsr      GameComposeScene
                    lbcs     GameCycleReturn
                    lbsr      PresentPicture
GameCycleReturn     rts
GameCycleSuccess    clrb
                    rts

* Returns B=0/C clear or an OS/validation error; A/X/D are scratch.
* Acquisition and modal reset policy stay here; rollover is common.
GameReadClock       ldu       <resourcebase
                    leax      gametime,u
GameClockTimeCall   os9       F$Time
                    lbcs     GameCycleReturn
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
* Assembly-time clock storage interface; no runtime dispatch.
                    ifne      WILDBITS
                    ifndef PLATFORM_WILDBITS_TIMING_BINDINGS
                    use platform/wildbits-timing.asm
                    endc
                    else
                    ifndef PLATFORM_COCO_TIMING_BINDINGS
                    use platform/sections.d
PLATFORM_SECTION    set PLATFORM_COCO_GAME_CLOCK_BINDINGS
                    use platform/coco-timing.asm
                    endc
                    endc
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
                    bsr      GameDirectionalKey
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
                    cmpa      vmvariables+6,u
                    bne       GameDirectionStore
                    clra
GameDirectionStore  sta       vmvariables+6,u
                    clrb
                    rts
GameArrowNext       leax      3,x
                    bra       GameArrowFind
GameDirectionDone   clrb
                    rts
GameArrowTable      fcb       $0C,$08,1,$0A,$10,5,$08,$20,7,$09,$40,3,0
GameNextBinding     leax      3,x
                    leay      1,y
                    lbra      GameKeyBinding

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

PLATFORM_WILDBITS_TIMING_CODE equ 1
                    use platform/wildbits-timing.asm

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_CYCLE_DATA
* ===== wildbits-game-cycle-data =====
* Game scheduling belongs to this owner, not the bytecode-only probe.
gamequit            rmb      1
gameclocklast       rmb      1
gameclockdelta      rmb      1
gameclockreset      rmb      1
gamecleanup         rmb      1
gametime            rmb      6
soundinstalled      rmb      1
gamerandom          rmb      2
gamekeybudget       rmb      1
gamekeypending      rmb      1
* Six bytes remain within the existing three private pages.
gameclockpath       rmb      1
gameclockticks      rmb      1
gameclockseen       rmb      1
gameclockcredit     rmb      2
gameclockmuted      rmb      1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_MOTION_CODE
* ===== wildbits-game-motion-code =====
* Native object stepping. Coordinates are checked against picture controls
* before being committed; view selection remains in its own component.
* Force redraw never advances object motion or cel countdowns.
GameForceUpdate     lbsr      ObjectAddress
                    lbcs      ObjectReturn
                    lbsr      AssetUnmap
                    lbcs      ObjectReturn
                    lbsr      PictureUnmap
                    lbcs      ObjectReturn
                    ldu       <resourcebase
                    tst       gamebackgroundowned,u
                    beq       GameForceCompose
                    lbsr      GameRestoreBackground
                    lbcs      ObjectReturn
GameForceCompose    lbsr      GameComposeScene
                    lbcs      ObjectReturn
                    lbra      PresentPicture

GameUpdateObjects   lbsr      AssetUnmap
                    lbcs      MotionReturn
                    lbsr      PictureUnmap
                    lbcs      MotionReturn
                    ldx       <resourcebase
                    tst       gamebackgroundowned,x
                    beq       MotionBackgroundReady
                    lbsr      GameRestoreBackground
                    lbcs      MotionReturn
MotionBackgroundReady ldx    <resourcebase
                    clr       motionid,x
                    clr       vmvariables+2,x
                    clr       vmvariables+4,x
                    clr       vmvariables+5,x
                    lda       vmvariables+6,x
                    sta       vmobjects+$21,x
MotionObjectNext    ldb       motionid,x
                    lda       #43
                    mul
                    leau      vmobjects,x
                    leau      d,u
                    stu       motionobject,x
                    ifne WILDBITS
                    ifndef PLATFORM_WILDBITS_OBJECTS_BINDINGS
                    use platform/wildbits-objects-bindings.asm
                    endc
                    else
                    ifndef PLATFORM_COCO_OBJECTS_BINDINGS
                    use platform/coco-objects-bindings.asm
                    endc
                    endc

                    use shared/object-motion.asm
                    MOTION_EMIT_SCHEDULE
MotionNotWander equ MotionScheduleNotWander
MotionNotFollow equ MotionScheduleNotFollow
MotionDirectionReady ldb      $21,u
                    cmpb      #8
                    lbhi      MotionInvalid
                    ldd       3,u
                    std       motionoldposition,x
                    clra
                    ldb       3,u
                    std       motionx,x
                    ldb       4,u
                    std       motiony,x
                    ldb       $1E,u
                    std       motionstep,x
                    clr       motionedge,x
                    MOTION_EMIT_COORDINATE_STEP
MotionClampX        equ ClampCoordinates
MotionClampRight    equ ClampRightLimit
MotionClampTop      equ ClampTopLimit
MotionClampBottom   equ ClampBottomLimit
MotionHorizon       equ ClampHorizon
                    MOTION_EMIT_CLAMP
MotionTargetClamp   lda       $22,u
                    cmpa      #3
                    bne       MotionCheckTerrain
* A move-to step stops exactly at the target rather than overshooting it.
                    clra
                    ldb       $27,u
                    pshs      d
                    ldb       $21,u
                    leay      MotionXDelta,pcr
                    lda       b,y
                    beq       MotionTargetXReady
                    bpl       MotionTargetXPositive
                    ldd       motionx,x
                    cmpd      ,s
                    bge       MotionTargetXReady
                    bra       MotionTargetXStore
MotionTargetXPositive ldd     motionx,x
                    cmpd      ,s
                    ble       MotionTargetXReady
MotionTargetXStore  ldd       ,s
                    std       motionx,x
MotionTargetXReady  leas      2,s
                    clra
                    ldb       $28,u
                    pshs      d
                    ldb       $21,u
                    leay      MotionYDelta,pcr
                    lda       b,y
                    beq       MotionTargetYReady
                    bpl       MotionTargetYPositive
                    ldd       motiony,x
                    cmpd      ,s
                    bge       MotionTargetYReady
                    bra       MotionTargetYStore
MotionTargetYPositive ldd     motiony,x
                    cmpd      ,s
                    ble       MotionTargetYReady
MotionTargetYStore  ldd       ,s
                    std       motiony,x
MotionTargetYReady  leas      2,s
MotionCheckTerrain  lbsr      GameCheckBlock
                    tstb
                    bne      MotionBlocked
                    lbsr      MotionTerrain
                    lbcs      MotionReturn
                    tstb
                    bne      MotionBlocked
MotionAccept        equ PositionAccepted
MotionOtherEdge     equ PositionOtherBoundary
                    MOTION_EMIT_COMMIT
MotionCheckDestination MOTION_CHECK_DESTINATION MotionNextObject,1,MotionArrived
                    bra       MotionNextObject
MotionBlocked       ldu       motionobject,x
                    lda       $22,u
                    cmpa      #1
                    beq       MotionMarkBlocked
                    cmpa      #2
                    bne       MotionNextObject
MotionMarkBlocked   lda       $25,u
                    ora       #$40
                    sta       $25,u
MotionNextObject    ldx       <resourcebase
                    inc       motionid,x
                    lda       motionid,x
                    cmpa      #64
                    lblo      MotionObjectNext
                    ldu       <resourcebase
                    lda       vmobjects+$21,u
                    sta       vmvariables+6,u
                    clrb
MotionReturn        rts
MotionInvalid       ldb       #E$BMode
                    orcc      #1
                    rts
MotionUnsupported   ldb       #E$UnkSvc
                    orcc      #1
                    rts
MotionXDelta        equ StepXDelta
MotionYDelta        equ StepYDelta
                    use shared/object-step-deltas.asm

* Each baseline pixel participates in control/water checks. Sprite colors
* are restored out of the composition buffer before this function is called.
MotionTerrain       tst       <pictureowned
                    beq      MotionInvalid
                    lda       #1
                    sta       motionwater,x
                    clr       motiontrigger,x
                    clr       motioncolumn,x
                    ifne WILDBITS
                    ifndef PLATFORM_WILDBITS_OBJECTS_BINDINGS
                    use platform/wildbits-objects-bindings.asm
                    endc
                    else
                    ifndef PLATFORM_COCO_OBJECTS_BINDINGS
                    use platform/coco-objects-bindings.asm
                    endc
                    endc
MotionTerrainPixel  equ TerrainPixelLoop
MotionTerrainAdvance equ TerrainPixelAdvance
                    use shared/object-terrain-scan.asm
                    lbsr      PictureUnmap
                    lbcs      MotionReturn
                    ldx       <resourcebase
                    ldu       motionobject,x
                    use shared/object-terrain-constraints.asm
MotionTerrainAccept tst       motionid,x
                    bne       MotionTerrainDone
                    lda       motionwater,x
                    sta       vmflags,x
                    lda       motiontrigger,x
                    sta       vmflags+3,x
MotionTerrainDone   clrb
                    rts
MotionTerrainBlocked lbsr     PictureUnmap
                    lbcs      MotionReturn
                    ldx       <resourcebase
                    ldb       #1
                    andcc     #$FE
                    rts
MotionTerrainError  ldb       <decodeerror
                    orcc      #1
                    rts

* Baseline collisions, including crossing another baseline between steps.
                    ifne WILDBITS
                    ifndef PLATFORM_WILDBITS_OBJECTS_BINDINGS
                    use platform/wildbits-objects-bindings.asm
                    endc
                    else
                    ifndef PLATFORM_COCO_OBJECTS_BINDINGS
                    use platform/coco-objects-bindings.asm
                    endc
                    endc
                    use shared/object-collision-filter.asm
MotionObjectCollision equ CollisionScan
MotionCollisionNext equ CollisionScanLoop
MotionCollisionAdvance equ CollisionScanAdvance
MotionNoCollision   equ CollisionScanEmpty
MotionCollided      equ CollisionScanHit
MotionCrossDown     equ CollisionCrossDown
                    use shared/object-collision-scan.asm

MotionMoveDirection equ TargetDirection
MotionArrived       equ TargetReached
MotionArrivedDone   equ TargetReachedReturn
                    MOTION_EMIT_TARGET

* Animation modes match the CoCo forward/reverse/end-of-loop transitions.
                    ifne WILDBITS
                    ifndef PLATFORM_WILDBITS_MEMORY_RESOURCES_BINDINGS
                    use platform/wildbits-memory-resources-bindings.asm
                    endc
                    else
                    ifndef PLATFORM_COCO_MEMORY_RESOURCES_BINDINGS
                    use platform/coco-memory-resources-bindings.asm
                    endc
                    endc

MotionAdvanceCel equ *
                    use shared/object-animation.asm
                    ANIMATION_EMIT_UPDATE
MotionCycleTick equ AnimationCycleTick
MotionCycleDone equ AnimationCycleDone
                    ANIMATION_EMIT_CEL_ADVANCE
                    ANIMATION_EMIT_DIRECTION_TABLES
* A=selection opcode, B=index. The ordinary view component refreshes cel
* metadata; scratch instruction arguments/opcode are restored afterwards.
MotionSelectView    pshs      a,b
                    lda       <vmopcode
                    pshs      a
                    lda       vmarguments,x
                    ldb       vmarguments+1,x
                    pshs      d
                    lda       motionid,x
                    sta       vmarguments,x
                    lda       4,s
                    sta       vmarguments+1,x
                    lda       3,s
                    sta       <vmopcode
                    lbsr      ViewCommand
                    pshs      cc,b
                    ldx       <resourcebase
                    ldd       2,s
                    std       vmarguments,x
                    lda       4,s
                    sta       <vmopcode
                    puls      cc,b
                    leas      5,s
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_MOTION_COMMAND
* ===== wildbits-game-motion-command =====
* move.obj / move.obj.v use private targets and a literal completion flag.
GameMoveCommand     lbsr      ObjectAddress
                    lbcs      MotionReturn
                    ldb       <vmopcode
                    cmpb      #82
                    beq       GameMoveVariables
                    ldd       vmarguments+1,u
                    bra       GameMoveTarget
GameMoveVariables   leay      vmvariables,u
                    clra
                    ldb       vmarguments+1,u
                    lda       d,y
                    pshs      a
                    clra
                    ldb       vmarguments+2,u
                    ldb       d,y
                    puls      a
GameMoveTarget      cmpa      #160
                    lbhs      ObjectBadIndex
                    cmpb      #168
                    lbhs      ObjectBadIndex
                    std       $27,x
                    lda       #3
                    sta       $22,x
                    OBJECT_MOVE_SETUP x,0,GameMoveFlag,GameMoveSetup
                    clrb
                    rts

GameFollowCommand   lbsr      ObjectAddress
                    lbcs      ObjectReturn
                    leay      vmarguments+1,u
                    OBJECT_FOLLOW_SETUP x,GameFollowDistance
                    lbra      ObjectDone
GameFollowSetFlag   pshs      a,x
                    ldx       <resourcebase
                    leax      vmflags,x
                    ldb       ,s
                    clra
                    leax      d,x
                    lda       #1
                    sta       ,x
                    puls      a,x,pc
FOLLOW_PRIVATE_STATE equ     1
                    use       shared/object-follow.asm
                    MOVE_DIRECTION_CODE
MoveTableData       fcb       8,1,2,7,0,3,6,5,4

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_MOTION_DATA
* ===== wildbits-game-motion-data =====
* Logical coordinates and private records; no mapped view/picture pointers.
motionobject        rmb      2
motionid            rmb      1
motionx             rmb      2
motiony             rmb      2
motionstep          rmb      2
motionedge          rmb      1
motioncolumn        rmb      1
motionwater         rmb      1
motiontrigger       rmb      1
motionoldposition   rmb      2
motioncollision     rmb      1
gamekeyscan         rmb      1
gamekeysense        rmb      1

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_REPOSITION_CODE
* ===== wildbits-game-reposition-code =====
* Relative signed-byte deltas and absolute coordinates, followed by the same
* left/down/right/up expanding placement search as CoCo. Bound failed searches.
GameReposition      lbsr      ObjectAddress
                    lbcs      ObjectReturn
                    ldd       3,x
                    std       $1A,x
                    lda       <vmopcode
                    cmpa      #40
                    bne       RepositionAbsolute
                    leay      vmvariables,u
                    clra
                    ldb       vmarguments+1,u
                    ldb       d,y
                    OBJECT_SIGNED_DELTA x,3,RepositionX
                    clra
                    ldb       vmarguments+2,u
                    ldb       d,y
                    OBJECT_SIGNED_DELTA x,4,RepositionY
                    bra       RepositionPlace
RepositionAbsolute  lda       <vmopcode
                    cmpa      #148
                    beq       RepositionVariables
                    OBJECT_POSITION x,0,0
                    bra       RepositionPlace
RepositionVariables OBJECT_POSITION x,1,0
RepositionPlace     stx       motionobject,u
                    lda       2,x
                    sta       motionid,u
                    lbsr      AssetUnmap
                    lbcs      ObjectReturn
                    lbsr      PictureUnmap
                    lbcs      ObjectReturn
                    ldx       <resourcebase
                    tst       gamebackgroundowned,x
                    beq       RepositionBackground
                    lbsr      GameRestoreBackground
                    lbcs      ObjectReturn
RepositionBackground ldx     <resourcebase
                    ldu       motionobject,x
                    lda       $26,u
                    bita      #8
                    bne       RepositionSearch
                    lda       <vmhorizon
                    cmpa      4,u
                    blo       RepositionSearch
                    inca
                    sta       4,u
RepositionSearch    leas      -5,s
                    clr       ,s         direction: left/down/right/up
                    lda       #1
                    sta       1,s        run length
                    sta       2,s        remaining steps
                    ldd       #$FFFF
                    std       3,s        explicit search budget
RepositionCandidate ldx      <resourcebase
                    ldu       motionobject,x
                    ifne WILDBITS
                    ifndef PLATFORM_WILDBITS_OBJECTS_BINDINGS
                    use platform/wildbits-objects-bindings.asm
                    endc
                    else
                    ifndef PLATFORM_COCO_OBJECTS_BINDINGS
                    use platform/coco-objects-bindings.asm
                    endc
                    endc
                    use shared/object-bounds.asm
                    OBJECT_CHECK_BOUNDS u,RepositionReject,RepositionBounds
                    ldd       3,u
                    std       motionoldposition,x
                    clra
                    ldb       3,u
                    std       motionx,x
                    ldb       4,u
                    std       motiony,x
                    lbsr      MotionObjectCollision
                    tstb
                    bne       RepositionReject
                    lbsr      MotionTerrain
                    lbcs      RepositionError
                    tstb
                    beq       RepositionFound
RepositionReject    ldu       motionobject,x
                    ldd       3,s
                    subd      #1
                    std       3,s
                    beq      RepositionExhausted
                    ifne WILDBITS
                    ifndef PLATFORM_WILDBITS_OBJECTS_BINDINGS
                    use platform/wildbits-objects-bindings.asm
                    endc
                    else
                    ifndef PLATFORM_COCO_OBJECTS_BINDINGS
                    use platform/coco-objects-bindings.asm
                    endc
                    endc
                    use shared/object-placement-step.asm
RepositionFound     ldu       motionobject,x
                    lda       $25,u
                    ora       #4
                    sta       $25,u
                    ldd       3,u
                    std       $1A,u
                    leas      5,s
                    clrb
                    rts
RepositionExhausted ldb       #E$BMode
                    orcc      #1
RepositionError     pshs      b,cc
                    ldx       <resourcebase
                    ldu       motionobject,x
                    ldd       $1A,u
                    std       3,u
                    puls      cc,b
                    leas      5,s
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_GAME_WANDER_CODE
* ===== wildbits-game-wander-code =====
                    ifndef PLATFORM_WILDBITS_OBJECTS_BINDINGS
                    use platform/wildbits-objects-bindings.asm
                    endc
                    use       shared/object-motion-setup.asm
GameWanderCommand   lbsr      ObjectAddress
                    lbcs      ObjectReturn
                    OBJECT_WANDER_SETUP x,GameWanderDone
                    lbra      ObjectDone
* Private 16-bit Galois LFSR; no mapped pointers or global random state.
GameRandomByte      ldx       <resourcebase
                    ldd       gamerandom,x
                    lsra
                    rorb
                    bcc       GameRandomStore
                    eora      #$B4
GameRandomStore     std       gamerandom,x
                    andcc     #$FE
                    rts
InitRandSeed        equ       GameRandomByte
DivideDivisor       equ       vmtemp
DivideBits          equ       vmleft
                    use       shared/divide-byte.asm
WANDER_PRIVATE_STATE equ      1
                    use       shared/object-wander.asm

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_WILDBITS_OBJECT_CODE
* ===== wildbits-object-code =====
                    ifndef PLATFORM_WILDBITS_OBJECTS_BINDINGS
                    use platform/wildbits-objects-bindings.asm
                    endc
* Assembly-time operand/storage interface; emits no runtime dispatch.
                    ifne      WILDBITS
                    ifndef PLATFORM_WILDBITS_OBJECTS_BINDINGS
                    use platform/wildbits-objects-bindings.asm
                    endc
                    else
                    ifndef PLATFORM_COCO_OBJECTS_BINDINGS
                    use platform/coco-objects-bindings.asm
                    endc
                    endc
                    ifndef SHARED_OBJECT_COMMANDS_DEFINED
                    use shared/object-commands.asm
                    endc
                    ifndef SHARED_OBJECT_COMMANDS_DEFINED
                    use shared/object-commands.asm
                    endc
                    ifne WILDBITS
                    ifndef PLATFORM_WILDBITS_OBJECTS_BINDINGS
                    use platform/wildbits-objects-bindings.asm
                    endc
                    else
                    ifndef PLATFORM_COCO_OBJECTS_BINDINGS
                    use platform/coco-objects-bindings.asm
                    endc
                    endc
                    ifndef SHARED_OBJECT_COMMANDS_DEFINED
                    use shared/object-commands.asm
                    endc
                    ifne WILDBITS
                    ifndef PLATFORM_WILDBITS_OBJECTS_BINDINGS
                    use platform/wildbits-objects-bindings.asm
                    endc
                    else
                    ifndef PLATFORM_COCO_OBJECTS_BINDINGS
                    use platform/coco-objects-bindings.asm
                    endc
                    endc
                    ifndef SHARED_OBJECT_COMMANDS_DEFINED
                    use shared/object-commands.asm
                    endc
* Private object-state commands adapted from mnln.asm's 43-byte records.
* The owner supplies 64 records. Drawing, cel selection and motion updates
* remain separate; these commands never retain a foreign resource pointer.
ObjectsInitialize   ldu       <resourcebase
                    leax      vmobjects,u
                    ldy       #2752
                    clra
ObjectsClear        sta       ,x+
                    leay      -1,y
                    bne       ObjectsClear
                    leax      vmobjects,u
                    clrb
ObjectsSetId        stb       2,x
                    lda       #1
                    sta       ,x
                    sta       1,x
                    sta       $1E,x
                    sta       $1F,x
                    sta       $20,x
                    leax      43,x
                    incb
                    cmpb      #64
                    blo       ObjectsSetId
                    rts
ObjectAddress       ldu       <resourcebase
                    lda       vmarguments,u
                    cmpa      #64
                    bhs       ObjectBadIndex
                    ldb       #43
                    mul
                    leax      vmobjects,u
                    leax      d,x
                    andcc     #$FE
                    rts
ObjectBadIndex      ldb       #E$IllArg
                    orcc      #1
                    rts
ObjectCommand       ldb       <vmopcode
                    cmpb      #34
                    beq       ObjectsUnanimate
                    bsr      ObjectAddress
                    bcs       ObjectReturn
                    ldb       <vmopcode
                    cmpb      #33
                    beq       ObjectAnimate
                    cmpb      #37
                    lbeq      ObjectPosition
                    cmpb      #38
                    lbeq      ObjectPositionVariables
                    cmpb      #39
                    lbeq      ObjectGetPosition
                    cmpb      #45
                    lbeq      ObjectFixLoop
                    cmpb      #46
                    lbeq      ObjectReleaseLoop
                    cmpb      #54
                    lbeq      ObjectPriority
                    cmpb      #55
                    lbeq      ObjectPriorityVariable
                    cmpb      #56
                    lbeq      ObjectReleasePriority
                    cmpb      #57
                    lbeq      ObjectGetPriority
                    cmpb      #58
                    lbeq      ObjectStopUpdate
                    cmpb      #59
                    lbeq      ObjectStartUpdate
                    cmpb      #86
                    lbeq      ObjectDirection
                    cmpb      #87
                    lbeq      ObjectGetDirection
                    ldb       #E$UnkSvc
                    orcc      #1
ObjectReturn        rts
ObjectAnimate       OBJECT_ANIMATE_STATE x,ObjectDone
ObjectDone          clrb
                    rts
ObjectsUnanimate    ldu       <resourcebase
                    leax      vmobjects,u
                    ldy       #64
                    OBJECT_UNANIMATE_ALL x,ObjectsUnanimateNext,ObjectsUnanimateDone
                    clrb
                    rts
ObjectPosition      OBJECT_POSITION x,0,1
                    clrb
                    rts
ObjectPositionVariables OBJECT_POSITION x,1,1
                    clrb
                    rts
ObjectGetPosition   OBJECT_GET_POSITION x,y
                    clrb
                    rts
* Stopped objects stay visible; the shared scheduler skips O_UPDATE=0.
ObjectStopUpdate    lda       $26,x
                    anda      #$EF
                    bra       ObjectUpdateStore
ObjectStartUpdate   lda       $26,x
                    ora       #$10
ObjectUpdateStore   sta       $26,x
                    bra      ObjectDone
ObjectFixLoop       lbra      CmdFixLoop
ObjectReleaseLoop   lbra      CmdReleaseLoop
ObjectArgumentValue leay      vmvariables,u
                    clra
                    ldb       vmarguments+1,u
                    ldb       d,y
                    rts
ObjectPriority      ldb       vmarguments+1,u
                    bra       ObjectSetPriority
ObjectPriorityVariable bsr   ObjectArgumentValue
ObjectSetPriority   OBJECT_SET_PRIORITY x,0
                    lbra      ObjectDone
ObjectReleasePriority lbra    cmd_release_priority
                    OBJECT_FIELD_QUERY ObjectGetPriority,$24,0
ObjectDirection     OBJECT_SET_DIRECTION x,b,ObjectDone
                    lbra      ObjectDone
                    OBJECT_FIELD_QUERY ObjectGetDirection,$21,0
* CoCo terrain/interaction flag operations; masks and offsets are immutable.
ObjectFlagCommand   ldb       <vmopcode
                    cmpb      #63
                    beq       ObjectSetHorizon
                    leay      ObjectFlagTable,pcr
ObjectFlagFind      lda       ,y
                    beq       ObjectFlagUnsupported
                    cmpa      <vmopcode
                    beq       ObjectFlagFound
                    leay      3,y
                    bra       ObjectFlagFind
ObjectFlagFound     lbsr      ObjectAddress
                    lbcs      ObjectReturn
                    ldd       1,y
                    leay      ObjectFlagTable,pcr
                    leay      d,y
                    jsr       ,y
                    rts
ObjectSetHorizon    ldu       <resourcebase
                    ldb       vmarguments,u
                    cmpb      #167
                    lbhi      ObjectBadIndex
                    stb       <vmhorizon
                    clrb
                    rts
ObjectFlagUnsupported ldb     #E$UnkSvc
                    orcc      #1
                    rts
                    ifndef SHARED_OBJECT_COMMANDS_DEFINED
                    use shared/object-commands.asm
                    endc
OBJECT_FLAG_TABLE   set       1
ObjectFlagTable     equ       *
                    use       shared/object-flag-rules.asm
                    fcb       0
OBJECT_FLAG_TABLE   set       0
                    use       shared/object-flag-rules.asm
* Cycle and step parameters; actual per-frame advancement is a separate body.
ObjectCycleCommand  lbsr      ObjectAddress
                    lbcs      ObjectReturn
                    ldb       <vmopcode
                    cmpb      #70
                    beq      ObjectStopCycle
                    cmpb      #71
                    beq      ObjectStartCycle
                    cmpb      #72
                    beq      ObjectNormalCycle
                    cmpb      #74
                    beq      ObjectReverseCycle
                    cmpb      #73
                    beq      ObjectEndCycle
                    cmpb      #75
                    beq      ObjectReverseEnd
                    cmpb      #76
                    beq      ObjectCycleTime
                    cmpb      #79
                    lbeq      ObjectStepSize
                    cmpb      #80
                    lbeq      ObjectStepTime
                    cmpb      #85
                    lbeq      ObjectNormalMotion
                    cmpb      #77
                    lbeq      ObjectStopMotion
                    cmpb      #78
                    lbeq      ObjectStartMotion
                    ldb       #E$UnkSvc
                    orcc      #1
                    rts
                    ifndef SHARED_OBJECT_COMMANDS_DEFINED
                    use shared/object-commands.asm
                    endc
ObjectStopCycle     bra      CmdStopCycling
ObjectStartCycle    bra      CmdStartCycling
ObjectNormalCycle   OBJECT_CYCLE_STATE 0,x,0
                    lbra      ObjectDone
ObjectReverseCycle  OBJECT_CYCLE_STATE 3,x,0
                    lbra      ObjectDone
ObjectEndCycle      OBJECT_CYCLE_STATE 1,x,1
                    bra       ObjectEndCycleFlag
ObjectReverseEnd    OBJECT_CYCLE_STATE 2,x,1
ObjectEndCycleFlag  equ       *
                    ldb       vmarguments+1,u
                    stb       $27,x
                    leay      vmflags,u
                    clra
                    leay      d,y
                    clr       ,y
                    lbra      ObjectDone
                    ifndef SHARED_OBJECT_COMMANDS_DEFINED
                    use shared/object-commands.asm
                    endc
ObjectCycleTime     lbsr      ObjectArgumentValue
                    OBJECT_RATE_STATE b,x,$1F,$20
                    lbra      ObjectDone
ObjectStepSize      lbsr      ObjectArgumentValue
                    OBJECT_RATE_STATE b,x,$1E,-1
                    lbra      ObjectDone
ObjectStepTime      lbsr      ObjectArgumentValue
                    OBJECT_RATE_STATE b,x,0,1
                    lbra      ObjectDone
                    ifndef SHARED_OBJECT_COMMANDS_DEFINED
                    use shared/object-commands.asm
                    endc
ObjectNormalMotion  OBJECT_MOTION_STATE x,0
                    lbra      ObjectDone
ObjectStopMotion    OBJECT_MOTION_STATE x,1
                    tst       vmarguments,u
                    lbne      ObjectDone
                    clr       vmvariables+6,u
                    clr       <vmplayercontrol
                    lbra      ObjectDone
ObjectStartMotion   OBJECT_MOTION_STATE x,0
                    tst       vmarguments,u
                    lbne      ObjectDone
                    clr       vmvariables+6,u
                    lda       #1
                    sta       <vmplayercontrol
                    lbra      ObjectDone

* Resolve object operands separately from the shared distance calculation.
ObjectDistanceCommand lbsr    ObjectAddress
                    lbcs      ObjectReturn
                    pshs      x
                    lda       vmarguments+1,u
                    cmpa      #64
                    bhs       ObjectDistanceBad
                    ldb       #43
                    mul
                    leau      vmobjects,u
                    leau      d,u
                    puls      x
                    bra      ObjectDistance
ObjectDistanceBad   leas      2,s
                    lbra      ObjectBadIndex
ObjectDistanceScratch equ     vmtemp
                    use       shared/object-distance.asm
StoreDistResult     ldu       <resourcebase
                    leax      vmvariables,u
                    ldb       vmarguments+2,u
                    abx
                    sta       ,x
                    clrb
                    rts

ObjectPositionTest  lbsr      ObjectAddress
                    lbcs      ObjectReturn
                    lda       3,x
                    sta       <vmtemp
                    sta       <vmright
                    ldb       4,x
                    stb       <vmleft
                    ldb       <vmopcode
                    cmpb      #11
                    beq       ObjectPositionBounds
                    lda       $1C,x
                    cmpb      #16
                    bne       ObjectPositionEdge
                    lsra
                    adda      3,x
                    bra       ObjectPositionPoint
ObjectPositionEdge  adda      3,x
                    deca
                    cmpb      #18
                    beq       ObjectPositionRight
ObjectPositionPoint sta       <vmtemp
ObjectPositionRight sta       <vmright
ObjectPositionBounds leay    vmarguments+1,u
                    bsr      TestPosnX
                    tfr       a,b
                    andcc     #$FE
                    rts
PositionLeftY       equ       vmtemp
PositionRight       equ       vmright
                    use       shared/object-position-test.asm
RetTrue             lda       #1
                    rts
RetFalse            clra
                    rts

                    else
                    error Unknown platform feature section
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
