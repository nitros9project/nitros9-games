* Assembly-time sound backend selection; emits no dispatch instructions.
* Each owner supplies its backend state/entry-point contract.
                    ifne      WILDBITS
                    use       platform/wildbits-sound-code.asm
                    else
                    use       platform/coco-sound-code.asm
                    endc
