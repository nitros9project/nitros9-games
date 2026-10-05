* X=source; destination register and count-step macro are owner bindings.
* Copy through NUL, or at most the positive character count and then append
* NUL. A count of N therefore requires N+1 destination bytes for truncation.
* Parameters: destination register, loop label, done label, count-step macro.
BOUNDED_STRING_COPY macro
\2                  lda       ,x+
                    sta       ,\1+
                    beq       \3
                    \4
                    bne       \2
                    clr       ,\1
\3
                    endm
BOUNDED_BYTE_COUNT  macro
                    decb
                    endm
