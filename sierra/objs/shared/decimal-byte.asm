* X=NUL-terminated decimal text; A=unsigned modulo-256 value.
* Skip leading ASCII spaces, stop at the first non-digit, preserve U/Y.
* Two stack-local bytes hold the accumulator and digit; no private state.
AtoI                leas      -$02,s    allocate 2-byte accumulator on stack
                    clra                clear A for accumulator init
                    sta       ,s        clear accumulated result
                    sta       $01,s     clear digit temp
AtoISkipSpace       ldb       ,x+       load byte from input, advance X
                    cmpb      #$20      check for space character
                    beq       AtoISkipSpace loop to skip leading spaces
AtoIDigitLoop       cmpb      #$30      compare to '0'
                    bcs       AtoIDone  branch if below '0' (not a digit)
                    cmpb      #$39      compare to '9'
                    bhi       AtoIDone  branch if above '9' (not a digit)
                    subb      #$30      convert ASCII digit to binary
                    stb       $01,s     save digit value
                    lda       #$0A      multiply accumulated result by 10
                    ldb       ,s        load current accumulator
                    mul                 compute accumulator * 10
                    addb      $01,s     add new digit to product
                    stb       ,s        save updated accumulator
                    ldb       ,x+       load next input byte, advance X
                    bne       AtoIDigitLoop loop if not null terminator
AtoIDone            lda       ,s        load final converted integer
                    leas      $02,s     release 2-byte accumulator
                    rts
