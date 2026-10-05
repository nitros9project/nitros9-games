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
                    use       platform/wildbits-asset-data.asm
                    use       platform/wildbits-lzw-data.asm
                    use       platform/wildbits-logic-data.asm
                    use       platform/wildbits-input-data.asm
                    use       platform/wildbits-screen-data.asm
                    use       platform/wildbits-view-data.asm
                    use       platform/wildbits-room-data.asm
                    use       platform/wildbits-menu-data.asm
                    use       platform/wildbits-replay-data.asm
                    use       platform/wildbits-message-data.asm
                    use       platform/wildbits-game-picture-data.asm
                    use       platform/wildbits-decoder-data.asm
                    use       platform/wildbits-presentation-data.asm
presentoffset       rmb       2
                    use       platform/wildbits-resource-data.asm
                    use       platform/wildbits-game-block-data.asm
                    use       platform/wildbits-game-motion-data.asm
                    use       platform/wildbits-game-text-data.asm
                    use       platform/wildbits-game-cycle-data.asm
                    use       platform/wildbits-inventory-data.asm
                    use       platform/wildbits-parser-data.asm
                    use       platform/wildbits-game-render-data.asm
                    ifne      GAME_TRACE
gametracestagebyte  rmb       1
gametracekeybyte    rmb       1
gametracemenuhit    rmb       1
                    endc
assetinput          rmb       512
* I/O, picture copies and message copies are separate phases.
picturestage        equ       assetinput
fillstack           rmb       4096
                    use       platform/wildbits-presentation-buffers.asm
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
                    use       platform/wildbits-resource-cli.asm
                    use       platform/wildbits-resource-code.asm
                    use       platform/wildbits-lzw-code.asm
                    use       platform/wildbits-asset-code.asm
                    use       platform/wildbits-logic-code.asm
                    use       platform/wildbits-logic-fetch.asm
                    use       platform/wildbits-message-code.asm
                    use       platform/wildbits-logic-cache.asm
                    use       platform/wildbits-input-code.asm
                    use       platform/wildbits-parser-code.asm
                    use       platform/wildbits-terminal-options.asm
                    use       platform/wildbits-dialog-code.asm
                    use       platform/wildbits-menu-code.asm
                    use       platform/wildbits-line-input-code.asm
                    use       platform/wildbits-format-code.asm
                    use       platform/wildbits-screen-code.asm
                    use       platform/wildbits-string-code.asm
                    use       platform/wildbits-view-code.asm
                    use       platform/wildbits-room-code.asm
                    use       platform/wildbits-menu-build-code.asm
                    use       platform/wildbits-object-code.asm
                    use       platform/wildbits-replay-code.asm
                    use       platform/wildbits-logic-platform.asm
                    use       platform/wildbits-game-picture-code.asm
                    use       platform/wildbits-game-background-code.asm
                    use       platform/wildbits-game-render-code.asm
                    use       platform/wildbits-game-cycle-code.asm
                    use       platform/wildbits-inventory-code.asm
                    use       platform/sound-code.asm
                    use       platform/wildbits-game-block-code.asm
                    use       platform/wildbits-game-wander-code.asm
                    use       platform/wildbits-game-math-code.asm
                    use       platform/wildbits-game-motion-code.asm
                    use       platform/wildbits-game-motion-command.asm
                    use       platform/wildbits-game-reposition-code.asm
                    use       platform/wildbits-game-text-code.asm
                    use       platform/wildbits-font-code.asm
                    use       platform/wildbits-decoder-code.asm
                    use       platform/wildbits-decoder-lines.asm
                    use       platform/wildbits-picture-memory.asm
                    use       platform/wildbits-decoder-fill.asm
                    use       platform/wildbits-decoder-pen.asm
                    use       platform/presentation.asm
                    use       platform/wildbits-presentation-helpers.asm
                    use       platform/wildbits-presentation-palette.asm
                    ifne      GAME_TRACE
                    use       platform/wildbits-game-trace-code.asm
                    endc
help                fcc       /Usage: wbgame game-directory logic-number/
                    fcb       C$CR
                    emod
eom                 equ       *
