* Native mapped AGI picture decoder probe, not the game interpreter.
                    nam       wbdecode
WILDBITS            equ       1
                    use       platform/wildbits-defsfile
DECODE_PICTURE      equ       1
PICTURE_BOUNDED_READ equ       1
cmd_start           equ       $F0
x_max               equ       159
y_max               equ       167
PICBUFF_WIDTH       equ       160
argdirectory        rmb       2
argnumber           rmb       2
argdigit            rmb       1
                    use       platform/wildbits-decoder-data.asm
                    use       platform/wildbits-resource-data.asm
fillstack           rmb       4096
picturestage        rmb       512
                    rmb       1024
size                equ       .
                    mod       eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs       /wbdecode/
                    fcb       1
                    use       platform/wildbits-resource-cli.asm
                    use       platform/wildbits-resource-code.asm
                    use       platform/wildbits-decoder-code.asm
                    use       platform/wildbits-decoder-lines.asm
                    use       platform/wildbits-picture-memory.asm
                    use       platform/wildbits-decoder-fill.asm
                    use       platform/wildbits-decoder-pen.asm
help                fcc       /Usage: wbdecode game-directory picture-number >combined-file/
                    fcb       C$CR
                    emod
eom                 equ       *
                    end
