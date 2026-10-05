* Common AGI executor: return, jump, condition and command control flow.
* Two stack-local condition bytes belong to each invocation, including nested
* logic calls. Owners supply context, reads, dispatch, branches and statuses.
ExecLogicScript     leas      -$02,s    ; allocate 2-byte local frame (if-state)
                    LOGIC_CONTEXT
ExecScriptLoop      LOGIC_FETCH_OPCODE       ; fetch next opcode
ExecScriptCheck     tstb                ; test opcode
                    LOGIC_BRANCH beq,ExecScriptDone ; opcode $00 = end of script
                    cmpb      #$FF
                    LOGIC_BRANCH beq,ExecScriptIf ; opcode $FF = if block
                    cmpb      #$FE
                    LOGIC_BRANCH bne,ExecScriptCmd ; not a jump
ExecScriptJump      LOGIC_READ_BRANCH
                    LOGIC_APPLY_BRANCH
                    LOGIC_BRANCH bra,ExecScriptLoop
ExecScriptCmd       LOGIC_DISPATCH
                    LOGIC_CONTINUE
ExecScriptDone      LOGIC_SUCCESS
                    LOGIC_BRANCH bra,ExecLogicScriptRet
                    use       shared/condition-flow.asm
                    LOGIC_SKIP_HELPER
ExecLogicScriptRet  leas      $02,s     ; release if-state local frame
                    rts
