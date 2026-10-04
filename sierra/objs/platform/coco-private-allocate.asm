* CoCo loader/memory backend: private-allocate.
* Included in place; see ../../PORTABILITY.md for ownership and constraints.

SetupVirq           ldu       #$0000    start of Sierra memory area
                    ldx       #int5EE   Intercept rourtine copied to mem area
                    os9       F$Icpt    install the trap

* Attach to the vrt memory descriptor
* Attaches and verifies loaded the VI descriptor
* entry:
*      a -> access mode
*          0 = use any special device capabilities
*          1 = read only
*          2 = write only
*          3 = update (read and write)
*      x -> address of device name string
*
* exit:
*      x -> updated past device name
*      u -> address of device table entry
*
* error:
*      b  -> error code (if any)
*      cc -> carry set on error

                    lda       #$01      attach for read
                    leax      >ViDevPath+1,pcr skip the slash Load VI only
                    os9       I$Attach  make the call
                    bcs       SetupVirqRet didn't work exit
                    stu       >ViDevAddr did work save address

* Open a path to the device /VI
* entry:
*       a -> access mode (D S PE PW PR E W R)
*       x -> address of the path list
*
* exit:
*       a -> path number
*       x -> address of the last byte if the pathlist + 1
*
* error:
*       b  -> error code(if any)
*       cc -> carry set on error
*
*                            a still contains $01 read
                    leax      >ViDevPath,pcr load with device name including /
                    os9       I$Open    make the call
                    bcs       SetupVirqRet didn't work exit
                    sta       >ViPathNum did work save path #

* Allocate process+path RAM blocks

                    ldb       #SS.ARAM  $CA function code for VIRQ
                    ldx       #21       13 game blocks + 8 private engine blocks
                    os9       I$SetStt  make the call
                    bcs       SetupVirqRet abort if allocation failed
                    tfr       x,d
                    tsta                legacy MMU code handles blocks 0-255
                    bne       PrivateRamRangeErr
                    addb      #21
                    bcs       PrivateRamRangeErr
                    stb       >PrivateLimit
                    subb      #8
                    stb       >PrivateNext
                    pshs      x         save allocated RAM pointer

* Set process+path VIRQ KQ3
                    lda       >ViPathNum restore path clobbered by allocation arithmetic
                    ldb       #SS.KSet  $C8 function code for VIRQ
                    os9       I$SetStt
                    bcs       SetupVirqError
                    puls      b,a       restore A and B after KSet call
                    rts
SetupVirqError      leas      2,s       retain the real SetStat error in B
SetupVirqRet        rts                 return from SetupVirq

PrivateRamRangeErr  comb
                    ldb       #E$MemFul
                    rts
