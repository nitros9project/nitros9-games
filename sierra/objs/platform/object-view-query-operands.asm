* Assembly-time object query operand/storage interface; no runtime dispatch.
                    ifne      WILDBITS
                    use       platform/wildbits-object-view-query-operands.asm
                    else
                    use       platform/coco-object-view-query-operands.asm
                    endc
