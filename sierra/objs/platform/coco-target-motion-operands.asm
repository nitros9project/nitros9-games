* CoCo direction threshold is the actual step. Completion uses packed flags.
TARGET_COMPLETE_ZERO equ 1
TARGET_STOP_FIRST equ 0
TARGET_PREPARE macro
                    endm
TARGET_STEP_READ macro
                    ldb       $1E,u
                    endm
TARGET_DIRECTION_CONTEXT macro
                    cmpu      <$0030
                    bne       TargetStoreDirection
                    sta       >$0437
                    endm
TARGET_DIRECTION_STORE macro
                    sta       <$21,u
                    endm
TARGET_STEP_STORE macro
                    sta       <$1E,u
                    endm
TARGET_STOP macro
                    lda       #0
                    sta       <$22,u
                    endm
TARGET_FLAG_SET macro
                    lda       <$2A,u
                    lbsr      SetFlag
                    endm
TARGET_EGO_TEST macro
                    cmpu      <$0030
                    endm
TARGET_EGO_STATE macro
                    lda       #1
                    sta       >$0250
                    clr       >$0437
                    endm
