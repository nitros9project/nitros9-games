* Shared logical clock and transient cycle-state rules. Definitions emit no code.
SHARED_GAME_CYCLE_DEFINED equ 1

* Clear parsed-input and said-accepted state at the next input-cycle boundary.
* Storage representation and store labels are supplied by the owner interface.
AGI_CYCLE_INPUT_RESET macro
                    CYCLE_STATIC_CLEAR 2,CycleInputFlag2Store
                    CYCLE_STATIC_CLEAR 4,CycleInputFlag4Store
CycleInputResetDone equ *
                    endm

* Room-entry and restart flags last for one root-logic cycle. Owners retain
* their existing scheduling boundary: CoCo cycle end, native next-cycle entry.
AGI_CYCLE_ROOM_RESET macro
                    CYCLE_STATIC_CLEAR 5,CycleRoomFlag5Store
                    CYCLE_STATIC_CLEAR 6,CycleRoomFlag6Store
CycleRoomResetDone equ *
                    endm

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


* Publish a room change without losing the old room: v1=old v0, v0=request.
* The owner binds variable addressing and the saved request location. A/B are
* scratch; no resource is acquired and the surrounding transition order stays
* with the owner. U/X/Y/S and every other AGI variable are preserved.
AGI_ROOM_VARIABLES macro
RoomVariablesBegin  ROOM_CURRENT_VARIABLE lda
                    ROOM_PREVIOUS_VARIABLE sta
                    ROOM_REQUEST_READ ldb
                    ROOM_CURRENT_VARIABLE stb
RoomVariablesDone   equ *
                    endm
