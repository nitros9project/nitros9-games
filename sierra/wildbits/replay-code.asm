* Size/reset/checkpoint commands adapted from mnln's script-buffer routines.
* A record is D = operation/resource. C/error B on overflow; U retained.
ReplayInitialize    ldu       <resourcebase
                    ldb       vmarguments,u
                    stb       <replaylimit
                    clr       <replayused
                    clr       <replayused+1
                    clr       <replaycheckpoint
                    clr       <replaycheckpoint+1
                    clrb
                    rts
ReplayPush          pshs      d,x
                    tst       <replaylimit
                    beq       ReplayDisabled
                    clra
                    ldb       <replaylimit
                    lslb
                    rola
                    cmpd      <replayused
                    bls       ReplayOverflow
                    ldu       <resourcebase
                    leax      replaybuffer,u
                    ldd       <replayused
                    leax      d,x
                    ldd       ,s
                    std       ,x
                    ldd       <replayused
                    addd      #2
                    std       <replayused
                    puls      d,x
                    andcc     #$FE
                    rts
ReplayDisabled      puls      d,x
                    andcc     #$FE
                    rts
ReplayOverflow      puls      d,x
                    ldb       #E$MemFul
                    orcc      #1
                    rts
ReplaySaveCheckpoint    ldd       <replayused
                    std       <replaycheckpoint
                    clrb
                    rts
ReplayRestore       ldd       <replaycheckpoint
                    cmpd      <replayused
                    bhi       ReplayInvalid
                    std       <replayused
                    clrb
                    rts
ReplayInvalid       ldb       #E$BMode
                    orcc      #1
                    rts
