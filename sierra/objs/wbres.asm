* Native resource-loading probe. stdout is the validated command stream.
                    nam       wbres
                    ttl       Wild Bits native AGI picture resource probe
                    use       platform/wildbits-defsfile
argdirectory        rmb       2
argnumber           rmb       2
argdigit            rmb       1
                    use       platform/wildbits-resource-data.asm
                    rmb       512               private stack beyond command buffer
size                equ       .
                    mod       eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs       /wbres/
                    fcb       1
                    use       platform/wildbits-resource-cli.asm
                    use       platform/wildbits-resource-code.asm
help                fcc       /Usage: wbres game-directory picture-number >command-file/
                    fcb       C$CR
                    emod
eom                 equ       *
                    end
