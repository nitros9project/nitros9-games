* CoCo ego is the first record; direction is variable six.
BLOCK_STATE_EGO     macro
                    cmpu      <$0030
                    bne       \1
                    endm
BLOCK_STATE_EGO_STOP macro
                    clr       >$0437
                    endm
UNANIMATE_LIMIT     macro
                    cmpu      <$0032
                    bcc       \1
                    endm
UNANIMATE_NEXT      macro
                    bra       \1
                    endm
