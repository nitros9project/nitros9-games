* CoCo permits zero width and retains A as the Boolean result accumulator.
BOUNDS_REJECT_ZERO_WIDTH equ 0
BOUNDS_HORIZON_COMPARE macro
                    cmpb      >$01D6
                    endm
BOUNDS_HORIZON_FLAGS macro
                    ldb       <$26,\1
                    bitb      #8
                    endm
