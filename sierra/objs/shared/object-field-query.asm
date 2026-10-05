* Shared AGI object-field queries on an owner's object record.
* QUERY_OBJECT resolves the decoded object operand and consumes its byte.
* QUERY_LOAD reads a record field into A. QUERY_VARIABLE_TABLE supplies
* X=variable[0], preserving A/B/Y; QUERY_RETURN preserves owner ABI.
* QUERY_LAST_VALID retains each owner's empty-loop policy before decrement.
OBJECT_FIELD_QUERY   macro
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
