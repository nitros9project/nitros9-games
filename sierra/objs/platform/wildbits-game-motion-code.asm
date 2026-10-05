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
                    leay      MotionXDelta,pcr
                    ldb       $21,u
                    lda       b,y
                    beq       MotionCalculateY
                    bpl       MotionAddX
                    ldd       motionx,x
                    subd      motionstep,x
                    bra       MotionStoreX
MotionAddX          ldd       motionx,x
                    addd      motionstep,x
MotionStoreX        std       motionx,x
MotionCalculateY    leay      MotionYDelta,pcr
                    ldb       $21,u
                    lda       b,y
                    beq       MotionClampX
                    bpl       MotionAddY
                    ldd       motiony,x
                    subd      motionstep,x
                    bra       MotionStoreY
MotionAddY          ldd       motiony,x
                    addd      motionstep,x
MotionStoreY        std       motiony,x
MotionClampX        ldd       motionx,x
                    bpl       MotionClampRight
                    ldd       #0
                    std       motionx,x
                    lda       #4
                    sta       motionedge,x
                    bra       MotionClampTop
MotionClampRight    clra
                    ldb       $1C,u
                    lbeq      MotionInvalid
                    cmpb      #160
                    lbhi      MotionInvalid
                    negb
                    coma
                    addd      #160
                    cmpd      motionx,x
                    bhs       MotionClampTop
                    std       motionx,x
                    lda       #2
                    sta       motionedge,x
MotionClampTop      clra
                    ldb       $1D,u
                    lbeq      MotionInvalid
                    decb
                    cmpd      motiony,x
                    ble       MotionClampBottom
                    std       motiony,x
                    lda       #1
                    sta       motionedge,x
MotionClampBottom   ldd       motiony,x
                    cmpd      #167
                    ble       MotionHorizon
                    ldd       #167
                    std       motiony,x
                    lda       #3
                    sta       motionedge,x
MotionHorizon       lda       $26,u
                    bita      #8
                    bne       MotionTargetClamp
                    clra
                    ldb       <vmhorizon
                    addd      #1
                    cmpd      motiony,x
                    ble       MotionTargetClamp
                    std       motiony,x
                    lda       #1
                    sta       motionedge,x
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
                    ldu       motionobject,x
                    ldb       motionx+1,x
                    stb       3,u
                    ldb       motiony+1,x
                    stb       4,u
                    lbsr      MotionObjectCollision
                    tstb
                    beq       MotionAccept
                    ldd       motionoldposition,x
                    std       3,u
                    lbra      MotionBlocked
MotionAccept        lda       $25,u
                    anda      #$BF
                    sta       $25,u
                    lda       motionedge,x
                    beq       MotionCheckDestination
                    ldb       motionid,x
                    bne       MotionOtherEdge
                    sta       vmvariables+2,x
                    bra       MotionCheckDestination
MotionOtherEdge     stb       vmvariables+4,x
                    sta       vmvariables+5,x
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
MotionTerrainPixel  ldb       motiony+1,x
                    lda       #160
                    mul
                    addd      motionx,x
                    addb      motioncolumn,x
                    adca      #0
                    lbsr      PicturePointer
                    tst       <decodeerror
                    bne       MotionTerrainError
                    lda       ,u
                    lsra
                    lsra
                    lsra
                    lsra
                    ldu       motionobject,x
                    tsta
                    beq       MotionTerrainBlocked
                    cmpa      #1
                    bne       MotionTerrainTrigger
                    ldb       $26,u
                    bitb      #2
                    beq       MotionTerrainBlocked
MotionTerrainTrigger cmpa     #2
                    bne       MotionTerrainWater
                    inc       motiontrigger,x
MotionTerrainWater  cmpa      #3
                    beq       MotionTerrainAdvance
                    clr       motionwater,x
MotionTerrainAdvance inc      motioncolumn,x
                    ldb       motioncolumn,x
                    cmpb      $1C,u
                    blo       MotionTerrainPixel
                    lbsr      PictureUnmap
                    lbcs      MotionReturn
                    ldx       <resourcebase
                    ldu       motionobject,x
                    lda       $25,u
                    bita      #1
                    beq       MotionTerrainLand
                    tst       motionwater,x
                    beq       MotionTerrainBlocked
MotionTerrainLand   bita      #8
                    beq       MotionTerrainAccept
                    tst       motionwater,x
                    bne       MotionTerrainBlocked
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
MotionObjectCollision COLLISION_IGNORE u,a,MotionNoCollision
                    clr       motioncollision,x
                    leay      vmobjects,x
MotionCollisionNext COLLISION_CANDIDATE y,a,MotionCollisionAdvance
                    clra
                    ldb       3,u
                    addb      $1C,u
                    adca      #0
                    pshs      d
                    ldb       3,y
                    cmpd      ,s++
                    bhs       MotionCollisionAdvance
                    clra
                    ldb       3,y
                    addb      $1C,y
                    adca      #0
                    pshs      d
                    ldb       3,u
                    clra
                    cmpd      ,s++
                    bhs       MotionCollisionAdvance
                    lda       4,u
                    cmpa      4,y
                    beq       MotionCollided
                    lda       motionoldposition+1,x
                    cmpa      4,y
                    blo       MotionCrossDown
                    lda       4,u
                    cmpa      4,y
                    blo       MotionCollided
                    bra       MotionCollisionAdvance
MotionCrossDown     lda       4,u
                    cmpa      4,y
                    bhi       MotionCollided
MotionCollisionAdvance leay  43,y
                    inc       motioncollision,x
                    lda       motioncollision,x
                    cmpa      #64
                    blo       MotionCollisionNext
MotionNoCollision   clrb
                    rts
MotionCollided      ldb       #1
                    rts

MotionMoveDirection clrb
                    lda       4,u
                    cmpa      $28,u
                    beq       MotionMoveHorizontal
                    blo       MotionMoveDown
                    ldb       #1
                    bra       MotionMoveHorizontal
MotionMoveDown      ldb       #5
MotionMoveHorizontal lda      3,u
                    cmpa      $27,u
                    beq       MotionMoveDirectionStore
                    blo       MotionMoveRight
                    tstb
                    bne       MotionMoveLeftDiagonal
                    ldb       #7
                    bra       MotionMoveDirectionStore
MotionMoveLeftDiagonal decb
                    bne       MotionMoveDirectionStore
                    ldb       #8
                    bra       MotionMoveDirectionStore
MotionMoveRight     tstb
                    bne       MotionMoveRightDiagonal
                    ldb       #3
                    bra       MotionMoveDirectionStore
MotionMoveRightDiagonal incb
                    cmpb      #6
                    bne       MotionMoveDirectionStore
                    ldb       #4
MotionMoveDirectionStore stb  $21,u
                    rts
MotionArrived       lda       $29,u
                    sta       $1E,u
                    clr       $21,u
                    clr       $22,u
                    ldb       $2A,u
                    leay      vmflags,x
                    clra
                    leay      d,y
                    lda       #1
                    sta       ,y
                    tst       motionid,x
                    bne       MotionArrivedDone
                    clr       vmvariables+6,x
                    sta       <vmplayercontrol
MotionArrivedDone   rts

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
