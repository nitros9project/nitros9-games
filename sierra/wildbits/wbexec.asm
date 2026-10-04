* Native logic execution probe; not yet the game main loop.
                    nam       wbexec
                    use       defsfile
AGI_ASSET           equ       1
AGI_VM              equ       1
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
                    use       resource-data.asm
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
help                fcc       /Usage: wbexec game-directory logic-number/
                    fcb       C$CR
                    emod
eom                 equ       *
