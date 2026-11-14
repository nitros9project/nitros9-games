# Host cross-build; no implicit native compiler rules.
.SUFFIXES:
C3ROOT ?= $(abspath ../../nitros9-languages/c3)
NITROS9DIR ?= $(abspath ../../nitros9)
PREP = $(C3ROOT)/build/unix/prep/c3prep
COMP = $(C3ROOT)/build/unix/comp/c3comp
OPTX = $(C3ROOT)/build/unix/optx/c3optx
PROG = solitaire
OBJECTS = solitaire mouse gpbuf
RFILES = $(addprefix build/,$(addsuffix .r,$(OBJECTS)))
C3LIB = $(C3ROOT)/lwbackend

.PHONY: all clean
all: build/$(PROG)
build:
	mkdir -p $@
build/%.r: %.c $(wildcard *.h) | build
	$(PREP) -DOS9 -v=$(C3ROOT)/defs -v=$(C3ROOT)/defs/cgfx -v=. $< > build/$*.i
	$(COMP) build/$*.i > build/$*.s
	$(OPTX) < build/$*.s > build/$*.opt.s
	awk -f $(C3LIB)/c3lw.awk build/$*.opt.s > build/$*.lw.s
	lwasm --format=obj -o $@ build/$*.lw.s
build/$(PROG): $(RFILES) $(C3LIB)/crt0.o $(C3LIB)/fpdummy.o $(C3LIB)/libc3.a $(C3LIB)/libc3lw.a build/libsupport.a
	cd build && lwlink --format=os9 -s $(C3LIB)/os9c3.ld -o $(PROG) $(C3LIB)/crt0.o $(C3LIB)/fpdummy.o $(notdir $(RFILES)) -L. -lsupport -L$(C3LIB) -lc3 -lc3lw
clean:
	rm -rf build cfg
	rm -f *.list *.map


build/libsupport.a: cross-support.sh cross-defs.sed | build
	C3ROOT="$(C3ROOT)" sh cross-support.sh
