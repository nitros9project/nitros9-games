# Shared interpreter compilation and backend dependencies for all titles.
# These title builds select CoCo. Wild Bits uses objs/wildbits.mk.
vpath %.asm ../objs

AFLAGS += -I. -I../objs

# Grouped features and common bodies are assembled in place. Track their
# complete source sets so new shared components cannot leave stale modules.
sierra mnln scrn shdw: $(wildcard ../objs/platform/coco-*.asm) \
	$(wildcard ../objs/shared/*.asm) ../objs/platform/sections.d \
	../objs/buffer-layout.d ../objs/platform/coco-buffer-layout.d

sierra mnln: ../objs/instance.d
scrn: ../objs/font-data.asm
