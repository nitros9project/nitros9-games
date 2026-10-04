* Assembly-time platform selection.
                    ifne      WILDBITS
                    error     Wild Bits platform backend is not implemented
                    else
                    use       platform/coco-keyboard-input.asm
                    endc
