* wildbits-memory-resources-bindings feature bindings. Included once; emits no code.
PLATFORM_WILDBITS_MEMORY_RESOURCES_BINDINGS equ 1

* ===== wildbits-animation-operands =====
* Native process-private scratch; X=private base, U=current object.
CycleCurrent        equ       vmleft
CycleLast           equ       vmright
CYCLE_READ_MODE     macro
                    lda       <$23,u
                    cmpa      #3
                    lbhi      MotionInvalid
                    endm
CYCLE_NOTIFY_FLAG   macro
                    ldb       $27,u
                    leay      vmflags,x
                    clra
                    leay      d,y
                    lda       #1
                    sta       ,y
                    endm
CYCLE_SET_CEL       macro
                    lda       #47
                    lbra      MotionSelectView
                    endm
CYCLE_RETURN        macro
                    clrb
                    rts
                    endm
