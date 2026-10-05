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
                    lda       $26,u
                    anda      #$51
                    cmpa      #$51
                    lbne      MotionNextObject
                    lbsr      MotionAdvanceCel
                    lbcs      MotionReturn
                    ldx       <resourcebase
                    ldu       motionobject,x
                    lda       1,u
                    cmpa      #1
                    bls       MotionStepReady
                    dec       1,u
                    lbra      MotionNextObject
MotionStepReady     lda       ,u
                    sta       1,u
                    lda       $22,u
                    beq       MotionDirectionReady
                    cmpa      #1
                    bne       MotionNotWander
                    lbsr      ObjAnimStep
                    bra       MotionDirectionReady
MotionNotWander     cmpa      #2
                    bne       MotionNotFollow
                    lbsr      CalcFollowDir
                    ldx       <resourcebase
                    ldu       motionobject,x
                    bra       MotionDirectionReady
MotionNotFollow     cmpa      #3
                    lbne      MotionUnsupported
                    lbsr      MotionMoveDirection
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
                    use platform/coordinate-step-operands.asm
                    use shared/object-coordinate-step.asm
                    use platform/coordinate-clamp-operands.asm
MotionClampX        equ ClampCoordinates
MotionClampRight    equ ClampRightLimit
MotionClampTop      equ ClampTopLimit
MotionClampBottom   equ ClampBottomLimit
MotionHorizon       equ ClampHorizon
                    use shared/object-coordinate-clamp.asm
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
                    use platform/position-commit-operands.asm
MotionAccept        equ PositionAccepted
MotionOtherEdge     equ PositionOtherBoundary
                    use shared/object-position-commit.asm
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

                    use platform/target-motion-operands.asm
MotionMoveDirection equ TargetDirection
MotionArrived       equ TargetReached
MotionArrivedDone   equ TargetReachedReturn
                    use shared/object-target-motion.asm

* Animation modes match the CoCo forward/reverse/end-of-loop transitions.
MotionAdvanceCel    lda       $25,u
                    bita      #$20
                    bne       MotionCycleTick
                    lda       $0B,u
                    cmpa      #2
                    blo       MotionCycleTick
                    cmpa      #4
                    bhi       MotionCycleTick
                    leay      DirTableFwd,pcr
                    cmpa      #4
                    bne       MotionChooseLoop
                    leay      DirTableRev,pcr
MotionChooseLoop    ldb       $21,u
                    cmpb      #8
                    lbhi      MotionInvalid
                    ldb       b,y
                    cmpb      #4
                    beq       MotionCycleTick
                    cmpb      $0A,u
                    beq       MotionCycleTick
                    lda       #43
                    lbsr      MotionSelectView
                    lbcs      MotionReturn
                    ldx       <resourcebase
                    ldu       motionobject,x
MotionCycleTick     lda       $26,u
                    bita      #$20
                    beq       MotionCycleDone
                    lda       $20,u
                    beq       MotionCycleDone
                    dec       $20,u
                    bne       MotionCycleDone
                    lda       $1F,u
                    sta       $20,u
                    lbra      AdvanceCelFrame
MotionCycleDone     clrb
                    rts
                    use       platform/wildbits-cel-advance.asm
                    use       shared/object-cel-advance.asm
                    use       shared/object-direction-tables.asm
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
