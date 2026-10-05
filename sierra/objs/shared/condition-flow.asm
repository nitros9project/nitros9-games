* Common short-circuit AND/OR/NOT traversal, with two private stack bytes.
* ,S=OR-active, 1,S=negate-next; operand cursors and callbacks belong to owners.
* Skipped predicates consume operands without invoking test callbacks.
* Owners supply reads, evaluation, skips, branch form and completion/error paths.
ExecScriptIf        ldd       #$0000
                    std       ,s        ; clear OR-active and negate-next
ExecScriptIfLoop    CONDITION_READ_CODE       ; fetch condition byte
                    cmpa      #$FC
                    CONDITION_BRANCH bhi,ExecScriptIfHi ; $FD/$FE/$FF are control bytes
                    CONDITION_BRANCH bne,ExecScriptEvalExpr ; non-$FC = condition to evaluate
                    CONDITION_VALIDATE_OR
                    lda       ,s        ; load OR-active state
                    CONDITION_BRANCH bne,ExecScriptSkipBlock ; all arms false: skip remaining AND terms
                    inc       ,s        ; open an OR group
                    CONDITION_BRANCH bra,ExecScriptIfLoop
ExecScriptIfHi      cmpa      #$FF
                    CONDITION_BRANCH bne,ExecScriptIfFD ; not $FF
                    CONDITION_VALIDATE_END
                    CONDITION_TRUE_BRANCH
ExecScriptIfFD      cmpa      #$FD
                    CONDITION_BRANCH bne,ExecScriptEvalExpr ; not $FD
                    lda       $01,s     ; load NOT-accumulator
                    eora      #$01      ; toggle NOT flag
                    sta       $01,s     ; store updated NOT flag
                    CONDITION_BRANCH bra,ExecScriptIfLoop
ExecScriptEvalExpr  CONDITION_EVALUATE  ; evaluate condition expression
                    eora      $01,s     ; XOR with NOT flag
                    clr       $01,s     ; clear NOT flag for next use
                    tsta                ; test result
                    CONDITION_BRANCH bne,ExecScriptTrueBlock ; condition true
                    lda       ,s        ; load OR-active state
                    CONDITION_BRANCH bne,ExecScriptIfLoop ; try another OR arm
ExecScriptSkipBlock clr       ,s        ; clear OR-active state
ExecScriptSkipLoop  CONDITION_READ_CODE       ; scan through skipped block
                    CONDITION_SCAN_CONTROL
                    cmpa      #$FF
                    CONDITION_BRANCH beq,CONDITION_FALSE_LABEL ; $FF = end of if block (with jump)
                    cmpa      #$FC
                    CONDITION_BRANCH bcc,ExecScriptSkipLoop ; $FC/$FD/$FE = control bytes, skip
                    CONDITION_SKIP_TEST ; consume skipped predicate operands
                    CONDITION_BRANCH bra,ExecScriptSkipLoop
ExecScriptTrueBlock lda       ,s        ; load OR-active state
                    CONDITION_BRANCH beq,ExecScriptIfLoop ; true AND term: continue evaluating
                    clr       ,s        ; clear OR-active state
                    CONDITION_TRUE_SCAN_BEGIN
ExecScriptTrueLoop  CONDITION_READ_CODE       ; fetch next byte in true block
                    CONDITION_SCAN_CONTROL
                    cmpa      #$FC
                    CONDITION_BRANCH bhi,ExecScriptTrueLoop ; $FD/$FE/$FF = skip
                    CONDITION_BRANCH beq,ExecScriptIfLoop ; $FC = end of if block
                    CONDITION_SKIP_TEST ; consume skipped predicate operands
                    CONDITION_BRANCH bra,ExecScriptTrueLoop
