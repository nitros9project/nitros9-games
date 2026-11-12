* Scan an object's baseline. Pixel access, counter and flags are owner operands.
* Priority 0 blocks, 1 observes the object's ignore-control bit, 2 signals,
* and 3 is water. Legacy preclassification preserves water state on rejection.
TerrainPixelLoop    TERRAIN_PIXEL_READ
                    TERRAIN_BLOCK beq
                    ifne TERRAIN_WATER_FIRST
                    cmpa      #TERRAIN_WATER
                    beq       TerrainPixelAdvance
                    TERRAIN_CLEAR_WATER
                    endc
                    cmpa      #TERRAIN_CONTROL
                    bne       TerrainPixelSignal
                    TERRAIN_IGNORE_CONTROL
                    TERRAIN_BLOCK beq
                    ifeq TERRAIN_WATER_FIRST
                    TERRAIN_CLEAR_WATER
                    endc
                    bra       TerrainPixelAdvance
TerrainPixelSignal  cmpa      #TERRAIN_SIGNAL
                    bne       TerrainPixelWater
                    TERRAIN_SET_SIGNAL
TerrainPixelWater   equ *
                    ifeq TERRAIN_WATER_FIRST
                    cmpa      #TERRAIN_WATER
                    beq       TerrainPixelAdvance
                    TERRAIN_CLEAR_WATER
                    endc
TerrainPixelAdvance TERRAIN_ADVANCE
TerrainScanDone     equ *
