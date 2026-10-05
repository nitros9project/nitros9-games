* CoCo script operands, object pointer in U, and fixed variable storage.
QUERY_OBJECT        macro
                    lda       ,y+
                    ldb       #$2B
                    mul
                    addd      <$0030
                    tfr       d,u
                    endm
QUERY_LOAD          macro
                    lda       \1,u
                    endm
QUERY_VARIABLE_TABLE macro
                    ldx       #$0431
                    endm
QUERY_LAST_VALID    macro
                    endm
QUERY_RETURN        macro
                    rts
                    endm
