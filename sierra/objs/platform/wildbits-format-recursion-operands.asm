* Native X=owned/copied message; U=private context. Caller saved X on S.
FORMAT_RECURSIVE_ARGUMENTS macro
                    ldu       <resourcebase
                    endm
FORMAT_RECURSIVE_TARGET equ FormatPart
FORMAT_RECURSIVE_RELEASE macro
                    endm
FORMAT_EXPANSION_RESULT macro
                    puls      x
                    endm
FORMAT_EXPANSION_CHECKED equ 1
FORMAT_EXPANSION_ERROR equ FormatPartError
FORMAT_EXPANSION_NEXT equ FormatNext
