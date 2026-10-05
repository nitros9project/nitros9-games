* Existing CoCo stack arguments: output pointer, then source pointer.
FORMAT_RECURSIVE_ARGUMENTS macro
                    ldd       $08,s
                    pshs      b,a
                    pshs      u
                    endm
FORMAT_RECURSIVE_TARGET equ FormatStr
FORMAT_RECURSIVE_RELEASE macro
                    leas      $04,s
                    endm
FORMAT_EXPANSION_RESULT macro
                    stu       $08,s
                    endm
FORMAT_EXPANSION_CHECKED equ 0
FORMAT_EXPANSION_NEXT equ FormatStrLoop
