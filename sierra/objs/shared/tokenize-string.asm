* U=NUL-terminated input. Output must have room for the input plus NUL.
* TOKENIZE_OUTPUT sets X to output start; it must not change A or U.
* TOKENIZE_FOLD optionally folds A, preserving the cursor registers.
* TOKENIZE_FINISH may inspect the output-end pointer at ,S before release.
* Input and output may be the same buffer: output never overtakes input.
TokenizeString      leas      -$02,s    allocate output-pointer slot
                    TOKENIZE_OUTPUT
                    stx       ,s        save output pointer on stack
TokenizeLoop        lda       ,u+       load next input character
                    beq       TokenizeDone done if null terminator
                    TOKENIZE_FOLD
                    leax      >PunctChars1,pcr point to punctuation set 1
                    lbsr      FindByte  check if char is punctuation
                    bne       TokenizeLoop skip if found (discard punct)
                    leax      >PunctChars2,pcr point to punctuation set 2
                    lbsr      FindByte  check second punct set
                    bne       TokenizeLoop skip if found (discard)
                    bra       TokenizeStoreChar non-punct: store it
TokenizeCharLoop    TOKENIZE_FOLD
                    leax      >PunctChars1,pcr point to punct set 1
                    lbsr      FindByte  check if char is punctuation
                    bne       TokenizeAddSpace if punct: insert space first
                    leax      >PunctChars2,pcr point to punct set 2
                    lbsr      FindByte  check second punct set
                    bne       TokenizeNextChar if punct: skip char
TokenizeStoreChar   ldx       ,s        load output pointer
                    sta       ,x+       store character to output
                    stx       ,s        update output pointer
TokenizeNextChar    lda       ,u+       load next input character
                    bne       TokenizeCharLoop loop if not null terminator
                    bra       TokenizeDone null: finish up
TokenizeAddSpace    lda       #$20      space character
                    ldx       ,s        load output pointer
                    sta       ,x+       write space to output
                    stx       ,s        update output pointer
                    bra       TokenizeLoop continue scanning
TokenizeDone        TOKENIZE_OUTPUT
                    cmpx      ,s        compare to end-of-output ptr
                    bcc       TokenizeTerminate skip trim if empty
                    ldx       ,s        load end-of-output pointer
                    lda       -$01,x    look at last character written
                    cmpa      #$20      check if trailing space
                    bne       TokenizeTerminate no trailing space: done
                    leax      -$01,x    back up to overwrite space
                    stx       ,s        update end-of-output pointer
TokenizeTerminate   clr       [,s]      null-terminate the output
                    TOKENIZE_FINISH
                    leas      $02,s     release local frame
                    rts
