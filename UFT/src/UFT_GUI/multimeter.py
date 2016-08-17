#!/usr/bin/env python
# encoding: utf-8
"""USB-1208FS is used in UFT as a 4 channels Multimeter to monitor the CAPV.
"""

__author__ = 'mzfa, qibo'

from mccdaq import MCCDAQ


def read_analog_ch(channel=0):
    mm = MCCDAQ()
    value = mm.AIn(BoardNum=0, Chan=channel, Gain=1)
    result = mm.ToEngUnits(BoardNum=0, Gain=1, DataValue=value)
    return result


if __name__ == "__main__":
    print read_analog_ch(0)
    print read_analog_ch(1)
    print read_analog_ch(2)
    print read_analog_ch(3)
