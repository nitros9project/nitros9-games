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
