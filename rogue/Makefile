include $(NITROS9DIR)/rules.mak

DEPENDS		= ./Makefile

DISK		= Rogue.dsk

CMDS		= rogue
MD		= $(LEVEL2)/coco3/modules
SYSGO		= $(MD)/sysgo_dd

# We make our own bootfile and kernel track
KERNEL		= $(MD)/rel_40 $(MD)/boot_1773_6ms $(MD)/krn

BOOTFILE	= $(MD)/krnp2 $(MD)/ioman $(MD)/init \
		$(MD)/rbf.mn \
		$(MD)/rb1773.dr $(MD)/ddd0_40d.dd \
		$(MD)/scf.mn $(MD)/vtio.dr $(MD)/co3hires.sb \
		$(MD)/joydrv_joy.sb $(MD)/snddrv_cc3.sb \
		$(MD)/cogrf.io $(MD)/term_win40.dt \
		$(MD)/clock_60hz $(MD)/clock2_soft

SUPPORTFILES	= rogue.dat rogue.hlp rogue.scr rogue.chr

ALLOBJS		= $(CMDS)
KERNELTRACK	= kerneltrack
OS9BOOT		= OS9Boot

.PHONY: all clean nitros9-files showfiles showobjs

all:	$(DISK)

clean:
	$(RM) $(DISK) $(ALLOBJS) $(KERNELTRACK) $(OS9BOOT) *.list *.map

nitros9-files:
	$(MAKE) -C $(MD) $(notdir $(KERNEL) $(BOOTFILE) $(SYSGO))
	$(MAKE) -C $(LEVEL2)/coco3/cmds shell_21 grfdrv

$(KERNELTRACK): nitros9-files
	$(MERGE) $(KERNEL) >$@

$(OS9BOOT): nitros9-files
	$(MERGE) $(BOOTFILE) >$@

$(DISK): $(ALLOBJS) $(KERNELTRACK) $(OS9BOOT)
	$(RM) $@
	$(OS9FORMAT_DS40) -q $@ -n"Rogue"
	$(OS9GEN) $@ -b=$(OS9BOOT) -t=$(KERNELTRACK)
	$(RM) $(OS9BOOT) $(KERNELTRACK)
	$(OS9COPY) $(SYSGO) $@,sysgo
	$(OS9ATTR_EXEC) $@,sysgo
	$(MAKDIR) $@,CMDS
	$(OS9COPY) -r $(LEVEL2)/coco3/cmds/shell_21 $@,CMDS/shell
	$(OS9ATTR_EXEC) $@,CMDS/shell
	$(OS9COPY) -r $(LEVEL2)/coco3/cmds/grfdrv $@,CMDS/grfdrv
	$(OS9ATTR_EXEC) $@,CMDS/grfdrv
	$(OS9COPY) -r $(CMDS) $@,CMDS
	$(OS9ATTR_EXEC) $(foreach file,$(CMDS),$@,CMDS/$(file))
	$(OS9RENAME) $@,CMDS/rogue AutoEx
	$(MAKDIR) $@,ROGUE
	$(OS9COPY) -r $(SUPPORTFILES) $@,ROGUE
	$(OS9ATTR_TEXT) $(foreach file,$(SUPPORTFILES),$@,ROGUE/$(file))

showfiles:
	@$(ECHO) $(SUPPORTFILES)

showobjs:
	@$(ECHO) $(ALLOBJS)
