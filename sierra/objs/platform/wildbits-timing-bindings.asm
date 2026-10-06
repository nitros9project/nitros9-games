* wildbits-timing-bindings feature bindings. Included once; emits no code.
PLATFORM_WILDBITS_TIMING_BINDINGS equ 1

* ===== wildbits-game-clock-operands =====
* Private native AGI clock variables 11..14.
GAME_CLOCK_ADDRESS  macro
                    leax      vmvariables+11,u
                    endm
