* Twenty-one bits track eight-pixel bands of the combined AGI picture.
* Mark both erased footprints and newly painted footprints. First pictures
* and modal restoration force all bands; failed presentations retain damage.
GameDamageAll       lda       #$FF
                    sta       <gamepresentdirty
                    sta       <gamepresentdirty+1
                    sta       <gamepresentdirty+2
                    rts

* U=clipped saved rectangle (record bytes 6..9). Preserve caller registers.
GameDamageSprite    pshs      d,x,y,u
                    ldb       9,u
                    beq       DamageReturn
                    addb      7,u
                    decb
                    lsrb
                    lsrb
                    lsrb
                    pshs      b
                    lda       7,u
                    lsra
                    lsra
                    lsra
DamageBand          tfr       a,b
                    andb      #7
                    leax      DamageMasks,pcr
                    ldb       b,x
                    pshs      b
                    tfr       a,b
                    lsrb
                    lsrb
                    lsrb
                    ldx       <dbase
                    leax      gamepresentdirty,x
                    leax      b,x
                    ldb       ,x
                    orb       ,s+
                    stb       ,x
                    cmpa      ,s
                    beq       DamageMarked
                    inca
                    bra       DamageBand
DamageMarked        leas      1,s
DamageReturn        puls      d,x,y,u,pc

* A=band index; return zero flag set if no repaint is needed.
GameDamageTest      tfr       a,b
                    andb      #7
                    leax      DamageMasks,pcr
                    ldb       b,x
                    pshs      b
                    lsra
                    lsra
                    lsra
                    ldx       <dbase
                    leax      gamepresentdirty,x
                    lda       a,x
                    anda      ,s+
                    rts
DamageMasks         fcb       1,2,4,8,16,32,64,128
