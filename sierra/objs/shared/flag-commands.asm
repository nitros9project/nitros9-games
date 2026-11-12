* Shared set/reset/toggle and variable-indexed flag commands 12..17.
* Y=decoded operands; FLAG_VARIABLE_TABLE supplies variable-table X.
* SetFlag/ClearFlag/ToggleFlag own packed-bit versus byte representation.
CmdSetImpl          lda       ,y+       load flag number from script
                    bra       SetFlag   jump to SetFlag to set it


CmdResetImpl        lda       ,y+       load flag number from script
                    bra       ClearFlag jump to ClearFlag to clear it


CmdToggleImpl       lda       ,y+       load flag number from script
                    bra       ToggleFlag jump to ToggleFlag to toggle it

CmdSetVImpl         ldb       ,y+       load variable number from script
                    FLAG_VARIABLE_TABLE    point to variable table
                    abx                 index to the variable
                    lda       ,x        load flag number from variable
                    bra       SetFlag   jump to SetFlag with flag number in A

CmdResetVImpl       ldb       ,y+       load variable number from script
                    FLAG_VARIABLE_TABLE    point to variable table
                    abx                 index to the variable
                    lda       ,x        load flag number from variable
                    bra       ClearFlag jump to ClearFlag with flag number

CmdToggleVImpl      ldb       ,y+       load variable number from script
                    FLAG_VARIABLE_TABLE     point to variable table
                    abx                 index to the variable
                    lda       ,x        load flag number from variable
                    bra       ToggleFlag jump to ToggleFlag with flag number

