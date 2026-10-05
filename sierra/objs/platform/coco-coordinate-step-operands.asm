* Candidate coordinates and step are in UpdateAllMotion's private stack frame.
STEP_JOIN_STORES    equ 0
STEP_X_D            macro
                    \1       $03,s
                    endm
STEP_Y_D            macro
                    \1       $05,s
                    endm
STEP_DISTANCE_D     macro
                    \1       $09,s
                    endm
STEP_X_DIRECTION    macro
                    leax      >x_dir_mult,pcr
                    lda       <$21,u
                    lda       a,x
                    endm
STEP_Y_DIRECTION    macro
                    leax      >y_dir_mult,pcr
                    lda       <$21,u
                    lda       a,x
                    endm
