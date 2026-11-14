PORT ?= coco3
export PORT
NITROS9DIR ?= $(abspath ../../nitros9)
.DEFAULT_GOAL := all
include $(NITROS9DIR)/rules.mak

TARGET = pacos9
OBJS = main90.o board90.o caged90.o check90.o ghosts90.o movpac90.o         score90.o scrns90.o setup90.o
SYSLIB = .lib/libnos96809l2.a
LFLAGS += -L.lib -lnos96809l2
all: $(TARGET)

$(TARGET): $(OBJS) $(SYSLIB)
	$(LINKER) $(LFLAGS) $(OBJS) -o$@

$(SYSLIB): .obj/sys6809l2.o
	mkdir -p .lib
	lwar -c $@ $<

.obj/sys6809l2.o: $(NITROS9DIR)/lib/sys6809l2.as
	mkdir -p .obj
	$(ASM) $(AFLAGS) $< $(ASOUT)$@

clean:
	$(RM) $(OBJS) $(TARGET) *.list *.map
	rm -rf .obj .lib

.PHONY: all clean
