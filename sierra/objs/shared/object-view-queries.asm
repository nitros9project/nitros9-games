* Shared AGI view-state queries 49..53 on an owner's object record.
* QUERY_OBJECT resolves the decoded object operand and consumes its byte.
* QUERY_LOAD reads a record field into A. QUERY_VARIABLE_TABLE supplies
* X=variable[0], preserving A/B/Y; QUERY_RETURN preserves owner ABI.
* QUERY_LAST_VALID retains each owner's empty-loop policy before decrement.
OBJECT_VIEW_QUERY   macro
\1                  QUERY_OBJECT
                    QUERY_LOAD \2
                    ifne      \3
                    QUERY_LAST_VALID
                    deca
                    endc
                    ldb       ,y+
                    QUERY_VARIABLE_TABLE
                    abx
                    sta       ,x
                    QUERY_RETURN
                    endm
                    OBJECT_VIEW_QUERY cmd_last_cel,$0F,1
                    OBJECT_VIEW_QUERY cmd_current_cel,$0E,0
                    OBJECT_VIEW_QUERY cmd_current_loop,$0A,0
                    OBJECT_VIEW_QUERY cmd_current_view,$05,0
                    OBJECT_VIEW_QUERY cmd_number_of_loops,$0B,0
