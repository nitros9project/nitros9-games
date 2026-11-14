NITROS9DIR ?= $(abspath ../../../nitros9)
PORT ?= coco3
.DEFAULT_GOAL := all
include $(NITROS9DIR)/rules.mak

DEPENDS		= ./Makefile

CMDS		= thexder thexs

SYSFILES	= ia.fnt

ROOTFILES	= empty_thexder.txt

ALLOBJS		= $(CMDS)

all:	$(ALLOBJS)

thexder:	thexder.asm
	$(AS) $(AFLAGS) $< $(ASOUT)$@

clean:
	$(RM) $(ALLOBJS) *.list *.map

showobjs:
	@$(ECHO) $(CMDS)

showsys:
	@$(ECHO) $(SYSFILES)

showroot:
	@$(ECHO) $(ROOTFILES)
