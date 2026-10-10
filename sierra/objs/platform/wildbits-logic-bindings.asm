* wildbits-logic-bindings feature bindings. Included once; emits no code.
PLATFORM_WILDBITS_LOGIC_BINDINGS equ 1

* ===== wildbits-logic-stream =====
* Bounded offset-based scripts and native command/status interfaces.
LOGIC_CONTEXT       macro
                    clr       <vmerror
                    ldd       #$FFFF
                    std       <vmsteps
                    endm
LOGIC_FETCH_OPCODE  macro
                    ldd       <vmsteps
                    subd      #1
                    std       <vmsteps
                    lbeq      VmLogicInvalid
                    lbsr      VmFetchByte
                    lbcs      VmLogicFailure
                    stb       <vmopcode
                    endm
LOGIC_READ_BRANCH   macro
                    lbsr      VmReadWord
                    lbcs      VmLogicFailure
                    endm
LOGIC_APPLY_BRANCH  macro
                    addd      <vmip
                    cmpd      #2
                    lblo      VmLogicInvalid
                    cmpd      <vmend
                    lbhs      VmLogicInvalid
                    std       <vmip
                    endm
LOGIC_DISPATCH      macro
                    cmpb      #181
                    lbhi      VmLogicInvalid
                    leax      VmArgumentCounts,pcr
* Two operand counts share a byte; carry retains the opcode parity.
                    lsrb
                    ldb       b,x
                    bcs       NativeCountLow
                    lsrb
                    lsrb
                    lsrb
                    lsrb
NativeCountLow    andb      #15
                    stb       <vmargcount
                    lbsr      VmReadArguments
                    lbcs      VmLogicFailure
                    ldb       <vmopcode
                    cmpb      #17
                    lbls      VmArithmetic
                    lbsr      VmPlatformCommand
                    lbcs      VmLogicFailure
                    endm
LOGIC_CONTINUE      macro
                    ifne      GAME_PRESENTATION
                    ldu       <resourcebase
                    tst       gamequit,u
                    lbne      ExecScriptDone
                    endc
                    tst       <vmroompending
                    lbne      ExecScriptDone
                    lbra      VmNext
                    endm
LOGIC_SUCCESS       macro
                    clrb
                    endm
LOGIC_BRANCH        macro
                    l\1       \2
                    endm
LOGIC_SKIP_HELPER   macro
                    endm

* ===== wildbits-random-operands =====
* Process-private variable-table binding for the common random command.
RANDOM_VARIABLE_TABLE macro
                    leax      vmvariables,u
                    endm

* ===== wildbits-condition-stream local macros =====
CONDITION_READ_CODE macro
                    lbsr      VmFetchByte
                    lbcs      VmConditionFailure
                    tfr       b,a
                    endm
CONDITION_EVALUATE  macro
                    lbsr      VmConditionTest
                    lbcs      VmConditionFailure
                    tfr       b,a
                    endm
CONDITION_SKIP_TEST macro
                    lbsr      VmConditionOperands
                    lbcs      VmConditionFailure
                    clr       1,s
                    endm
CONDITION_BRANCH    macro
                    l\1       \2
                    endm
CONDITION_VALIDATE_END macro
                    ldd       ,s
                    lbne      VmConditionInvalid
                    endm
CONDITION_VALIDATE_OR macro
                    tst       1,s
                    lbne      VmConditionInvalid
                    endm
CONDITION_SCAN_CONTROL macro
                    lbsr      VmConditionScanControl
                    lbcs      VmConditionFailure
                    endm
CONDITION_TRUE_SCAN_BEGIN macro
                    inc       ,s
                    endm
CONDITION_TRUE_BRANCH macro
                    lbsr      VmReadWord
                    lbcs      VmConditionFailure
                    lbra      VmNext
                    endm

* ===== wildbits-game-math-code local macros =====
MATH_DIVIDE         macro
                    lbsr      Div8
                    endm

* ===== wildbits-logic-code local macros =====
VARIABLE_TABLE      macro
                    leax      vmvariables,u
                    endm
FLAG_VARIABLE_TABLE macro
                    leax      vmvariables,u
                    endm
TEST_VARIABLE_TABLE macro
                    leax      vmvariables,u
                    endm
AGI_TEST            macro
                    fcb       (\2)/256
                    endm
NATIVE_COMMAND_TABLE_MODE set 0
NATIVE_COUNT_PAIR    set 0
NATIVE_COUNT_HIGH    set 0
NATIVE_ROUTE        macro
                    ifeq NATIVE_COMMAND_TABLE_MODE-3
NativeRoute\1       set -1
NativeRouteEmitted\1 set 0
                    else
                    ifeq NATIVE_COMMAND_TABLE_MODE-1
                    ifeq NativeRoute\1+1
NativeRoute\1       set NATIVE_ROUTE_COUNT
NATIVE_ROUTE_COUNT  set NATIVE_ROUTE_COUNT+1
                    endc
                    fcb NativeRoute\1
                    else
                    ifeq NativeRouteEmitted\1
NativeRouteEmitted\1 set 1
                    fdb \1-VmPlatformRouteTable
                    endc
                    endc
                    endc
                    endm
NATIVE_ROUTE_COUNT  set 0
AGI_COMMAND         macro
                    ifne NATIVE_COMMAND_TABLE_MODE
                    ifne \4
                    ifne GAME_PRESENTATION
                    NATIVE_ROUTE \3
                    else
                    NATIVE_ROUTE VmPlatformUnsupported
                    endc
                    else
                    NATIVE_ROUTE \3
                    endc
                    else
                    ifeq NATIVE_COUNT_PAIR
NATIVE_COUNT_HIGH    set (\2)/256
NATIVE_COUNT_PAIR    set 1
                    else
                    fcb       NATIVE_COUNT_HIGH*16+(\2)/256
NATIVE_COUNT_PAIR    set 0
                    endc
                    endc
                    endm


* Static cycle flags are private bytes; U remains the process-state base.
CYCLE_STATIC_CLEAR macro
\2                  clr       vmflags+\1,u
                    endm


* Native X addresses the variables; the pending room is in private DP state.
ROOM_CURRENT_VARIABLE macro
                    \1       ,x
                    endm
ROOM_PREVIOUS_VARIABLE macro
                    \1       1,x
                    endm
ROOM_REQUEST_READ macro
                    \1       <vmnewroom
                    endm
