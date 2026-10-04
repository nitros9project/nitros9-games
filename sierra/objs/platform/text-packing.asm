* Assembly-time renderer selection; no per-pixel dispatch.
                    ifne      WILDBITS
                    error     Wild Bits renderer backend is not implemented
                    else
                    use       platform/coco-text-packing.asm
                    endc
