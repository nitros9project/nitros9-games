* Owner operand/storage bindings for shared object coordinate commands.
OBJECT_FETCH_POSITION macro
                    ldd       ,y++
                    endm
OBJECT_FETCH_VARIABLE_X macro
                    ldx       #$0431
                    ldb       ,y+
                    abx
                    lda       ,x
                    endm
OBJECT_FETCH_VARIABLE_Y macro
                    ldx       #$0431
                    ldb       ,y+
                    abx
                    ldb       ,x
                    endm
OBJECT_POSITION_RESULT_POINTER macro
                    ldx       #$0431
                    ldb       ,y+
                    abx
                    endm
OBJECT_DELTA_SAVE   macro
                    std       ,s
                    endm
OBJECT_DELTA_ADD    macro
                    addd      ,s
                    endm
