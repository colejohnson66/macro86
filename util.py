import sys

from nmigen.back import rtlil
from nmigen.hdl import Fragment

if sys.version_info < (3, 9):
    print("Python 3.9 or higher is required.")
    sys.exit(1)


def main(cls, filename: str):
    if len(sys.argv) < 2 or (sys.argv[1] != "sim" and sys.argv[1] != "gen"):
        print(f"Usage: python {sys.argv[0]} sim|gen")
        sys.exit(1)

    if sys.argv[1] == "sim":
        cls.sim()
    else:
        design, ports = cls.formal()
        fragment = Fragment.get(design, None)
        output = rtlil.convert(fragment, ports=ports)
        with open(filename, "w") as f:
            f.write(output)
