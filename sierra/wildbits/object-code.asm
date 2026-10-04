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
ObjectAnimate       lda       $26,x
                    bita      #$40
                    bne       ObjectDone
                    lda       #$70
                    sta       $26,x
                    clr       $22,x
                    clr       $23,x
                    clr       $21,x
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
ObjectPosition      ldd       vmarguments+1,u
                    std       3,x
                    std       $1A,x
                    clrb
                    rts
ObjectPositionVariables leay  vmvariables,u
                    ldb       vmarguments+1,u
                    clra
                    lda       d,y
                    pshs      a
                    clra
                    ldb       vmarguments+2,u
                    ldb       d,y
                    puls      a
                    std       3,x
                    std       $1A,x
                    clrb
                    rts
ObjectGetPosition   leay      vmvariables,u
                    clra
                    ldb       vmarguments+1,u
                    leay      d,y
                    lda       3,x
                    sta       ,y
                    leay      vmvariables,u
                    clra
                    ldb       vmarguments+2,u
                    leay      d,y
                    lda       4,x
                    sta       ,y
                    clrb
                    rts
ObjectFixLoop       lda       $25,x
                    ora       #$20
                    sta       $25,x
                    bra       ObjectDone
ObjectReleaseLoop   lda       $25,x
                    anda      #$DF
                    sta       $25,x
                    bra       ObjectDone
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
ObjectReleasePriority lda     $26,x
                    anda      #$FB
                    sta       $26,x
                    lbra      ObjectDone
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
                    leay      4,y
                    bra       ObjectFlagFind
ObjectFlagFound     lbsr      ObjectAddress
                    lbcs      ObjectReturn
                    ldb       1,y
                    abx
                    lda       ,x
                    anda      2,y
                    ora       3,y
                    sta       ,x
                    clrb
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
ObjectFlagTable     fcb       61,$26,$FF,$08
                    fcb       62,$26,$F7,$00
                    fcb       64,$25,$FF,$01
                    fcb       65,$25,$FF,$08
                    fcb       66,$25,$F6,$00
                    fcb       67,$25,$FF,$02
                    fcb       68,$25,$FD,$00
                    fcb       88,$26,$FF,$02
                    fcb       89,$26,$FD,$00
                    fcb       0
* Cycle and step parameters; actual per-frame advancement is a separate body.
ObjectCycleCommand  lbsr      ObjectAddress
                    lbcs      ObjectReturn
                    ldb       <vmopcode
                    cmpb      #70
                    beq       ObjectStopCycle
                    cmpb      #71
                    beq       ObjectStartCycle
                    cmpb      #72
                    beq       ObjectNormalCycle
                    cmpb      #74
                    beq       ObjectReverseCycle
                    cmpb      #73
                    beq       ObjectEndCycle
                    cmpb      #75
                    beq       ObjectReverseEnd
                    cmpb      #76
                    beq       ObjectCycleTime
                    cmpb      #79
                    beq       ObjectStepSize
                    cmpb      #80
                    beq       ObjectStepTime
                    cmpb      #85
                    beq       ObjectNormalMotion
                    cmpb      #77
                    lbeq      ObjectStopMotion
                    cmpb      #78
                    lbeq      ObjectStartMotion
                    ldb       #E$UnkSvc
                    orcc      #1
                    rts
ObjectStopCycle     lda       $26,x
                    anda      #$DF
                    sta       $26,x
                    lbra      ObjectDone
ObjectNormalCycle   clr       $23,x
ObjectStartCycle    lda       $26,x
                    ora       #$20
                    sta       $26,x
                    lbra      ObjectDone
ObjectReverseCycle  lda       #3
                    sta       $23,x
                    bra       ObjectStartCycle
ObjectEndCycle      lda       #1
                    bra       ObjectEndCycleMode
ObjectReverseEnd    lda       #2
ObjectEndCycleMode  sta       $23,x
                    lda       $25,x
                    ora       #$10
                    sta       $25,x
                    lda       $26,x
                    ora       #$30
                    sta       $26,x
                    ldb       vmarguments+1,u
                    stb       $27,x
                    leay      vmflags,u
                    clra
                    leay      d,y
                    clr       ,y
                    lbra      ObjectDone
ObjectCycleTime     lbsr      ObjectArgumentValue
                    stb       $1F,x
                    stb       $20,x
                    lbra      ObjectDone
ObjectStepSize      lbsr      ObjectArgumentValue
                    stb       $1E,x
                    lbra      ObjectDone
ObjectStepTime      lbsr      ObjectArgumentValue
                    stb       ,x
                    stb       1,x
                    lbra      ObjectDone
ObjectNormalMotion  clr       $22,x
                    lbra      ObjectDone
ObjectStopMotion    clr       $22,x
                    clr       $21,x
                    tst       vmarguments,u
                    lbne      ObjectDone
                    clr       vmvariables+6,u
                    clr       <vmplayercontrol
                    lbra      ObjectDone
ObjectStartMotion   clr       $22,x
                    tst       vmarguments,u
                    lbne      ObjectDone
                    clr       vmvariables+6,u
                    lda       #1
                    sta       <vmplayercontrol
                    lbra      ObjectDone
