* Fixed-point priority bands: scale=floor((168-base)*168/10).
* For y>=base: min(15,5+floor((y-base)*168/scale)); otherwise 4.
* Owner supplies base access, division ABI and scale storage.
                    ifndef SHARED_PRIORITY_BANDS
SHARED_PRIORITY_BANDS equ 1
PRIORITY_MULTIPLY_OFFSET macro
                    lda       #168
                    mul
                    endm
* Fixed default-band depth; source is the owner's priority byte operand.
PRIORITY_PROJECT_DEFAULT macro
                    lda       \1,\2
                    suba      #5
                    ldb       #12
                    mul
                    addb      #48
                    endm
PRIORITY_BUILD_SCALE macro
                    ldb       #168
                    PRIORITY_SCALE_BASE
                    PRIORITY_MULTIPLY_OFFSET
                    PRIORITY_SCALE_DIVIDE
                    PRIORITY_SCALE_STORE
                    endm
                    endc
