* CoCo memory backend: picture-map.
* Included in place to preserve code addresses and instruction timing.
* See ../../PORTABILITY.md for dependencies and current contract.

TwiddleMmu          cmpa      ShdwMmuBlock compare to shdw mem block
                    beq       TwiddleMmuDone equal ?? no work to be done move on
                    orcc      #IntMasks turn off interupts
                    sta       ShdwMmuBlock store the value passed in by a
                    lda       SierraPdBlk get sierra process descriptor map block
                    sta       GimeMmuReg map it in to $2000-$3FFF
                    ldu       Sierra2ndBlk 2nd 8K data block in Sierra
                    lda       ShdwMmuBlock load my mem block value
                    sta       ,u        save my values at address held in Sierra2ndBlk
                    stb       $02,u     save block value byte 2
                    std       GimeMmuReg map it to task 1 block 2
                    andcc     #^IntMasks restore the interupts
TwiddleMmuDone      rts                 we done
