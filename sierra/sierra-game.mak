include $(NITROS9DIR)/rules.mak

.DEFAULT_GOAL := all

vpath %.asm ../objs

AFLAGS		+= -I. -I../objs
DEPENDS		= ./Makefile ../sierra-game.mak

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

CMDS		= sierra mnln scrn shdw tocgen
MD		= $(LEVEL2)/coco3/modules
SYSGO		= $(MD)/sysgo_dd

ifeq ($(TRACKS),40)
DISK_FORMAT	= $(OS9FORMAT_DS40)
DISK_DESCRIPTOR = ddd0_40d.dd
else ifeq ($(TRACKS),80)
DISK_FORMAT	= $(OS9FORMAT_DS80)
DISK_DESCRIPTOR = ddd0_80d.dd
else
$(error TRACKS must be 40 or 80)
endif

KERNEL		= $(MD)/rel_32 $(MD)/boot_1773_6ms $(MD)/krn

BOOTFILE	= $(MD)/krnp2 $(MD)/ioman $(MD)/init \
		$(MD)/rbf.mn \
		$(MD)/rb1773.dr $(MD)/$(DISK_DESCRIPTOR) \
		$(MD)/scf.mn $(MD)/vtio.dr $(MD)/co3hires.sb \
		$(MD)/joydrv_joy.sb $(MD)/snddrv_cc3.sb \
		$(MD)/covdg.io $(MD)/term_vdg.dt \
		$(MD)/vrn.dr $(MD)/vi.dd \
		$(MD)/clock_60hz $(MD)/clock2_soft

BOOTCMDS	= $(MD)/shell $(MD)/setime

STARTUP		?= ../startup
DISKS		= $(strip $(DISK1) $(DISK2) $(DISK3))
ALLOBJS		= $(CMDS)
KERNELTRACK	= kerneltrack
OS9BOOT		= OS9Boot
SIERRASHELL	= shell

MAME_BINARY	?= mame
MAME_MACHINE	?= coco3
MAME_FLAGS	?= -rompath $(MAME_ROM_PATH) -window -nothrottle -skip_gameinfo \
		-autoboot_delay 5 -autoboot_command "DOS\n" \
		-ext fdc -ext:fdc:wd17xx:0 525qd

.PHONY: all clean nitros9-files run

all:	$(DISKS)

run:	$(DISKS)
	$(MAME_BINARY) $(MAME_MACHINE) $(MAME_FLAGS) \
		-flop1 $(DISK1) $(if $(DISK2),-flop2 $(DISK2))

clean:
	$(RM) $(DISKS) $(ALLOBJS) $(KERNELTRACK) $(OS9BOOT) $(SIERRASHELL) \
		toctmp *.list *.map

nitros9-files:
	$(MAKE) -C $(NITROS9DIR)/recipes/coco3/floppy MODDIR=$(MD) \
		$(addprefix $(MD)/,$(notdir $(KERNEL) $(BOOTFILE) $(SYSGO) $(BOOTCMDS)))

$(KERNELTRACK): nitros9-files
	$(MERGE) $(KERNEL) >$@

$(OS9BOOT): nitros9-files
	$(MERGE) $(BOOTFILE) >$@

$(SIERRASHELL): nitros9-files
	$(MERGE) $(BOOTCMDS) >$@

$(DISK1): $(DEPENDS) $(ALLOBJS) $(KERNELTRACK) $(OS9BOOT) $(SIERRASHELL) \
		$(STARTUP) $(TOC_INPUT) $(SUPPORTFILES1)
	$(RM) $@
	$(DISK_FORMAT) -q $@ -n$(DISK1_NAME)
	$(OS9GEN) $@ -b=$(OS9BOOT) -t=$(KERNELTRACK)
	$(RM) $(OS9BOOT) $(KERNELTRACK)
	$(OS9COPY) $(SYSGO) $@,sysgo
	$(OS9ATTR_EXEC) $@,sysgo
	$(MAKDIR) $@,CMDS
	$(OS9COPY) -r $(SIERRASHELL) $@,CMDS/shell
	$(OS9ATTR_EXEC) $@,CMDS/shell
	$(OS9COPY) -r $(CMDS) $@,CMDS
	$(OS9ATTR_EXEC) $(foreach file,$(CMDS),$@,CMDS/$(file))
	$(OS9RENAME) $@,CMDS/sierra AutoEx
ifneq ($(strip $(STARTUP)),)
	$(CPL) -r $(STARTUP) $@,startup
endif
	$(CPL) -r $(TOC_INPUT) $@,tOC.txt
	$(OS9COPY) -r $(SUPPORTFILES1) $@,.
	$(MOVE) tocgen toctmp
	tocgen $@,tOC.txt $@,tOC
	$(MOVE) toctmp tocgen

ifneq ($(strip $(DISK2)),)
$(DISK2): $(DEPENDS) $(SUPPORTFILES2)
	$(RM) $@
	$(DISK_FORMAT) -q $@ -n$(DISK2_NAME)
	$(OS9COPY) -r $(SUPPORTFILES2) $@,.
endif

ifneq ($(strip $(DISK3)),)
$(DISK3): $(DEPENDS) $(SUPPORTFILES3)
	$(RM) $@
	$(DISK_FORMAT) -q $@ -n$(DISK3_NAME)
	$(OS9COPY) -r $(SUPPORTFILES3) $@,.
endif
