* Checked dimensions and word-sized candidates in private context X.
CLAMP_CHECK_DIMENSIONS equ 1
CLAMP_CANDIDATE_FIRST equ 1
CLAMP_VERTICAL_EXIT equ 0
CLAMP_BYTE_HORIZON equ 0
CLAMP_LEFT_READ     macro
                    ldd       motionx,x
                    endm
CLAMP_WIDTH_READ    macro
                    ldb       $1C,u
                    endm
CLAMP_HEIGHT_READ   macro
                    ldb       $1D,u
                    endm
CLAMP_NEGATE_HIGH   macro
                    coma
                    endm
CLAMP_EDGE_STORE    macro
                    sta       motionedge,x
                    endm
CLAMP_HORIZON_READ  macro
                    ldb       <vmhorizon
                    endm
CLAMP_REJECT       macro
                    l\1       MotionInvalid
                    endm
