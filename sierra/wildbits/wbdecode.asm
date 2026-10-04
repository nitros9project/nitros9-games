* Native mapped AGI picture decoder probe, not the game interpreter.
                    nam       wbdecode
                    use       defsfile
DECODE_PICTURE      equ       1
cmd_start           equ       $F0
x_max               equ       159
y_max               equ       167
PICBUFF_WIDTH       equ       160
argdirectory        rmb       2
argnumber           rmb       2
argdigit            rmb       1
                    use       decoder-data.asm
                    use       resource-data.asm
fillstack           rmb       4096
picturestage        rmb       512
                    rmb       1024
size                equ       .
                    mod       eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs       /wbdecode/
                    fcb       1
                    use       resource-cli.asm
                    use       resource-code.asm
                    use       decoder-code.asm
                    use       decoder-lines.asm
                    use       picture-memory.asm
                    use       decoder-fill.asm
                    use       decoder-pen.asm
help                fcc       /Usage: wbdecode game-directory picture-number >combined-file/
                    fcb       C$CR
                    emod
eom                 equ       *
                    end
