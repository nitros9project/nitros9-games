# Shared interpreter compilation and backend dependencies for all titles.
# sierra.asm selects the runtime composition at assembly time; these title
# builds use the CoCo branch (Wild Bits supplies -DWILDBITS=1 in wildbits.mk).
vpath %.asm ../objs

AFLAGS		+= -I. -I../objs

sierra mnln scrn shdw: ../objs/buffer-layout.d ../objs/platform/coco-buffer-layout.d

sierra mnln: ../objs/instance.d

mnln: ../objs/platform/sections.d \
	../objs/platform/coco-audio.asm

# Mapping backends are included in place, without runtime dispatch.
sierra: ../objs/platform/sections.d \
	../objs/platform/coco-memory-resources.asm
mnln: ../objs/platform/coco-logic.asm \
	../objs/platform/coco-memory-resources.asm
scrn: ../objs/platform/sections.d ../objs/platform/coco-graphics.asm
shdw: ../objs/platform/sections.d ../objs/platform/coco-graphics.asm


sierra: ../objs/platform/coco-graphics.asm
sierra: ../objs/platform/coco-input.asm
mnln: ../objs/platform/coco-graphics.asm

scrn: ../objs/font-data.asm
scrn: ../objs/platform/coco-text-ui.asm
mnln: ../objs/platform/coco-text-ui.asm

mnln: ../objs/platform/coco-input.asm
sierra: ../objs/platform/coco-timing.asm

shdw: ../objs/platform/coco-objects.asm

shdw: ../objs/shared/picture-pen.asm ../objs/shared/picture-pen-tables.asm
shdw: ../objs/shared/picture-line.asm
mnln: ../objs/shared/object-animation.asm
shdw: ../objs/shared/picture-coordinates.asm
mnln: ../objs/shared/object-distance.asm
mnln: ../objs/shared/agi-command-table.asm
mnln: ../objs/shared/object-block-test.asm
mnln: ../objs/shared/divide-byte.asm ../objs/shared/object-wander.asm
mnln: ../objs/shared/object-position-test.asm
mnln: ../objs/shared/object-follow.asm ../objs/shared/object-move-direction.asm

mnln: ../objs/shared/math-commands.asm

mnln: ../objs/shared/object-commands.asm \
	../objs/platform/coco-objects-bindings.asm

sierra: ../objs/shared/game-clock-tick.asm

mnln: ../objs/shared/decimal-index.asm \
	../objs/platform/coco-text-ui-bindings.asm

mnln: ../objs/shared/unsigned-decimal.asm \
	../objs/shared/formatter.asm \
	../objs/shared/nul-string-copy.asm \
	../objs/shared/agi-xor-key.asm \
	../objs/shared/xor-decrypt.asm \
	../objs/shared/object-step-deltas.asm \
	../objs/shared/object-placement-step.asm \
	../objs/shared/object-bounds.asm \
	../objs/shared/object-collision-filter.asm

mnln: ../objs/shared/dictionary-lookup.asm

mnln: ../objs/shared/object-motion.asm


shdw: ../objs/shared/object-terrain-scan.asm \
	../objs/shared/object-terrain-constraints.asm \
	../objs/platform/coco-objects-bindings.asm

mnln: ../objs/shared/object-collision-scan.asm




sierra mnln scrn shdw: $(wildcard ../objs/platform/*.asm) ../objs/platform/sections.d
