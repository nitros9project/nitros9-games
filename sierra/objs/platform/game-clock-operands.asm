* Assembly-time clock storage interface; no runtime dispatch.
                    ifne      WILDBITS
                    use       platform/wildbits-game-clock-operands.asm
                    else
                    use       platform/coco-game-clock-operands.asm
                    endc
