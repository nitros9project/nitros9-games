* Original private engine conversion buffer and full 16-bit divide.
DECIMAL_OUTPUT_END  macro
                    leax      >NumConvEnd,pcr
                    endm
DECIMAL_OUTPUT_DIVIDE macro
                    bsr       UIntDivide
                    endm
