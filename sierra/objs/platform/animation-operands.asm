                    ifne WILDBITS
                    use platform/wildbits-animation-operands.asm
                    else
                    use platform/coco-animation-operands.asm
                    endc

* View acquisition and continuation ABI for the shared animation stage.
ANIMATION_SELECT_LOOP macro
                    ifne WILDBITS
                    lda       #43
                    lbsr      MotionSelectView
                    lbcs      MotionReturn
                    ldx       <resourcebase
                    ldu       motionobject,x
                    else
                    lbsr      SetLoopHelper
                    endc
                    endm
ANIMATION_FINISH macro
                    ifne WILDBITS
                    clrb
                    rts
                    endc
                    endm
ANIMATION_REVERSE_ENABLE macro
                    lda       >$01B0
                    anda      #8
                    endm
