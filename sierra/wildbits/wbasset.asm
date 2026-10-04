* Native expanded logic-resource probe; reusable loader/decoder components.
                    nam       wbasset
                    use       defsfile
AGI_ASSET           equ       1
argdirectory        rmb       2
argnumber           rmb       2
argdigit            rmb       1
                    use       asset-data.asm
                    use       lzw-data.asm
                    use       resource-data.asm
assetinput          rmb       512
                    rmb       1024
size                equ       .
                    mod       eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs       /wbasset/
                    fcb       1
                    use       resource-cli.asm
                    use       resource-code.asm
                    use       lzw-code.asm
                    use       asset-code.asm
                    use       asset-write.asm
help                fcc       /Usage: wbasset game-directory logic-number >expanded-file/
                    fcb       C$CR
                    emod
eom                 equ       *
