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
                    lda       $1E,x
                    sta       $29,x
                    ldb       vmarguments+3,u
                    lda       <vmopcode
                    cmpa      #82
                    bne       GameMoveStep
                    leay      vmvariables,u
                    clra
                    ldb       d,y
GameMoveStep        tstb
                    beq       GameMoveFlag
                    stb       $1E,x
GameMoveFlag        ldb       vmarguments+4,u
                    stb       $2A,x
                    leay      vmflags,u
                    clra
                    leay      d,y
                    clr       ,y
                    lda       #3
                    sta       $22,x
                    lda       $26,x
                    ora       #$10
                    sta       $26,x
                    tst       2,x
                    bne       GameMoveSetup
                    clr       <vmplayercontrol
GameMoveSetup       stx       motionobject,u
                    lda       2,x
                    sta       motionid,u
                    tfr       x,y
                    tfr       u,x
                    tfr       y,u
                    lbsr      MotionMoveDirection
                    clrb
                    rts

GameFollowCommand   lbsr      ObjectAddress
                    lbcs      ObjectReturn
                    lda       #2
                    sta       $22,x
                    lda       $1E,x
                    cmpa      vmarguments+1,u
                    bhs       GameFollowDistance
                    lda       vmarguments+1,u
GameFollowDistance  sta       $27,x
                    ldb       vmarguments+2,u
                    stb       $28,x
                    leay      vmflags,u
                    clra
                    clr       d,y
                    lda       #$FF
                    sta       $29,x
                    lda       $26,x
                    ora       #$10
                    sta       $26,x
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
                    use       shared/object-move-direction.asm
MoveTableData       fcb       8,1,2,7,0,3,6,5,4
