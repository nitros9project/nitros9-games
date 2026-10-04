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
