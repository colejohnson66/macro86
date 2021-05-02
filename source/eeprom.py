"""
A ROM similar to a 28C64-like IC
https://ww1.microchip.com/downloads/en/DeviceDoc/doc0270.pdf
(`/datasheets/at28c64.pdf`)
"""

# pylint error is for snake_case, but also covers short names
# pylint: disable=C0103

from typing import List, Tuple
from nmigen import Array, ClockDomain, Elaboratable, Module, Mux, Signal
from nmigen.build import Platform
from nmigen.sim import Simulator, Delay
from nmigen.asserts import Assert, Assume, Cover, Fell, Past, Rose, Stable
from util import main


class EEProm(Elaboratable):
    """
    A ROM similar to a 28C64-like IC
    https://ww1.microchip.com/downloads/en/DeviceDoc/doc0270.pdf

    Attributes:
        [I] a:      The address lines
        [I] io_in:  The data lines (when writing)
        [O] io_out: The data lines (when reading)
        [I] _oe:    Output enable (active low)
        [I] _we:    Write enable (active low)
            /: `__mem[a] := io_in`
    """
    a: Signal
    io_in: Signal
    io_out: Signal
    _oe: Signal
    _we: Signal
    a_bits: int
    io_bits: int
    __mem: Array

    def __init__(self, data_bits: int, addr_bits: int):
        """
        Constructs a `EEProm`

        Arguments:
            data_bits: The width of the data bus
            addr_bits: The width of the address bus
        """
        assert data_bits > 0
        assert addr_bits > 0
        assert addr_bits <= 32

        self.a = Signal(addr_bits)
        self.io_in = Signal(data_bits)
        self.io_out = Signal(data_bits)
        self._oe = Signal(1)
        self._we = Signal(1)
        self.a_bits = addr_bits
        self.io_bits = data_bits

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
        m.d.comb += self.io_out.eq(0)
        with m.If(~self._oe & self._we):
            m.d.comb += self.io_out.eq(self.__mem[self.a])

        # When ~WE goes high, save the data
        m.d.we_clk += self.__mem[self.a].eq(self.io_in)

        return m

    def ports(self):
        """Gets the ports for a `EEProm`"""
        return [
            self.a,
            self.io_in, self.io_out,
            self._oe,
            self._we
        ]

    @classmethod
    def sim(cls):
        """Simulate a 4x16bit `EEProm`"""
        m = Module()
        m.submodules.rom = rom = EEProm(16, 4)

        sim = Simulator(m)

        # Simulates "AC Write Waveforms (~WE Controlled)" (p. 8)
        # Simulates "AC Read Waveforms" (p. 6)
        def process():
            yield rom._oe.eq(1)

            # Write at address 0
            yield rom.a.eq(0)
            yield rom.io_in.eq(0x1111)
            yield rom._we.eq(0)
            yield Delay(1e-6)
            yield rom._we.eq(1)
            yield Delay(1e-6)

            # Write at address 1
            yield rom.a.eq(1)
            yield rom.io_in.eq(0x2222)
            yield rom._we.eq(0)
            yield Delay(1e-6)
            yield rom._we.eq(1)
            yield Delay(1e-6)

            # Stop inputing data
            yield rom.io_in.eq(0)

            # Read back address 0
            yield rom.a.eq(0)
            yield rom._oe.eq(0)
            yield Delay(1e-6)
            # read0 = yield rom.io_out
            # want0 = yield rom.__mem[0]
            # if read0 != want0:
            #     print(f"ERROR: io_out({read0}) != mem[0]({want0})")
            # if read0 != 0x1111:
            #     print(f"ERROR: io_out({read0}) != 0x1111")
            yield rom._oe.eq(1)
            yield Delay(1e-6)

            # Read back address 1
            yield rom.a.eq(1)
            yield rom._oe.eq(0)
            yield Delay(1e-6)
            # read1 = yield rom.io_out
            # want1 = yield rom.__mem[1]
            # if read1 != want1:
            #     print(f"ERROR: io_out({read0}) != mem[1]({want0})")
            # if read1 != 0x2222:
            #     print(f"ERROR: io_out({read0}) != 0x2222")
            yield rom._oe.eq(1)
            yield Delay(1e-6)

        sim.add_process(process)
        with sim.write_vcd("eeprom.vcd", "eeprom.gtkw", traces=rom.ports()):
            sim.run()

    @classmethod
    def formal(cls) -> Tuple[Module, List[Signal]]:
        assert False


if __name__ == "__main__":
    main(EEProm, "eeprom.il")
