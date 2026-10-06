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
                    clra
                    ldb       d,x
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
AGI_COMMAND         macro
                    fcb       (\2)/256
                    endm
