* Assembly-time platform selection.
                    ifne      WILDBITS
                    error     Wild Bits platform backend is not implemented
                    else
                    use       platform/coco-priority-address.asm
                    endc
