* coco-timing-bindings feature bindings. Included once; emits no code.
PLATFORM_COCO_TIMING_BINDINGS equ 1

* ===== coco-game-clock-operands =====
* CoCo signal-handler data area; retain the original indexed addressing.
GAME_CLOCK_ADDRESS  macro
                    leax      >TimeOfDay,u
                    endm
