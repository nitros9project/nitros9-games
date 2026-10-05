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
