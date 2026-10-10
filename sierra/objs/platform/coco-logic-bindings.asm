* coco-logic-bindings feature bindings. Included once; emits no code.
PLATFORM_COCO_LOGIC_BINDINGS equ 1

* ===== coco-condition-stream =====
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

* ===== coco-logic-stream =====
* Contiguous CoCo scripts, page setup and trace-aware command dispatch.
LOGIC_CONTEXT       macro
                    ldy       <$0062    ; load current logic pointer
                    ldd       $04,y     ; get logic page from logic slot
                    lbsr      SetLogicPage ; switch to logic's page
                    ldy       $08,y     ; load pointer to logic bytecode
                    endm
LOGIC_FETCH_OPCODE  macro
                    ldb       ,y+
                    endm
LOGIC_READ_BRANCH   macro
                    ldb       ,y+
                    lda       ,y+
                    endm
LOGIC_APPLY_BRANCH  macro
                    leay      d,y
                    endm
LOGIC_DISPATCH      macro
                    lbsr      DispatchCmd
                    endm
LOGIC_CONTINUE      macro
                    leay      ,y
                    bne       ExecScriptCheck
                    endm
LOGIC_SUCCESS       macro
                    endm
LOGIC_BRANCH        macro
                    \1       \2
                    endm
LOGIC_SKIP_HELPER   macro
ExecScriptExecCmd   cmpa      #$0E
                    bne       ExecScriptExecCmdImpl ; not cmd $0E (return)
                    lda       ,y+       ; fetch return target offset
                    lsla                ; multiply by 2
                    leay      a,y       ; apply offset
                    rts

ExecScriptExecCmdImpl lsla                ; multiply cmd by 2
                    lsla                ; multiply by 2 again (*4)
                    adda      #$02      ; add 2 for command dispatch table base
                    leax      >eval_table,pcr ; point to command dispatch table
                    lda       a,x       ; load relative offset for this command
                    leay      a,y       ; advance Y past command arguments
                    rts
                    endm

* ===== coco-random-operands =====
* Fixed CoCo variable-table binding for the common random command.
RANDOM_VARIABLE_TABLE macro
                    ldx       #$0431
                    endm


* Static cycle flags use the same packed, MSB-first AGI flag representation.
* Parameters: literal flag index, label on its storage instruction.
CYCLE_STATIC_CLEAR macro
                    lda       >($01AE+(\1/8))
                    anda      #(255-($80>>(\1&7)))
\2                  sta       >($01AE+(\1/8))
                    endm
