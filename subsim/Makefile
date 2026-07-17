include $(NITROS9DIR)/rules.mak

DEPENDS		= ./Makefile

DISK		= SubBattleSimulator.dsk

CMDS		= presub sub sub1 sub2 sub3 sub4 sub5 sub6
MD		= $(LEVEL2)/coco3/modules
SYSGO		= $(MD)/sysgo_dd

# We make our own bootfile and kernel track
KERNEL		= $(MD)/rel_32 $(MD)/boot_1773_6ms $(MD)/krn

BOOTFILE	= $(MD)/krnp2 $(MD)/ioman $(MD)/init \
		$(MD)/rbf.mn \
		$(MD)/rb1773.dr $(MD)/ddd0_40d.dd \
		$(MD)/scf.mn $(MD)/vtio.dr $(MD)/co3hires.sb \
		$(MD)/joydrv_joy.sb $(MD)/snddrv_cc3.sb \
		$(MD)/covdg_small.io $(MD)/term_vdg.dt \
		$(MD)/clock_60hz $(MD)/clock2_soft

SUPPORTFILES	= control1.cmp convoys.dat diesel.dat fonts.dat germap.cmp \
		hiscore.dat mission.txt missions.dat radar.dat shipmap2.dat \
		sintbl.dat stitle.pic sub.dat usamap.cmp status.dat substats.dat

ALLOBJS		= $(CMDS)
KERNELTRACK	= kerneltrack
OS9BOOT		= OS9Boot

.PHONY: all clean nitros9-files

all:	$(DISK)

clean:
	$(RM) $(DISK) $(ALLOBJS) $(KERNELTRACK) $(OS9BOOT) *.list *.map

nitros9-files:
	$(MAKE) -C $(MD) $(notdir $(KERNEL) $(BOOTFILE) $(SYSGO))
	$(MAKE) -C $(LEVEL2)/coco3/cmds shell_21

$(KERNELTRACK): nitros9-files
	$(MERGE) $(KERNEL) >$@

$(OS9BOOT): nitros9-files
	$(MERGE) $(BOOTFILE) >$@

$(DISK): $(ALLOBJS) $(KERNELTRACK) $(OS9BOOT)
	$(RM) $@
	$(OS9FORMAT_DS40) -q $@ -n"Sub Battle Simulator"
	$(OS9GEN) $@ -b=$(OS9BOOT) -t=$(KERNELTRACK)
	$(RM) $(OS9BOOT) $(KERNELTRACK)
	$(OS9COPY) $(SYSGO) $@,sysgo
	$(OS9ATTR_EXEC) $@,sysgo
	$(MAKDIR) $@,CMDS $@,SUB
	$(OS9COPY) -r $(LEVEL2)/coco3/cmds/shell_21 $@,CMDS/shell
	$(OS9ATTR_EXEC) $@,CMDS/shell
	$(OS9COPY) -r $(CMDS) $@,CMDS
	$(OS9ATTR_EXEC) $(foreach file,$(CMDS),$@,CMDS/$(file))
	$(OS9RENAME) $@,CMDS/presub AutoEx
	$(OS9COPY) -r $(SUPPORTFILES) $@,SUB
	$(OS9COPY) -r sub6 $@,SUB
	$(OS9ATTR_EXEC) $@,SUB/sub6
	$(OS9ATTR_TEXT) $(foreach file,$(SUPPORTFILES),$@,SUB/$(file))
