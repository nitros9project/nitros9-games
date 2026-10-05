* Begin animation only once; repeated animate.obj preserves the live record.
* Parameters: record pointer register, owner's already-animated continuation.
OBJECT_ANIMATE_STATE macro
                    lda       <$26,\1
                    bita      #$40
                    bne       \2
                    lda       #$70
                    sta       <$26,\1
                    lda       #$00
                    sta       <$22,\1
                    sta       <$23,\1
                    sta       <$21,\1
                    endm
