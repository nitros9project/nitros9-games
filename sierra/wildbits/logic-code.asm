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
VmConditionStart    lda       #1
                    sta       <vmcondition
                    clr       <vmoractive
                    clr       <vmorvalue
                    clr       <vmnegate
VmConditionNext     lbsr      VmFetchByte
                    lbcs      VmReturn
                    cmpb      #$FF
                    lbeq      VmConditionEnd
                    cmpb      #$FD
                    beq       VmNot
                    cmpb      #$FC
                    beq       VmOr
                    cmpb      #1
                    lblo      VmInvalid
                    cmpb      #18
                    lbhi      VmInvalid
                    stb       <vmopcode
                    cmpb      #14
                    beq       VmSaidArguments
                    leax      VmTestCounts,pcr
                    ldb       b,x
                    stb       <vmargcount
                    bra       VmTestArguments
VmSaidArguments     lbsr      VmFetchByte
                    lbcs      VmReturn
                    cmpb      #127
                    lbhi      VmInvalid
                    lslb
                    stb       <vmargcount
VmTestArguments     lbsr      VmReadArguments
                    lbcs      VmReturn
                    lbsr      VmEvaluateTest
                    lbcs      VmReturn
                    eorb      <vmnegate
                    clr       <vmnegate
                    tst       <vmoractive
                    beq       VmAndResult
                    orb       <vmorvalue
                    stb       <vmorvalue
                    lbra      VmConditionNext
VmAndResult         andb      <vmcondition
                    stb       <vmcondition
                    lbra      VmConditionNext
VmNot               lda       <vmnegate
                    eora      #1
                    sta       <vmnegate
                    lbra      VmConditionNext
VmOr                tst       <vmnegate
                    lbne      VmInvalid
                    tst       <vmoractive
                    beq       VmOrOpen
                    ldb       <vmorvalue
                    andb      <vmcondition
                    stb       <vmcondition
                    clr       <vmoractive
                    lbra      VmConditionNext
VmOrOpen            inc       <vmoractive
                    clr       <vmorvalue
                    lbra      VmConditionNext
VmConditionEnd      tst       <vmoractive
                    lbne      VmInvalid
                    tst       <vmnegate
                    lbne      VmInvalid
                    lbsr      VmReadWord
                    lbcs      VmReturn
                    tst       <vmcondition
                    lbne      VmNext
                    addd      <vmip
                    cmpd      #2
                    lblo      VmInvalid
                    cmpd      <vmend
                    lbhs      VmInvalid
                    std       <vmip
                    lbra      VmNext
VmEvaluateTest      ldu       <resourcebase
                    leax      vmarguments,u
                    ldb       ,x
                    stb       <vmtemp
                    lda       1,x
                    sta       <vmright
                    ldb       <vmopcode
                    cmpb      #8
                    bhi       VmExternalTest
                    cmpb      #7
                    bhs       VmFlagTest
                    leax      vmvariables,u
                    clra
                    ldb       <vmtemp
                    lda       d,x
                    sta       <vmleft
                    ldb       <vmopcode
                    bitb      #1
                    bne       VmCompare
                    clra
                    ldb       <vmright
                    lda       d,x
                    sta       <vmright
VmCompare           lda       <vmleft
                    cmpa      <vmright
                    ldb       <vmopcode
* LDB preserves the comparison carry but changes Z; compare again after
* choosing each relation so every branch uses the actual operand flags.
                    cmpb      #2
                    bls       VmEqual
                    cmpb      #4
                    bls       VmLess
                    lda       <vmleft
                    cmpa      <vmright
                    bhi       VmTrue
                    bra       VmFalse
VmEqual             lda       <vmleft
                    cmpa      <vmright
                    beq       VmTrue
                    bra       VmFalse
VmLess              lda       <vmleft
                    cmpa      <vmright
                    blo       VmTrue
                    bra       VmFalse
VmFlagTest          ldb       <vmtemp
                    lda       <vmopcode
                    cmpa      #8
                    bne       VmTestFlagDirect
                    leax      vmvariables,u
                    clra
                    ldb       d,x
VmTestFlagDirect    leax      vmflags,u
                    clra
                    lda       d,x
                    bne       VmTrue
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
VmTestCounts        fcb       0,2,2,2,2,2,2,1,1,1,2,5,1,0,0,2,5,5,5
* Operand counts follow the existing CoCo command table.
AGI_COMMAND         macro
                    fcb       (\2)/256
                    endm
VmArgumentCounts    equ       *
                    use       shared/agi-command-table.asm
