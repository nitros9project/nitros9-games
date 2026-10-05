* Native priority is preloaded in B; reject before mutating the record.
PRIORITY_PRELOADED equ 1
PRIORITY_VALIDATE macro
                    cmpb      #15
                    lbhi      ObjectBadIndex
                    endm
DIRECTION_READ     macro
                    lbsr      ObjectArgumentValue
                    endm
DIRECTION_VALIDATE macro
                    cmpb      #8
                    lbhi      ObjectBadIndex
                    endm
DIRECTION_EGO_TEST macro
                    tst       vmarguments,u
                    lbne      \1
                    endm
DIRECTION_EGO_STORE macro
                    stb       vmvariables+6,u
                    endm
