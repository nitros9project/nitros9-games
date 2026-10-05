* Store a step/cycle rate; optionally reset its countdown to the same value.
* Parameters: value accumulator, record register, rate field, countdown field
* (-1 omits countdown). Preserve owners' original indexed encodings.
OBJECT_RATE_STATE   macro
                    ifeq      \3
                    st\1      ,\2
                    else
                    st\1      \3,\2
                    endc
                    ifge      \4
                    st\1      \4,\2
                    endc
                    endm
