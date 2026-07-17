include $(NITROS9DIR)/rules.mak

DEPENDS		= ./Makefile

DSK_FLOPPY	= KoronisRift.dsk
DSK_DW		= KoronisRift_dw.dsk
DSK_DW_BECKER	= KoronisRift_becker.dsk
CMDS		= koronis
MD		= $(LEVEL2)/coco3/modules
SYSGO		= $(MD)/sysgo_dd

DSKS		= $(DSK_FLOPPY)

# We make our own bootfile and kernel track
KERNEL_FLOPPY	= $(MD)/rel_32 $(MD)/boot_1773_6ms $(MD)/krn
KERNEL_DW	= $(MD)/rel_32 $(MD)/boot_dw $(MD)/krn
KERNEL_DW_BECKER	= $(MD)/rel_32 $(MD)/boot_dw_becker $(MD)/krn
BOOTFILE_FLOPPY	= $(MD)/krnp2 $(MD)/ioman $(MD)/init \
		$(MD)/rbf.mn \
		$(MD)/rb1773.dr $(MD)/ddd0_40d.dd \
		$(MD)/scf.mn $(MD)/vtio.dr $(MD)/co3hires.sb \
		$(MD)/joydrv_joy.sb $(MD)/snddrv_cc3.sb \
		$(MD)/covdg_small.io $(MD)/term_vdg.dt \
		$(MD)/clock_60hz $(MD)/clock2_soft

BOOTFILE_DW	= $(MD)/krnp2 $(MD)/ioman $(MD)/init \
		$(MD)/rbf.mn \
		$(MD)/rbdw.dr $(MD)/dwio.sb $(MD)/ddx0.dd \
		$(MD)/scf.mn $(MD)/vtio.dr $(MD)/co3hires.sb \
		$(MD)/joydrv_joy.sb $(MD)/snddrv_cc3.sb \
		$(MD)/covdg_small.io $(MD)/term_vdg.dt \
		$(MD)/clock_60hz $(MD)/clock2_dw

BOOTFILE_DW_BECKER	= $(MD)/krnp2 $(MD)/ioman $(MD)/init \
		$(MD)/rbf.mn \
		$(MD)/rbdw.dr $(MD)/dwio_becker.sb $(MD)/ddx0.dd \
		$(MD)/scf.mn $(MD)/vtio.dr $(MD)/co3hires.sb \
		$(MD)/joydrv_joy.sb $(MD)/snddrv_cc3.sb \
		$(MD)/covdg_small.io $(MD)/term_vdg.dt \
		$(MD)/clock_60hz $(MD)/clock2_dw

SUPPORTFILES	= SAVE1 SAVE2 crobot2.c ctitle.c korvar \
		level01 level02 level03 level04 level05 level06 level07 \
		level08 level09 level10 level11 level12 level13 level14 \
		level15 level16 level17 level18 level19 level20 \
		robotbuff sinwave ultek

ALLOBJS		= $(CMDS)
KERNELTRACK	= kerneltrack
OS9BOOT		= OS9Boot

.PHONY: all clean nitros9-floppy-files

all:	$(DSKS)

clean:
	$(RM) $(DSKS) $(ALLOBJS) $(KERNELTRACK) $(OS9BOOT) *.list *.map

nitros9-floppy-files:
	$(MAKE) -C $(MD) $(notdir $(KERNEL_FLOPPY) $(BOOTFILE_FLOPPY) $(SYSGO))
	$(MAKE) -C $(LEVEL2)/coco3/cmds shell_21

$(KERNELTRACK): nitros9-floppy-files
	$(MERGE) $(KERNEL_FLOPPY) >$@

$(OS9BOOT): nitros9-floppy-files
	$(MERGE) $(BOOTFILE_FLOPPY) >$@

$(DSK_FLOPPY): $(ALLOBJS) $(KERNELTRACK) $(OS9BOOT)
	$(RM) $@
	$(OS9FORMAT_DS40) -q $@ -n"Koronis Rift"
	$(OS9GEN) $@ -b=$(OS9BOOT) -t=$(KERNELTRACK)
	$(RM) $(OS9BOOT) $(KERNELTRACK)
	$(OS9COPY) $(SYSGO) $@,sysgo
	$(OS9ATTR_EXEC) $@,sysgo
	$(MAKDIR) $@,CMDS
	$(OS9COPY) -r $(LEVEL2)/coco3/cmds/shell_21 $@,CMDS/shell
	$(OS9ATTR_EXEC) $@,CMDS/shell
	$(OS9COPY) -r $(CMDS) $@,CMDS
	$(OS9ATTR_EXEC) $(foreach file,$(CMDS),$@,CMDS/$(file))
	$(OS9RENAME) $@,CMDS/koronis AutoEx
	$(OS9COPY) -r $(SUPPORTFILES) $@,.

$(DSK_DW):
	$(RM) $@
	$(CD) $(LEVEL2)/coco3; make
	$(OS9FORMAT_SS35) -q $@ -n"Koronis Rift"
	$(MERGE) $(BOOTFILE_DW)>os9boot
	$(MERGE) $(KERNEL_DW)>kernel
	$(OS9GEN) $@ -b=os9boot -t=kernel
	$(RM) os9boot kernel
	$(OS9COPY) $(SYSGO) $@,sysgo
	$(OS9ATTR_EXEC) $@,sysgo
	$(MAKDIR) $@,CMDS
	$(OS9COPY) $(LEVEL2)/coco3/cmds/shell_21 $@,CMDS/shell
	$(OS9ATTR_EXEC) $@,CMDS/shell
	$(OS9COPY) $(CMDS) $@,CMDS
	$(OS9ATTR_EXEC) $(foreach file,$(CMDS),$@,CMDS/$(file))
	$(OS9RENAME) $@,CMDS/koronis AutoEx
	$(OS9COPY) $(SUPPORTFILES) $@,.
	$(OS9ATTR_TEXT) $(foreach file,$(SUPPORTFILES),$@,$(file))

$(DSK_DW_BECKER):
	$(RM) $@
	$(CD) $(LEVEL2)/coco3; make
	$(OS9FORMAT_SS35) -q $@ -n"Koronis Rift"
	$(MERGE) $(BOOTFILE_DW_BECKER)>os9boot
	$(MERGE) $(KERNEL_DW_BECKER)>kernel
	$(OS9GEN) $@ -b=os9boot -t=kernel
	$(RM) os9boot kernel
	$(OS9COPY) $(SYSGO) $@,sysgo
	$(OS9ATTR_EXEC) $@,sysgo
	$(MAKDIR) $@,CMDS
	$(OS9COPY) $(LEVEL2)/coco3/cmds/shell_21 $@,CMDS/shell
	$(OS9ATTR_EXEC) $@,CMDS/shell
	$(OS9COPY) $(CMDS) $@,CMDS
	$(OS9ATTR_EXEC) $(foreach file,$(CMDS),$@,CMDS/$(file))
	$(OS9RENAME) $@,CMDS/koronis AutoEx
	$(OS9COPY) $(SUPPORTFILES) $@,.
	$(OS9ATTR_TEXT) $(foreach file,$(SUPPORTFILES),$@,$(file))
