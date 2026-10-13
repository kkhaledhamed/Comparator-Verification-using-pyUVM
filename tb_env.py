"""
# ============================================================
# Author:    Khaled Ahmed Hamed
# Date:      5 Sept, 2026
# ============================================================
Full pyuvm testbench for comparator.
item -> sequences -> sequencer -> driver -> monitor
-> scoreboard -> agent -> env -> test.
"""

# pyUVM imports
import random
import cocotb 
from cocotb.triggers import Timer, FallingEdge, RisingEdge, ReadOnly
from intf import ComparatorBfm
from pyuvm import (ConfigDB, uvm_test, uvm_env, uvm_agent, uvm_driver, 
                   uvm_monitor, uvm_subscriber, uvm_analysis_port, 
                   uvm_sequencer, uvm_sequence, uvm_sequence_item, test)

# Sequence Item
class seq_item (uvm_sequence_item):
    def __init__(self, name="seq_item", a=None, b=None, rst_n=None):
        super().__init__(name)
        self.a = a
        self.b = b
        self.rst_n = rst_n
        self.eq = None
        self.gt = None
        self.lt = None

# Sequences
class reset_seq (uvm_sequence):
    async def body(self):
        item = seq_item("reset_item")
        await self.start_item(item)
        item.rst_n = 0
        item.a = 0
        item.b = 0
        await self.finish_item(item)

class equal_seq (uvm_sequence):
    async def body(self):
        item = seq_item("equal_item")
        await self.start_item(item)
        item.rst_n = 1
        item.a = random.randint(0,3)
        item.b = item.a
        await self.finish_item(item)

class greater_seq (uvm_sequence):
    async def body(self):
        item = seq_item("greater_item")
        await self.start_item(item)
        item.rst_n = 1
        item.a = 3
        item.b = 1
        await self.finish_item(item)

class less_seq (uvm_sequence):
    async def body(self):
        item = seq_item("less_item")
        await self.start_item(item)
        item.rst_n = 1
        item.a = 1
        item.b = 3
        await self.finish_item(item)

class random_seq (uvm_sequence):
    def __init__(self, name="random_seq", num_items=30):
        super().__init__(name)
        self.num_items = num_items

    async def body(self):
        for i in range(self.num_items):
            item = seq_item(f"rand_item_{i}")
            await self.start_item(item)
            item.rst_n = 1
            item.a = random.randint(0,3)
            item.b = random.randint(0,3)
            await self.finish_item(item)

# Sequencer
class sequencer (uvm_sequencer):
    pass

# Driver
class driver(uvm_driver):
    def build_phase(self):
        self.bfm = ConfigDB().get(self, "", "BFM")

    async def run_phase(self):
        while True:
            item = await self.seq_item_port.get_next_item()
            await FallingEdge(self.bfm.clk)
            self.bfm.rst_n.value = item.rst_n
            self.bfm.a.value = item.a
            self.bfm.b.value = item.b
            await RisingEdge(self.bfm.clk)
            self.seq_item_port.item_done()

# Monitor
class monitor (uvm_monitor):
    def build_phase(self):
        self.analysis_port = uvm_analysis_port("analysis_port", self)
        self.bfm = ConfigDB().get(self, "", "BFM")
    
    async def run_phase(self):
        item = seq_item("monitor_item")
        while True:
            await self.bfm.wait_for_clock_edge()
            item.a = int(self.bfm.a.value)
            item.b = int(self.bfm.b.value)
            item.rst_n = int(self.bfm.rst_n.value)
            item.eq = int(self.bfm.eq.value)
            item.gt = int(self.bfm.gt.value)
            item.lt = int(self.bfm.lt.value)
            self.analysis_port.write(item)


class scoreboard(uvm_subscriber):
    def build_phase(self):
        self.observed_transactions = 0
        self.failures = []

    def write(self, item):
        self.observed_transactions += 1

        if (item.rst_n == 0):
            exp_eq, exp_gt, exp_lt = 0, 0, 0
        else:
            exp_eq = int(item.a == item.b)
            exp_gt = int(item.a > item.b)
            exp_lt = int(item.a < item.b)

        if (item.eq, item.gt, item.lt) != (exp_eq, exp_gt, exp_lt):
            self.failures.append(
            f"rst_n = {item.rst_n} a={item.a} b={item.b}: expected (eq={exp_eq},gt={exp_gt},lt={exp_lt}) "
            f"got (eq={item.eq},gt={item.gt},lt={item.lt})"
            )

    def check_phase(self):
        if self.observed_transactions == 0:
            raise AssertionError("Scoreboard observed no transactions")
        if self.failures:
            raise AssertionError("Mismatches:\n" + "\n".join(self.failures))

# Agent
class agent(uvm_agent):
    def build_phase(self):
        self.sequencer = sequencer("sequencer", self)
        self.driver = driver("driver", self)
        self.monitor = monitor("monitor", self)
    def connect_phase(self):
        self.driver.seq_item_port.connect(self.sequencer.seq_item_export)

# Env
class env(uvm_env):
    def build_phase(self):
        self.agent = agent("agent", self)
        self.scoreboard = scoreboard("scoreboard", self)
    def connect_phase(self):
        self.agent.monitor.analysis_port.connect(self.scoreboard.analysis_export)

# Base Test
class base_test(uvm_test):
    def build_phase(self):
        self.bfm = ComparatorBfm(cocotb.top)
        ConfigDB().set(self, "*", "BFM", self.bfm)
        self.env = env("env", self)
    async def run_phase(self):
        self.raise_objection()
        await reset_seq("reset").start(self.env.agent.sequencer)
        await self.run_sequence()
        await RisingEdge(self.bfm.clk) # drain the last pipelined result
        self.drop_objection()
    async def run_sequence(self):
        raise NotImplementedError # Overridden by each concrete test

@test()
class equal_test(base_test):
    async def run_sequence(self):
        await equal_seq("equal_sequence").start(self.env.agent.sequencer)

@test()
class greater_test(base_test):
    async def run_sequence(self):
        await greater_seq("greater_sequence").start(self.env.agent.sequencer)

@test()
class less_test(base_test):
    async def run_sequence(self):
        await less_seq("less_sequence").start(self.env.agent.sequencer)

@test()
class random_test(base_test):
    async def run_sequence(self):
        await random_seq("random_sequence", num_items=30).start(
            self.env.agent.sequencer
        )