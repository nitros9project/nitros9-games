include $(NITROS9DIR)/rules.mak

.DEFAULT_GOAL := all

include ../sierra-engine.mak
DEPENDS		= ./Makefile

DISK		= BlackCauldron.dsk
DISK_NAME	= "The Black Cauldron"

CMDS		= sierra mnln scrn shdw tocgen
MD		= $(LEVEL2)/coco3/modules
SYSGO		= $(MD)/sysgo_dd

# We make our own bootfile and kernel track
KERNEL		= $(MD)/rel_32 $(MD)/boot_1773_6ms $(MD)/krn

BOOTFILE	= $(MD)/krnp2 $(MD)/ioman $(MD)/init \
		$(MD)/rbf.mn \
		$(MD)/rb1773.dr $(MD)/ddd0_80d.dd \
		$(MD)/scf.mn $(MD)/vtio.dr $(MD)/co3hires.sb \
		$(MD)/joydrv_joy.sb $(MD)/snddrv_cc3.sb \
		$(MD)/covdg.io $(MD)/term_vdg.dt \
		$(MD)/vrn.dr $(MD)/vi.dd \
		$(MD)/clock_60hz $(MD)/clock2_soft

BOOTCMDS	= $(MD)/shell $(MD)/setime

SUPPORTFILES	= logDir object picDir sndDir viewDir vol.0 vol.1 vol.2 words.tok

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

all:	$(DISK)

run:	$(DISK)
	$(MAME_BINARY) $(MAME_MACHINE) $(MAME_FLAGS) -flop1 $(DISK)

clean:
	$(RM) $(DISK) $(ALLOBJS) $(KERNELTRACK) $(OS9BOOT) $(SIERRASHELL) *.list *.map

nitros9-files:
	$(MAKE) -C $(NITROS9DIR)/recipes/coco3/floppy MODDIR=$(MD) \
		$(addprefix $(MD)/,$(notdir $(KERNEL) $(BOOTFILE) $(SYSGO) $(BOOTCMDS)))

$(KERNELTRACK): nitros9-files
	$(MERGE) $(KERNEL) >$@

$(OS9BOOT): nitros9-files
	$(MERGE) $(BOOTFILE) >$@

$(SIERRASHELL): nitros9-files
	$(MERGE) $(BOOTCMDS) >$@

$(DISK): $(ALLOBJS) $(KERNELTRACK) $(OS9BOOT) $(SIERRASHELL)
	$(RM) $@
	$(OS9FORMAT_DS80) -q $@ -n$(DISK_NAME)
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
	$(CPL) -r ../startup tOC_40d.txt $@,.
	$(OS9RENAME) $@,tOC_40d.txt tOC.txt
	$(OS9COPY) -r $(SUPPORTFILES) $@,.
	$(MOVE) tocgen toctmp
	tocgen $@,tOC.txt $@,tOC
	$(MOVE) toctmp tocgen
