"""
A transparent latch similar to one of a 74x373
https://assets.nexperia.com/documents/data-sheet/74HC_HCT373.pdf
"""

# pylint error is for snake_case, but also covers short names
# pylint: disable=C0103

from typing import List, Tuple
from nmigen import Signal, Module, Elaboratable, ClockDomain
from nmigen import Mux
from nmigen.build import Platform
from nmigen.sim import Simulator, Delay
from nmigen.asserts import Assert, Cover, Fell, Past
from util import main


class TransparentLatch(Elaboratable):
    """
    A transparent latch similar to one of a 74x373
    https://assets.nexperia.com/documents/data-sheet/74HC_HCT373.pdf

    Attributes:
        d: The input data
        q: The output data
        le: Latch enable (requires `_oe == 1`)
            0: `q := Past(q)`
            1: `q := d`
        _oe: Output enable (active low)
            0: `q` is unchanged from what `le` does
            1: `q := 0` (overriding `le`)
        bits: The width of this latch in bits
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

    @classmethod
    def sim(cls):
        assert False

    @classmethod
    def formal(cls) -> Tuple[Module, List[Signal]]:
        assert False


if __name__ == "__main__":
    main(TransparentLatch, "transparent_latch.il")
