                    use       defsfile
                    use       lzw-data.asm
inputpointer        rmb       2
inputend            rmb       2
outputpointer       rmb       2
workspace           rmb       8192
size                equ       .
                    mod       eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs       /lzwtest/
start               leax      workspace,u
                    lbsr      DecodeLzw
finish              nop
                    bra       finish
LzwReadByte         pshs      x
                    ldx       inputpointer,u
                    cmpx      inputend,u
                    bhs       NoInput
                    ldb       ,x+
                    stx       inputpointer,u
                    puls      x
                    andcc     #$FE
                    rts
NoInput             puls      x
                    ldb       #E$EOF
                    orcc      #1
                    rts
LzwWriteByte        pshs      x
                    ldx       outputpointer,u
                    stb       ,x+
                    stx       outputpointer,u
                    puls      x
                    andcc     #$FE
                    rts
                    use       lzw-code.asm
                    emod
eom                 equ       *
