PORT ?= coco3
export PORT
# Compile game modules only. Disk images and MAME live in nitros9 recipes.
NITROS9DIR ?= $(abspath ../../nitros9)
.DEFAULT_GOAL := all
include $(NITROS9DIR)/rules.mak

CMDS = mm mod1.dat mod2.dat mod3.dat mod4.dat mod5.dat  		mod6.sbr mod7.sbr mod8.sbr
all: $(CMDS)
$(CMDS): Makefile

clean:
	$(RM) $(CMDS) *.list *.map

showobjs:
	@$(ECHO) $(CMDS)

.PHONY: all clean showobjs
