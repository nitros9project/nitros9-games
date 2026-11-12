* X/U = two 43-byte object records; Y preserved.
* Returns A via owner StoreDistResult; DP ObjectDistanceScratch is private.
* Invisible objects return 255; visible Manhattan distance saturates at 254.
ObjectDistance      equ       *
                    lda       #$FF      default distance = 255 (max)
                    ldb       <$26,x    load first object state flags
                    bitb      #$01      test drawn/visible flag
                    beq       StoreDistResult branch if first object not visible
                    ldb       <$26,u    load second object state flags
                    bitb      #$01      test drawn/visible flag
                    beq       StoreDistResult branch if second object not visible
                    lda       <$1C,u    load second object width
                    lsra                halve width to get center offset
                    adda      $03,u     add Y to get center Y
                    ldb       <$1C,x    load first object width
                    lsrb                halve width to get center offset
                    addb      $03,x     add Y to get center Y
                    stb       <ObjectDistanceScratch    save first object center Y
                    suba      <ObjectDistanceScratch    subtract to get delta Y
                    bcc       CalcDistStoreX branch if delta is positive
                    nega                negate to get absolute delta Y
CalcDistStoreX      sta       <ObjectDistanceScratch    save absolute delta Y
                    lda       $04,u     load second object X position
                    suba      $04,x     subtract first object X
                    bcc       CalcDistAddY branch if delta X is positive
                    nega                negate to get absolute delta X
CalcDistAddY        adda      <ObjectDistanceScratch    add absolute delta Y to get Manhattan distance
                    bcs       DistMaxOut branch if sum overflowed (distance > 255)
                    cmpa      #$FF      check if distance equals max
                    bne       StoreDistResult branch if distance is not 255
DistMaxOut          lda       #$FE      cap distance at 254
