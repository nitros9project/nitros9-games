* Advance one AGI second on four consecutive byte fields: sec/min/hour/day.
* GAME_CLOCK_ADDRESS supplies X=seconds, preserving D and the owner context.
* Values wrap as bytes; >=60 seconds/minutes and >=24 hours roll to zero.
* The owner supplies the continuation label; tick acquisition stays outside.
AGI_CLOCK_TICK      macro
                    ldd       #$003C
                    GAME_CLOCK_ADDRESS
                    inc       ,x
                    cmpb      ,x
                    bhi       \1
                    sta       ,x+
                    inc       ,x
                    cmpb      ,x
                    bhi       \1
                    sta       ,x+
                    inc       ,x
                    ldb       #$18
                    cmpb      ,x
                    bhi       \1
                    sta       ,x+
                    inc       ,x
                    endm
