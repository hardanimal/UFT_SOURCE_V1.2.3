#!/usr/bin/env python
# encoding: utf-8
"""Description: test base.check_power_fail function
"""

__version__ = "0.1"
__author__ = "@boqiling"
__all__ = [""]

from UFT import channel
import logging

barcode_list = ["AGIGA9601-002BCA02143500000001-04",
                "AGIGA9601-002BCA02143500000002-04",
                "AGIGA9601-002BCA02143500000003-04",
                "AGIGA9601-002BCA02143500000004-04"]

ch = channel.Channel(name="test", barcode_list=barcode_list)

ch.init()
print ch.dut_list[0].barcode
print ch.dut_list[0].status
ch.charge_dut()
ch.check_power_fail()
print ch.dut_list[0].barcode
print ch.dut_list[0].status


