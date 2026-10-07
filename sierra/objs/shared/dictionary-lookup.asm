* Prefix-compressed words.tok lookup. U is the normalized input cursor;
* D returns the word ID ($FFFF unknown), U the owner's next-word cursor.
* Six stack bytes hold result, best boundary, matched-prefix length, and
* comparison character. X is an opaque dictionary cursor, not an assumed
* physical address. Providers bind cursor reads/advances and letter selection.
* Character decoding, prefix traversal, longest phrase selection and word
* boundaries live here. Owners supply case folding and result text policy.
* The mapped provider expands inline to retain the CoCo instruction schedule.
DICT_BRANCH         macro
                    ifne DICTIONARY_LONG_BRANCHES
                    ifne DICTIONARY_SHORT_INNER
                    \1        \2
                    else
                    l\1       \2
                    endc
                    else
                    \1        \2
                    endc
                    endm
* The outer loop spans the complete decoder; native inner branches remain local.
DICT_OUTER_BRANCH   macro
                    ifne DICTIONARY_LONG_BRANCHES
                    l\1       \2
                    else
                    \1        \2
                    endc
                    endm
LookupWord          leas      -$06,s    ; allocate 6-byte local frame
                    ldd       #$FFFF
                    std       ,s        ; init word-ID slot to not-found
                    ldd       #$0000
                    std       $02,s     ; init post-word pointer to null
                    ifne DICTIONARY_ALPHA_REQUIRED
                    lda       ,u        ; load first character of input word
                    DICTIONARY_FOLD
                    cmpa      #$61
                    DICT_BRANCH bcs,LookupNotAlpha ; branch if below 'a'
                    cmpa      #$7A
                    DICT_BRANCH bls,LookupAlphaNext ; branch if 'a'..'z'
LookupNotAlpha      DICTIONARY_UNKNOWN
                    lbra      LookupWordRet
LookupAlphaNext     ldb       $01,u     ; load second input character
                    cmpb      #$20
                    DICT_BRANCH beq,LookupSingleWord ; branch if followed by space (single char word)
                    cmpb      #$00
                    DICT_BRANCH bne,LookupAlphaSearch ; branch if more chars follow
LookupSingleWord    cmpa      #$61
                    DICT_BRANCH beq,LookupSingleFound ; 'a' alone is a known word
                    cmpa      #$69
                    DICT_BRANCH bne,LookupAlphaSearch ; 'i' alone is also a known word
LookupSingleFound   clrb
                    stb       ,s        ; store word-ID low byte (0)
                    stb       $01,s     ; store word-ID high byte (0)
                    leax      $01,u     ; point past first character
                    stx       $02,s     ; save post-word pointer
                    ldb       ,x+       ; fetch delimiter after single char
                    cmpb      #$20
                    DICT_BRANCH bne,LookupAlphaSearch ; if not space, still search trie
                    stx       $02,s     ; update pointer past delimiter
                    endc
LookupAlphaSearch   DICTIONARY_START
                    clr       $04,s     ; clear input character position counter
LookupWordOuter     lda       $04,s     ; load current input char index
                    DICTIONARY_PREFIX
                    DICT_BRANCH bhi,LookupWordNotFound ; past all candidates, no match
                    DICT_BRANCH bne,LookupCharMiss ; wrong position, skip this node
LookupCharMatch     DICTIONARY_CHARACTER
                    anda      #$7F      ; strip high bit (word-end flag)
                    sta       $05,s     ; save masked char
                    lda       ,u        ; load next input character
                    DICTIONARY_FOLD
                    eora      #$7F      ; XOR for inverted comparison
                    cmpa      $05,s     ; compare against trie char
                    DICT_BRANCH bne,LookupCharMiss ; mismatch, skip node
                    leau      $01,u     ; advance input pointer
                    inc       $04,s     ; increment character position
                    DICTIONARY_CHARACTER
                    anda      #$80      ; test word-end flag
                    DICT_BRANCH beq,LookupCharNext ; not end of trie word yet
                    lda       ,u        ; check what follows in input
                    cmpa      #$00
                    DICT_BRANCH beq,LookupWordFound ; end of input = complete match
                    cmpa      #$20
                    DICT_BRANCH bne,LookupSkipWord ; not space/end, partial match only
LookupWordFound     DICTIONARY_ID
                    std       ,s        ; store matched word ID
                    stu       $02,s     ; save pointer at end of word
                    lda       ,u        ; check character after matched word
                    cmpa      #$00
                    DICT_BRANCH beq,LookupWordRet ; end of input, done
                    tfr       u,d       ; copy pointer to D
                    addd      #$0001    ; advance past delimiter
                    std       $02,s     ; update post-word pointer
                    DICT_BRANCH bra,LookupSkipWord ; continue scanning
LookupCharNext      DICTIONARY_ADVANCE
                    DICT_BRANCH bra,LookupCharMatch ; check next character
LookupCharMiss      lda       ,u        ; check remaining input
                    cmpa      #$00
                    DICT_BRANCH beq,LookupWordNotFound ; no more input, no match
LookupSkipWord      DICTIONARY_CHARACTER_NEXT
                    DICT_BRANCH bpl,LookupSkipWord ; high bit clear = continue skipping
                    DICTIONARY_SKIP_ID
                    cmpa      #$00
                    DICT_OUTER_BRANCH bne,LookupWordOuter ; more nodes at same level
LookupWordNotFound  ldu       $02,s     ; restore best partial pointer
                    lbeq      LookupNotAlpha ; if null, strip invalid word
                    lda       ,u        ; check char at partial pointer
                    DICT_BRANCH beq,LookupWordRet ; end of input, return partial
                    DICTIONARY_BOUNDARY
                    ifeq DICTIONARY_ALPHA_REQUIRED
                    lbra      LookupWordRet
LookupNotAlpha      DICTIONARY_UNKNOWN
                    DICT_BRANCH bra,LookupWordRet
                    endc
LookupWordRet       ldd       ,s        ; load word ID result
                    DICTIONARY_RETURN
                    leas      $06,s     ; release local frame
                    rts

