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
                    ldb       $1C,u
                    beq       RepositionReject
                    addb      3,u
                    bcs       RepositionReject
                    cmpb      #160
                    bhi       RepositionReject
                    ldb       4,u
                    cmpb      #167
                    bhi       RepositionReject
                    incb
                    cmpb      $1D,u
                    blo       RepositionReject
                    decb
                    cmpb      <vmhorizon
                    bhi       RepositionBounds
                    lda       $26,u
                    bita      #8
                    beq       RepositionReject
RepositionBounds    ldd       3,u
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
                    bcs       RepositionError
                    tstb
                    beq       RepositionFound
RepositionReject    ldu       motionobject,x
                    ldd       3,s
                    subd      #1
                    std       3,s
                    beq       RepositionExhausted
                    lda       ,s
                    beq       RepositionLeft
                    cmpa      #1
                    beq       RepositionDown
                    cmpa      #2
                    beq       RepositionRight
                    dec       4,u
                    bra       RepositionNextStep
RepositionLeft      dec       3,u
                    bra       RepositionNextStep
RepositionDown      inc       4,u
                    bra       RepositionNextStep
RepositionRight     inc       3,u
RepositionNextStep  dec       2,s
                    bne       RepositionCandidate
                    inc       ,s
                    lda       ,s
                    anda      #3
                    sta       ,s
                    bita      #1
                    bne       RepositionSameLength
                    inc       1,s
RepositionSameLength lda      1,s
                    beq       RepositionExhausted
                    sta       2,s
                    lbra      RepositionCandidate
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
