* Native frame: direction, run length, remaining steps, 16-bit budget.
SPIRAL_DIRECTION   equ 0
SPIRAL_LENGTH      equ 1
SPIRAL_REMAINING   equ 2
SPIRAL_CHECK_LENGTH equ 1
SPIRAL_CANDIDATE   equ RepositionCandidate
SPIRAL_EXHAUSTED   equ RepositionExhausted
SPIRAL_RESUME      macro
                    lbra      RepositionCandidate
                    endm
SPIRAL_REPEAT      macro
                    lbne      RepositionCandidate
                    endm
SPIRAL_LENGTH_ERROR macro
                    lbeq      RepositionExhausted
                    endm
