* Native private completion flags, wander reset and ego input control.
* U=private base; X=record; preserve X while clearing the literal flag in A.
MOTION_CLEAR_FLAG   macro
                    leay      vmflags,u
                    tfr       a,b
                    clra
                    clr       d,y
                    endm
MOTION_RESET_WANDER macro
                    clr       $27,\1
                    endm
MOTION_DISABLE_EGO  macro
                    tst       2,x
                    bne       \1
                    clr       <vmplayercontrol
                    endm
* One native handler selects literal/variable step from the staged opcode.
MOTION_FETCH_STEP   macro
                    ldb       <vmopcode
                    cmpb      #82
                    beq       GameMoveVariableStep
                    lda       vmarguments+3,u
                    bra       GameMoveStepRead
GameMoveVariableStep leay     vmvariables,u
                    clra
                    ldb       vmarguments+3,u
                    lda       d,y
GameMoveStepRead
                    endm
MOTION_FETCH_MOVE_FLAG macro
                    lda       vmarguments+4,u
                    endm
MOTION_START_MOVE    macro
                    stx       motionobject,u
                    lda       2,x
                    sta       motionid,u
                    tfr       x,y
                    tfr       u,x
                    tfr       y,u
                    lbsr      MotionMoveDirection
                    endm
