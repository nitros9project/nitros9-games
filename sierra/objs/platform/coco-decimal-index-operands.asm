* Preserve CoCo's modulo-256 parsing and original return condition codes.
DECIMAL_INDEX_ADJUST macro
                    subb      #$30
                    endm
DECIMAL_INDEX_VALIDATE macro
                    endm
DECIMAL_INDEX_RETURN macro
                    rts
                    endm
