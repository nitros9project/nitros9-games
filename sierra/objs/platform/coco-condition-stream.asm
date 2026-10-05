* Streamed condition operands and existing trace-aware CoCo callbacks.
CONDITION_READ_CODE macro
                    lda       ,y+
                    endm
CONDITION_EVALUATE  macro
                    lbsr      EvalExpr
                    endm
CONDITION_SKIP_TEST macro
                    bsr       ExecScriptExecCmd
                    endm
CONDITION_BRANCH    macro
                    \1       \2
                    endm
CONDITION_VALIDATE_END macro
                    endm
CONDITION_VALIDATE_OR macro
                    endm
CONDITION_SCAN_CONTROL macro
                    endm
CONDITION_TRUE_SCAN_BEGIN macro
                    endm
CONDITION_TRUE_BRANCH macro
                    leay      $02,y
                    bra       ExecScriptLoop
                    endm
CONDITION_FALSE_LABEL equ     ExecScriptJump
