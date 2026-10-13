# ============================================================
# Cocotb + Icarus simulation flow for the sequential comparator DUT.
# Adapted from Khaled's cocotb+Questa flow -- same structure, retargeted
# to an open-source simulator and this project's file layout.
#
#   Usage:
#     make                    -> plain simulation (COVERAGE=0), all tests
#     make COVERAGE=1         -> simulation + Python coverage report + HTML
#     make TESTCASE=RandomTest -> run only one specific pyuvm test
#     make DUT=comparator SIM=questa -> override simulator/DUT
#     make clean              -> remove all generated artifacts
# ============================================================

# ============================================================
# Simulator (override with e.g. `make SIM=questa` if you have a license)
# ============================================================
export SIM ?= questa
export TOPLEVEL_LANG = verilog
export COCOTB_HDL_TIMEUNIT = 1ns
export COCOTB_HDL_TIMEPRECISION = 1ps

# ============================================================
# Parameters (override on command line, e.g. make DUT=other_dut)
# ============================================================
export DUT       ?= comparator
export RTL_DIR   ?= $(PWD)
export TB_MODULE ?= tb_env
export TESTCASE  ?=

# ============================================================
# RTL / toplevel
# ============================================================
export VERILOG_SOURCES = $(RTL_DIR)/$(DUT).sv
export COCOTB_TOPLEVEL = $(DUT)
export COCOTB_TEST_MODULES = $(TB_MODULE)
ifneq ($(TESTCASE),)
export COCOTB_TEST_FILTER = $(TESTCASE)
endif

# Waveforms
export WAVES = 1

# ============================================================
# Coverage switch: 0 = disabled (default), 1 = enabled
# Usage: make COVERAGE=1
# ============================================================
COVERAGE ?= 0

ifeq ($(COVERAGE),1)
export COCOTB_USER_COVERAGE = 1
endif

# ============================================================
# Pretty-print helpers
# ============================================================
LINE = "============================================================"
BANNER = @echo $(LINE)

# ============================================================
# Targets
# ============================================================
.PHONY: all sim report html clean info

# ------------------------------------------------------------
# Top-level target
# ------------------------------------------------------------
all: info clean sim
	$(BANNER)
ifeq ($(COVERAGE),1)
	@echo "[all] COVERAGE=1 -> generating reports..."
	$(BANNER)
	$(MAKE) report
	$(MAKE) html
else
	@echo "[all] COVERAGE=0 -> skipping report/html generation."
	@echo "      (run 'make COVERAGE=1' to enable coverage reports)"
endif
	$(BANNER)
	@echo "[all] Flow completed for DUT = $(DUT)"
	$(BANNER)

# ------------------------------------------------------------
# Show current configuration before running
# ------------------------------------------------------------
info:
	$(BANNER)
	@echo "  Cocotb + $(SIM) Simulation Flow"
	$(BANNER)
	@echo "  DUT             : $(DUT)"
	@echo "  RTL source      : $(VERILOG_SOURCES)"
	@echo "  Test module     : $(COCOTB_TEST_MODULES)"
	@echo "  Testcase filter : $(if $(TESTCASE),$(TESTCASE),<all tests>)"
	@echo "  Simulator       : $(SIM)"
	@echo "  Coverage        : $(COVERAGE)"
	@echo "  Waves enabled   : $(WAVES)"
	$(BANNER)

# ------------------------------------------------------------
# Simulation (coverage on/off based on COVERAGE flag)
# ------------------------------------------------------------
sim:
	$(BANNER)
ifeq ($(COVERAGE),1)
	@echo "[sim] Running simulation WITH Python code coverage..."
else
	@echo "[sim] Running simulation (no coverage)..."
endif
	$(BANNER)
	$(MAKE) -f $(shell cocotb-config --makefiles)/Makefile.sim
	$(BANNER)
	@echo "[sim] Simulation finished."
	$(BANNER)

# ------------------------------------------------------------
# Coverage reports (only meaningful if COVERAGE=1 was used)
# ------------------------------------------------------------
report:
	$(BANNER)
	@echo "[report] Generating terminal coverage summary..."
	$(BANNER)
	coverage report
	$(BANNER)
	@echo "[report] Done."
	$(BANNER)

html:
	$(BANNER)
	@echo "[html] Generating HTML coverage report..."
	$(BANNER)
	coverage html
	$(BANNER)
	@echo "[html] Report generated -> open htmlcov/index.html"
	$(BANNER)

# ------------------------------------------------------------
# Clean generated files
# ------------------------------------------------------------
clean:
	$(BANNER)
	@echo "[clean] Removing generated artifacts..."
	$(BANNER)
	rm -rf sim_build
	@echo "  [clean] Removed sim_build/"
	rm -rf htmlcov
	@echo "  [clean] Removed htmlcov/"
	rm -f .coverage
	@echo "  [clean] Removed .coverage"
	$(BANNER)
	@echo "[clean] Done."
	$(BANNER)
