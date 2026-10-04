* Assembly-time memory backend selection; no runtime dispatch.
                    ifne      WILDBITS
                    error     Wild Bits memory backend is not implemented
                    else
                    use       platform/coco-logic-map.asm
                    endc
