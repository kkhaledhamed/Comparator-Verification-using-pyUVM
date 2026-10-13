import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Edge, First, ReadOnly, RisingEdge

class ComparatorBfm:
    def __init__(self, dut=None):
        dut = dut if dut is not None else cocotb.top
        self.clk = dut.clk
        self.rst_n = dut.rst_n
        self.a = dut.a
        self.b = dut.b
        self.eq = dut.eq
        self.gt = dut.gt
        self.lt = dut.lt

        # Safe defaults before the driver's first FallingEdge --
        # avoids driving/reading 'X' on the very first clock edge.
        self.rst_n.value = 1
        self.a.value = 0
        self.b.value = 0

        # Start the clock 
        self.start_clock()

    def start_clock (self, period=10):
        clk = Clock(self.clk, period, unit='ns') 
        cocotb.start_soon(clk.start())
               

    async def wait_for_clock_edge(self):
        """Used by the monitor: wait for the edge, then let all signals
        settle (ReadOnly) before sampling."""
        await RisingEdge(self.clk)
        await ReadOnly()
