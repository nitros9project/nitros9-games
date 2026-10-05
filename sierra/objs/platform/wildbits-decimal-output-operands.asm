* Native values are AGI bytes (D <= 255); caller supplies X=buffer end.
DECIMAL_OUTPUT_END  macro
                    endm
DECIMAL_OUTPUT_DIVIDE macro
                    lbsr      FormatByteDivide10
                    endm
