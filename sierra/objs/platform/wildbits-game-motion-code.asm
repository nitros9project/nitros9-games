* Native object stepping. Coordinates are checked against picture controls
* before being committed; view selection remains in its own component.
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
                    use platform/motion-operands.asm
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
                    lbne      MotionBlocked
                    lbsr      MotionTerrain
                    lbcs      MotionReturn
                    tstb
                    lbne      MotionBlocked
MotionAccept        equ PositionAccepted
MotionOtherEdge     equ PositionOtherBoundary
                    MOTION_EMIT_COMMIT
MotionCheckDestination lda    $22,u
                    cmpa      #3
                    bne       MotionNextObject
                    ldd       3,u
                    cmpd      $27,u
                    bne       MotionNextObject
                    lbsr      MotionArrived
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
                    lbeq      MotionInvalid
                    lda       #1
                    sta       motionwater,x
                    clr       motiontrigger,x
                    clr       motioncolumn,x
                    use platform/terrain-operands.asm
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
                    use platform/object-collision-operands.asm
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
                    use platform/animation-operands.asm
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
