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
