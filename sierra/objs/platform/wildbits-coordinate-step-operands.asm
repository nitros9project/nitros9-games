* X is the private motion context, U the object; Y is the table scratch cursor.
STEP_JOIN_STORES    equ 1
STEP_X_D            macro
                    \1       motionx,x
                    endm
STEP_Y_D            macro
                    \1       motiony,x
                    endm
STEP_DISTANCE_D     macro
                    \1       motionstep,x
                    endm
STEP_X_DIRECTION    macro
                    leay      MotionXDelta,pcr
                    ldb       $21,u
                    lda       b,y
                    endm
STEP_Y_DIRECTION    macro
                    leay      MotionYDelta,pcr
                    ldb       $21,u
                    lda       b,y
                    endm
