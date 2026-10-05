* Native private room bytes; U=private base, X=room, Y=operand/variable.
INVENTORY_ITEM      macro
                    ifne      \1
                    lbsr      InventoryVariableItemAddress
                    else
                    lbsr      InventoryItemAddress
                    endc
                    lbcs      InventoryReturn
                    endm
INVENTORY_VARIABLE_ADDRESS macro
                    ldb       ,y+
                    leay      vmvariables,u
                    clra
                    leay      d,y
                    endm
INVENTORY_VARIABLE_LOAD macro
                    lda       ,y
                    endm
INVENTORY_VARIABLE_STORE macro
                    sta       ,y
                    endm
INVENTORY_READ_ROOM macro
                    lda       ,x
                    endm
INVENTORY_WRITE_ROOM macro
                    sta       ,x
                    endm
INVENTORY_TEST_ITEM macro
                    lbsr      InventoryItemAddress
                    lbcs      InventoryReturn
                    endm
INVENTORY_EXPECTED_ROOM macro
                    ldb       1,y
                    leax      vmvariables,u
                    clra
                    lda       d,x
                    endm
INVENTORY_TEST_ROOM_ITEM macro
                    pshs      a
                    ldb       ,y++
                    lbsr      InventoryResolveItem
                    puls      a
                    lbcs      InventoryReturn
                    endm
INVENTORY_COMPARE_ROOM macro
                    cmpa      ,x
                    endm
INVENTORY_TEST_RESULT macro
                    bne       InventoryFalse
                    ldb       #1
                    andcc     #$FE
                    rts
                    endm
