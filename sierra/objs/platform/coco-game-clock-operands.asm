* CoCo signal-handler data area; retain the original indexed addressing.
GAME_CLOCK_ADDRESS  macro
                    leax      >TimeOfDay,u
                    endm
