* The whole baseline must be water for water-only objects; land-only objects
* reject all-water baselines. Object status bits are common AGI flags.
TerrainCheckConstraints TERRAIN_STATUS_READ
                    bita      #1
                    beq       TerrainCheckLand
                    TERRAIN_TEST_WATER
                    TERRAIN_BLOCK beq
TerrainCheckLand    bita      #8
                    beq       TerrainConstraintsDone
                    TERRAIN_TEST_WATER
                    TERRAIN_BLOCK bne
TerrainConstraintsDone equ *
