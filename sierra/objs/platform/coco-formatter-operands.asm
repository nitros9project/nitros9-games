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
FORMAT_DIRECTIVE_EXTENDED equ 1
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
