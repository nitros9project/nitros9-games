# Shared interpreter compilation and backend dependencies for all titles.
# sierra.asm selects the runtime composition at assembly time; these title
# builds use the CoCo branch (Wild Bits supplies -DWILDBITS=1 in wildbits.mk).
vpath %.asm ../objs

AFLAGS		+= -I. -I../objs

sierra mnln scrn shdw: ../objs/buffer-layout.d ../objs/platform/coco-buffer-layout.d

sierra mnln: ../objs/instance.d

mnln: ../objs/platform/sound-data.asm ../objs/platform/sound-code.asm \
	../objs/platform/coco-sound-data.asm ../objs/platform/coco-sound-code.asm

# Mapping backends are included in place, without runtime dispatch.
sierra: ../objs/platform/engine-switch.asm ../objs/platform/coco-engine-switch.asm \
	../objs/platform/map-snapshot.asm ../objs/platform/coco-map-snapshot.asm
mnln: ../objs/platform/logic-map.asm ../objs/platform/coco-logic-map.asm \
	../objs/platform/priority-map.asm ../objs/platform/coco-priority-map.asm
scrn: ../objs/platform/screen-map.asm ../objs/platform/coco-screen-map.asm
shdw: ../objs/platform/picture-map.asm ../objs/platform/coco-picture-map.asm

sierra: ../objs/platform/process-map.asm ../objs/platform/coco-process-map.asm
sierra: ../objs/platform/runtime-copy.asm ../objs/platform/coco-runtime-copy.asm
sierra: ../objs/platform/engine-load.asm ../objs/platform/coco-engine-load.asm
sierra: ../objs/platform/map-restore.asm ../objs/platform/coco-map-restore.asm
sierra: ../objs/platform/address-blocks.asm ../objs/platform/coco-address-blocks.asm
sierra: ../objs/platform/private-load.asm ../objs/platform/coco-private-load.asm
sierra: ../objs/platform/private-allocate.asm ../objs/platform/coco-private-allocate.asm
sierra: ../objs/platform/private-release.asm ../objs/platform/coco-private-release.asm

sierra: ../objs/platform/screen-colors.asm ../objs/platform/coco-screen-colors.asm
sierra: ../objs/platform/monitor-select.asm ../objs/platform/coco-monitor-select.asm
sierra: ../objs/platform/screen-setup.asm ../objs/platform/coco-screen-setup.asm
sierra: ../objs/platform/terminal-options.asm ../objs/platform/coco-terminal-options.asm
sierra: ../objs/platform/screen-restore.asm ../objs/platform/coco-screen-restore.asm
mnln: ../objs/platform/game-palette-data.asm ../objs/platform/coco-game-palette-data.asm
mnln: ../objs/platform/game-palette-set.asm ../objs/platform/coco-game-palette-set.asm

scrn: ../objs/font-data.asm
scrn: ../objs/platform/render-spans.asm ../objs/platform/coco-render-spans.asm
scrn: ../objs/platform/render-view.asm ../objs/platform/coco-render-view.asm
scrn: ../objs/platform/render-glyphs.asm ../objs/platform/coco-render-glyphs.asm
mnln: ../objs/platform/text-packing.asm ../objs/platform/coco-text-packing.asm

mnln: ../objs/platform/joystick-input.asm ../objs/platform/coco-joystick-input.asm
mnln: ../objs/platform/keyboard-input.asm ../objs/platform/coco-keyboard-input.asm
sierra: ../objs/platform/timer-intercept.asm ../objs/platform/coco-timer-intercept.asm
sierra: ../objs/platform/service-check.asm ../objs/platform/coco-service-check.asm
mnln: ../objs/platform/presentation.asm ../objs/platform/coco-presentation.asm
mnln: ../objs/platform/priority-address.asm ../objs/platform/coco-priority-address.asm
shdw: ../objs/platform/picture-storage.asm ../objs/platform/coco-picture-storage.asm
shdw: ../objs/platform/picture-orientation.asm ../objs/platform/coco-picture-orientation.asm

shdw: ../objs/platform/object-storage.asm ../objs/platform/coco-object-storage.asm
mnln: ../objs/platform/sound-elapsed.asm ../objs/platform/coco-sound-elapsed.asm

shdw: ../objs/shared/picture-pen.asm ../objs/shared/picture-pen-tables.asm
shdw: ../objs/shared/picture-line.asm
mnln: ../objs/shared/object-direction-tables.asm
shdw: ../objs/shared/picture-coordinates.asm
mnln: ../objs/shared/object-distance.asm
mnln: ../objs/shared/agi-command-table.asm
mnln: ../objs/shared/object-block-test.asm
mnln: ../objs/shared/divide-byte.asm ../objs/shared/object-wander.asm
mnln: ../objs/shared/object-position-test.asm
mnln: ../objs/shared/object-follow.asm ../objs/shared/object-move-direction.asm

mnln: ../objs/shared/math-commands.asm

mnln: ../objs/shared/object-view-queries.asm \
	../objs/platform/object-view-query-operands.asm \
	../objs/platform/coco-object-view-query-operands.asm

sierra: ../objs/shared/game-clock-tick.asm \
	../objs/platform/game-clock-operands.asm \
	../objs/platform/coco-game-clock-operands.asm

mnln: ../objs/shared/decimal-index.asm \
	../objs/platform/decimal-index-operands.asm \
	../objs/platform/coco-decimal-index-operands.asm

mnln: ../objs/shared/unsigned-decimal.asm \
	../objs/platform/decimal-output-operands.asm \
	../objs/platform/coco-decimal-output-operands.asm \
	../objs/shared/format-scan.asm \
	../objs/platform/format-scan-operands.asm \
	../objs/platform/coco-format-scan-operands.asm \
	../objs/shared/format-directives.asm \
	../objs/platform/format-directive-operands.asm \
	../objs/platform/coco-format-directive-operands.asm \
	../objs/shared/format-string-slot.asm \
	../objs/shared/nul-string-copy.asm \
	../objs/platform/format-string-operands.asm \
	../objs/platform/coco-format-string-operands.asm \
	../objs/platform/coco-nul-string-write.asm \
	../objs/shared/format-recursive-call.asm \
	../objs/shared/format-expansion.asm \
	../objs/platform/format-recursion-operands.asm \
	../objs/platform/coco-format-recursion-operands.asm \
	../objs/shared/agi-xor-key.asm \
	../objs/shared/xor-decrypt.asm \
	../objs/shared/object-block-state.asm \
	../objs/shared/object-unanimate.asm \
	../objs/shared/object-step-deltas.asm \
	../objs/platform/object-control-operands.asm \
	../objs/platform/coco-object-control-operands.asm \
	../objs/shared/object-field-query.asm \
	../objs/shared/object-scalar-state.asm \
	../objs/platform/object-scalar-operands.asm \
	../objs/platform/coco-object-scalar-operands.asm \
	../objs/shared/object-placement-step.asm \
	../objs/platform/object-placement-operands.asm \
	../objs/platform/coco-object-placement-operands.asm \
	../objs/shared/object-bounds.asm \
	../objs/platform/object-bounds-operands.asm \
	../objs/platform/coco-object-bounds-operands.asm \
	../objs/shared/object-collision-filter.asm \
	../objs/platform/object-collision-operands.asm \
	../objs/platform/coco-object-collision-operands.asm

mnln: ../objs/shared/dictionary-lookup.asm ../objs/platform/dictionary-operands.asm \
	../objs/platform/coco-dictionary-operands.asm

mnln: ../objs/shared/object-coordinate-step.asm ../objs/platform/coordinate-step-operands.asm \
	../objs/platform/coco-coordinate-step-operands.asm

mnln: ../objs/shared/object-coordinate-clamp.asm ../objs/platform/coordinate-clamp-operands.asm \
	../objs/platform/coco-coordinate-clamp-operands.asm

shdw: ../objs/shared/object-terrain-scan.asm ../objs/shared/object-terrain-constraints.asm \
	../objs/platform/terrain-operands.asm ../objs/platform/coco-terrain-operands.asm

mnln: ../objs/shared/object-collision-scan.asm

mnln: ../objs/shared/object-position-commit.asm ../objs/platform/position-commit-operands.asm \
	../objs/platform/coco-position-commit-operands.asm

mnln: ../objs/shared/object-target-motion.asm ../objs/platform/target-motion-operands.asm \
	../objs/platform/coco-target-motion-operands.asm

mnln: ../objs/shared/object-animation-update.asm ../objs/platform/animation-update-operands.asm

mnln: ../objs/shared/object-motion-schedule.asm ../objs/platform/motion-schedule-operands.asm
