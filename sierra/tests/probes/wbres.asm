* Native resource-loading probe. stdout is the validated command stream.
                    nam       wbres
                    ttl       Wild Bits native AGI picture resource probe
                    use       platform/wildbits-defsfile
argdirectory        rmb       2
argnumber           rmb       2
argdigit            rmb       1
                    use platform/sections.d
PLATFORM_SECTION    set PLATFORM_WILDBITS_RESOURCE_DATA
                    use platform/wildbits-memory-resources.asm
                    rmb       512               private stack beyond command buffer
size                equ       .
                    mod       eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs       /wbres/
                    fcb       1
PLATFORM_SECTION    set PLATFORM_WILDBITS_RESOURCE_CLI
                    use platform/wildbits-memory-resources.asm
PLATFORM_SECTION    set PLATFORM_WILDBITS_RESOURCE_CODE
                    use platform/wildbits-memory-resources.asm
help                fcc       /Usage: wbres game-directory picture-number >command-file/
                    fcb       C$CR
                    emod
eom                 equ       *
                    end
