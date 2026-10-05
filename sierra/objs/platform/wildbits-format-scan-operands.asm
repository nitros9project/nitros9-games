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
