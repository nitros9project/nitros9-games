* Geometric placement bounds on a 43-byte record: right edge, baseline,
* height and horizon. Owner binds horizon storage, flags scratch and width
* loading/zero-width policy. Parameters: record register, failure, success.
OBJECT_CHECK_BOUNDS macro
                    ifne      BOUNDS_REJECT_ZERO_WIDTH
                    ldb       <$1C,\1
                    beq       \2
                    addb      $03,\1
                    else
                    ldb       $03,\1
                    addb      <$1C,\1
                    endc
                    bcs       \2
                    cmpb      #160
                    bhi       \2
                    ldb       $04,\1
                    cmpb      #167
                    bhi       \2
                    incb
                    cmpb      <$1D,\1
                    bcs       \2
                    decb
                    BOUNDS_HORIZON_COMPARE
                    bhi       \3
                    BOUNDS_HORIZON_FLAGS \1
                    beq       \2
\3
                    endm
