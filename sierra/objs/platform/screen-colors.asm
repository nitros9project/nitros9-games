* Assembly-time screen backend selection; no runtime dispatch.
                    ifne      WILDBITS
                    error     Wild Bits screen backend is not implemented
                    else
                    use       platform/coco-screen-colors.asm
                    endc
