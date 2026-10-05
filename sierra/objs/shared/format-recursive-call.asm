* Invoke the formatter using the owner's argument ABI. Arguments describe
* source/output/context only; the recursive traversal is the owner's entry.
FORMAT_RECURSIVE_CALL macro
                    FORMAT_RECURSIVE_ARGUMENTS
                    lbsr      FORMAT_RECURSIVE_TARGET
                    FORMAT_RECURSIVE_RELEASE
                    endm
