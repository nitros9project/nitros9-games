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
