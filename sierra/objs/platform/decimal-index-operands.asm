* Assembly-time formatter index policy; no runtime dispatch.
                    ifne      WILDBITS
                    use       platform/wildbits-decimal-index-operands.asm
                    else
                    use       platform/coco-decimal-index-operands.asm
                    endc
