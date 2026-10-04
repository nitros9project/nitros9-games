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
                    use       message-data.asm
                    use       resource-data.asm
assetinput          rmb       512
messagebuffer       rmb       512
vmgameid            rmb       8
vmvariables         rmb       256
vmflags             rmb       256
vmarguments         rmb       255
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
                    use       logic-platform.asm
help                fcc       /Usage: wbexec game-directory logic-number/
                    fcb       C$CR
                    emod
eom                 equ       *
