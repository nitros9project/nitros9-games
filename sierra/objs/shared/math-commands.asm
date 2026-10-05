* Shared AGI commands 165..168; Y addresses two decoded byte operands.
* VARIABLE_TABLE supplies X=variable[0], preserving A/B/Y/U.
* MATH_DIVIDE implements B / A for nonzero A, preserving X/Y/U.
* Owners retain their existing zero-divisor policy outside this interface.
cmd_multn           VARIABLE_TABLE      ; variable table base
                    ldb       ,y+       ; fetch destination variable index
                    abx                 ; point to variable
                    lda       ,x        ; load variable value
                    ldb       ,y+       ; fetch immediate multiplier
                    mul                 ; multiply A × B → D
                    stb       ,x        ; store low byte of result
                    rts

cmd_multv           ldb       $01,y     ; fetch multiplier variable index
                    VARIABLE_TABLE      ; variable table base
                    abx                 ; point to multiplier variable
                    lda       ,x        ; read multiplier
                    ldb       ,y++      ; fetch destination variable index
                    VARIABLE_TABLE      ; variable table base
                    abx                 ; point to destination variable
                    ldb       ,x        ; read destination value
                    mul                 ; multiply A × B → D
                    stb       ,x        ; store low byte of result
                    rts

cmd_divn            VARIABLE_TABLE      ; variable table base
                    ldb       ,y+       ; fetch destination variable index
                    abx                 ; point to variable
                    ldb       ,x        ; load variable value (dividend)
                    lda       ,y+       ; fetch immediate divisor
                    MATH_DIVIDE         ; divide B by nonzero A, quotient in B
                    stb       ,x        ; store quotient
                    rts

cmd_divv            ldb       $01,y     ; fetch divisor variable index
                    VARIABLE_TABLE      ; variable table base
                    abx                 ; point to divisor variable
                    lda       ,x        ; read divisor
                    ldb       ,y++      ; fetch destination variable index
                    VARIABLE_TABLE      ; variable table base
                    abx                 ; point to destination variable
                    ldb       ,x        ; read dividend
                    MATH_DIVIDE         ; divide B by nonzero A, quotient in B
                    stb       ,x        ; store quotient
                    rts
