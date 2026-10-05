* Native record U and private context X; motionid zero identifies ego.
BLOCK_STATE_EGO     macro
                    tst       motionid,x
                    bne       \1
                    endm
BLOCK_STATE_EGO_STOP macro
                    clr       vmvariables+6,x
                    endm
* Native unanimate receives X=first record and positive Y=record count.
UNANIMATE_LIMIT     macro
                    endm
UNANIMATE_NEXT      macro
                    leay      -1,y
                    bne       \1
                    endm
