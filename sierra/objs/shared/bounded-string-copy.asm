                    ifndef SHARED_BOUNDED_COPY_MACROS
SHARED_BOUNDED_COPY_MACROS equ 1
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

* Emit a reusable counted-word copy. D=words, X=source, Y=destination.
* Returns D=0/C=0, advances X/Y by 2*count and preserves U. Zero is safe.
* X holds the count during the loop because LEAX supplies the loop condition.
COPY_WORD_SPAN      macro
\1                  pshs      u
                    tfr       x,u
                    tfr       d,x
                    leax      ,x
                    beq       \1Done
\1Loop              ldd       ,u++
                    std       ,y++
                    leax      -1,x
                    bne       \1Loop
\1Done              tfr       u,x
                    clra
                    clrb
                    puls      u,pc
                    endm

* set.simple copies a string-table entry into the automatic save name.
* Its operand is a string index, not a physical save-file slot. Owner bindings
* provide operand validation, table/name addresses and the bounded copier.
AGI_SIMPLE_SAVE_NAME macro
                    SIMPLE_SAVE_FETCH
                    ldb       #40
                    mul
                    SIMPLE_SAVE_STRING_TABLE
                    leax      d,x
                    SIMPLE_SAVE_NAME_ADDRESS
                    ldd       #31
                    SIMPLE_SAVE_COPY
                    rts
                    endm
                    endc
