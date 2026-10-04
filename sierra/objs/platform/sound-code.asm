* Assembly-time sound backend selection; emits no dispatch instructions.
* WILDBITS is currently unsupported: never silently emit CoCo PIA access.
                    ifne      WILDBITS
                    error     Wild Bits sound backend is not implemented
                    else
                    use       platform/coco-sound-code.asm
                    endc
