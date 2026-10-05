* Shared position/get-position/reposition state on the common 43-byte record.
* Owners supply operand reads, output variable pointers and signed-delta storage.
* Coordinate arithmetic retains byte wrapping above 255 and clamps negative
* signed relative results to zero before platform-specific placement validation.
OBJECT_POSITION     macro
                    ifne      \2
                    OBJECT_FETCH_VARIABLE_X
                    OBJECT_FETCH_VARIABLE_Y
                    else
                    OBJECT_FETCH_POSITION
                    endc
                    std       $03,\1
                    ifne      \3
                    std       <$1A,\1
                    endc
                    endm
OBJECT_GET_POSITION macro
                    OBJECT_POSITION_RESULT_POINTER 1
                    lda       $03,\1
                    sta       ,\2
                    OBJECT_POSITION_RESULT_POINTER 2
                    lda       $04,\1
                    sta       ,\2
                    endm
OBJECT_SIGNED_DELTA macro
                    sex
                    OBJECT_DELTA_SAVE
                    clra
                    ldb       \2,\1
                    OBJECT_DELTA_ADD
                    bpl       \3
                    clrb
\3                  stb       \2,\1
                    endm
