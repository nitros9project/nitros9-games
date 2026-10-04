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
