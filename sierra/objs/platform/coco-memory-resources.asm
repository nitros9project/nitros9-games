* coco-memory-resources feature: code and related private state.
* Named layout sections preserve existing module and private-data addresses.

                    ifeq PLATFORM_SECTION-PLATFORM_COCO_ADDRESS_BLOCKS
* ===== coco-address-blocks =====
* CoCo loader/memory backend: address-blocks.
* Included in place; see ../../PORTABILITY.md for ownership and constraints.

TwiddleAddr         tfr       x,d       Move address to D
*         exg   a,b          Swap MSB/LSB
*         lsrb               Divide MSB by 32 (calculate 8k block # in proc map)
*         lsrb
*         lsrb
*         lsrb
*         lsrb
*         pshs  b            Save block # in process map
*         ldu   #$FFA8       Point to start of user DAT image
*         lda   b,u
                    ldb       #8        hi_byte × 8 / 256 = 8K block index in A
                    mul                 compute block index from address high byte
                    pshs      a         save block index (0-7)
                    ldu       #mmubuf+8 point to task-1 physical MMU block table
                    lda       a,u       get MMU value
                    ldb       ,s        reload block index from stack
                    incb                index of next adjacent block
                    andb      #$07      wrap within 8 task-1 slots
                    ldb       b,u       read physical block # of adjacent slot
                    tfr       d,u       U = both physical block numbers
                    puls      a         restore block index
                    rts                 return: A=block index, U=physical block pair

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_ENGINE_LOAD
* ===== coco-engine-load =====
* CoCo loader/memory backend: engine-load.
* Included in place; see ../../PORTABILITY.md for ownership and constraints.

LoadModules         lda       >MultitaskFlag
                    sta       >MultitaskFlagCopy
                    ldb       >PrivateNext
                    subb      #13       original heap allocation begins 13 blocks earlier
                    tfr       b,a       don't see what's going on here
                    incb                make B one higher than A for block pair
                    std       <BlkMapLow but we save off a bunch of values

                    addd      #$0202    advance A and B by 2 for next block pair
                    std       <BlkMapHigh save high block map pair

                    addd      #$0202    advance again for task-1 slots
                    sta       <PathTable save path table index
                    std       <MmuTask1Blk2 init task-1 MMU block slots 2-3
                    std       <MmuTask1Blk4 init task-1 MMU block slots 4-5

                    ldu       #$001A    remap table offset for Shdw
                    stu       <ShdwRemap store Shdw remap offset
                    leax      >ShdwModName,pcr shdw
                    lbsr      NMLoadModule NMLoads named module
                    bcs       LoadModulesRet return on error

                    ldu       #$0012    remap table offset for Scrn
                    stu       <ScrnRemap store Scrn remap offset
                    leax      >ScrnModName,pcr scrn
                    lbsr      NMLoadModule NMLoads named module
                    bcs       LoadModulesRet return on error

                    ldu       #$000A    remap table offset for MnLn
                    stu       <MnlnRemap store MnLn remap offset
                    leax      >MnlnModName,pcr mnln
                    lbsr      NMLoadModule NMLoads named module

                    leau      >$2000,u  advance past module header to entry vectors
                    stu       <EntryTable save entry table address for MmuSwitch
LoadModulesRet      rts                 return from LoadModules

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_ENGINE_SWITCH
* ===== coco-engine-switch =====
* CoCo memory backend: engine-switch.
* Included in place to preserve code addresses and instruction timing.
* See ../../PORTABILITY.md for dependencies and current contract.

MmuSwitch           ldd       ,s++      load d with current stack pointer and bump it
*                         from mnln we come in with $4040
                    std       <CallerSp save the calling stack pointer in CallerSp
                    orcc      #IntMasks mask the interrupts
                    lda       <SierraPdBlk load Sierra's process descriptor block #
                    sta       ,x        x is loaded with value from ShdwRemap in mnln
                    sta       >$FFA9    task 1 block 2 x2000 - x3FFF
                    ldu       <Sierra2ndBlk point to Sierra's DAT image in process descriptor
                    lda       $06,x     get calling module's MMU block 6 entry
                    sta       MmuTask1Blk2,u save in Sierra's task-1 map slot 2
                    sta       >$FFAF    task 1 block 8 xE000 - xFFFF
                    lda       $05,x     get calling module's MMU block 5 entry
                    sta       MmuTask1Blk0,u save in Sierra's task-1 map slot 0
                    sta       >$FFAE    task 1 block 7 xC000 - xDFFF
                    lda       $04,x     get calling module's MMU block 4 entry
                    sta       MmuSaveTmp,u save to MMU scratch slot
                    sta       >$FFAD    task 1 block 6 xA000 - xBFFF
                    lda       $03,x     get calling module's MMU block 3 entry
                    sta       ScrEndAddr,u save to ScrEndAddr slot
                    sta       >$FFAC    task 1 block 5 x8000 - x9FFF
                    lda       $02,x     get calling module's MMU block 2 entry
                    sta       ScrStartAddr,u save to ScrStartAddr slot
                    sta       >$FFAB    task 1 block 4 x6000 - x7FFF
                    andcc     #^IntMasks unmask interrupts

                    lda       $07,x     get dispatch index from remap table
                    ldu       <EntryTable point to module entry vector table
                    adda      MmuTask1Blk0,u compute entry vector offset
                    jsr       a,u       dispatch to target module entry point

                    orcc      #IntMasks disable interrupts for MMU restore
                    lda       <SierraPdBlk Sierra's process descriptor block #
                    sta       >$FFA9    map Sierra's PD block into $2000
                    ldu       <Sierra2ndBlk point to Sierra's DAT image
                    lda       <MmuTask1Blk6 saved task-1 block 6 value
                    sta       MmuTask1Blk2,u restore DAT image entry for block 2
                    sta       >$FFAF    restore GIME MMU slot 7 (xE000)
                    lda       <MmuTask1Blk5 saved task-1 block 5 value
                    sta       MmuTask1Blk0,u restore DAT image entry for block 0
                    sta       >$FFAE    restore GIME MMU slot 6 (xC000)
                    lda       <MmuTask1Blk4 saved task-1 block 4 value
                    sta       MmuSaveTmp,u restore scratch slot
                    sta       >$FFAD    restore GIME MMU slot 5 (xA000)
                    lda       <MmuTask1Blk3 saved task-1 block 3 value
                    sta       ScrEndAddr,u restore ScrEndAddr slot
                    sta       >$FFAC    restore GIME MMU slot 4 (x8000)
                    lda       <MmuTask1Blk1 saved task-1 block 1 value
                    sta       MmuBlk2Orig,u restore MmuBlk2Orig slot
                    sta       >$FFAA    restore GIME MMU slot 2 (x4000)
                    lda       <MmuTask1Blk0 saved task-1 block 0 value
                    sta       ,u        restore DAT image task-1 slot 0
                    sta       >$FFA9    restore GIME MMU slot 1 (x2000)
                    andcc     #^IntMasks re-enable interrupts

                    jmp       [>$002A]  jump through CallerSp to restore caller

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_MAP_RESTORE
* ===== coco-map-restore =====
* CoCo loader/memory backend: map-restore.
* Included in place; see ../../PORTABILITY.md for ownership and constraints.

RestoreMmu          tst       >ProcMapReady
                    beq       RestoreMmuRet
                    clr       >ProcMapReady
                    orcc      #IntMasks Shut off interrupts
                    lda       <SierraPdBlk get MMU Block #
                    sta       >$FFA9    Restore original block 0 onto MMU
                    ldx       <Sierra2ndBlk reload Sierra DAT image pointer
                    ldd       >SierraMmuBlk3 Origanl 3rd block of MMU
                    std       1,x       restore 3rd block in Sierra's DAT map
                    stb       >$FFAA    Restore original block 1 onto MMU
                    ldd       >SierraMmuBlk2 Original 2nd block of MMU
                    std       -1,x      restore 2nd block in Sierra's DAT map
                    stb       >$FFA9    Restore block 0 again
                    andcc     #^IntMasks Turn interrupts back on

RestoreMmuRet       rts                 return from RestoreMmu

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_MAP_SNAPSHOT
* ===== coco-map-snapshot =====
* CoCo memory backend: map-snapshot.
* Included in place to preserve code addresses and instruction timing.
* See ../../PORTABILITY.md for dependencies and current contract.

mmuini1             lbsr      mmuini2
                    pshs      cc,d,x,y
                    orcc      #IntMasks
                    lda       >mmubuf+9
                    pshs      a
                    clr       >$FFA9
                    ldx       >D.SysDAT+$2000
                    leax      $2000,x    the system descriptor is in system block 0
                    ldy       #mmubuf
                    ldb       #8
m2lup               lda       1,x       low byte of the physical block number
                    sta       ,y+
                    leax      2,x
                    decb
                    bne       m2lup
                    puls      a
                    sta       >$FFA9
                    puls      cc,d,x,y,pc
* Get $FFA8-$FFAF
mmuini2             pshs      cc,x,y    save registers across system calls
                    orcc      #$50      disable interrupts
                    os9       F$ID      get our ID#
                    ldx       #gprbuf point to process descriptor buffer
                    os9       F$GPrDsc  get our process descriptor
                    leay      $41,x     point to our mmu block values
                    ldx       #mmubuf+8 destination: task-1 MMU snapshot buffer
                    ldb       #8        copy 8 MMU block entries
mloop               lda       ,y++      read MMU value from process descriptor
                    sta       ,x+       store block number and advance
                    decb                decrement copy count
                    bne       mloop     loop until all 8 copied
                    puls      cc,x,y,pc restore registers and return

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_PRIORITY_MAP
* ===== coco-priority-map =====
* CoCo memory backend: priority-map.
* Included in place to preserve code addresses and instruction timing.
* See ../../PORTABILITY.md for dependencies and current contract.

MapShdwPage         orcc      #$50      disable interrupts for MMU access
                    lda       >$FFA9    read current MMU slot 9
                    ldb       <$0042    load shadow page number
                    stb       >$FFA9    map shadow page to slot 9
                    ldx       <$0043    load MMU control ptr
                    ldb       <$005F    load base priority page
                    addb      #$08      advance 8 pages into shadow
                    stb       $04,x     update MMU slot 4
                    stb       >$FFAB    write to MMU hardware
                    sta       >$FFA9    restore original slot 9
                    andcc     #$AF      re-enable interrupts
                    rts

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_PRIVATE_ALLOCATE
* ===== coco-private-allocate =====
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

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_PRIVATE_LOAD
* ===== coco-private-load =====
* CoCo loader/memory backend: private-load.
* Included in place; see ../../PORTABILITY.md for ownership and constraints.

NMLoadModule        leas      -10,s
                    stu       ,s        remap-table base
                    stx       2,s       module name
                    lda       #Prgrm+Objct
                    os9       F$Link
                    bcc       PrivateLinked
                    ldx       2,s
                    lda       #Prgrm+Objct
                    os9       F$Load
                    bcs       PrivateLoadRet
PrivateLinked       stu       6,s
                    tfr       u,d
                    addd      M$Size,u
                    bcs       PrivateBadSize
                    subd      #1
                    bcs       PrivateBadSize
                    anda      #$E0
                    clrb
                    std       8,s       last occupied source page
                    cmpd      #$C000    relocated code must end below the I/O page
                    bhi       PrivateBadSize
                    tfr       u,d
                    anda      #$E0
                    clrb
                    cmpd      #$6000    $4000 is the private copy window
                    blo       PrivateBadSize
                    std       4,s       first occupied source page
PrivatePageLoop     lda       >PrivateNext
                    cmpa      >PrivateLimit
                    bhs       PrivateBadSize
                    ldd       4,s
                    ldb       #8
                    mul                 A = source logical slot
                    ldx       ,s
                    leax      a,x
                    lda       >PrivateNext
                    sta       ,x        save private page in the runtime remap table
                    ldx       4,s
                    lbsr      CopyPrivatePage
                    inc       >PrivateNext
                    ldd       4,s
                    cmpd      8,s
                    beq       PrivateCopyDone
                    addd      #$2000
                    std       4,s
                    bra       PrivatePageLoop
PrivateCopyDone     ldu       6,s
                    os9       F$UnLink  releases our template reference and mappings
                    bra       PrivateLoadRet
PrivateBadSize      ldu       6,s
                    os9       F$UnLink
                    comb
                    ldb       #E$MemFul
PrivateLoadRet      leas      10,s
                    rts

* X=source page, A=private destination block. The $4000 data alias is
* borrowed only while interrupts are masked; the process DAT image is
* unchanged and no system calls occur before the hardware map is restored.
CopyPrivatePage     pshs      cc,d,x,y,u
                    orcc      #IntMasks
                    ldb       <MmuBlk2Orig the copy window normally aliases private data
                    pshs      b
                    sta       >$FFAA
                    ldu       #CocoCopyWindow
                    ldy       #CocoCopyWords
PrivateWordLoop     ldd       ,x++
                    std       ,u++
                    leay      -1,y
                    bne       PrivateWordLoop
                    puls      b
                    stb       >$FFAA
                    puls      cc,d,x,y,u,pc

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_PRIVATE_RELEASE
* ===== coco-private-release =====
* CoCo loader/memory backend: private-release.
* Included in place; see ../../PORTABILITY.md for ownership and constraints.

CloseVirqPath       lda       >ViPathNum load path number to /VI device
                    beq       DetachVi  no path open check for device table addr
                    ldb       #SS.KClr  $C9 Clear KQ3 VIRQ
                    os9       I$SetStt  make the call
                    ldb       #SS.DRAM  $CB deallocate the ram
                    os9       I$SetStt  make the call
                    os9       I$Close   close the path to /VI
                    clr       >ViPathNum
DetachVi            ldu       >ViDevAddr load device table address for VI
                    beq       CloseVirqRet don't have one leave now
                    os9       I$Detach  else detach it
                    ldd       #0
                    std       >ViDevAddr
CloseVirqRet        rts                 return from CloseVirqPath

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_PROCESS_MAP
* ===== coco-process-map =====
* CoCo loader/memory backend: process-map.
* Included in place; see ../../PORTABILITY.md for ownership and constraints.

SetupProcMap        os9       F$ID
                    sta       >OwnProcessId
                    orcc      #IntMasks Shut interrupts off
                    ldx       #$0002    ???
                    stx       <BlockRef save block reference pair

*        As per above NOTE, should postpone this until we have DAT image
*        available for Sierra process

*         lda   >$FFAF         Get MMU block # SIERRA is in
                    lda       >mmubuf+$0F read task-0 MMU slot 15 (Sierra's block)
                    sta       <MmuSaveTmp Save it
                    clr       >$FFA9    Map system block 0 into $2000-$3FFF
                    ldx       >D.PrcDBT+$2000
                    leax      $2000,x   process-pointer table resides in system block 0
                    ldb       >OwnProcessId
                    lda       b,x       process descriptors are aligned to $200
                    clrb
                    tfr       d,y       retain the full system descriptor address
                    anda      #$1F      Keep non-MMU dependent address

* NOTE: OFFSET IS STUPID, SHOULD USE EVEN BYTE SO LDD'S BELOW
*       CAN USE FASTER LDD ,X INSTEAD OF OFFSET,X

                    addd      #$2000+P$DATImg+3 Set up ptr for what we want out of it
                    std       <Sierra2ndBlk Save it
                    tfr       y,d
                    tfr       a,b       MSB of our descriptor address
                    andb      #$E0      Calculate which 8K block within
*                                 system task it's in
*         lsrb
*         lsrb
*         lsrb
*         lsrb
*         lsrb
                    lda       #8        hi_byte × 8 / 256 = 8K block index
                    mul                 compute MMU block offset for this address

* NOTE: HAVE TO CHANGE THIS TO GET BLOCK #'S FROM SYSTEM DAT IMAGE,
*       NOT RAW GIME REGS (TO WORK WITH >512K MACHINES)
*         ldx   #$FFA0       Point to base of System task DAT register set block 0 task 0
                    ldx       #mmubuf point to task-0 physical MMU block table
*         lda   b,x          Get block # that has process desc. for SIERRA
                    lda       a,x       read block # at computed offset
                    sta       <SierraPdBlk Save it
                    sta       >$FFA9    Map in block with process dsc. to $2000-$3FFF
                    ldx       <Sierra2ndBlk Get offset to 2nd 8K block in DAT map for SIERRA
                    ldd       -1,x      Get MMU block # of current 2nd 8k block in SIERRA
                    std       >SierraMmuBlk2 Save it
                    ldd       1,x       Get MMU block # of current 3rd 8k block in SIERRA
                    std       >SierraMmuBlk3 Save it
                    ldd       -3,x      Get data area block 3 from sierra (1st block)
                    std       -1,x      Move 8k data area to 2nd block
                    std       1,x       And to 3rd block
                    tfr       b,a       D=Raw MMU block # for both

* HAVE TO CHANGE TO ALLOW FOR DISTO DAT EXTENSION
                    std       >$FFA9    Map data area block into both blocks 2&3
                    std       <MmuBlk2Orig Save both block #'s
                    inc       >ProcMapReady
                    andcc     #^IntMasks Turn interrupts back on
                    rts                 return from SetupProcMap

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_RUNTIME_COPY
* ===== coco-runtime-copy =====
* CoCo loader/memory backend: runtime-copy.
* Included in place; see ../../PORTABILITY.md for ownership and constraints.

CopySubsToData      leax      MmuSwitchEnd,pcr load end-address of MmuSwitch routine
                    pshs      x         save end pointer on stack
                    leax      >MmuSwitch,pc Point to routine
*         ldu   #$0659      Point to place in data area to copy it
                    ldu       #sub659   point to data-area slot for MmuSwitch copy
CopySub1Loop        lda       ,x+       Copy routine
                    sta       ,u+       write byte to data area and advance
                    cmpx      ,s        Done whole routine yet?
                    blo       CopySub1Loop No, keep going

* get next routine interrupt intecept routine
                    leax      >CloseVirqPath,pcr point to end of routine
                    stx       ,s        save pointer
                    leax      >SigIntercept,pcr point to routine
                    ldu       #int5EE   point to place in data area to copy it
CopySub2Loop        lda       ,x+       copy routine
                    sta       ,u+       write byte to data area and advance
                    cmpx      ,s        Done whole routine yet?
                    blo       CopySub2Loop No, keep going
*         leas  $02,s        clean up stack
*         rts                return
                    puls      x,pc      restore X and return (clean stack)

                    else
                    ifeq PLATFORM_SECTION-PLATFORM_COCO_SERVICE_CHECK
* ===== coco-service-check =====
* CoCo platform boundary: service-check.
* Included in place; see ../../PORTABILITY.md.

CheckInstanceServices lda     #StdIn
                    ldb       #SS.DevNm
                    ldx       #gprbuf
                    os9       I$GetStt
                    bcs       InstanceServiceRet
                    lda       #StdOut
                    ldb       #SS.DevNm
                    ldx       #gprbuf+32
                    os9       I$GetStt
                    bcs       InstanceServiceRet
                    ldx       #gprbuf
                    ldy       #gprbuf+32
                    ldb       #32
InstanceNameLoop    lda       ,x+
                    cmpa      ,y+
                    bne       InstanceServiceBad
                    tsta
                    beq       InstanceNamesMatch
                    bmi       InstanceNamesMatch
                    decb
                    bne       InstanceNameLoop
InstanceServiceBad  comb
                    ldb       #E$IllArg
                    rts
InstanceNamesMatch  lda       #StdOut
                    ldb       #SS.AScrn
                    os9       I$GetStt  query the ownership-aware application-screen ABI
                    bcs       InstanceServiceRet
                    cmpx      #2
                    bcc       InstanceServiceOK
                    comb
                    ldb       #E$UnkSvc
InstanceServiceRet  rts
InstanceServiceOK   clrb
                    rts

                    else
                    error Unknown platform feature section
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
                    endc
