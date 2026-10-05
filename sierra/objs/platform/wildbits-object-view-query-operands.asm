* Validated private record in X, decoded arguments, and native return ABI.
QUERY_OBJECT        macro
                    leay      vmarguments+1,u
                    endm
QUERY_LOAD          macro
                    lda       \1,x
                    endm
QUERY_VARIABLE_TABLE macro
                    leax      vmvariables,u
                    endm
QUERY_LAST_VALID    macro
                    beq       ViewInvalidQuery
                    endm
QUERY_RETURN        macro
                    clrb
                    rts
                    endm
