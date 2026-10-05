* Assembly-time operand/storage interface; emits no runtime dispatch.
                    ifne      WILDBITS
                    use       platform/wildbits-object-coordinate-operands.asm
                    else
                    use       platform/coco-object-coordinate-operands.asm
                    endc
