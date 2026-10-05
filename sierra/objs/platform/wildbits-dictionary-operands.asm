* Streamed vocabulary: X is a file offset; U is an input cursor.
* Decoder validation and file/cache ownership remain in the native provider.
DICTIONARY_LONG_BRANCHES equ 1
DICTIONARY_ALPHA_REQUIRED equ 0
DICTIONARY_FOLD macro
                    endm
DICTIONARY_START macro
                    pshs      u
                    ldu       <resourcebase
                    ldx       dictionaryentry,u
                    puls      u
                    cmpx      #$FFFF
                    lbeq      LookupNotAlpha
                    endm
DICTIONARY_UNKNOWN macro
                    ldu       <resourcebase
                    ldb       parserposition,u
                    leau      parserline,u
                    leau      b,u
                    endm
DICTIONARY_PREFIX macro
                    lbsr      DictionaryPrefix
                    lbcs      DictionaryReadFailure
                    pshs      b
                    cmpa      ,s+
                    endm
DICTIONARY_CHARACTER macro
                    lbsr      DictionaryReadAt
                    lbcs      DictionaryReadFailure
                    endm
DICTIONARY_ID macro
                    lbsr      DictionaryReadID
                    lbcs      DictionaryReadFailure
                    endm
DICTIONARY_ADVANCE macro
                    leax      1,x
                    endm
DICTIONARY_CHARACTER_NEXT macro
                    lbsr      DictionaryReadAt
                    lbcs      DictionaryReadFailure
                    leax      1,x
                    tsta
                    endm
DICTIONARY_SKIP_ID macro
                    leax      2,x
                    endm
DICTIONARY_BOUNDARY macro
                    endm
DICTIONARY_RETURN macro
                    andcc     #$FE
                    endm
