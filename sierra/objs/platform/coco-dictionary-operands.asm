* Mapped original vocabulary: X is a resident words.tok cursor.
DICTIONARY_FOLD     macro
                    lbsr      ToLower
                    endm
DICTIONARY_UNKNOWN  macro
                    lbsr      StripLastWord
                    endm
DICTIONARY_START    macro
                    suba      #$61
                    lsla
                    ldx       >$01A8
                    ldd       a,x
                    beq       LookupNotAlpha
                    leax      d,x
                    endm
DICTIONARY_PREFIX   macro
                    cmpa      ,x+
                    endm
DICTIONARY_CHARACTER macro
                    lda       ,x
                    endm
DICTIONARY_ID       macro
                    ldd       $01,x
                    endm
DICTIONARY_ADVANCE  macro
                    leax      $01,x
                    endm
DICTIONARY_CHARACTER_NEXT macro
                    lda       ,x+
                    endm
DICTIONARY_SKIP_ID  macro
                    leax      $02,x
                    endm
DICTIONARY_BOUNDARY macro
                    clr       -$01,u
                    endm
