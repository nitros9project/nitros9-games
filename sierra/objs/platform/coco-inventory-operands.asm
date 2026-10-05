* CoCo three-byte object entries; U=item entry, X=variable pointer.
INVENTORY_ITEM      macro
                    ifne      \1
                    bsr       GetObjPtrV
                    else
                    bsr       GetObjPtr
                    endc
                    endm
INVENTORY_VARIABLE_ADDRESS macro
                    ldb       ,y+
                    ldx       #$0431
                    abx
                    endm
INVENTORY_VARIABLE_LOAD macro
                    lda       ,x
                    endm
INVENTORY_VARIABLE_STORE macro
                    sta       ,x
                    endm
INVENTORY_READ_ROOM macro
                    lda       $02,u
                    endm
INVENTORY_WRITE_ROOM macro
                    sta       $02,u
                    endm
* Predicates preserve the CoCo expression reader's original registers/cursor.
INVENTORY_TEST_ITEM macro
                    ldb       ,y+
                    ldx       <$0038
                    abx
                    abx
                    abx
                    endm
INVENTORY_EXPECTED_ROOM macro
                    ldb       $01,y
                    ldx       #$0431
                    abx
                    lda       ,x
                    endm
INVENTORY_TEST_ROOM_ITEM macro
                    ldb       ,y++
                    ldx       <$0038
                    abx
                    abx
                    abx
                    endm
INVENTORY_COMPARE_ROOM macro
                    cmpa      $02,x
                    endm
INVENTORY_TEST_RESULT macro
                    lbne      RetFalse
                    lbra      RetTrue
                    endm
