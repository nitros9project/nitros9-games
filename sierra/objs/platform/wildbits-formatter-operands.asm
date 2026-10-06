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
                    lbeq FormatDone
                    endm
FORMAT_SCAN_ESCAPE macro
                    beq FormatDirective
                    endm
FORMAT_SCAN_WRITE macro
                    lbsr FormatPut
                    lbcs FormatPartError
                    endm

* ===== format-directive =====
FORMAT_DIRECTIVE_EXTENDED equ 0
FORMAT_DIRECTIVE_COMPARE macro
                    cmpa #\1
                    endm
FORMAT_DIRECTIVE_WORD macro
                    lbeq FormatWord
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
