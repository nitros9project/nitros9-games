* Assembly-time platform selection.
* CoCo entry: gfx_picbuff_update, legacy module ABI.
* Wild Bits entries: PresentPicture/PresentationRelease, native private ABI.
* Callers must supply the selected state contract; these are not ABI aliases.
                    ifne      WILDBITS
                    use       platform/wildbits-presentation.asm
                    else
                    use       platform/coco-presentation.asm
                    endc
