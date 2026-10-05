* Native expanded logic-resource probe; reusable loader/decoder components.
                    nam       wbasset
                    use       platform/wildbits-defsfile
AGI_ASSET           equ       1
argdirectory        rmb       2
argnumber           rmb       2
argdigit            rmb       1
                    use       platform/wildbits-asset-data.asm
                    use       platform/wildbits-lzw-data.asm
                    use       platform/wildbits-resource-data.asm
assetinput          rmb       512
                    rmb       1024
size                equ       .
                    mod       eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs       /wbasset/
                    fcb       1
                    use       platform/wildbits-resource-cli.asm
                    use       platform/wildbits-resource-code.asm
                    use       platform/wildbits-lzw-code.asm
                    use       platform/wildbits-asset-code.asm
                    use       platform/wildbits-asset-write.asm
help                fcc       /Usage: wbasset game-directory logic-number >expanded-file/
                    fcb       C$CR
                    emod
eom                 equ       *
