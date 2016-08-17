#!/usr/bin/env python
# encoding: utf-8
"""Description: for UI test.
"""

__version__ = "0.1"
__author__ = "@boqiling"

import threading
from Queue import Queue
import logging
from UFT.models import DUT_STATUS
import time

logger = logging.getLogger(__name__)

class DUT(object):
    def __init__(self, slotnum, status):
        self.slotnum = slotnum
        self.status = status


class ChannelStates(object):
    EXIT = -1
    INIT = 0x0A
    LOAD_DISCHARGE = 0x0C
    CHARGE = 0x0E
    PROGRAM_VPD = 0x0F
    CHECK_CAPACITANCE = 0x1A
    CHECK_ENCRYPTED_IC = 0x1B
    CHECK_TEMP = 0x1C
    DUT_DISCHARGE = 0x1D

class Channel(threading.Thread):
    def __init__(self, name, barcode_list, channel_id=0):

        self.channel = channel_id

        # setup dut_list
        self.dut_list = []

        for i in range(4):
            dut = DUT(slotnum=i, status=DUT_STATUS.Idle)
            self.dut_list.append(dut)

        self.config_list = []
        self.barcode_list = barcode_list

        self.progressbar = 0
        self.exit = False
        self.queue = Queue()

        super(Channel, self).__init__(name=name)

    def set_dut(self, status):
        for dut in self.dut_list:
            dut.status = status

    def run(self):
        """ override thread.run()
        :return: None
        """
        while(not self.exit):
            state = self.queue.get()
            if(state == ChannelStates.EXIT):
                self.set_dut(DUT_STATUS.Pass)
                self.exit = True
                logger.info("Channel: Exit Successfully.")
            elif(state == ChannelStates.INIT):
                logger.info("Channel: Initialize.")
                self.progressbar += 20
            elif(state == ChannelStates.CHARGE):
                logger.info("Channel: Charge DUT.")
                self.set_dut(DUT_STATUS.Charging)
                time.sleep(2)
                self.progressbar += 30
            elif(state == ChannelStates.LOAD_DISCHARGE):
                logger.info("Channel: Discharge DUT.")
                self.set_dut(DUT_STATUS.Discharging)
                time.sleep(2)
                self.progressbar += 20
            elif(state == ChannelStates.PROGRAM_VPD):
                logger.info("Channel: Program VPD.")
                self.progressbar += 5
            elif(state == ChannelStates.CHECK_ENCRYPTED_IC):
                logger.info("Channel: Check Encrypted IC.")
                self.progressbar += 5
            elif(state == ChannelStates.CHECK_TEMP):
                logger.info("Channel: Check Temperature")
                self.progressbar += 5
            elif(state == ChannelStates.CHECK_CAPACITANCE):
                logger.info("Channel: Check Capacitor Value")
                self.progressbar += 5
            elif(state == ChannelStates.DUT_DISCHARGE):
                logger.info("Channel: Self Mesaured Capacitor")
                self.progressbar += 10
            else:
                logger.error("unknown dut state, exit...")
                self.exit = True

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    barcode = "AGIGA9601-002BCA02143500000002-04"
    ch = Channel(barcode_list=[barcode, "", "", ""], channel_id=0,
                 name="UFT_CHANNEL")
    ch.queue.put(ChannelStates.INIT)
    ch.queue.put(ChannelStates.CHARGE)
    ch.queue.put(ChannelStates.PROGRAM_VPD)
    ch.queue.put(ChannelStates.CHECK_ENCRYPTED_IC)
    ch.queue.put(ChannelStates.CHECK_TEMP)
    ch.queue.put(ChannelStates.LOAD_DISCHARGE)
    ch.queue.put(ChannelStates.CHECK_CAPACITANCE)
    ch.queue.put(ChannelStates.EXIT)

    ch.start()
