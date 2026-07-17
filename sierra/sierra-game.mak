include $(NITROS9DIR)/rules.mak

.DEFAULT_GOAL := all

vpath %.asm ../objs

AFLAGS		+= -I.
DEPENDS		= ./Makefile ../sierra-game.mak

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
		$(MD)/covdg_small.io $(MD)/term_vdg.dt \
		$(MD)/vrn.dr $(MD)/vi.dd \
		$(MD)/clock_60hz $(MD)/clock2_soft

BOOTCMDS	= $(LEVEL2)/coco3/cmds/shell_21 $(LEVEL2)/coco3/cmds/date \
		$(LEVEL2)/coco3/cmds/echo $(LEVEL2)/coco3/cmds/link \
		$(LEVEL2)/coco3/cmds/setime

STARTUP		?= ../startup
DISKS		= $(strip $(DISK1) $(DISK2) $(DISK3))
ALLOBJS		= $(CMDS)
KERNELTRACK	= kerneltrack
OS9BOOT		= OS9Boot
SIERRASHELL	= shell

.PHONY: all clean nitros9-files

all:	$(DISKS)

clean:
	$(RM) $(DISKS) $(ALLOBJS) $(KERNELTRACK) $(OS9BOOT) $(SIERRASHELL) \
		toctmp *.list *.map

nitros9-files:
	$(MAKE) -C $(MD) $(notdir $(KERNEL) $(BOOTFILE) $(SYSGO))
	$(MAKE) -C $(LEVEL2)/coco3/cmds $(notdir $(BOOTCMDS))

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
