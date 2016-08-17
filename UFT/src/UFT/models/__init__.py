#!/usr/bin/env python
# encoding: utf-8
"""description: Cororado PGEM models
"""
__version__ = "0.1"
__author__ = "@fanmuzhi, @boqiling"
__all__ = ["PGEMBase", "DUT", "DUT_STATUS", "Cycle"]

from base import PGEMBase, Diamond4
from dut import DUT, DUT_STATUS, Cycle


class Crystal(PGEMBase):
    pass


class Saphire(PGEMBase):
    PGEM_ID = {"name": "INITIALCAP", "addr": 0x077, "length": 1, "type": "int"}

    def write_pgemid(self):
        # write to VPD
        self.device.slave_addr = 0x53
        #
        self.device.write_reg(i, buffebf[i])
        self.device.sleep(5)
