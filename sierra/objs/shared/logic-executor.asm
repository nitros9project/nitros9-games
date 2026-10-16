* Common AGI executor: return, jump, condition and command control flow.
* Branch parameter three is a long-range hint; owners choose encodings.
* Two stack-local condition bytes belong to each invocation, including nested
* logic calls. Owners supply context, reads, dispatch, branches and statuses.
ExecLogicScript     leas      -$02,s    ; allocate 2-byte local frame (if-state)
                    LOGIC_CONTEXT
ExecScriptLoop      LOGIC_FETCH_OPCODE       ; fetch next opcode
ExecScriptCheck     tstb                ; test opcode
                    LOGIC_BRANCH beq,ExecScriptDone,0 ; opcode $00 = end of script
                    cmpb      #$FF
                    LOGIC_BRANCH beq,ExecScriptIf,0 ; opcode $FF = if block
                    cmpb      #$FE
                    LOGIC_BRANCH bne,ExecScriptCmd,0 ; not a jump
ExecScriptJump      LOGIC_READ_BRANCH
                    LOGIC_APPLY_BRANCH
                    LOGIC_BRANCH bra,ExecScriptLoop,0
ExecScriptCmd       LOGIC_DISPATCH
                    LOGIC_CONTINUE
ExecScriptDone      LOGIC_SUCCESS
                    LOGIC_BRANCH bra,ExecLogicScriptRet,1
                    use       shared/condition-flow.asm
                    LOGIC_SKIP_HELPER
ExecLogicScriptRet  leas      $02,s     ; release if-state local frame
                    rts
