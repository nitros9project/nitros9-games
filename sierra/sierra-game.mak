include $(NITROS9DIR)/rules.mak

.DEFAULT_GOAL := all

include ../sierra-engine.mak

DEPENDS		= ./Makefile ../sierra-game.mak ../sierra-engine.mak

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

# Shared picture commands must rebuild the CoCo decoder as well.
shdw: ../objs/shared/picture-colors.asm ../objs/shared/picture-commands.asm

shdw: ../objs/shared/picture-command-table.asm

mnln: ../objs/shared/variable-commands.asm

mnln: ../objs/shared/flag-commands.asm

mnln: ../objs/platform/coco-flag-storage.asm

mnln: ../objs/shared/condition-tests.asm

mnln: ../objs/shared/agi-test-table.asm

mnln: ../objs/shared/object-flag-mask.asm ../objs/shared/object-flag-rules.asm

mnln: ../objs/shared/object-cycle-state.asm

mnln: ../objs/shared/object-motion-state.asm

mnln: ../objs/shared/object-rate-state.asm

mnln: ../objs/shared/said-match.asm

mnln: ../objs/shared/ascii-lower.asm

mnln: ../objs/shared/tokenize-string.asm ../objs/shared/find-byte.asm ../objs/shared/parser-punctuation.asm

mnln: ../objs/shared/compare-strings.asm ../objs/shared/string-punctuation.asm

mnln: ../objs/shared/object-coordinate-state.asm ../objs/shared/object-animation-state.asm
mnln: ../objs/platform/object-coordinate-operands.asm ../objs/platform/coco-object-coordinate-operands.asm

mnln: ../objs/shared/condition-flow.asm ../objs/platform/coco-condition-stream.asm

mnln: ../objs/shared/logic-executor.asm ../objs/platform/coco-logic-stream.asm

mnln: ../objs/shared/random-command.asm ../objs/platform/coco-random-operands.asm

mnln: ../objs/shared/object-motion-setup.asm ../objs/platform/coco-motion-setup.asm

mnln: ../objs/shared/inventory-commands.asm ../objs/platform/coco-inventory-operands.asm

mnln: ../objs/shared/bounded-string-copy.asm ../objs/platform/coco-string-copy-count.asm

mnln: ../objs/shared/decimal-byte.asm
