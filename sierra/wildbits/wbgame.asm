* Native game owner: shared AGI logic with Wild Bits platform components.
                    nam       wbgame
WILDBITS            equ       1
                    use       defsfile
AGI_ASSET           equ       1
AGI_VM              equ       1
DECODE_PICTURE      equ       1
PICTURE_BOUNDED_READ equ       1
PRESENT_PICTURE     equ       1
GAME_PRESENTATION   equ       1
                    use       presentation.d
cmd_start           equ       $F0
x_max               equ       159
y_max               equ       167
PICBUFF_WIDTH       equ       160
argdirectory        rmb       2
argnumber           rmb       2
argdigit            rmb       1
                    use       asset-data.asm
                    use       lzw-data.asm
                    use       logic-data.asm
                    use       input-data.asm
                    use       screen-data.asm
                    use       view-data.asm
                    use       room-data.asm
                    use       menu-data.asm
                    use       replay-data.asm
                    use       message-data.asm
                    use       game-picture-data.asm
                    use       decoder-data.asm
                    use       presentation-data.asm
presentoffset       rmb       2
                    use       resource-data.asm
                    use       game-block-data.asm
                    use       game-motion-data.asm
                    use       game-text-data.asm
                    use       game-cycle-data.asm
                    use       game-render-data.asm
                    ifne      GAME_TRACE
gametracestagebyte  rmb       1
                    endc
assetinput          rmb       512
picturestage        rmb       512
fillstack           rmb       4096
                    use       presentation-buffers.asm
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
vmcontrollers       rmb       256
vmstrings           rmb       480
vmobjects           rmb       2752
vmcache             rmb       448
vmcallstack         rmb       128
                    rmb       1024
size                equ       .
                    mod       eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs       /wbgame/
                    fcb       1
                    use       resource-cli.asm
                    use       resource-code.asm
                    use       lzw-code.asm
                    use       asset-code.asm
                    use       logic-code.asm
                    use       logic-fetch.asm
                    use       message-code.asm
                    use       logic-cache.asm
                    use       input-code.asm
                    use       screen-code.asm
                    use       string-code.asm
                    use       view-code.asm
                    use       room-code.asm
                    use       menu-code.asm
                    use       object-code.asm
                    use       replay-code.asm
                    use       logic-platform.asm
                    use       game-picture-code.asm
                    use       game-background-code.asm
                    use       game-render-code.asm
                    use       game-cycle-code.asm
                    use       platform/sound-code.asm
                    use       game-block-code.asm
                    use       game-wander-code.asm
                    use       game-motion-code.asm
                    use       game-motion-command.asm
                    use       game-text-code.asm
                    use       ../objs/font-data.asm
                    use       decoder-code.asm
                    use       decoder-lines.asm
                    use       platform/wildbits-picture-memory.asm
                    use       decoder-fill.asm
                    use       decoder-pen.asm
                    use       platform/presentation.asm
                    use       platform/wildbits-presentation-helpers.asm
                    use       platform/wildbits-presentation-palette.asm
                    ifne      GAME_TRACE
                    use       game-trace-code.asm
                    endc
help                fcc       /Usage: wbgame game-directory logic-number/
                    fcb       C$CR
                    emod
eom                 equ       *
