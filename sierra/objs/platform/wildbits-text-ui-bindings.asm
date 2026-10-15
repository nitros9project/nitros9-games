* wildbits-text-ui-bindings feature bindings. Included once; emits no code.
PLATFORM_WILDBITS_TEXT_UI_BINDINGS equ 1

* ===== wildbits-decimal-index-operands =====
* Keep the complete product until overflow is checked; record accepted digits.
DECIMAL_INDEX_ADJUST macro
                    subd      #$30
                    endm
DECIMAL_INDEX_VALIDATE macro
                    adca      #0
                    tsta
                    bne       DecimalIndexOverflow
                    stb       parserwordlength,u
                    inc       parserbestlength,u
                    endm
DECIMAL_INDEX_RETURN macro
                    andcc     #$FE
                    rts
                    endm

* ===== wildbits-decimal-output-operands =====
* Native values are AGI bytes (D <= 255); caller supplies X=buffer end.
DECIMAL_OUTPUT_END  macro
                    endm
DECIMAL_OUTPUT_DIVIDE macro
                    lbsr      FormatByteDivide10
                    endm

* ===== wildbits-dictionary-operands =====
* Streamed vocabulary: X is a file offset; U is an input cursor.
* Decoder validation and file/cache ownership remain in the native provider.
DICTIONARY_LONG_BRANCHES equ 1
DICTIONARY_SHORT_INNER equ 1
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

* ===== wildbits-formatter-operands =====
* wildbits formatter bindings. No code is emitted by this include.

* ===== format-recursion =====
* Native X=owned/copied message; U=private context. Caller saved X on S.
FORMAT_RECURSIVE_ARGUMENTS macro
                    ldu       <resourcebase
                    endm
FORMAT_RECURSIVE_TARGET equ FormatPart
FORMAT_RECURSIVE_RELEASE macro
                    endm
FORMAT_EXPANSION_RESULT macro
                    puls      x
                    endm
FORMAT_EXPANSION_CHECKED equ 1
FORMAT_EXPANSION_ERROR equ FormatPartError
FORMAT_EXPANSION_NEXT equ FormatNext

* ===== format-scan =====
* Native reads consume X; FormatPut owns bounds and output storage.
FORMAT_SCAN_LINES equ 0
FORMAT_SCAN_LIMIT macro
                    endm
FORMAT_SCAN_READ macro
                    lda ,x+
                    endm
FORMAT_SCAN_END macro
                    beq FormatDone
                    endm
FORMAT_SCAN_ESCAPE macro
                    beq FormatDirective
                    endm
FORMAT_SCAN_WRITE macro
                    lbsr FormatPut
                    bcs FormatPartError
                    endm

* ===== format-directive =====
FORMAT_DIRECTIVE_GLOBAL_ENABLED equ 1
FORMAT_DIRECTIVE_OBJECT_ENABLED equ 1
FORMAT_DIRECTIVE_COMPARE macro
                    cmpa #\1
                    endm
FORMAT_DIRECTIVE_WORD macro
                    beq FormatWord
                    endm
FORMAT_DIRECTIVE_STRING macro
                    lbeq FormatString
                    endm
FORMAT_DIRECTIVE_MESSAGE macro
                    lbeq FormatMessage
                    endm
FORMAT_DIRECTIVE_VARIABLE macro
                    lbeq FormatVariable
                    endm

FORMAT_DIRECTIVE_GLOBAL macro
                    lbeq FormatExternal
                    endm

FORMAT_DIRECTIVE_OBJECT macro
                    lbeq FormatExternal
                    endm

* ===== format-string =====
* Native slot validation and process-owned string table; input B=index.
FORMAT_STRING_PREPARE macro
                    cmpb      #12
                    lbhs      FormatPartInvalid
                    endm
FORMAT_STRING_ADDRESS macro
                    leay      vmstrings,u
                    leay      d,y
                    endm
FORMAT_STRING_EXPAND macro
                    endm
FORMAT_STRING_WRITE macro
                    lbsr      FormatPut
                    endm
FORMAT_STRING_DONE macro
                    lbeq      FormatNext
                    endm
FORMAT_STRING_ERROR macro
                    lbcs      FormatPartError
                    endm
FORMAT_NUMBER_DONE macro
                    beq       FormatVariableDone
                    endm
FORMAT_NUMBER_ERROR macro
                    bcs       FormatVariableError
                    endm

* ===== wildbits-inventory-operands =====
* Native private room bytes; U=private base, X=room, Y=operand/variable.
INVENTORY_ITEM      macro
                    ifne      \1
                    lbsr      InventoryVariableItemAddress
                    else
                    lbsr      InventoryItemAddress
                    endc
                    lbcs      InventoryReturn
                    endm
INVENTORY_VARIABLE_ADDRESS macro
                    ldb       ,y+
                    leay      vmvariables,u
                    clra
                    leay      d,y
                    endm
INVENTORY_VARIABLE_LOAD macro
                    lda       ,y
                    endm
INVENTORY_VARIABLE_STORE macro
                    sta       ,y
                    endm
INVENTORY_READ_ROOM macro
                    lda       ,x
                    endm
INVENTORY_WRITE_ROOM macro
                    sta       ,x
                    endm
INVENTORY_TEST_ITEM macro
                    lbsr      InventoryItemAddress
                    lbcs      InventoryReturn
                    endm
INVENTORY_EXPECTED_ROOM macro
                    ldb       1,y
                    leax      vmvariables,u
                    clra
                    lda       d,x
                    endm
INVENTORY_TEST_ROOM_ITEM macro
                    pshs      a
                    ldb       ,y++
                    lbsr      InventoryResolveItem
                    puls      a
                    lbcs      InventoryReturn
                    endm
INVENTORY_COMPARE_ROOM macro
                    cmpa      ,x
                    endm
INVENTORY_TEST_RESULT macro
                    bne       InventoryFalse
                    ldb       #1
                    andcc     #$FE
                    rts
                    endm

* ===== wildbits-format-code local macros =====
NUL_FRAME_WRITE     macro
                    sta       ,y+
                    endm

* ===== wildbits-parser-code local macros =====
TOKENIZE_OUTPUT     macro
                    ldx       <resourcebase
                    leax      parserline,x
                    endm
TOKENIZE_FOLD       macro
                    lbsr      ParserLower
                    endm
TOKENIZE_FINISH     macro
                    ldu       <resourcebase
                    leax      parserline,u
                    pshs      x
                    ldd       2,s
                    subd      ,s++
                    stb       parserlength,u
                    endm

* ===== wildbits-string-code local macros =====
NORMAL_STRING_TABLE macro
                    ldu       <resourcebase
                    leau      vmstrings,u
                    endm
