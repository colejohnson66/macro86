"""
A static RAM modeled after the likes of the 62xx ICs
https://en.wikipedia.org/wiki/6264
https://www.cs.uml.edu/~fredm/courses/91.305/files/cy6264.pdf
(`/datasheets/cy6264.pdf`)
"""

# pylint error is for snake_case, but also covers short names
# pylint: disable=C0103

from typing import List, Tuple
from nmigen import Array, ClockDomain, Elaboratable, Module, Mux, Signal
from nmigen.build import Platform
from nmigen.sim import Simulator, Delay
from nmigen.asserts import Assert, Assume, Cover, Fell, Past, Rose, Stable
from util import main


class SRam(Elaboratable):
    """
    A static RAM modeled after the likes of the 62xx ICs
    https://en.wikipedia.org/wiki/6264
    https://www.cs.uml.edu/~fredm/courses/91.305/files/cy6264.pdf

    Attributes:
        [I] addr:     The address lines
        [I] data_in:  The input data
        [O] data_out: The output data
        [I] _oe:      Output enable (active low)
        [I] _we:      Write enable (active low)
            /: `__mem[a] := data_in`
    """
    addr: Signal
    data_in: Signal
    data_out: Signal
    _oe: Signal
    _we: Signal
    data_bits: int
    addr_bits: int
    __mem: Array

    def __init__(self, data_bits: int, addr_bits: int):
        """
        Constructs an `SRam`

        Arguments:
            data_bits: The width of the data bus
            addr_bits: The width of the address bus
        """
        assert data_bits > 0
        assert addr_bits > 0
        assert addr_bits <= 32

        self.addr = Signal(addr_bits)
        self.data_in = Signal(data_bits)
        self.data_out = Signal(data_bits)
        self._oe = Signal(1)
        self._we = Signal(1)
        self.data_bits = data_bits
        self.addr_bits = addr_bits

        self.__mem = Array(
            [Signal(data_bits, reset_less=True) for _ in range(2**addr_bits)]
        )

    def elaborate(self, _: Platform) -> Module:
        m = Module()

        # Data is written in on a positive edge
        we_clk = ClockDomain("we_clk", clk_edge="pos", local=True)
        m.domains.we_clk = we_clk
        we_clk.clk = self._we

        # Read out data if ~OE and not ~WE
        m.d.comb += self.data_out.eq(0)
        with m.If(~self._oe & self._we):
            m.d.comb += self.data_out.eq(self.__mem[self.addr])

        # When ~WE goes high, save the data
        m.d.we_clk += self.__mem[self.addr].eq(self.data_in)

        return m

    def ports(self):
        """Gets the ports for an `SRam`"""
        return [
            self.addr,
            self.data_in,
            self.data_out,
            self._oe,
            self._we
        ]

    @classmethod
    def sim(cls):
        """Simulate an `SRam` with a 4 bit address and 16 bit data bus"""
        m = Module()
        m.submodules.mem = mem = SRam(16, 4)

        sim = Simulator(m)

        # Simulates "Write Cycle No. 1 (~WE Controlled)" (p. 4)
        # Simulates "Read Cycle No. 2" (p. 4)
        def process():
            yield mem._oe.eq(1)

            # Write at address 0
            yield mem.addr.eq(0)
            yield mem.data_in.eq(0x1111)
            yield mem._we.eq(0)
            yield Delay(1e-6)
            yield mem._we.eq(1)
            yield Delay(1e-6)

            # Write at address 1
            yield mem.addr.eq(1)
            yield mem.data_in.eq(0x2222)
            yield mem._we.eq(0)
            yield Delay(1e-6)
            yield mem._we.eq(1)
            yield Delay(1e-6)

            # Stop inputing data
            yield mem.data_in.eq(0)

            # Read back address 0
            yield mem.addr.eq(0)
            yield mem._oe.eq(0)
            yield Delay(1e-6)
            # read0 = yield mem.data_out
            # want0 = yield mem.__mem[0]
            # if read0 != want0:
            #     print(f"ERROR: data_out({read0}) != mem[0]({want0})")
            # if read0 != 0x1111:
            #     print(f"ERROR: data_out({read0}) != 0x1111")
            yield mem._oe.eq(1)
            yield Delay(1e-6)

            # Read back address 1
            yield mem.addr.eq(1)
            yield mem._oe.eq(0)
            yield Delay(1e-6)
            # read1 = yield mem.data_out
            # want1 = yield mem.__mem[1]
            # if read1 != want1:
            #     print(f"ERROR: data_out({read0}) != mem[1]({want0})")
            # if read1 != 0x2222:
            #     print(f"ERROR: data_out({read0}) != 0x2222")
            yield mem._oe.eq(1)
            yield Delay(1e-6)

        sim.add_process(process)
        with sim.write_vcd("out/SRam.vcd", "out/SRam.gtkw", traces=mem.ports()):
            sim.run()

    @classmethod
    def formal(cls) -> Tuple[Module, List[Signal]]:
        """Formally verify an `SRam` with a 4 bit address and 16 bit data bus"""
        m = Module()
        m.submodules.rom = rom = EEProm(16, 4)

        # TODO: Formally verify

        return m, rom.ports()


if __name__ == "__main__":
    main(SRam, "out/SRam.il")
