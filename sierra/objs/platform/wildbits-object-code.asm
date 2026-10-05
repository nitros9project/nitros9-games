                    use       platform/object-coordinate-operands.asm
                    use       shared/object-coordinate-state.asm
                    use       shared/object-animation-state.asm
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
                    lbsr      ObjectAddress
                    bcs       ObjectReturn
                    ldb       <vmopcode
                    cmpb      #33
                    beq       ObjectAnimate
                    cmpb      #37
                    beq       ObjectPosition
                    cmpb      #38
                    beq       ObjectPositionVariables
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
ObjectsUnanimateNext lda      $26,x
                    anda      #$BE
                    sta       $26,x
                    leax      43,x
                    leay      -1,y
                    bne       ObjectsUnanimateNext
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
ObjectFixLoop       lbra      CmdFixLoop
ObjectReleaseLoop   lbra      CmdReleaseLoop
ObjectArgumentValue leay      vmvariables,u
                    clra
                    ldb       vmarguments+1,u
                    ldb       d,y
                    rts
ObjectPriority      ldb       vmarguments+1,u
                    bra       ObjectSetPriority
ObjectPriorityVariable lbsr   ObjectArgumentValue
ObjectSetPriority   cmpb      #15
                    lbhi      ObjectBadIndex
                    stb       $24,x
                    lda       $26,x
                    ora       #4
                    sta       $26,x
                    lbra      ObjectDone
ObjectReleasePriority lbra    cmd_release_priority
ObjectGetPriority   lda       $24,x
                    bra       ObjectStoreResult
ObjectDirection     lbsr      ObjectArgumentValue
                    cmpb      #8
                    lbhi      ObjectBadIndex
                    stb       $21,x
                    tst       vmarguments,u
                    lbne      ObjectDone
                    stb       vmvariables+6,u
                    lbra      ObjectDone
ObjectGetDirection  lda       $21,x
ObjectStoreResult   pshs      a
                    leay      vmvariables,u
                    clra
                    ldb       vmarguments+1,u
                    leay      d,y
                    puls      a
                    sta       ,y
                    clrb
                    rts
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
                    use       shared/object-flag-mask.asm
OBJECT_FLAG_RULE    macro
                    ifne      OBJECT_FLAG_TABLE
                    fcb       \2
                    fdb       \1-ObjectFlagTable
                    else
\1                  equ       *
                    OBJECT_FLAG_MASK \3,\4,\5,x
                    clrb
                    rts
                    endc
                    endm
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
                    lbeq      ObjectStopCycle
                    cmpb      #71
                    lbeq      ObjectStartCycle
                    cmpb      #72
                    lbeq      ObjectNormalCycle
                    cmpb      #74
                    lbeq      ObjectReverseCycle
                    cmpb      #73
                    lbeq      ObjectEndCycle
                    cmpb      #75
                    lbeq      ObjectReverseEnd
                    cmpb      #76
                    lbeq      ObjectCycleTime
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
                    use       shared/object-cycle-state.asm
ObjectStopCycle     lbra      CmdStopCycling
ObjectStartCycle    lbra      CmdStartCycling
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
                    use       shared/object-rate-state.asm
ObjectCycleTime     lbsr      ObjectArgumentValue
                    OBJECT_RATE_STATE b,x,$1F,$20
                    lbra      ObjectDone
ObjectStepSize      lbsr      ObjectArgumentValue
                    OBJECT_RATE_STATE b,x,$1E,-1
                    lbra      ObjectDone
ObjectStepTime      lbsr      ObjectArgumentValue
                    OBJECT_RATE_STATE b,x,0,1
                    lbra      ObjectDone
                    use       shared/object-motion-state.asm
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
                    lbra      ObjectDistance
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
                    lbsr      TestPosnX
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
