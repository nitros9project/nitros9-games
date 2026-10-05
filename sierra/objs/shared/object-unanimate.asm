* Clear animated/visible bits in every owned 43-byte record, preserving
* all other fields. Owner supplies exclusive-end or positive-count traversal.
* Parameters: record register, loop label, completion label.
OBJECT_UNANIMATE_ALL macro
\2                  UNANIMATE_LIMIT \3
                    lda       <$26,\1
                    anda      #$BE
                    sta       <$26,\1
                    lea\1     <$2B,\1
                    UNANIMATE_NEXT \2
\3
                    endm
