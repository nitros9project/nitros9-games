* Shared character traversal; line tracking is an assembly-time trait.
FormatStrLoop       FORMAT_SCAN_LIMIT
                    FORMAT_SCAN_READ
                    FORMAT_SCAN_END
                    ifne FORMAT_SCAN_LINES
                    cmpa      >FORMAT_SCAN_LITERAL    ; check for literal-next prefix
                    bne       FormatStrCheckEsc ; not literal, check for escape
                    tst       ,x+       ; consume literal-next byte
                    bra       FormatStrStoreChar ; store next char literally
                    endc
FormatStrCheckEsc   cmpa      #$25      ; check for '%' escape prefix
                    FORMAT_SCAN_ESCAPE
                    ifne FORMAT_SCAN_LINES
                    cmpa      #$0A      ; check for newline
                    bne       FormatStrCheckNl
                    lbsr      IncrLineCount ; count this line
                    bra       FormatStrCopyChar ; copy newline to output
FormatStrCheckNl    cmpa      #$20      ; check for space (word break point)
                    bne       FormatStrStoreChar
                    stu       >FORMAT_SCAN_WRAP_POINT    ; save current output pointer as word-wrap point
FormatStrStoreChar  inc       >FORMAT_SCAN_LINE_LENGTH    ; increment char count on line
                    endc
FormatStrCopyChar   FORMAT_SCAN_WRITE
                    bra       FormatStrLoop
