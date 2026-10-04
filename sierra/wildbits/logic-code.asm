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
VmArithmetic        ldu       <resourcebase
                    leax      vmarguments,u
                    ldb       ,x
                    stb       <vmtemp
                    lda       1,x
                    sta       <vmright
                    leax      vmvariables,u
                    abx
                    lda       ,x
                    sta       <vmleft
                    ldb       <vmopcode
                    cmpb      #1
                    bne       VmNotIncrement
                    cmpa      #255
                    beq       VmArithmeticDone
                    inca
                    bra       VmStoreVariable
VmNotIncrement      cmpb      #2
                    bne       VmNotDecrement
                    tsta
                    beq       VmArithmeticDone
                    deca
                    bra       VmStoreVariable
VmNotDecrement      cmpb      #12
                    lbhs      VmFlagCommand
                    cmpb      #4
                    beq       VmResolveRight
                    cmpb      #6
                    beq       VmResolveRight
                    cmpb      #8
                    beq       VmResolveRight
                    cmpb      #9
                    bne       VmResolved
VmResolveRight      ldu       <resourcebase
                    leay      vmvariables,u
                    clra
                    ldb       <vmright
                    lda       d,y
                    sta       <vmright
VmResolved          ldb       <vmopcode
                    cmpb      #3
                    beq       VmAssign
                    cmpb      #4
                    beq       VmAssign
                    cmpb      #5
                    beq       VmAdd
                    cmpb      #6
                    beq       VmAdd
                    cmpb      #7
                    beq       VmSubtract
                    cmpb      #8
                    beq       VmSubtract
                    cmpb      #10
                    beq       VmRightIndirect
* lindirectn/v: destination is variable[variable[arg0]].
                    ldu       <resourcebase
                    leax      vmvariables,u
                    ldb       <vmleft
                    abx
                    bra       VmAssign
VmRightIndirect     ldu       <resourcebase
                    leay      vmvariables,u
                    clra
                    ldb       <vmright
                    ldb       d,y
                    clra
                    lda       d,y
                    bra       VmStoreVariable
VmAdd               lda       <vmleft
                    adda      <vmright
                    bra       VmStoreVariable
VmSubtract          lda       <vmleft
                    suba      <vmright
                    bra       VmStoreVariable
VmAssign            lda       <vmright
VmStoreVariable     sta       ,x
VmArithmeticDone    lbra      VmNext
VmFlagCommand       ldu       <resourcebase
                    leax      vmflags,u
                    ldb       <vmtemp
                    lda       <vmopcode
                    cmpa      #15
                    blo       VmFlagDirect
                    leay      vmvariables,u
                    clra
                    ldb       d,y
VmFlagDirect        abx
                    lda       <vmopcode
                    cmpa      #15
                    blo       VmFlagOperation
                    suba      #3
VmFlagOperation     cmpa      #12
                    bne       VmFlagNotSet
                    lda       #1
                    bra       VmStoreVariable
VmFlagNotSet        cmpa      #13
                    bne       VmFlagToggle
                    clra
                    bra       VmStoreVariable
VmFlagToggle        lda       ,x
                    eora      #1
                    bra       VmStoreVariable

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
VmArgumentCounts
                    fcb       0,1,1,2,2,2,2,2,2,2,2,2,1,1,1,1
                    fcb       1,1,1,1,1,1,1,1,1,1,0,1,1,0,1,1
                    fcb       1,1,0,1,1,3,3,3,3,2,2,2,2,1,1,2
                    fcb       2,2,2,2,2,2,2,2,1,2,1,1,1,1,1,1
                    fcb       1,1,1,1,1,3,1,1,1,2,1,2,2,1,1,2
                    fcb       2,5,5,3,1,1,2,2,1,1,4,0,1,1,1,2
                    fcb       2,2,1,2,0,1,1,3,3,3,0,0,1,2,1,3
                    fcb       0,0,2,5,2,1,2,0,0,3,7,7,0,0,0,0
                    fcb       0,1,3,0,0,1,1,0,0,0,0,0,0,0,1,1
                    fcb       1,0,0,3,3,0,3,4,4,1,5,2,1,2,0,1
                    fcb       1,0,1,0,0,2,2,2,2,0,1,0,0,0,1,1
                    fcb       0,1,0,4,2,0
