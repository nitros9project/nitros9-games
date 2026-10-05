* CoCo packed completion flags and ego input-control bindings.
MOTION_CLEAR_FLAG   macro
                    lbsr      ClearFlag
                    endm
MOTION_RESET_WANDER macro
                    endm
MOTION_DISABLE_EGO  macro
                    cmpu      <$0030
                    bne       \1
                    clr       >$0250
                    endm
MOTION_FETCH_STEP  macro
                    ifne      \1
                    ldb       ,y+
                    ldx       #$0431
                    abx
                    lda       ,x
                    else
                    lda       ,y+
                    endc
                    endm
MOTION_FETCH_MOVE_FLAG macro
                    lda       ,y+
                    endm
MOTION_START_MOVE    macro
                    lbsr      SetObjMotion
                    endm
