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
