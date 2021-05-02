"""
A transparent latch similar to one of a 74x373
https://assets.nexperia.com/documents/data-sheet/74HC_HCT373.pdf
(`/datasheets/74HC_HCT373.pdf`)
"""

# pylint error is for snake_case, but also covers short names
# pylint: disable=C0103

from typing import List, Tuple
from nmigen import Array, ClockDomain, Elaboratable, Module, Mux, Signal
from nmigen.build import Platform
from nmigen.sim import Simulator, Delay
from nmigen.asserts import Assert, Assume, Cover, Fell, Past, Rose, Stable
from util import main


class TransparentLatch(Elaboratable):
    """
    A transparent latch similar to one of a 74x373
    https://assets.nexperia.com/documents/data-sheet/74HC_HCT373.pdf

    Attributes:
        [I] d:    The input data
        [O] q:    The output data
        [I] le:   Latch enable (requires `_oe == 1`)
            0: `q := Past(d)` (output the internal register)
            1: `q := d`
        [I] _oe:  Output enable (active low)
            0: `q` is unchanged from what `le` does
            1: `q := 0` (overriding `le`)
    """
    d: Signal
    q: Signal
    le: Signal
    _oe: Signal
    bits: int

    def __init__(self, bits: int):
        """
        Constructs a `TransparentLatch`

        Arguments:
            bits: The width of the latch
        """
        assert bits > 0

        self.d = Signal(bits)
        self.q = Signal(bits)
        self.le = Signal(1)
        self._oe = Signal(1)
        self.bits = bits

    def elaborate(self, _: Platform) -> Module:
        m = Module()

        internal_reg = Signal(self.bits, reset=0, reset_less=True)

        # The 74x373 clocks on the negative edge
        le_clk = ClockDomain("le_clk", clk_edge="neg", local=True)
        m.domains.le_clk = le_clk
        le_clk.clk = self.le

        m.d.le_clk += internal_reg.eq(self.d)
        m.d.comb += self.q.eq(Mux(self._oe, 0, internal_reg))
        with m.If(self.le & ~self._oe):
            m.d.comb += self.q.eq(self.d)

        return m

    def ports(self):
        """Gets the ports for a `TransparentLatch`"""
        return [
            self.d,
            self.q,
            self.le,
            self._oe
        ]

    @classmethod
    def sim(cls):
        """Simulate a 74x373 transparent latch of 16 bits"""
        m = Module()
        m.submodules.latch = latch = TransparentLatch(16)

        sim = Simulator(m)

        def process():
            yield latch._oe.eq(1)

            # Write in data twice
            yield latch.le.eq(1)
            yield Delay(1e-6)
            yield latch.d.eq(0x1234)
            yield Delay(1e-6)
            yield latch.d.eq(0x5678)
            yield Delay(1e-6)
            yield latch.le.eq(0)
            yield Delay(1e-6)
            yield latch.d.eq(0x1234)
            yield Delay(1e-6)
            yield latch.le.eq(1)
            yield Delay(1e-6)
            yield latch._oe.eq(0)
            yield Delay(1e-6)

        sim.add_process(process)
        with sim.write_vcd("out/TransparentLatch.vcd", "out/TransparentLatch.gtkw", traces=latch.ports()):
            sim.run()

    @classmethod
    def formal(cls) -> Tuple[Module, List[Signal]]:
        """Formal verification of a `TransparentLatch` of 16 bits"""
        m = Module()
        m.submodules.latch = latch = TransparentLatch(16)

        m.d.sync += Cover((latch.q == 0x1234)
                          & (latch.le == 0)
                          & (Past(latch.q, 2) == 0x5678)
                          & (Past(latch.le, 2) == 0))

        with m.If(latch._oe == 1):
            m.d.comb += Assert(latch.q == 0)

        with m.If((latch._oe == 0) & (latch.le == 1)):
            m.d.comb += Assert(latch.d == latch.q)

        with m.If((latch._oe == 0) & (Fell(latch.le))):
            m.d.sync += Assert(latch.q == Past(latch.d))

        return m, latch.ports()


if __name__ == "__main__":
    main(TransparentLatch, "out/TransparentLatch.il")
