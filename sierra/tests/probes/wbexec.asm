* Native logic execution probe; not yet the game main loop.
                    nam       wbexec
WILDBITS            equ       1
                    use       platform/wildbits-defsfile
AGI_ASSET           equ       1
AGI_VM              equ       1
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
                    use       platform/wildbits-resource-data.asm
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
                    use       platform/wildbits-resource-cli.asm
                    use       platform/wildbits-resource-code.asm
                    use       platform/wildbits-lzw-code.asm
                    use       platform/wildbits-asset-code.asm
                    use       platform/wildbits-logic-code.asm
                    use       platform/wildbits-logic-fetch.asm
                    use       platform/wildbits-message-code.asm
                    use       platform/wildbits-logic-cache.asm
                    use       platform/wildbits-input-code.asm
                    use       platform/wildbits-screen-code.asm
                    use       platform/wildbits-string-code.asm
                    use       platform/wildbits-view-code.asm
                    use       platform/wildbits-room-code.asm
                    use       platform/wildbits-menu-build-code.asm
                    use       platform/wildbits-object-code.asm
                    use       platform/wildbits-replay-code.asm
                    use       platform/wildbits-logic-platform.asm
help                fcc       /Usage: wbexec game-directory logic-number/
                    fcb       C$CR
                    emod
eom                 equ       *
