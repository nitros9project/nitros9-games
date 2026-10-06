* Native game owner: shared AGI logic with Wild Bits platform components.
                    nam       wbgame
                    use       platform/wildbits-defsfile
AGI_ASSET           equ       1
AGI_VM              equ       1
DECODE_PICTURE      equ       1
PICTURE_BOUNDED_READ equ       1
PRESENT_PICTURE     equ       1
GAME_PRESENTATION   equ       1
                    use       platform/wildbits-presentation.d
cmd_start           equ       $F0
x_max               equ       159
y_max               equ       167
PICBUFF_WIDTH       equ       160
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
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_PICTURE_DATA
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_DECODER_DATA
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_PRESENTATION_DATA
                    use platform/wildbits-graphics.asm
presentoffset       rmb       2
PLATFORM_SECTION    set PLATFORM_WILDBITS_RESOURCE_DATA
                    use platform/wildbits-memory-resources.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_BLOCK_DATA
                    use platform/wildbits-objects.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_MOTION_DATA
                    use platform/wildbits-objects.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_TEXT_DATA
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_CYCLE_DATA
                    use platform/wildbits-objects.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_INVENTORY_DATA
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_PARSER_DATA
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_RENDER_DATA
                    use platform/wildbits-graphics.asm
                    ifne      GAME_TRACE
gametracestagebyte  rmb       1
gametracekeybyte    rmb       1
gametracemenuhit    rmb       1
                    endc
assetinput          rmb       512
* I/O, picture copies and message copies are separate phases.
picturestage        equ       assetinput
fillstack           rmb       4096
PLATFORM_SECTION    set PLATFORM_WILDBITS_PRESENTATION_BUFFERS
                    use platform/wildbits-graphics.asm
messagebuffer       equ       assetinput
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
gamefont            rmb       1024
                    rmb       512
size                equ       .
                    mod       eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs       /wbgame/
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
                    use       platform/wildbits-parser-code.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_TERMINAL_OPTIONS
                    use platform/wildbits-input.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_DIALOG_CODE
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_MENU_CODE
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_LINE_INPUT_CODE
                    use platform/wildbits-input.asm
                    use       platform/wildbits-format-code.asm
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
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_PICTURE_CODE
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_BACKGROUND_CODE
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_RENDER_CODE
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_CYCLE_CODE
                    use platform/wildbits-objects.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_INVENTORY_CODE
                    use platform/wildbits-text-ui.asm
* Assembly-time sound backend selection; emits no dispatch instructions.
* Each owner supplies its backend state/entry-point contract.
                    ifne      WILDBITS
PLATFORM_SECTION    set PLATFORM_WILDBITS_SOUND_CODE
                    use platform/wildbits-audio.asm
                    else
PLATFORM_SECTION    set PLATFORM_COCO_SOUND_CODE
                    use platform/coco-audio.asm
                    endc
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_BLOCK_CODE
                    use platform/wildbits-objects.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_WANDER_CODE
                    use platform/wildbits-objects.asm
                    use       platform/wildbits-game-math-code.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_MOTION_CODE
                    use platform/wildbits-objects.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_MOTION_COMMAND
                    use platform/wildbits-objects.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_REPOSITION_CODE
                    use platform/wildbits-objects.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_TEXT_CODE
                    use platform/wildbits-text-ui.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_FONT_CODE
                    use platform/wildbits-graphics.asm
                    use       platform/wildbits-decoder-code.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_DECODER_LINES
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_PICTURE_MEMORY
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_DECODER_FILL
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_DECODER_PEN
                    use platform/wildbits-graphics.asm
* Assembly-time platform selection.
* CoCo entry: gfx_picbuff_update, legacy module ABI.
* Wild Bits entries: PresentPicture/PresentationRelease, native private ABI.
* Callers must supply the selected state contract; these are not ABI aliases.
                    ifne      WILDBITS
PLATFORM_SECTION    set PLATFORM_WILDBITS_PRESENTATION
                    use platform/wildbits-graphics.asm
                    else
PLATFORM_SECTION    set PLATFORM_COCO_PRESENTATION
                    use platform/coco-graphics.asm
                    endc
PLATFORM_SECTION    set PLATFORM_WILDBITS_PRESENTATION_HELPERS
                    use platform/wildbits-graphics.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_PRESENTATION_PALETTE
                    use platform/wildbits-graphics.asm
                    ifne      GAME_TRACE
PLATFORM_SECTION    set PLATFORM_WILDBITS_GAME_TRACE_CODE
                    use platform/wildbits-logic.asm
                    endc
help                fcc       /Usage: wbgame game-directory logic-number/
                    fcb       C$CR
                    emod
eom                 equ       *
