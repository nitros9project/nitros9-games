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
                    use platform/object-bounds-operands.asm
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
                    lbeq      RepositionExhausted
                    use platform/object-placement-operands.asm
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
