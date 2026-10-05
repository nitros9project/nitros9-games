* CoCo reads priority after setting its fixed-priority bit.
PRIORITY_PRELOADED  equ 0
PRIORITY_READ       macro
                    ifne \1
                    ldx       #$0431
                    ldb       ,y+
                    abx
                    lda       ,x
                    else
                    lda       ,y+
                    endc
                    endm
DIRECTION_READ     macro
                    ldb       ,y+
                    ldx       #$0431
                    abx
                    lda       ,x
                    endm
DIRECTION_VALIDATE macro
                    endm
DIRECTION_EGO_TEST macro
                    endm
DIRECTION_EGO_STORE macro
                    endm
