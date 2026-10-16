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

* Menu input is a request. The event loop consumes it after the script returns.
* Owners supply the permission test and process-private pending-byte store.
AGI_MENU_REQUEST macro
                    MENU_REQUEST_ALLOWED
                    beq       \1
                    lda       #1
                    MENU_REQUEST_STORE
\1                 MENU_REQUEST_RETURN
                    rts
                    endm

* Shared debug configuration and scheduling rules; all storage is owner-bound.
AGI_TRACE_CONFIG macro
                    TRACE_CONFIG_FETCH
                    TRACE_CONFIG_LOGIC
                    TRACE_CONFIG_FETCH
                    TRACE_CONFIG_LINE
                    TRACE_CONFIG_FETCH
                    cmpa      #2
                    bcc       \1
                    lda       #2
\1                  TRACE_CONFIG_ROWS
                    TRACE_SUCCESS
                    rts
                    endm
* Activation is permitted only once; the owner supplies its flag representation.
AGI_TRACE_ACTIVATE macro
                    TRACE_MODE_READ a
\2                  bne       \1
                    TRACE_PERMISSION
                    beq       \1
                    lda       #1
                    TRACE_MODE_STORE
                    endm
* CoCo retains its redundant zero check for exact existing output.
AGI_TRACE_STEP_GATE macro
                    TRACE_MODE_READ \1
                    ifne      \3
                    beq       \2
                    endc
                    TRACE_MODE_COMPARE \1
                    bne       \2
                    endm
AGI_TRACE_LOGIC_ENTRY macro
                    TRACE_MODE_READ a
                    ifne      \2
                    beq       \1
                    endc
                    cmpa      #2
                    bne       \1
                    lda       #1
                    TRACE_MODE_STORE
                    endm
* Every keyboard event advances; '+' skips the rest of this logic invocation.
AGI_TRACE_KEY_ADVANCE macro
                    TRACE_KEY_READ
                    cmpa      #$2B
                    bne       \1
                    lda       #2
                    TRACE_MODE_STORE
                    endm
