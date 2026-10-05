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
