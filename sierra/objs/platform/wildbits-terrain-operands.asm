* Private context X and object U. Picture provider may map one owned block.
TERRAIN_WATER_FIRST equ 0
TERRAIN_WATER equ 3
TERRAIN_CONTROL equ 1
TERRAIN_SIGNAL equ 2
TERRAIN_PIXEL_READ macro
                    ldb       motiony+1,x
                    lda       #160
                    mul
                    addd      motionx,x
                    addb      motioncolumn,x
                    adca      #0
                    lbsr      PicturePointer
                    tst       <decodeerror
                    lbne      MotionTerrainError
                    lda       ,u
                    lsra
                    lsra
                    lsra
                    lsra
                    ldu       motionobject,x
                    tsta
                    endm
TERRAIN_BLOCK macro
                    \1       MotionTerrainBlocked
                    endm
TERRAIN_CLEAR_WATER macro
                    clr       motionwater,x
                    endm
TERRAIN_IGNORE_CONTROL macro
                    ldb       $26,u
                    bitb      #2
                    endm
TERRAIN_SET_SIGNAL macro
                    inc       motiontrigger,x
                    endm
TERRAIN_ADVANCE macro
                    inc       motioncolumn,x
                    ldb       motioncolumn,x
                    cmpb      $1C,u
                    blo       TerrainPixelLoop
                    endm
TERRAIN_STATUS_READ macro
                    lda       $25,u
                    endm
TERRAIN_TEST_WATER macro
                    tst       motionwater,x
                    endm
