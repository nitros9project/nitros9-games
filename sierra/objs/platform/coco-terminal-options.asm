* CoCo screen backend: terminal-options.
* Included in place; see ../../PORTABILITY.md for the current contract.

DisableKbdInt       leas      <-$20,s   Make temp buffer to hold PD.OPT data
                    lda       #StdIn    $00 Get 32 byte PD.OPT from Std In
                    ldb       #SS.OPT   $00
                    leax      ,s        point to our temp buffer
                    os9       I$GetStt  make the call
                    bcs       SetOptsDone error goto exit sub

* NOTE: make sure following lines assemble into 5 bit, not 8 bit
*       These appear to be loading the  echo EOF, INT and QUIT with
*       null values and saving the original ones back to vars
*       since L0115 - L0118 were initialized with $00

                    lda       >EchoSave load saved echo value (initially 0)
                    ldb       PD.EKO-PD.OPT,x Get echo option
                    sta       PD.EKO-PD.OPT,x change echo option no echo
                    stb       >EchoSave Save original echo option

                    lda       >EofSave load saved EOF char value
                    ldb       PD.EOF-PD.OPT,x Change EOF char
                    sta       PD.EOF-PD.OPT,x disable EOF character
                    stb       >EofSave save original EOF character

                    lda       >IntSave load saved interrupt char value
                    ldb       <PD.INT-PD.OPT,x Change INTerrupt char (normally CTRL-C)
                    sta       <PD.INT-PD.OPT,x disable interrupt character
                    stb       >IntSave save original interrupt character

                    lda       >QuitSave load saved quit char value
                    ldb       <PD.QUT-PD.OPT,x Change QUIT char (normally CTRL-E)
                    sta       <PD.QUT-PD.OPT,x disable quit character
                    stb       >QuitSave save original quit character

*  set current options packet
*  SetStat Function Code $00
*          Writes the options section of the path descriptor
*          from the 32 byte area pointed to by reg X`
* entry:
*       a -> path number
*       b -> function code $00 (SS.OPT)
*       x -> address holding the status packet
*
* error:
*       CC -> Carry set on error
*       b  -> error code (if any)
*

*                                x is still pointing to our temp buff
                    lda       #StdIn    $00 Set VDG screen to new options
                    ldb       #SS.OPT   $00
                    os9       I$SetStt  set them to be our new values

SetOptsDone         leas      <$20,s    Eat temp stack & return
                    rts                 return from DisableKbdInt
