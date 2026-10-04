* Assembly-time loader/memory backend selection.
                    ifne      WILDBITS
                    error     Wild Bits loader backend is not implemented
                    else
                    use       platform/coco-runtime-copy.asm
                    endc
