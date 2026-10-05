* Native rejects zero width; A is scratch and horizon belongs to the process.
BOUNDS_REJECT_ZERO_WIDTH equ 1
BOUNDS_HORIZON_COMPARE macro
                    cmpb      <vmhorizon
                    endm
BOUNDS_HORIZON_FLAGS macro
                    lda       <$26,\1
                    bita      #8
                    endm
