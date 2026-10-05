* Bounded AGI bytecode control/arithmetic layer, adapted from mnln's command
* semantics. No address patching: dispatch uses opcode values and PCR tables.
* ExecuteLogic uses VmFetchByte (B byte, C/error B) and platform command/test
* callbacks. All callbacks preserve U/DP; private controls survive callbacks.
* vmvariables and vmflags contain 256 bytes each; vmarguments holds 255 bytes.
* Platform commands must implement their semantics or return an error, never
* silently skip an unsupported command. This component is not a whole game.
ExecuteLogic        clr       <vmerror
                    ldd       #$FFFF
                    std       <vmsteps
VmNext              ldd       <vmsteps
                    subd      #1
                    std       <vmsteps
                    lbeq      VmInvalid
                    lbsr      VmFetchByte
                    lbcs      VmReturn
                    stb       <vmopcode
                    cmpb      #0
                    lbeq      VmSuccess
                    cmpb      #$FF
                    lbeq      VmConditionStart
                    cmpb      #$FE
                    lbeq      VmJump
                    cmpb      #181
                    lbhi      VmInvalid
                    leax      VmArgumentCounts,pcr
                    clra
                    ldb       d,x
                    stb       <vmargcount
                    lbsr      VmReadArguments
                    lbcs      VmReturn
                    ldb       <vmopcode
                    cmpb      #17
                    bls       VmArithmetic
                    lbsr      VmPlatformCommand
                    lbcs      VmReturn
                    ifne      GAME_PRESENTATION
                    ldu       <resourcebase
                    tst       gamequit,u
                    lbne      VmSuccess
                    endc
                    tst       <vmroompending
                    lbne      VmSuccess
                    lbra      VmNext
VmReadArguments     clr       <vmargindex
VmArgumentLoop      lda       <vmargindex
                    cmpa      <vmargcount
                    bhs       VmArgumentsDone
                    lbsr      VmFetchByte
                    lbcs      VmReturn
                    ldu       <resourcebase
                    leax      vmarguments,u
                    pshs      b
                    ldb       <vmargindex
                    abx
                    puls      b
                    stb       ,x
                    inc       <vmargindex
                    bra       VmArgumentLoop
VmArgumentsDone     clrb
                    rts
* The exact variable-command bodies are also assembled by CoCo mnln.
* Operand acquisition remains in each owner; the arithmetic is shared.
VmArithmetic        ldu       <resourcebase
                    leay      vmarguments,u
                    ldb       <vmopcode
                    decb
                    lslb
                    leax      VmVariableCommands,pcr
                    ldd       b,x
                    leax      d,x
                    jsr       ,x
                    lbra      VmNext
VARIABLE_TABLE      macro
                    leax      vmvariables,u
                    endm
                    use       shared/variable-commands.asm
VmVariableCommands  fdb       cmd_increment-VmVariableCommands
                    fdb       cmd_decrement-VmVariableCommands
                    fdb       cmd_assignn-VmVariableCommands
                    fdb       cmd_assignv-VmVariableCommands
                    fdb       cmd_addn-VmVariableCommands
                    fdb       cmd_addv-VmVariableCommands
                    fdb       cmd_subn-VmVariableCommands
                    fdb       cmd_subv-VmVariableCommands
                    fdb       cmd_lindirectv-VmVariableCommands
                    fdb       cmd_rindirect-VmVariableCommands
                    fdb       cmd_lindirectn-VmVariableCommands
                    fdb       CmdSetImpl-VmVariableCommands
                    fdb       CmdResetImpl-VmVariableCommands
                    fdb       CmdToggleImpl-VmVariableCommands
                    fdb       CmdSetVImpl-VmVariableCommands
                    fdb       CmdResetVImpl-VmVariableCommands
                    fdb       CmdToggleVImpl-VmVariableCommands
FLAG_VARIABLE_TABLE macro
                    leax      vmvariables,u
                    endm
                    use       shared/flag-commands.asm
                    use       platform/wildbits-flag-storage.asm

VmJump              lbsr      VmReadWord
                    lbcs      VmReturn
                    addd      <vmip
                    cmpd      #2
                    lblo      VmInvalid
                    cmpd      <vmend
                    lbhs      VmInvalid
                    std       <vmip
                    lbra      VmNext
VmReadWord          lbsr      VmFetchByte
                    lbcs      VmReturn
                    pshs      b
                    lbsr      VmFetchByte
                    bcs       VmWordError
                    tfr       b,a
                    puls      b
                    andcc     #$FE
                    rts
VmWordError         leas      1,s
                    rts
                    use       platform/wildbits-condition-stream.asm
VmEvaluateTest      ldu       <resourcebase
                    ldb       <vmopcode
                    cmpb      #8
                    lbhi      VmExternalTest
                    leay      vmarguments,u
                    decb
                    lslb
                    leax      VmBuiltinTests,pcr
                    ldd       b,x
                    leax      d,x
                    jmp       ,x
TEST_VARIABLE_TABLE macro
                    leax      vmvariables,u
                    endm
CONDITION_TRUE      equ       VmTrue
CONDITION_FALSE     equ       VmFalse
                    use       shared/condition-tests.asm
VmBuiltinTests      fdb       TestEqualN-VmBuiltinTests
                    fdb       TestEqualV-VmBuiltinTests
                    fdb       TestLessN-VmBuiltinTests
                    fdb       TestLessV-VmBuiltinTests
                    fdb       TestGreaterN-VmBuiltinTests
                    fdb       TestGreaterV-VmBuiltinTests
                    fdb       TestIsSet-VmBuiltinTests
                    fdb       TestIsSetV-VmBuiltinTests
VmFalse             clrb
                    rts
VmTrue              ldb       #1
                    andcc     #$FE
                    rts
VmExternalTest      lbsr      VmPlatformTest
                    rts
VmSuccess           clrb
                    rts
VmInvalid           ldb       #E$BMode
                    stb       <vmerror
                    orcc      #1
VmReturn            rts
AGI_TEST            macro
                    fcb       (\2)/256
                    endm
VmTestCounts        equ       *
                    use       shared/agi-test-table.asm
* Operand counts follow the existing CoCo command table.
AGI_COMMAND         macro
                    fcb       (\2)/256
                    endm
VmArgumentCounts    equ       *
                    use       shared/agi-command-table.asm
