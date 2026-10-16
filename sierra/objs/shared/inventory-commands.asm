* Inventory locations: $FF means carried, $00 means nowhere; put reads a
* room variable, and get.room.v stores a room in a destination variable.
* Owners provide item resolution/bounds and room/variable storage bindings.
INVENTORY_SET_LOCATION macro
                    INVENTORY_ITEM \1
                    lda       #\2
                    INVENTORY_WRITE_ROOM
                    endm
INVENTORY_PUT_LOCATION macro
                    INVENTORY_ITEM \1
                    INVENTORY_VARIABLE_ADDRESS
                    INVENTORY_VARIABLE_LOAD
                    INVENTORY_WRITE_ROOM
                    endm
INVENTORY_GET_LOCATION macro
                    INVENTORY_ITEM 1
                    INVENTORY_VARIABLE_ADDRESS
                    INVENTORY_READ_ROOM
                    INVENTORY_VARIABLE_STORE
                    endm
* Inventory predicates: has(item) and obj.in.room(item,room-variable).
INVENTORY_HAS_TEST  macro
                    INVENTORY_TEST_ITEM
                    lda       #$FF
                    INVENTORY_COMPARE_ROOM
                    INVENTORY_TEST_RESULT
                    endm
INVENTORY_ROOM_TEST macro
                    INVENTORY_EXPECTED_ROOM
                    INVENTORY_TEST_ROOM_ITEM
                    INVENTORY_COMPARE_ROOM
                    INVENTORY_TEST_RESULT
                    endm
