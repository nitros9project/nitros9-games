* Expand a substitution recursively and resume the saved outer scan.
* A checked reader may jump to FormatExpansionReturn on acquisition failure,
* bypassing recursion while still restoring its saved source cursor.
FormatExpansion     FORMAT_RECURSIVE_CALL
FormatExpansionReturn FORMAT_EXPANSION_RESULT
                    ifne      FORMAT_EXPANSION_CHECKED
                    lbcs      FORMAT_EXPANSION_ERROR
                    endc
                    lbra      FORMAT_EXPANSION_NEXT
