* Immutable Wild Bits UI/audio provider; mutable cells belong to the caller.
* Persistence code stays in wbstate and is copied only for state operations.
AUDIO_USER_COPY     equ 1
WILDBITS            equ 1
WILDBITS_LAYOUT_ONLY equ 1
                    use platform/wildbits-runtime.asm
                    org 0
                    mod UiEnd,UiName,Sbrtn+Objct,ReEnt+1,UiEntry,0
UiName              fcs /wbui/
                    fcb 1
UiEntry             bra UiInvalid
                    STATE_ABI
                    fdb AudioBlobEnd-AudioBlobStart,AudioInstall,AuxTextStore,AuxPrintWait,0,AuxClearTextRect,AuxRestart,AuxScreenCommand,AuxShowObject,AuxShakeScreen,AuxMenuInput,AuxFormatExpansion
* The public entry is a directory, never the copied persistence dispatcher.
UiInvalid           ldb #E$BMode
                    orcc #1
                    rts
UiPrefixEnd         equ *
                    WILDBITS_PRIORITY_SCALE
PLATFORM_SECTION    set PLATFORM_WILDBITS_SOUND_CODE
                    use platform/wildbits-audio.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_TEXT_STORE_CODE
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_DIALOG_WAIT_CODE
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_TEXT_RECT_CODE
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_RESTART_CODE
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_SHOW_OBJECT_CODE
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_SCREEN_COLD_CODE
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_SHAKE_CODE
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_MENU_COLD_CODE
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_FORMAT_COLD_CODE
                    use platform/wildbits-text-ui.asm
                    emod
UiEnd               equ *
                    ifgt AudioBlobEnd-AudioBlobStart-512
                    error Private audio adapter exceeds its reserved workspace
                    endc
                    ifgt UiEnd-8192
                    error Immutable UI provider exceeds its code window
                    endc
