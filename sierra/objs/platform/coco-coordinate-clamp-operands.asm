* Legacy frame and byte-horizon semantics, including early vertical exits.
CLAMP_CHECK_DIMENSIONS equ 0
CLAMP_CANDIDATE_FIRST equ 0
CLAMP_VERTICAL_EXIT equ 1
CLAMP_BYTE_HORIZON equ 1
CLAMP_LEFT_READ     macro
                    ldd       #0
                    cmpd      $03,s
                    endm
CLAMP_WIDTH_READ    macro
                    ldb       <$1C,u
                    endm
CLAMP_HEIGHT_READ   macro
                    ldb       <$1D,u
                    endm
CLAMP_NEGATE_HIGH   macro
                    lda       #$FF
                    endm
CLAMP_EDGE_STORE    macro
                    sta       $02,s
                    endm
CLAMP_HORIZON_READ  macro
                    lda       >$01D6
                    endm
CLAMP_HORIZON_COMPARE macro
                    cmpa      $06,s
                    endm
CLAMP_HORIZON_STORE macro
                    sta       $06,s
                    endm
