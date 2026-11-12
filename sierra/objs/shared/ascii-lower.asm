* A=byte; lowercase ASCII A..Z only. Preserve B/X/Y/U; flags unspecified.
LowercaseByte       cmpa      #'A
                    bcs       LowercaseReturn
                    cmpa      #'Z
                    bhi       LowercaseReturn
                    ora       #$20
LowercaseReturn     rts
