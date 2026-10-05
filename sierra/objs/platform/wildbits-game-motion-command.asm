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
                    use       shared/object-move-direction.asm
MoveTableData       fcb       8,1,2,7,0,3,6,5,4
