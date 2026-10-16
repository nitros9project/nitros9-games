* Shared AGI commands 1..11. Y addresses already-decoded byte operands.
* VARIABLE_TABLE supplies X=variable[0], preserving A/B/Y/U. Byte indices
* inherently cover exactly 256 variables. No stream/mapping pointers retained.
cmd_increment       ldb       ,y+       ; fetch variable index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to variable
                    lda       ,x        ; load current value
                    inca                ; increment
                    beq       IncrSkip  ; skip store if wrapped to 0 (255)
                    sta       ,x        ; store incremented value
IncrSkip            rts

cmd_decrement       ldb       ,y+       ; fetch variable index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to variable
                    lda       ,x        ; load current value
                    beq       DecrSkip  ; skip if already 0
                    deca                ; decrement
                    sta       ,x        ; store decremented value
DecrSkip            rts

cmd_assignn         ldb       ,y+       ; fetch destination variable index
                    VARIABLE_TABLE    ; variable table base
                    lda       ,y+       ; fetch immediate value
                    abx                 ; point to destination variable
                    sta       ,x        ; store value into variable
                    rts

cmd_assignv         ldb       $01,y     ; fetch source variable index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to source variable
                    lda       ,x        ; read source value
                    ldb       ,y++      ; fetch destination variable index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to destination variable
                    sta       ,x        ; store source value into destination
                    rts

cmd_addn            ldb       ,y+       ; fetch destination variable index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to variable
                    lda       ,x        ; load current value
                    adda      ,y+       ; add immediate value
                    sta       ,x        ; store result
                    rts

cmd_addv            ldb       $01,y     ; fetch source variable index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to source variable
                    lda       ,x        ; read source value
                    ldb       ,y++      ; fetch destination variable index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to destination variable
                    adda      ,x        ; add source to destination
                    sta       ,x        ; store result
                    rts

cmd_subn            ldb       ,y+       ; fetch destination variable index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to variable
                    lda       ,x        ; load current value
                    suba      ,y+       ; subtract immediate
                    sta       ,x        ; store result
                    rts

cmd_subv            ldb       $01,y     ; fetch source variable index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to source variable
                    lda       ,x        ; read source value
                    nega                ; negate source
                    ldb       ,y++      ; fetch destination variable index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to destination variable
                    adda      ,x        ; add negated source to destination
                    sta       ,x        ; store result (destination - source)
                    rts

cmd_lindirectv      ldb       $01,y     ; fetch value variable index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to value variable
                    lda       ,x        ; read value
                    ldb       ,y++      ; fetch index variable index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to index variable
                    ldb       ,x        ; dereference index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to indexed variable
                    sta       ,x        ; store value via indirect
                    rts

cmd_lindirectn      lda       $01,y     ; fetch immediate value
                    ldb       ,y++      ; fetch index variable index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to index variable
                    ldb       ,x        ; dereference index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to indexed variable
                    sta       ,x        ; store immediate via indirect
                    rts

cmd_rindirect       ldb       $01,y     ; fetch index variable index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to index variable
                    ldb       ,x        ; dereference index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to indexed variable
                    lda       ,x        ; read value via indirect
                    ldb       ,y++      ; fetch destination variable index
                    VARIABLE_TABLE    ; variable table base
                    abx                 ; point to destination variable
                    sta       ,x        ; store value into destination
                    rts

