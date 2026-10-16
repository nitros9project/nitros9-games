* coco-text-ui-bindings feature bindings. Included once; emits no code.
PLATFORM_COCO_TEXT_UI_BINDINGS equ 1

* ===== coco-decimal-index-operands =====
* Preserve CoCo's modulo-256 parsing and original return condition codes.
DECIMAL_INDEX_ADJUST macro
                    subb      #$30
                    endm
DECIMAL_INDEX_VALIDATE macro
                    endm
DECIMAL_INDEX_RETURN macro
                    rts
                    endm

* ===== coco-decimal-output-operands =====
* Original private engine conversion buffer and full 16-bit divide.
DECIMAL_OUTPUT_END  macro
                    leax      >NumConvEnd,pcr
                    endm
DECIMAL_OUTPUT_DIVIDE macro
                    bsr       UIntDivide
                    endm

* ===== coco-dictionary-operands =====
DICTIONARY_LONG_BRANCHES equ 0
DICTIONARY_ALPHA_REQUIRED equ 1
DICTIONARY_RETURN macro
                    endm
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

* ===== coco-formatter-operands =====
* coco formatter bindings. No code is emitted by this include.

* ===== format-recursion =====
* Existing CoCo stack arguments: output pointer, then source pointer.
FORMAT_RECURSIVE_ARGUMENTS macro
                    ldd       $08,s
                    pshs      b,a
                    pshs      u
                    endm
FORMAT_RECURSIVE_TARGET equ FormatStr
FORMAT_RECURSIVE_RELEASE macro
                    leas      $04,s
                    endm
FORMAT_EXPANSION_RESULT macro
                    stu       $08,s
                    endm
FORMAT_EXPANSION_CHECKED equ 0
FORMAT_EXPANSION_NEXT equ FormatStrLoop

* ===== format-scan =====
* CoCo peeks at X; copying consumes the character into U.
FORMAT_SCAN_LITERAL equ $0101
FORMAT_SCAN_WRAP_POINT equ $0155
FORMAT_SCAN_LINE_LENGTH equ $0157
FORMAT_SCAN_LINES equ 1
FORMAT_SCAN_LIMIT macro
                    lda >$0157
                    cmpa >$0158
                    lbcc FormatStrWordWrap
                    endm
FORMAT_SCAN_READ macro
                    lda ,x
                    endm
FORMAT_SCAN_END macro
                    lbeq FormatStrDone
                    endm
FORMAT_SCAN_ESCAPE macro
                    beq FormatStrEscape
                    endm
FORMAT_SCAN_WRITE macro
                    lda ,x+
                    sta ,u+
                    endm

* ===== format-directive =====
FORMAT_DIRECTIVE_GLOBAL_ENABLED equ 1
FORMAT_DIRECTIVE_OBJECT_ENABLED equ 1
FORMAT_DIRECTIVE_COMPARE macro
                    cmpb #\1
                    endm
FORMAT_DIRECTIVE_WORD macro
                    beq FormatStrEscapeW
                    endm
FORMAT_DIRECTIVE_STRING macro
                    beq FormatStrEscapeS
                    endm
FORMAT_DIRECTIVE_MESSAGE macro
                    beq FormatStrEscapeM
                    endm
FORMAT_DIRECTIVE_GLOBAL macro
                    beq FormatStrEscapeG
                    endm
FORMAT_DIRECTIVE_VARIABLE macro
                    lbeq FormatStrEscapeV
                    endm
FORMAT_DIRECTIVE_OBJECT macro
                    bne FormatStrLoop
                    endm

* ===== format-string =====
* Existing CoCo format frame, index parser and fixed string-slot base.
FORMAT_STRING_PREPARE macro
                    stu       $08,s
                    lbsr      ParseDecStr
                    endm
FORMAT_STRING_ADDRESS macro
                    addd      #$0251
                    tfr       d,u
                    endm
FORMAT_STRING_EXPAND macro
                    bra       FormatStrEscapeRec
                    endm

* ===== coco-inventory-operands =====
* CoCo three-byte object entries; U=item entry, X=variable pointer.
INVENTORY_ITEM      macro
                    ifne      \1
                    bsr       GetObjPtrV
                    else
                    bsr       GetObjPtr
                    endc
                    endm
INVENTORY_VARIABLE_ADDRESS macro
                    ldb       ,y+
                    ldx       #$0431
                    abx
                    endm
INVENTORY_VARIABLE_LOAD macro
                    lda       ,x
                    endm
INVENTORY_VARIABLE_STORE macro
                    sta       ,x
                    endm
INVENTORY_READ_ROOM macro
                    lda       $02,u
                    endm
INVENTORY_WRITE_ROOM macro
                    sta       $02,u
                    endm
* Predicates preserve the CoCo expression reader's original registers/cursor.
INVENTORY_TEST_ITEM macro
                    ldb       ,y+
                    ldx       <$0038
                    abx
                    abx
                    abx
                    endm
INVENTORY_EXPECTED_ROOM macro
                    ldb       $01,y
                    ldx       #$0431
                    abx
                    lda       ,x
                    endm
INVENTORY_TEST_ROOM_ITEM macro
                    ldb       ,y++
                    ldx       <$0038
                    abx
                    abx
                    abx
                    endm
INVENTORY_COMPARE_ROOM macro
                    cmpa      $02,x
                    endm
INVENTORY_TEST_RESULT macro
                    lbne      RetFalse
                    lbra      RetTrue
                    endm

* ===== coco-nul-string-write =====
* Direct destination U; STA preserves the source byte's zero flag.
NUL_COCO_WRITE      macro
                    sta       ,u+
                    endm

* ===== coco-string-copy-count =====
* Existing CoCo MemCopyNull 16-bit count in its stack-local frame.
BOUNDED_COCO_COUNT  macro
                    ldd       ,s
                    subd      #$0001
                    std       ,s
                    endm

WORD_HEX_OUTPUT_END macro
                    leax      >NumConvEnd,pcr
                    endm
