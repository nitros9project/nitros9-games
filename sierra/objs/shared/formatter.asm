* Formatter component. Definitions emit no code until invoked.
* Named expansion sites preserve module layout and direct branch/call targets.

* ===== format-recursive-call =====
* Invoke the formatter using the owner's argument ABI. Arguments describe
* source/output/context only; the recursive traversal is the owner's entry.
FORMAT_RECURSIVE_CALL macro
                    FORMAT_RECURSIVE_ARGUMENTS
                    lbsr      FORMAT_RECURSIVE_TARGET
                    FORMAT_RECURSIVE_RELEASE
                    endm

* ===== format-scan =====
FORMAT_EMIT_SCAN macro
* Shared character traversal; line tracking is an assembly-time trait.
FormatStrLoop       FORMAT_SCAN_LIMIT
                    FORMAT_SCAN_READ
                    FORMAT_SCAN_END
                    ifne FORMAT_SCAN_LINES
                    cmpa      >FORMAT_SCAN_LITERAL    ; check for literal-next prefix
                    bne       FormatStrCheckEsc ; not literal, check for escape
                    tst       ,x+       ; consume literal-next byte
                    bra       FormatStrStoreChar ; store next char literally
                    endc
FormatStrCheckEsc   cmpa      #$25      ; check for '%' escape prefix
                    FORMAT_SCAN_ESCAPE
                    ifne FORMAT_SCAN_LINES
                    cmpa      #$0A      ; check for newline
                    bne       FormatStrCheckNl
                    lbsr      IncrLineCount ; count this line
                    bra       FormatStrCopyChar ; copy newline to output
FormatStrCheckNl    cmpa      #$20      ; check for space (word break point)
                    bne       FormatStrStoreChar
                    stu       >FORMAT_SCAN_WRAP_POINT    ; save current output pointer as word-wrap point
FormatStrStoreChar  inc       >FORMAT_SCAN_LINE_LENGTH    ; increment char count on line
                    endc
FormatStrCopyChar   FORMAT_SCAN_WRITE
                    bra       FormatStrLoop
                    endm

* ===== format-directives =====
FORMAT_EMIT_DIRECTIVES macro
* Shared substitution selection. The caller has read the directive letter;
* its decimal operand/source context remains owned by the formatter.
                    FORMAT_DIRECTIVE_COMPARE 'w
                    FORMAT_DIRECTIVE_WORD
                    FORMAT_DIRECTIVE_COMPARE 's
                    FORMAT_DIRECTIVE_STRING
                    FORMAT_DIRECTIVE_COMPARE 'm
                    FORMAT_DIRECTIVE_MESSAGE
                    ifne FORMAT_DIRECTIVE_GLOBAL_ENABLED
                    FORMAT_DIRECTIVE_COMPARE 'g
                    FORMAT_DIRECTIVE_GLOBAL
                    endc
                    FORMAT_DIRECTIVE_COMPARE 'v
                    FORMAT_DIRECTIVE_VARIABLE
                    ifne FORMAT_DIRECTIVE_OBJECT_ENABLED
                    FORMAT_DIRECTIVE_COMPARE 'o
                    FORMAT_DIRECTIVE_OBJECT
                    endc
* Fall through to the owner's object handler or unsupported-directive policy.
                    endm

* ===== format-string-slot =====
FORMAT_EMIT_STRING_SLOT macro
* Resolve a 40-byte AGI string slot, then expand its contents. The caller
* supplies B=index (or an adapter which parses it), validation and storage.
* Both owners recursively format a resolved slot using their expansion ABI.
FormatStringSlot    FORMAT_STRING_PREPARE
                    lda       #40
                    mul
                    FORMAT_STRING_ADDRESS
                    FORMAT_STRING_EXPAND
                    endm

* ===== format-expansion =====
FORMAT_EMIT_EXPANSION macro
* Expand a substitution recursively and resume the saved outer scan.
* A checked reader may jump to FormatExpansionReturn on acquisition failure,
* bypassing recursion while still restoring its saved source cursor.
FormatExpansion     FORMAT_RECURSIVE_CALL
FormatExpansionReturn FORMAT_EXPANSION_RESULT
                    ifne      FORMAT_EXPANSION_CHECKED
                    lbcs      FORMAT_EXPANSION_ERROR
                    endc
                    lbra      FORMAT_EXPANSION_NEXT
                    endm
