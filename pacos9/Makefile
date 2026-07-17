include $(NITROS9DIR)/rules.mak

TARGET = pacos9
OBJS = main90.o board90.o caged90.o check90.o ghosts90.o movpac90.o \
       score90.o scrns90.o setup90.o
LFLAGS += -L$(NITROS9DIR)/lib -lnos96809l2

DISK = PacOS9.dsk
MD = $(LEVEL2)/coco3/modules
SYSGO = $(MD)/sysgo_dd
KERNEL = $(MD)/rel_40 $(MD)/boot_1773_6ms $(MD)/krn
BOOTFILE = $(MD)/krnp2 $(MD)/ioman $(MD)/init \
	$(MD)/rbf.mn $(MD)/rb1773.dr $(MD)/ddd0_40d.dd \
	$(MD)/scf.mn $(MD)/vtio.dr $(MD)/co3hires.sb \
	$(MD)/joydrv_joy.sb $(MD)/snddrv_cc3.sb \
	$(MD)/cogrf.io $(MD)/term_win40.dt $(MD)/w.dw $(MD)/w1.dw $(MD)/w2.dw \
	$(MD)/clock_60hz $(MD)/clock2_soft
KERNELTRACK = kerneltrack
OS9BOOT = OS9Boot

.PHONY: all clean nitros9-files

all: $(DISK)
	@$(ECHO) "**************************************************"
	@$(ECHO) "*                                                *"
	@$(ECHO) "*                    Pac OS-9                    *"
	@$(ECHO) "*                                                *"
	@$(ECHO) "**************************************************"

$(TARGET): $(OBJS)
	$(LINKER) $(LFLAGS) $^ -o$@

nitros9-files:
	$(MAKE) -C $(MD) $(notdir $(KERNEL) $(BOOTFILE) $(SYSGO))
	$(MAKE) -C $(LEVEL2)/coco3/cmds shell_21 grfdrv

$(KERNELTRACK): nitros9-files
	$(MERGE) $(KERNEL) >$@

$(OS9BOOT): nitros9-files
	$(MERGE) $(BOOTFILE) >$@

$(DISK): $(TARGET) $(KERNELTRACK) $(OS9BOOT) startup
	$(RM) $@
	$(OS9FORMAT_DS40) -q $@ -n"Larry Olson's Pacos9"
	$(OS9GEN) $@ -b=$(OS9BOOT) -t=$(KERNELTRACK)
	$(RM) $(OS9BOOT) $(KERNELTRACK)
	$(OS9COPY) $(SYSGO) $@,sysgo
	$(OS9ATTR_EXEC) $@,sysgo
	$(MAKDIR) $@,CMDS
	$(OS9COPY) $(LEVEL2)/coco3/cmds/shell_21 $@,CMDS/shell
	$(OS9ATTR_EXEC) $@,CMDS/shell
	$(OS9COPY) $(LEVEL2)/coco3/cmds/grfdrv $@,CMDS/grfdrv
	$(OS9ATTR_EXEC) $@,CMDS/grfdrv
	$(OS9COPY) -r $(TARGET) $@,CMDS
	$(OS9ATTR_EXEC) $@,CMDS/$(TARGET)
	$(CPL) -r startup $@,startup
	$(OS9ATTR_TEXT) $@,startup

clean:
	$(RM) $(DISK) $(OBJS) $(TARGET) $(KERNELTRACK) $(OS9BOOT) *.list *.map
