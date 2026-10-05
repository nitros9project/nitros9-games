* Shared unsigned variable comparisons and direct/indirect flag predicates.
* Y=decoded operands; owners supply variable base, TestFlag, CONDITION_TRUE/False.
TestEqualN          ldb       ,y+       load variable number (var==value test)
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to the variable
                    lda       ,x        load variable value
                    cmpa      ,y+       compare to immediate operand
                    lbne      CONDITION_FALSE  branch if not equal
                    lbra      CONDITION_TRUE   var==value matched, return true
TestEqualV          ldb       ,y+       load first variable number (var==var test)
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to first variable
                    lda       ,x        load first variable value
                    ldb       ,y+       load second variable number, advance Y
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to second variable
                    cmpa      ,x        compare first to second variable
                    lbne      CONDITION_FALSE  branch if not equal
                    lbra      CONDITION_TRUE   var==var matched, return true
TestLessN           ldb       ,y+       load variable number (var<value test)
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to the variable
                    lda       ,x        load variable value
                    cmpa      ,y+       compare to immediate operand
                    lbcc      CONDITION_FALSE  branch if var >= value
                    lbra      CONDITION_TRUE   var<value matched, return true
TestLessV           ldb       ,y+       load first variable number (var<var test)
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to first variable
                    lda       ,x        load first variable value
                    ldb       ,y+       load second variable number
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to second variable
                    cmpa      ,x        compare first to second variable
                    lbcc      CONDITION_FALSE  branch if first >= second
                    lbra      CONDITION_TRUE   var<var matched, return true
TestGreaterN        ldb       ,y+       load variable number (var>value test)
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to the variable
                    lda       ,x        load variable value
                    cmpa      ,y+       compare to immediate operand
                    lbls      CONDITION_FALSE  branch if var <= value
                    lbra      CONDITION_TRUE   var>value matched, return true
TestGreaterV        ldb       ,y+       load first variable number (var>var test)
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to first variable
                    lda       ,x        load first variable value
                    ldb       ,y+       load second variable number
                    TEST_VARIABLE_TABLE    point to variable table
                    abx                 index to second variable
                    cmpa      ,x        compare first to second variable
                    lbls      CONDITION_FALSE  branch if first <= second
                    lbra      CONDITION_TRUE   var>var matched, return true
TestIsSet           lda       ,y+       load flag number (isset test)
                    lbsr      TestFlag  test if flag is set
                    lbeq      CONDITION_FALSE  branch if flag not set
                    lbra      CONDITION_TRUE   flag is set, return true
TestIsSetV          ldb       ,y+       load variable number (isset.v test)
                    TEST_VARIABLE_TABLE    point to variable table for isset.v
                    abx                 index to the flag-number variable
                    lda       ,x        load flag result (from TestFlag above)
                    lbsr      TestFlag  test flag for isset.v (flag in variable)
                    lbeq      CONDITION_FALSE  branch if flag not set
                    lbra      CONDITION_TRUE   isset.v matched, return true
