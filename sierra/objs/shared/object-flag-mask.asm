* Shared object flag mutation; compile out identity operations.
* Parameters: field offset, AND mask, OR mask, record pointer register.
OBJECT_FLAG_MASK    macro
                    lda       <\1,\4
                    ifne      (\2)-$FF
                    anda      #\2
                    endc
                    ifne      \3
                    ora       #\3
                    endc
                    sta       <\1,\4
                    endm
