* Shared substitution selection. The caller has read the directive letter;
* its decimal operand/source context remains owned by the formatter.
                    FORMAT_DIRECTIVE_COMPARE 'w
                    FORMAT_DIRECTIVE_WORD
                    FORMAT_DIRECTIVE_COMPARE 's
                    FORMAT_DIRECTIVE_STRING
                    FORMAT_DIRECTIVE_COMPARE 'm
                    FORMAT_DIRECTIVE_MESSAGE
                    ifne FORMAT_DIRECTIVE_EXTENDED
                    FORMAT_DIRECTIVE_COMPARE 'g
                    FORMAT_DIRECTIVE_GLOBAL
                    endc
                    FORMAT_DIRECTIVE_COMPARE 'v
                    FORMAT_DIRECTIVE_VARIABLE
                    ifne FORMAT_DIRECTIVE_EXTENDED
                    FORMAT_DIRECTIVE_COMPARE 'o
                    FORMAT_DIRECTIVE_OBJECT
                    endc
* Fall through to the owner's object handler or unsupported-directive policy.
