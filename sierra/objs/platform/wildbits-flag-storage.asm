* Native flag storage adapter. Index in A; U is the process-private base.
SetFlag             tfr       a,b
                    leax      vmflags,u
                    abx
                    lda       #1
                    sta       ,x
                    rts
ClearFlag           tfr       a,b
                    leax      vmflags,u
                    abx
                    clr       ,x
                    rts
ToggleFlag          tfr       a,b
                    leax      vmflags,u
                    abx
                    lda       ,x
                    eora      #1
                    sta       ,x
                    rts

