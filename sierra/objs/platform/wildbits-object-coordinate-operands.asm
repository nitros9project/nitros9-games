* Owner operand/storage bindings for shared object coordinate commands.
OBJECT_FETCH_POSITION macro
                    ldd       vmarguments+1,u
                    endm
OBJECT_FETCH_VARIABLE_X macro
                    leay      vmvariables,u
                    ldb       vmarguments+1,u
                    clra
                    lda       d,y
                    endm
OBJECT_FETCH_VARIABLE_Y macro
                    pshs      a
                    clra
                    ldb       vmarguments+2,u
                    ldb       d,y
                    puls      a
                    endm
OBJECT_POSITION_RESULT_POINTER macro
                    leay      vmvariables,u
                    clra
                    ldb       vmarguments+\1,u
                    leay      d,y
                    endm
OBJECT_DELTA_SAVE   macro
                    pshs      d
                    endm
OBJECT_DELTA_ADD    macro
                    addd      ,s++
                    endm
