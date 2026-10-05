* A/B=40-byte string slot indices, A=boolean result. Uses 85 bytes of locals.
* NORMAL_STRING_TABLE sets U=slot-table base without changing D.
* NORMAL_STRING_FOLD folds ASCII A while preserving the cursor registers.
* Inputs must contain a NUL within their 40-byte slots; owners validate indices.
* The comparison removes only StrPunctuation, which differs from sentence rules.
MatchWord           leas      <-$53,s   ; allocate 83-byte local frame
                    stb       ,s        ; save word index (1 = word2)
                    leau      $01,s     ; first normalized word buffer
                    bsr       NormWord  ; normalize first input word
                    lda       ,s        ; second word index
                    leau      <$2A,s    ; second normalized word buffer
                    bsr       NormWord  ; normalize second input word
                    leau      $01,s     ; start of first word
                    leax      <$2A,s    ; start of second word
MatchWordLoop       lda       ,u+       ; read char from first word
                    beq       MatchWordFound ; null = end of first word
                    cmpa      ,x+       ; compare with second word char
                    beq       MatchWordLoop ; loop if chars match
                    bra       MatchWordNoMatch ; mismatch
MatchWordFound      lda       #$01      ; match result = true
                    ldb       ,x        ; remaining char in second word
                    beq       MatchWordRet ; both at null = full match
MatchWordNoMatch    clra                ; match result = false
MatchWordRet        leas      <$53,s    ; release local frame
                    rts

NormWord            leas      -$02,s    ; allocate 2-byte local frame
                    stu       ,s        ; save output buffer pointer
                    ldb       #$28      ; 40 chars per slot
                    mul                 ; offset = slot index × 40
                    NORMAL_STRING_TABLE
                    leau      d,u       ; point to input string slot
NormWordLoop        lda       ,u+       ; read char from input
                    beq       NormWordNull ; stop at null terminator
                    leax      >StrPunctuation,pcr ; punctuation character set
                    lbsr      FindByte  ; check if char is punctuation
                    bne       NormWordLoop ; skip punctuation characters
                    lbsr      NORMAL_STRING_FOLD ; convert letter to lowercase
                    ldx       ,s        ; output buffer pointer
                    sta       ,x+       ; store normalized char
                    stx       ,s        ; update output pointer
                    bra       NormWordLoop ; process next char
NormWordNull        ldx       ,s        ; output pointer at end
                    clr       ,x        ; null-terminate normalized word
                    leas      $02,s     ; release local frame
                    rts
