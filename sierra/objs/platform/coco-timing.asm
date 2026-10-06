                    ifndef PLATFORM_COCO_TIMING_BINDINGS
* coco-timing-bindings feature bindings. Included once; emits no code.
PLATFORM_COCO_TIMING_BINDINGS equ 1

* ===== coco-game-clock-operands =====
* CoCo signal-handler data area; retain the original indexed addressing.
GAME_CLOCK_ADDRESS  macro
                    leax      >TimeOfDay,u
                    endm
                    endc

                    ifeq PLATFORM_SECTION-PLATFORM_COCO_GAME_CLOCK_BINDINGS
* Clock bindings only; no executable body.
                    else
* coco-timing feature: code and related private state.
* Named layout sections preserve existing module and private-data addresses.

                    ifeq PLATFORM_SECTION-PLATFORM_COCO_TIMER_INTERCEPT
* ===== coco-timer-intercept =====
* CoCo platform boundary: timer-intercept.
* Included in place; see ../../PORTABILITY.md.

SigIntercept        cmpb      #$80      b gets the signal code if not $80 ignore
                    bne       SigInterceptRet $80 is user defined
                    tfr       u,d       copy U (data area ptr) into D
                    tfr       a,dp      set direct page register to data area base
                    dec       <IrqCountdown decrement IRQ countdown counter
                    bne       SigInterceptRet not yet time — return
                    bsr       SigHandlerCore call timer and game-clock handler
                    lda       #$03      reload countdown to 3 intervals
                    sta       <IrqCountdown reset IRQ countdown
SigInterceptRet     rti                 return from interrupt

                    else
                    error Unknown platform feature section
                    endc
                    endc
