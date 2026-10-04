# Shared interpreter compilation and backend dependencies for all titles.
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
