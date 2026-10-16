* Shared unsigned variable comparisons and direct/indirect flag predicates.
* TEST_BRANCH takes condition, target, long-range hint; CoCo retains long forms.
* Y=decoded operands; owners supply variable base, TestFlag, CONDITION_TRUE/False.
TestEqualN          ldb       ,y+       load variable number (var==value test)
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to the variable
                    lda       ,x        load variable value
                    cmpa      ,y+       compare to immediate operand
                    TEST_BRANCH bne,CONDITION_FALSE,1  branch if not equal
                    TEST_BRANCH bra,CONDITION_TRUE,1   var==value matched, return true
TestEqualV          ldb       ,y+       load first variable number (var==var test)
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to first variable
                    lda       ,x        load first variable value
                    ldb       ,y+       load second variable number, advance Y
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to second variable
                    cmpa      ,x        compare first to second variable
                    TEST_BRANCH bne,CONDITION_FALSE,1  branch if not equal
                    TEST_BRANCH bra,CONDITION_TRUE,1   var==var matched, return true
TestLessN           ldb       ,y+       load variable number (var<value test)
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to the variable
                    lda       ,x        load variable value
                    cmpa      ,y+       compare to immediate operand
                    TEST_BRANCH bcc,CONDITION_FALSE,0  branch if var >= value
                    TEST_BRANCH bra,CONDITION_TRUE,0   var<value matched, return true
TestLessV           ldb       ,y+       load first variable number (var<var test)
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to first variable
                    lda       ,x        load first variable value
                    ldb       ,y+       load second variable number
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to second variable
                    cmpa      ,x        compare first to second variable
                    TEST_BRANCH bcc,CONDITION_FALSE,0  branch if first >= second
                    TEST_BRANCH bra,CONDITION_TRUE,0   var<var matched, return true
TestGreaterN        ldb       ,y+       load variable number (var>value test)
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to the variable
                    lda       ,x        load variable value
                    cmpa      ,y+       compare to immediate operand
                    TEST_BRANCH bls,CONDITION_FALSE,0  branch if var <= value
                    TEST_BRANCH bra,CONDITION_TRUE,0   var>value matched, return true
TestGreaterV        ldb       ,y+       load first variable number (var>var test)
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to first variable
                    lda       ,x        load first variable value
                    ldb       ,y+       load second variable number
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to second variable
                    cmpa      ,x        compare first to second variable
                    TEST_BRANCH bls,CONDITION_FALSE,0  branch if first <= second
                    TEST_BRANCH bra,CONDITION_TRUE,0   var>var matched, return true
TestIsSet           lda       ,y+       load flag number (isset test)
                    lbsr      TestFlag  test if flag is set
                    TEST_BRANCH beq,CONDITION_FALSE,0  branch if flag not set
                    TEST_BRANCH bra,CONDITION_TRUE,0   flag is set, return true
TestIsSetV          ldb       ,y+       load variable number (isset.v test)
                    TEST_VARIABLE_TABLE    point to variable table for isset.v
                    abx                 index to the flag-number variable
                    lda       ,x        load flag result (from TestFlag above)
                    lbsr      TestFlag  test flag for isset.v (flag in variable)
                    TEST_BRANCH beq,CONDITION_FALSE,0  branch if flag not set
                    TEST_BRANCH bra,CONDITION_TRUE,0   isset.v matched, return true
