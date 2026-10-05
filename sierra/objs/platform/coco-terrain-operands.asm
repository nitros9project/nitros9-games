* Packed mapped picture bytes, X=object, U=baseline cursor, B=width countdown.
TERRAIN_WATER_FIRST equ 1
TERRAIN_WATER equ $30
TERRAIN_CONTROL equ $10
TERRAIN_SIGNAL equ $20
TERRAIN_PIXEL_READ macro
                    lda       ,u+
                    anda      #$F0
                    endm
TERRAIN_BLOCK macro
                    \1       ClearFlagControl
                    endm
TERRAIN_CLEAR_WATER macro
                    clr       ScratchA6
                    endm
TERRAIN_IGNORE_CONTROL macro
                    lda       $26,x
                    bita      #2
                    endm
TERRAIN_SET_SIGNAL macro
                    sta       ScratchA5
                    endm
TERRAIN_ADVANCE macro
                    decb
                    bne       TerrainPixelLoop
                    endm
TERRAIN_STATUS_READ macro
                    lda       $25,x
                    endm
TERRAIN_TEST_WATER macro
                    tst       ScratchA6
                    endm
