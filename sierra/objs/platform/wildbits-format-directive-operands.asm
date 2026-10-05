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
