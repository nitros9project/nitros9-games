PYTHON ?= python3
LWASM ?= lwasm
XROAR ?= xroar
.PHONY: all check clean
all:
	$(PYTHON) tools/build.py --lwasm $(LWASM)
check: all
	$(PYTHON) tests/check_platform.py --xroar $(XROAR)

clean:
	rm -rf build
