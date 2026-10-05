* Object U/control state: clear crossing bit, or stop after a crossing.
* The owner binds ego identity and its direction variable; no mapping occurs.
OBJECT_BLOCK_CLEAR  macro
                    lda       <$26,\1
                    anda      #$7F
                    sta       <$26,\1
                    endm
OBJECT_BLOCK_STOP   macro
                    lda       <$26,\1
                    ora       #$80
                    sta       <$26,\1
                    clr       <$21,\1
                    BLOCK_STATE_EGO \2
                    BLOCK_STATE_EGO_STOP
                    endm
