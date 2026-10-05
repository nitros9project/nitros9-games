* Bounded, process-private adapter to the common condition traversal.
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
                    leas      2,s
                    lbra      VmNext
                    endm
CONDITION_FALSE_LABEL equ     VmConditionFalse
VmConditionStart    leas      -2,s
                    use       shared/condition-flow.asm

* A=test number. Decode operands for evaluated and skipped predicates alike.
VmConditionOperands sta       <vmopcode
                    cmpa      #1
                    lblo      VmInvalid
                    cmpa      #18
                    lbhi      VmInvalid
                    cmpa      #14
                    beq       VmConditionSaid
                    leax      VmTestCounts,pcr
                    ldb       a,x
                    stb       <vmargcount
                    lbra      VmReadArguments
VmConditionSaid     lbsr      VmFetchByte
                    lbcs      VmReturn
                    cmpb      #127
                    lbhi      VmInvalid
                    lslb
                    stb       <vmargcount
                    lbra      VmReadArguments
VmConditionTest     lbsr      VmConditionOperands
                    lbcs      VmReturn
                    lbra      VmEvaluateTest
VmConditionFalse    lbsr      VmReadWord
                    bcs       VmConditionFailure
                    addd      <vmip
                    cmpd      #2
                    blo       VmConditionInvalid
                    cmpd      <vmend
                    bhs       VmConditionInvalid
                    std       <vmip
                    leas      2,s
                    lbra      VmNext
VmConditionInvalid  leas      2,s
                    lbra      VmInvalid
VmConditionFailure  leas      2,s
                    lbra      VmReturn

* Validate grammar while skipping callbacks. Helper return occupies ,S;
* the shared OR/NOT locals are therefore 2,S and 3,S. A remains the code byte.
VmConditionScanControl cmpa   #$FE
                    beq       VmConditionScanInvalid
                    cmpa      #$FD
                    beq       VmConditionScanNot
                    cmpa      #$FC
                    beq       VmConditionScanOr
                    cmpa      #$FF
                    bne       VmConditionScanValid
                    ldb       2,s
                    orb       3,s
                    bne       VmConditionScanInvalid
VmConditionScanValid andcc    #$FE
                    rts
VmConditionScanNot  ldb       3,s
                    eorb      #1
                    stb       3,s
                    bra       VmConditionScanValid
VmConditionScanOr   tst       3,s
                    bne       VmConditionScanInvalid
                    ldb       2,s
                    eorb      #1
                    stb       2,s
                    bra       VmConditionScanValid
VmConditionScanInvalid lbra   VmInvalid
