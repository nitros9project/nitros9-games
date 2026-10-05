* Assembly-time decimal output storage/division interface.
                    ifne      WILDBITS
                    use       platform/wildbits-decimal-output-operands.asm
                    else
                    use       platform/coco-decimal-output-operands.asm
                    endc
