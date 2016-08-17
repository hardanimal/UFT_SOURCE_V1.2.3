#!/usr/bin/env python
# encoding: utf-8
"""Description: check base.encrypted_ic
"""

__version__ = "0.1"
__author__ = "@boqiling"
__all__ = [""]

from UFT.devices.aardvark import pyaardvark


def run():
    device = pyaardvark.Adapter()
    device.open(portnum=0)
    device.slave_addr = 0x40

    val = device.read_reg(0x00, length=128)
    # valid data in 0x00 to 0x80 (address 0 to 127)
    # 0xFF in 0x80 to 0xFF (address 128 to 256)
    try:
        for v in val:
            assert v == 255
    except AssertionError:
        # good
        return True
    return False

    device.close()

if __name__ == "__main__":
    print run()
