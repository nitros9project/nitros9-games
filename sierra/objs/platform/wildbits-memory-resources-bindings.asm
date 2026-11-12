* wildbits-memory-resources-bindings feature bindings. Included once; emits no code.
PLATFORM_WILDBITS_MEMORY_RESOURCES_BINDINGS equ 1

* ===== wildbits-animation-operands =====
* Native process-private scratch; X=private base, U=current object.
                    ifne AGI_VM
CycleCurrent        equ       vmleft
CycleLast           equ       vmright
                    endc
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
                    bra       MotionSelectView
                    endm
CYCLE_RETURN        macro
                    clrb
                    rts
                    endm

* Native LZW dictionary cursor X and bounded private workspace stack.
* Codec-only consumers need no VM state; animation aliases above are gated.
LZW_CHAIN_VALIDATE macro
                    cmpd      #258
                    lblo      LzwInvalid
                    cmpd      <lzwnext
                    lbhs      LzwInvalid
                    endm
LZW_CHAIN_PREPARE macro
                    std       <lzwchain
                    endm
LZW_CHAIN_SCALE macro
                    addd      <lzwchain
                    addd      <lzwchain
                    endm
LZW_CHAIN_BASE macro
                    ldx       <lzwwork
                    endm
LZW_CHAIN_PUSH macro
                    lbsr      LzwPush
                    bcs       LzwReturn
                    endm
LZW_CHAIN_RETAIN macro
                    endm


* Animation-stage interface. Native validates 2..4 direction-driven loops,
* restores resource context after view acquisition and tail-calls cel advance.
ANIMATION_STRICT_LOOP_COUNTS equ 1
ANIMATION_PREPARE macro
                    endm
ANIMATION_SELECT_LOOP macro
                    lda       #43
                    lbsr      MotionSelectView
                    lbcs      MotionReturn
                    ldx       <resourcebase
                    ldu       motionobject,x
                    endm
ANIMATION_FINISH macro
                    clrb
                    rts
                    endm
ANIMATION_ADVANCE_BEFORE_RESET macro
                    endm
ANIMATION_ADVANCE_AFTER_RESET macro
                    bra       AdvanceCelFrame
                    endm
