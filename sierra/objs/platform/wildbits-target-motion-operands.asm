* Native stepping classifies exact signs; target clamp uses the real step.
TARGET_COMPLETE_ZERO equ 0
TARGET_STOP_FIRST equ 1
TARGET_PREPARE macro
                    pshs      x
                    endm
TARGET_STEP_READ macro
                    ldd       #1
                    endm
TARGET_DIRECTION_CONTEXT macro
                    puls      x
                    endm
TARGET_DIRECTION_STORE macro
                    tfr       a,b
                    stb       $21,u
                    endm
TARGET_STEP_STORE macro
                    sta       $1E,u
                    endm
TARGET_STOP macro
                    clr       $21,u
                    clr       $22,u
                    endm
TARGET_FLAG_SET macro
                    ldb       $2A,u
                    leay      vmflags,x
                    clra
                    leay      d,y
                    lda       #1
                    sta       ,y
                    endm
TARGET_EGO_TEST macro
                    tst       motionid,x
                    endm
TARGET_EGO_STATE macro
                    clr       vmvariables+6,x
                    sta       <vmplayercontrol
                    endm
