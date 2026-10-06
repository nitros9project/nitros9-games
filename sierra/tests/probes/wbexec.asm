* Native logic execution probe; not yet the game main loop.
                    nam       wbexec
WILDBITS            equ       1
                    use       platform/wildbits-defsfile
AGI_ASSET           equ       1
AGI_VM              equ       1
argdirectory        rmb       2
argnumber           rmb       2
argdigit            rmb       1
                    use platform/sections.d
PLATFORM_SECTION    set PLATFORM_WILDBITS_ASSET_DATA
                    use platform/wildbits-memory-resources.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_LZW_DATA
                    use platform/wildbits-memory-resources.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_LOGIC_DATA
                    use platform/wildbits-logic.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_INPUT_DATA
                    use platform/wildbits-input.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_SCREEN_DATA
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_VIEW_DATA
                    use platform/wildbits-memory-resources.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_ROOM_DATA
                    use platform/wildbits-memory-resources.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_MENU_DATA
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_REPLAY_DATA
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_MESSAGE_DATA
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_RESOURCE_DATA
                    use platform/wildbits-memory-resources.asm
assetinput          rmb       512
messagebuffer       rmb       512
vmgameid            rmb       8
vmvariables         rmb       256
vmflags             rmb       256
vmarguments         rmb       255
replaybuffer        rmb       510
menutitles          rmb       32
menuentries         rmb       192
menutext            rmb       768
vmkeys              rmb       150
vmcontrollers       rmb       32
vmstrings           rmb       480
vmobjects           rmb       2752
vmcache             rmb       448
vmcallstack         rmb       128
                    rmb       1024
size                equ       .
                    mod       eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs       /wbexec/
                    fcb       1
PLATFORM_SECTION    set PLATFORM_WILDBITS_RESOURCE_CLI
                    use platform/wildbits-memory-resources.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_RESOURCE_CODE
                    use platform/wildbits-memory-resources.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_LZW_CODE
                    use platform/wildbits-memory-resources.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_ASSET_CODE
                    use platform/wildbits-memory-resources.asm
                    use       platform/wildbits-logic-code.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_LOGIC_FETCH
                    use platform/wildbits-logic.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_MESSAGE_CODE
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_LOGIC_CACHE
                    use platform/wildbits-logic.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_INPUT_CODE
                    use platform/wildbits-input.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_SCREEN_CODE
                    use platform/wildbits-graphics.asm
                    use       platform/wildbits-string-code.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_VIEW_CODE
                    use platform/wildbits-memory-resources.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_ROOM_CODE
                    use platform/wildbits-memory-resources.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_MENU_BUILD_CODE
                    use platform/wildbits-text-ui.asm
                    use       platform/wildbits-object-code.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_REPLAY_CODE
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_LOGIC_PLATFORM
                    use platform/wildbits-logic.asm
help                fcc       /Usage: wbexec game-directory logic-number/
                    fcb       C$CR
                    emod
eom                 equ       *
