include $(NITROS9DIR)/rules.mak

vpath %.asm ../objs

AFLAGS		+= -I.
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
		$(MD)/covdg_small.io $(MD)/term_vdg.dt \
		$(MD)/vrn.dr $(MD)/vi.dd \
		$(MD)/clock_60hz $(MD)/clock2_soft

BOOTCMDS	= $(LEVEL2)/coco3/cmds/shell_21 $(LEVEL2)/coco3/cmds/date \
		$(LEVEL2)/coco3/cmds/echo $(LEVEL2)/coco3/cmds/link \
		$(LEVEL2)/coco3/cmds/setime

SUPPORTFILES	= logDir object picDir sndDir viewDir vol.0 vol.1 vol.2 words.tok

ALLOBJS		= $(CMDS)
KERNELTRACK	= kerneltrack
OS9BOOT		= OS9Boot
SIERRASHELL	= shell

.PHONY: all clean nitros9-files

all:	$(DISK)

clean:
	$(RM) $(DISK) $(ALLOBJS) $(KERNELTRACK) $(OS9BOOT) $(SIERRASHELL) *.list *.map

nitros9-files:
	$(MAKE) -C $(MD) $(notdir $(KERNEL) $(BOOTFILE) $(SYSGO))
	$(MAKE) -C $(LEVEL2)/coco3/cmds $(notdir $(BOOTCMDS))

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
