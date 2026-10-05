* CoCo frame: object pointer, run length, direction, remaining steps.
SPIRAL_DIRECTION   equ 3
SPIRAL_LENGTH      equ 2
SPIRAL_REMAINING   equ 4
SPIRAL_CHECK_LENGTH equ 0
SPIRAL_CANDIDATE   equ FindObjPosIter
SPIRAL_RESUME      macro
                    bra       FindObjPosIter
                    endm
SPIRAL_REPEAT      macro
                    bne       FindObjPosIter
                    endm
