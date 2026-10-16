* NUL-terminated traversal with either a direct terminator-inclusive copy
* or a checked emitter which handles completion before writing the NUL.
* Parameters: source register, loop label, copy-NUL trait, write macro,
* completion macro, error macro. Checked writers preserve A/source register.
NUL_STRING_COPY     macro
\2                  lda       ,\1+
                    ifne      \3
                    \4
                    bne       \2
                    else
                    \5
                    \4
                    \6
                    bra       \2
                    endc
                    endm
NUL_COPY_NOOP       macro
                    endm
