* wildbits-graphics feature macro bindings. Emits no code.
PLATFORM_WILDBITS_GRAPHICS_BINDINGS equ 1

* ===== wildbits-decoder-code local macros =====
PICTURE_COMMAND     macro
                    fdb       \1-DecodeDispatch
                    endm
