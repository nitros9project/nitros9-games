include $(NITROS9DIR)/rules.mak

DISK		= arcadepack_40d.dsk
KERNELTRACK	= kerneltrack
OS9BOOT		= OS9Boot

NITROS_MODULE_DIR = $(NITROS9DIR)/level2/coco3/modules
NITROS_CMD_DIR    = $(NITROS9DIR)/level2/coco3/cmds

KERNEL_MODULES = rel_40 boot_1773_6ms krn
BOOT_MODULES = krnp2 ioman init \
		rbf.mn rb1773.dr ddd0_40d.dd \
		scf.mn vtio.dr joydrv_joy.sb snddrv_cc3.sb \
		cogrf.io term_win40.dt w.dw w1.dw w2.dw w3.dw \
		w4.dw w5.dw w6.dw w7.dw \
		clock_60hz clock2_soft sysgo_dd
BASECMDS = shell grfdrv

GAMECMDS	= smash/smash smash/custom \
		thexder/thexder thexder/thexs \
		shanghai/shanghai shanghai/stile
SYSFILES	= smash/flags.dat smash/ia.fnt smash/smash.dat smash/smash.hsc \
		thexder/ia.fnt \
		shanghai/cards.til shanghai/shanghai.til shanghai/traffic.til
ROOTFILES	= smash/empty_smash.txt thexder/empty_thexder.txt \
		shanghai/empty_tiles.vef

.PHONY: all clean games nitros9-files

all: $(DISK)

games:
	$(MAKE) -C smash
	$(MAKE) -C thexder
	$(MAKE) -C shanghai

nitros9-files:
	$(MAKE) -C $(NITROS_MODULE_DIR) $(KERNEL_MODULES) $(BOOT_MODULES)
	$(MAKE) -C $(NITROS_CMD_DIR) $(BASECMDS)

$(KERNELTRACK): nitros9-files
	$(MERGE) $(addprefix $(NITROS_MODULE_DIR)/,$(KERNEL_MODULES)) >$@

$(OS9BOOT): nitros9-files
	$(MERGE) $(addprefix $(NITROS_MODULE_DIR)/,$(BOOT_MODULES)) >$@

$(DISK): games $(KERNELTRACK) $(OS9BOOT) startup
	$(RM) $@
	$(OS9FORMAT_DS40) -q $@ -n"NitrOS-9/6809 Level 2 Arcade Pak"
	$(OS9GEN) $@ -b=$(OS9BOOT) -t=$(KERNELTRACK)
	$(RM) $(OS9BOOT) $(KERNELTRACK)
	$(MAKDIR) $@,CMDS
	$(OS9COPY) $(addprefix $(NITROS_CMD_DIR)/,$(BASECMDS)) $@,CMDS
	$(OS9COPY) -r $(GAMECMDS) $@,CMDS
	$(OS9ATTR_EXEC) $(foreach file,$(BASECMDS) $(notdir $(GAMECMDS)),$@,CMDS/$(file))
	$(MAKDIR) $@,SYS
	$(OS9COPY) -r $(SYSFILES) $@,SYS
	$(OS9COPY) -r $(ROOTFILES) $@,
	$(CPL) -r startup $@,

clean:
	$(RM) $(DISK) $(KERNELTRACK) $(OS9BOOT) *.list *.map
	$(MAKE) -C smash clean
	$(MAKE) -C thexder clean
	$(MAKE) -C shanghai clean
