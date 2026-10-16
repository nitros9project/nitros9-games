* Private regression probe for the shared OS frame clock, not a game module.
* Default three-second calendar interval; optional 3..9-second argument.
* Writes a two-byte big-endian signal count to stdout, then unregisters.
                    use platform/wildbits-defsfile
                    org 0
ticks               rmb 2
path                rmb 1
clock               rmb 6
first               rmb 1
duration            rmb 1
                    rmb 256
size                equ .
                    mod eom,name,Prgrm+Objct,ReEnt+1,start,size
name                fcs /wbsol/
                    fcb 1
start               lda #3
                    sta duration,u
                    lda ,x
                    cmpa #'3
                    blo default
                    cmpa #'9
                    bhi default
                    suba #'0
                    sta duration,u
default             clr ticks,u
                    clr ticks+1,u
                    leax intercept,pcr
                    os9 F$Icpt
                    bcs failure
                    leax device,pcr
                    lda #UPDAT.
                    os9 I$Open
                    bcs failure
                    sta path,u
                    leax clock,u
                    os9 F$Time
                    bcs failure
                    lda clock+5,u
                    sta first,u
                    lda path,u
                    ldb #SS.SOLIRQ
                    ldx #0
                    ldy #$82
                    os9 I$SetStt
                    bcs failure
loop                ldx #2
                    os9 F$Sleep
                    leax clock,u
                    os9 F$Time
                    bcs failure
                    lda clock+5,u
                    suba first,u
                    bcc elapsed
                    adda #60
elapsed             cmpa duration,u
                    blo loop
                    lda #1
                    leax ticks,u
                    ldy #2
                    os9 I$Write
                    lda path,u
                    ldb #SS.SOLIRQ
                    ldx #0
                    ldy #0
                    os9 I$SetStt
                    lda path,u
                    os9 I$Close
                    clrb
failure             os9 F$Exit
intercept           cmpb #$82
                    bne done
                    ldd ticks,u
                    addd #1
                    std ticks,u
done                rti
device              fcc |/fSOL|
                    fcb C$CR
                    emod
eom                 equ *
