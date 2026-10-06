* coco-memory-resources-bindings feature bindings. Included once; emits no code.
PLATFORM_COCO_MEMORY_RESOURCES_BINDINGS equ 1

* ===== coco-animation-operands =====
* CoCo original scratch, packed completion flags and mapped view callback.
CycleCurrent        equ       $0074
CycleLast           equ       $0075
CYCLE_READ_MODE     macro
                    lda       <$23,u
                    endm
CYCLE_NOTIFY_FLAG   macro
                    lda       <$27,u
                    lbsr      SetFlag
                    endm
CYCLE_SET_CEL       macro
                    lbsr      SetCelHelper
                    endm
CYCLE_RETURN        macro
                    rts
                    endm

* CoCo LZW dictionary cursor U, direct mapped entries and hardware stack.
LZW_CHAIN_VALIDATE macro
                    endm
LZW_CHAIN_PREPARE macro
                    endm
LZW_CHAIN_SCALE macro
                    addd      <$00A6
                    addd      <$00A6
                    endm
LZW_CHAIN_BASE macro
                    ldu       #$6400
                    endm
LZW_CHAIN_PUSH macro
                    pshs      b
                    inc       <$00B6
                    endm
LZW_CHAIN_RETAIN macro
                    std       <$00A6
                    endm
