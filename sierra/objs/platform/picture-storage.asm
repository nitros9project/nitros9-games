* Assembly-time platform selection.
* Shared line/pen entry: SbuffPlot uses PosInitX/Y and DrawColor/Mask in DP.
* Wild Bits preserves D,X,Y,U and reports mapped-access errors in decodeerror.
* CoCo retains its contiguous-buffer pointer result and optimized span loops.
                    ifne      WILDBITS
                    use       platform/wildbits-picture-storage.asm
                    else
                    use       platform/coco-picture-storage.asm
                    endc
