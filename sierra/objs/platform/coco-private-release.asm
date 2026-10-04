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
