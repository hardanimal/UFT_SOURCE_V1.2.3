#!/usr/bin/env python
# encoding: utf-8
"""Description: pgem parallel test on UFT test fixture.
Currently supports 4 duts in parallel.
"""

from UFT.config import PS_VOLT
from UFT.config import RESULT_LOG
from UFT.config import RESULT_DB
from UFT.config import SD_COUNTER
from UFT.config import START_VOLT
from UFT.config import CONFIG_DB
from UFT.config import DIAMOND4_LIST
from UFT.config import PS_OCP
from UFT.config import PS_OVP
from UFT.config import PS_CURR
from UFT.config import PS_CHAN
from UFT.config import PS_ADDR
from UFT.config import TOTAL_SLOTNUM
from UFT.config import LD_DELAY
from UFT.config import LD_PORT
from UFT.config import ADK_PORT
from UFT.config import INTERVAL


__version__ = "0.1"
__author__ = "@fanmuzhi, @boqiling"
__all__ = ["Channel", "ChannelStates"]

from UFT.devices import pwr, load, aardvark
from UFT.models import DUT_STATUS, DUT, Cycle, PGEMBase, Diamond4
from UFT.backend import load_config, load_test_item
from UFT.backend.session import SessionManager
from UFT.backend import simplexml
from UFT.config import *
import threading
from Queue import Queue
import logging
import time
import math
import os
import traceback
import datetime
import numpy as np

logger = logging.getLogger(__name__)

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
    CHECK_POWER_FAIL = 0x1E


class Channel(threading.Thread):
    # aardvark
    adk = aardvark.Adapter(portnum=ADK_PORT)
    # setup load
    ld = load.DCLoad(port=LD_PORT, timeout=LD_DELAY)
    # setup main power supply
    ps = pwr.PowerSupply()

    def __init__(self, name, barcode_list, cable_barcodes_list, channel_id=0):
        """initialize channel
        :param name: thread name
        :param barcode_list: list of 2D barcode of dut.
        :param channel_id: channel ID, from 0 to 7
        :return: None
        """
        # channel number for mother board.
        # 8 mother boards can be stacked from 0 to 7.
        # use 1 motherboard in default.
        self.channel = channel_id

        # setup dut_list
        self.dut_list = []
        self.config_list = []
        self.barcode_list = barcode_list
        self.cable_barcodes_list = cable_barcodes_list

        # progress bar, 0 to 100
        self.progressbar = 0

        # counter, to calculate charge and discharge time based on interval
        self.counter = 0

        # pre-discharge current, default to 0.8A
        self.current = 2.0

        # exit flag and queue for threading
        self.exit = False
        self.queue = Queue()
        self.product_class = "Crystal"
        super(Channel, self).__init__(name=name)

    def read_volt(self, dut):
        if self.product_class == "Crystal":
            val = self.ld.read_volt()
        elif self.product_class == "Diamond4":
            val = dut.meas_vcap()
        return val

    def init(self):
        """ hardware initialize in when work loop starts.
        :return: None.
        """
         # setup load
        self.ld.reset()
        time.sleep(2)
        for slot in range(TOTAL_SLOTNUM):
            self.ld.select_channel(slot)
            self.ld.input_off()
            time.sleep(1)
            self.ld.protect_on()
            self.ld.change_func(load.DCLoad.ModeCURR)
            time.sleep(1)

        # setup power supply
        self.ps.selectChannel(node=PS_ADDR, ch=PS_CHAN)

        setting = {"volt": PS_VOLT, "curr": PS_CURR,
                   "ovp": PS_OVP, "ocp": PS_OCP}
        self.ps.set(setting)
        self.ps.activateOutput()
        time.sleep(2)
        volt = self.ps.measureVolt()
        curr = self.ps.measureCurr()
        if not ((PS_VOLT - 1) < volt < (PS_VOLT + 1)):
            self.ps.setVolt(0.0)
            logging.error("Power Supply Voltage {0} "
                          "is not in range".format(volt))
            raise AssertionError("Power supply voltage is not in range")
        if not (curr >= 0):
            self.ps.setVolt(0.0)
            logging.error("Power Supply Current {0} "
                          "is not in range".format(volt))
            raise AssertionError("Power supply current is not in range")

        # setup dut_list
        for i, bc in enumerate(self.barcode_list):
            if bc != "":
                # dut is present
                dut = PGEMBase(device=self.adk,
                               slot=i,
                               barcode=bc)
                if dut.partnumber in DIAMOND4_LIST:
                    self.product_class = "Diamond4"
                    dut = Diamond4(device=self.adk,
                                   slot=i,
                                   barcode=bc)
                dut.status = DUT_STATUS.Idle
                dut.cable_barcode = self.cable_barcodes_list[i]
                dut.testdate = datetime.datetime.utcnow()
                self.dut_list.append(dut)
                dut_config = load_config("sqlite:///" + CONFIG_DB,
                                         dut.partnumber, dut.revision)
                self.config_list.append(dut_config)
            else:
                # dut is not loaded on fixture
                self.dut_list.append(None)
                self.config_list.append(None)



    def reset_dut(self):
        """disable all charge and self-discharge, enable auto-discharge.
        just like the dut is not present.
        :return: None
        """
        for dut in self.dut_list:
            if dut is not None:
                self.switch_to_dut(dut.slotnum)
                # dut.write_ltc3350(0x17, 0x01)
                try:
                    # disable self discharge
                    dut.self_discharge(status=False)
                except:
                    # maybe dut has no power, doesn't response
                    pass
                # disable charge
                dut.charge(status=False)

                # enable auto discharge
                self.switch_to_mb()
                self.auto_discharge(slot=dut.slotnum, status=True)

                # empty the dut, one by one
                self.switch_to_dut(dut.slotnum)
                self.ld.select_channel(dut.slotnum)
                # val = self.read_volt(dut)
                self.ps.setVolt(0.0)
                time.sleep(1.5)
                val = self.ld.read_volt()
                if (val > START_VOLT):
                    # self.ps.setVolt(0.0)
                    self.ld.set_curr(self.current)
                    self.ld.input_on()
                    time.sleep(1.5)
                    dut.status = DUT_STATUS.Discharging
                while (val > START_VOLT):
                    # print "start_volt", val
                    # self.ps.setVolt(0.0)
                    # val = self.read_volt(dut)
                    val = self.ld.read_volt()
                    time.sleep(INTERVAL)
                self.ps.setVolt(PS_VOLT)
                time.sleep(1.5)
                self.ld.input_off()
                dut.status = DUT_STATUS.Idle

    def charge_dut(self):
        """charge
        """
        for dut in self.dut_list:
            if dut is None:
                continue
            config = load_test_item(self.config_list[dut.slotnum],
                                    "Charge")
            # print dut.slotnum
            if (not config["enable"]):
                continue
            if (config["stoponfail"]) & (dut.status != DUT_STATUS.Idle):
                continue
            # disable auto discharge
            self.switch_to_mb()
            self.auto_discharge(slot=dut.slotnum, status=False)
            self.switch_to_dut(dut.slotnum)
            try:
                # disable self discharge
                dut.self_discharge(status=False)
            except aardvark.USBI2CAdapterException:
                # maybe dut has no power, doesn't response
                pass
            # start charge
            dut.charge(option=config, status=True)
            dut.status = DUT_STATUS.Charging
            # dut.write_ltc3350(0x02, 0x78)
            # dut.write_ltc3350(0x17, 0x01)

        all_charged = False
        self.counter = 0
        start_time = time.time()
        while (not all_charged):
            all_charged = True
            for dut in self.dut_list:
                if dut is None:
                    continue
                config = load_test_item(self.config_list[dut.slotnum],
                                        "Charge")
                if (not config["enable"]):
                    continue
                if (config["stoponfail"]) & \
                        (dut.status != DUT_STATUS.Charging):
                    continue
                self.switch_to_dut(dut.slotnum)

                this_cycle = Cycle()
                this_cycle.vin = self.ps.measureVolt()
                this_cycle.counter = self.counter
                this_cycle.time = time.time()
                try:
                    temperature = dut.check_temp()
                except aardvark.USBI2CAdapterException:
                    # temp ic not ready
                    temperature = 0
                this_cycle.temp = temperature
                this_cycle.state = "charge"
                self.counter += 1

                self.ld.select_channel(dut.slotnum)
                this_cycle.vcap = self.read_volt(dut)

                threshold = float(config["Threshold"].strip("aAvV"))
                max_chargetime = config["max"]
                min_chargetime = config["min"]

                charge_time = this_cycle.time - start_time
                dut.charge_time = charge_time
                if (charge_time > max_chargetime):
                    all_charged &= True
                    dut.self_capacitance_measured=this_cycle.vcap # record the last voltage measured in self_capacitance_measured if charge time too long
                    dut.status = DUT_STATUS.Fail
                    dut.errormessage = "Charge Time Too Long."
                elif (this_cycle.vcap > threshold):
                    all_charged &= True
                    # dut.charge(status=False)
                    if (charge_time < min_chargetime):
                        dut.status = DUT_STATUS.Fail
                        dut.errormessage = "Charge Time Too Short."
                    else:
                        dut.status = DUT_STATUS.Idle  # pass
                else:
                    all_charged &= False
                dut.cycles.append(this_cycle)
                logger.info("dut: {0} status: {1} vcap: {2} "
                            "temp: {3} message: {4} ".
                            format(dut.slotnum, dut.status, this_cycle.vcap,
                                   this_cycle.temp, dut.errormessage))
            time.sleep(INTERVAL)

    def discharge_dut(self):
        """discharge
        """
        for dut in self.dut_list:
            if dut is None:
                continue
            config = load_test_item(self.config_list[dut.slotnum],
                                    "Discharge")
            if (not config["enable"]):
                continue
            if (config["stoponfail"]) & (dut.status != DUT_STATUS.Idle):
                continue
            # disable auto discharge
            self.switch_to_mb()
            self.auto_discharge(slot=dut.slotnum, status=False)
            # disable self discharge
            self.switch_to_dut(dut.slotnum)
            dut.self_discharge(status=False)
            # disable charge
            dut.charge(status=False)

            self.ld.select_channel(dut.slotnum)
            self.current = float(config["Current"].strip("aAvV"))
            self.ld.set_curr(self.current)  # set discharge current
            self.ld.input_on()
            dut.status = DUT_STATUS.Discharging

        # start discharge cycle
        all_discharged = False
        start_time = time.time()
        self.ps.setVolt(0.0)
        while (not all_discharged):
            all_discharged = True
            for dut in self.dut_list:
                if dut is None:
                    continue
                config = load_test_item(self.config_list[dut.slotnum],
                                        "Discharge")
                if (not config["enable"]):
                    continue
                if (config["stoponfail"]) & \
                        (dut.status != DUT_STATUS.Discharging):
                    continue
                self.switch_to_dut(dut.slotnum)
                # cap_in_ltc = dut.meas_capacitor()
                # print cap_in_ltc
                this_cycle = Cycle()
                this_cycle.vin = self.ps.measureVolt()
                try:
                    temperature = dut.check_temp()
                except aardvark.USBI2CAdapterException:
                    # temp ic not ready
                    temperature = 0
                this_cycle.temp = temperature
                this_cycle.counter = self.counter
                this_cycle.time = time.time()

                this_cycle.state = "discharge"
                self.ld.select_channel(dut.slotnum)
                this_cycle.vcap = self.read_volt(dut)
                # this_cycle.vcap = self.ld.read_volt()
                self.counter += 1

                threshold = float(config["Threshold"].strip("aAvV"))
                max_dischargetime = config["max"]
                min_dischargetime = config["min"]

                discharge_time = this_cycle.time - start_time
                dut.discharge_time = discharge_time
                if (discharge_time > max_dischargetime):
                    all_discharged &= True
                    self.ld.select_channel(dut.slotnum)
                    self.ld.input_off()
                    dut.status = DUT_STATUS.Fail
                    dut.errormessage = "Discharge Time Too Long."
                elif (this_cycle.vcap < threshold):
                    all_discharged &= True
                    self.ld.select_channel(dut.slotnum)
                    self.ld.input_off()
                    if (discharge_time < min_dischargetime):
                        dut.status = DUT_STATUS.Fail
                        dut.errormessage = "Discharge Time Too Short."
                    else:
                        dut.status = DUT_STATUS.Idle  # pass
                else:
                    all_discharged &= False
                dut.cycles.append(this_cycle)
                logger.info("dut: {0} status: {1} vcap: {2} "
                            "temp: {3} message: {4} ".
                            format(dut.slotnum, dut.status, this_cycle.vcap,
                                   this_cycle.temp, dut.errormessage))
            #time.sleep(0)
        self.ps.setVolt(PS_VOLT)

    def check_dut_discharge(self):
        """ check auto/self discharge function on each DUT.
        :return: None
        """
        for dut in self.dut_list:
            if dut is None:
                continue
            config = load_test_item(self.config_list[dut.slotnum],
                                    "Self_Measured_Capacitor")
            if (not config["enable"]):
                continue
            if (config["stoponfail"]) & (dut.status != DUT_STATUS.Idle):
                continue

            # disable auto discharge
            self.switch_to_mb()
            self.auto_discharge(slot=dut.slotnum, status=False)
            # disable charge
            self.switch_to_dut(dut.slotnum)
            dut.charge(status=False)

            # enable self discharge
            dut.self_discharge(status=True)

        for i in range(SD_COUNTER):
            for dut in self.dut_list:
                if dut is None:
                    continue
                if (not config["enable"]):
                    continue
                if (config["stoponfail"]) & (dut.status != DUT_STATUS.Idle):
                    continue

                self.switch_to_dut(dut.slotnum)
                this_cycle = Cycle()
                this_cycle.vin = self.ps.measureVolt()
                try:
                    temperature = dut.check_temp()
                except aardvark.USBI2CAdapterException:
                    # temp ic not ready
                    temperature = 0
                this_cycle.temp = temperature
                this_cycle.counter = self.counter
                this_cycle.time = time.time()
                this_cycle.state = "self_discharge"
                self.ld.select_channel(dut.slotnum)
                this_cycle.vcap = self.read_volt(dut)
                self.counter += 1
                logger.info("dut: {0} status: {1} vcap: {2} "
                            "temp: {3} message: {4} ".
                            format(dut.slotnum, dut.status, this_cycle.vcap,
                                   this_cycle.temp, dut.errormessage))
                dut.cycles.append(this_cycle)
            time.sleep(INTERVAL)

        for dut in self.dut_list:
            if dut is None:
                continue
            config = load_test_item(self.config_list[dut.slotnum],
                                    "Self_Measured_Capacitor")
            if (not config["enable"]):
                continue
            if (config["stoponfail"]) & (dut.status != DUT_STATUS.Idle):
                continue
            if dut.status != DUT_STATUS.Idle:
                continue
            cap_list = []
            pre_vcap, pre_time = None, None
            for cycle in dut.cycles:
                if cycle.state == "self_discharge":
                    if pre_vcap is None:
                        pre_vcap = cycle.vcap
                        pre_time = cycle.time
                    else:
                        cur_vcap = cycle.vcap
                        cur_time = cycle.time
                        cap = (cur_time - pre_time) \
                              / (float(config["Resistance"]) * math.log(pre_vcap /
                                                                        cur_vcap))
                        cap_list.append(cap)
            if (len(cap_list) > 0):
                capacitor = sum(cap_list) / float(len(cap_list))
                dut.self_capacitance_measured = capacitor
                logger.debug(cap_list)
            else:
                dut.capacitance_measured = 0
            if not (config["min"] < dut.self_capacitance_measured <
                        config["max"]):
                dut.status = DUT_STATUS.Fail
                dut.errormessage = "Capacitor out of range."
                logger.info("dut: {0} self meas capacitor: {1} message: {2} ".
                            format(dut.slotnum, dut.capacitance_measured,
                                   dut.errormessage))

    def program_dut(self):
        """ program vpd of DUT.
        :return: None
        """
        for dut in self.dut_list:
            if dut is None:
                continue
            config = load_test_item(self.config_list[dut.slotnum],
                                    "Program_VPD")
            if (not config["enable"]):
                continue
            if (config["stoponfail"]) & (dut.status != DUT_STATUS.Idle):
                continue
            self.switch_to_dut(dut.slotnum)

            try:
                dut.write_vpd(config["File"], config["PGEMID"])
                dut.read_vpd()
                dut.program_vpd = 1
            except AssertionError:
                dut.status = DUT_STATUS.Fail
                dut.errormessage = "Programming VPD Fail"
                logger.info("dut: {0} status: {1} message: {2} ".
                            format(dut.slotnum, dut.status, dut.errormessage))
            self.check_crc(dut)

    def check_crc(self,dut):

        crc_address_list1=[0x41,0x42,0x43,0x44,0x45,0x46,0x47,
                          0x48,0x49,0x4A,0x4B,0x4C,0x4D,0x4E,0x4F,
                          0x50,0x51,0x52,0x53,0x54,0x55,0x56,0x57,
                          0x58,0x59,0x5A,0x5B,
                          0x64,0x65,
                          0x78,0x79,0x7C,0x7F,
                          0x80,0x81,0x82,0x83,0x84,0x85,0x86,0x87,
                          0x88,0x89,0x8A,0x8B,0x8C,0x8D]
        crc_address_list2=[0x41,0x42,0x43,0x44,0x45,0x46,0x47,
                          0x48,0x49,0x4A,0x4B,0x4C,0x4D,0x4E,0x4F,
                          0x50,0x51,0x52,0x53,0x54,0x55,0x56,0x57,
                          0x58,0x59,0x5A,0x5B,
                          0x64,0x65,
                          0x78,0x79,0x7C,0x7F,
                          0x80,0x81,0x82,0x83,0x84,0x85,0x86,0x87,
                          0x88,0x89,0x8A,0x8B,0x8C,0x8D,
                          0xD0,0xD1,0xD2,0xD3,0xD4,0xD5,0xD6,0xD7,
                          0xD8,0xD9,
                          0xFF]


        crc=np.int16(0)
        temp1=np.int16(0)
        for temp in crc_address_list1:
            temp1=dut.read_vpd_byaddress(temp)
            crc=np.int16(np.bitwise_xor(crc,np.left_shift(temp1,8)))
            #logger.info("VPD1: {0} crc1 {1}  ".format(temp1 & 0xFF,crc & 0xffff))
            for i in range(8):
                if(np.bitwise_and(crc,0x8000)):
                    crc=np.int16(np.bitwise_xor(np.int16(np.left_shift(crc,1)),0x1021))
                else:
                    crc=np.int16(np.left_shift(crc,1))
        crc=hex(crc&0xffff)

        temp1=dut.read_vpd_byaddress(0x7D)
        crc_temp=(dut.read_vpd_byaddress(0x7E)<<8)+temp1
        logger.info("CRC1: {0} crc1 {1}  ".format(crc,crc_temp&0xffff))
        if crc_temp != int(crc,16):
            logger.info("crc not === {0}".format(type(crc)))
            dut.status=DUT_STATUS.Fail
            dut.errormessage="CRC fail"

        crc=np.int16(0)
        temp1=np.int16(0)
        for temp in crc_address_list2:
            temp1=dut.read_vpd_byaddress(temp)
            crc=np.int16(np.bitwise_xor(crc,np.left_shift(temp1,8)))
            #logger.info("VPD2: {0} crc2 {1}  ".format(temp1 & 0xFF,crc & 0xffff))
            for i in range(8):
                if(np.bitwise_and(crc,0x8000)):
                    crc=np.int16(np.bitwise_xor(np.int16(np.left_shift(crc,1)),0x1021))
                else:
                    crc=np.int16(np.left_shift(crc,1))
        crc=hex(crc&0xffff)

        temp1=dut.read_vpd_byaddress(0xFD)
        crc_temp=(dut.read_vpd_byaddress(0xFE)<<8)+temp1
        logger.info("crc2: {0} crc2 {1}  ".format(crc,crc_temp & 0xffff))
        if crc_temp != int(crc,16):
            logger.info("crc not === {0}".format(type(crc)))
            dut.status=DUT_STATUS.Fail
            dut.errormessage="CR2C fail"

    def check_temperature_dut(self):
        """
        check temperature value of IC on DUT.
        :return: None.
        """
        for dut in self.dut_list:
            if dut is None:
                continue
            config = load_test_item(self.config_list[dut.slotnum],
                                    "Check_Temp")
            if (not config["enable"]):
                continue
            if (config["stoponfail"]) & (dut.status != DUT_STATUS.Idle):
                continue
            self.switch_to_dut(dut.slotnum)
            temp = dut.check_temp()
            if not (config["min"] < temp < config["max"]):
                dut.status = DUT_STATUS.Fail
                dut.errormessage = "Temperature out of range."
                logger.info("dut: {0} status: {1} message: {2} ".
                            format(dut.slotnum, dut.status, dut.errormessage))

    def check_encryptedic_dut(self):
        """ check the data in encrypted ic, if data is not all zero, dut is
        passed.
        :return: None
        """
        for dut in self.dut_list:
            if dut is None:
                continue
            config = load_test_item(self.config_list[dut.slotnum],
                                    "Check_EncryptedIC")
            if (not config["enable"]):
                continue
            if (config["stoponfail"]) & (dut.status != DUT_STATUS.Idle):
                continue
            if dut.status != DUT_STATUS.Idle:
                continue

            self.switch_to_dut(dut.slotnum)
            if (not dut.encrypted_ic()):
                dut.status = DUT_STATUS.Fail
                dut.errormessage = "Check I2C on Encrypted IC Fail."
                logger.info("dut: {0} status: {1} message: {2} ".
                            format(dut.slotnum, dut.status, dut.errormessage))

    def auto_discharge(self, slot, status=False):
        """output PRESENT/AUTO_DISCH signal on TCA9555 on mother board.
           When status=True, discharge;
           When status=False, not discharge.
        """
        if (status):
            IO = 0
        else:
            IO = 1

        chnum = self.channel

        self.adk.slave_addr = 0x20 + chnum
        REG_INPUT = 0x00
        REG_OUTPUT = 0x02
        REG_CONFIG = 0x06

        # config PIO-0 to output and PIO-1 to input
        # first PIO-0 then PIO-1
        wdata = [REG_CONFIG, 0x00, 0xFF]
        self.adk.write(wdata)

        # read current status
        val = self.adk.read_reg(REG_INPUT, length=2)
        val = val[0]  # only need port 0 value

        # set current slot
        if (IO == 1):
            # set bit
            val |= (IO << slot)
        else:
            # clear bit
            val &= ~(0X01 << slot)

        # output
        # first PIO-0, then PIO-1
        wdata = [REG_OUTPUT, val, 0xFF]
        self.adk.write(wdata)

        # read status back
        val = self.adk.read_reg(REG_INPUT, length=2)
        val = val[0]  # only need port 0 value
        val = (val & (0x01 << slot)) >> slot
        assert val == IO

    def switch_to_dut(self, slot):
        """switch I2C ports by PCA9548A, only 1 channel is enabled.
        chnum(channel number): 0~7
        slotnum(slot number): 0~7
        """
        chnum = self.channel
        self.adk.slave_addr = 0x70 + chnum  # 0111 0000
        wdata = [0x01 << slot]

        # Switch I2C connection to current PGEM
        # Need call this function every time before communicate with PGEM
        self.adk.write(wdata)

    def switch_to_mb(self):
        """switch I2C ports back to mother board
           chnum(channel number): 0~7
        """
        chnum = self.channel
        self.adk.slave_addr = 0x70 + chnum  # 0111 0000
        wdata = 0x00

        # Switch I2C connection to mother board
        # Need call this function every time before communicate with
        # mother board
        self.adk.write(wdata)

    def read_power_fail_io(self, dut):
        """read power_fail_int signal on TCA9555 on mother board
        """
        chnum = self.channel
        self.adk.slave_addr = 0x20 + chnum
        REG_INPUT = 0x00
        # REG_OUTPUT = 0x02
        REG_CONFIG = 0x06
        # config PIO-0 to output and PIO-1 to input
        # first PIO-0 then PIO-1
        wdata = [REG_CONFIG, 0x00, 0xFF]
        self.adk.write(wdata)
        # read reg_input
        val = self.adk.read_reg(REG_INPUT, length=2)
        val = val[1]  # only need port 1 value
        # check current slot
        val = (val & (0x01 << dut.slotnum)) >> dut.slotnum
        return val

    def check_power_fail(self):
        self.switch_to_mb()

        # check power fail io with power on
        for dut in self.dut_list:
            if dut is None:
                continue
            config = load_test_item(self.config_list[dut.slotnum],
                                    "Check_PowerFailInt")
            if (not config["enable"]):
                continue
            if (config["stoponfail"]) & (dut.status != DUT_STATUS.Idle):
                continue
            if dut.status != DUT_STATUS.Idle:
                continue

            val = self.read_power_fail_io(dut)

            if (val != int(config["ON"])):
                dut.status = DUT_STATUS.Fail
                dut.errormessage = "check power_fail_int fail."
                logger.info("dut: {0} status: {1} int_io: {2} message: {3} ".
                            format(dut.slotnum, dut.status,
                                   val, dut.errormessage))

        # set power supply to 9V
        self.ps.setVolt(9.0)
        time.sleep(1.5)

        # check power fail io with power below 10
        for dut in self.dut_list:
            if dut is None:
                continue
            config = load_test_item(self.config_list[dut.slotnum],
                                    "Check_PowerFailInt")
            if (not config["enable"]):
                continue
            if (config["stoponfail"]) & (dut.status != DUT_STATUS.Idle):
                continue
            if dut.status != DUT_STATUS.Idle:
                continue

            val = self.read_power_fail_io(dut)

            if (val != int(config["OFF"])):
                dut.status = DUT_STATUS.Fail
                dut.errormessage = "check power_fail_int fail."
                logger.info("dut: {0} status: {1} int_io: {2} message: {3} ".
                            format(dut.slotnum, dut.status,
                                   val, dut.errormessage))

        # set power supply to normal
        self.ps.setVolt(PS_VOLT)

    def calculate_capacitance(self):
        """ calculate the capacitance of DUT, based on vcap list in discharging.
        :return: capacitor value
        """
        for dut in self.dut_list:
            if dut is None:
                continue
            config = load_test_item(self.config_list[dut.slotnum],
                                    "Capacitor")
            if (not config["enable"]):
                continue
            if (config["stoponfail"]) & (dut.status != DUT_STATUS.Idle):
                continue
            if dut.status != DUT_STATUS.Idle:
                continue
            cap_list = []
            pre_vcap, pre_time = None, None
            for cycle in dut.cycles:
                if cycle.state == "discharge":
                    if pre_vcap is None:
                        pre_vcap = cycle.vcap
                        pre_time = cycle.time
                    else:
                        cur_vcap = cycle.vcap
                        cur_time = cycle.time
                        if ( 5.2 < pre_vcap < 6.3) & ( 5.2 < cur_vcap < 6.3):
                            cap = (self.current * (cur_time - pre_time)) \
                                  / (pre_vcap - cur_vcap)
                            cap_list.append(cap)
                            #logger.info("pre_vcap: {0} cur_vcap: {1} cur_time: {2} pre_time: {3} ".
                                #format(pre_vcap, cur_vcap,cur_time,pre_time))
                        pre_vcap = cur_vcap
                        pre_time = cur_time
            if (len(cap_list) > 0):
                capacitor = sum(cap_list) / float(len(cap_list))
                dut.capacitance_measured = capacitor
                logger.info("capacitor: {0} ".format(dut.capacitance_measured))
            else:
                dut.capacitance_measured = 0
            if not (config["min"] < dut.capacitance_measured < config["max"]):
                dut.status = DUT_STATUS.Fail
                dut.errormessage = "Capacitor out of range."
                logger.info("dut: {0} capacitor: {1} message: {2} ".
                            format(dut.slotnum, dut.capacitance_measured,
                                   dut.errormessage))

    def save_db(self):
        # setup database
        # db should be prepared in cli.py
        sm = SessionManager()
        sm.prepare_db("sqlite:///" + RESULT_DB, [DUT, Cycle])
        session = sm.get_session("sqlite:///" + RESULT_DB)

        for dut in self.dut_list:
            if dut is None:
                continue
            for pre_dut in session.query(DUT). \
                    filter(DUT.barcode == dut.barcode).all():
                pre_dut.archived = 1
                session.add(pre_dut)
                session.commit()
            dut.archived = 0
            session.add(dut)
            session.commit()
        session.close()

    def save_file(self):
        """ save dut info to xml file
        :return:
        """
        for dut in self.dut_list:
            if dut is None:
                continue
            if not os.path.exists(RESULT_LOG):
                os.makedirs(RESULT_LOG)

            filename = dut.barcode + ".xml"
            filepath = os.path.join(RESULT_LOG, filename)
            i = 1
            while os.path.exists(filepath):
                filename = "{0}({1}).xml".format(dut.barcode, i)
                filepath = os.path.join(RESULT_LOG, filename)
                i += 1
            result = simplexml.dumps(dut.to_dict(), "entity")
            with open(filepath, "wb") as f:
                f.truncate()
                f.write(result)

    def prepare_to_exit(self):
        """ cleanup and save to database before exit.
        :return: None
        """
        for dut in self.dut_list:
            if dut is None:
                continue
            if (dut.status == DUT_STATUS.Idle):
                dut.status = DUT_STATUS.Pass
                msg = "passed"
            else:
                msg = dut.errormessage
            logger.info("TEST RESULT: dut {0} ===> {1}".format(
                dut.slotnum, msg))

        # save to xml logs
        self.save_file()

        # power off
        self.ps.deactivateOutput()

    def run(self):
        """ override thread.run()
        :return: None
        """
        while (not self.exit):
            state = self.queue.get()
            if (state == ChannelStates.EXIT):
                try:
                    self.prepare_to_exit()
                    self.exit = True
                    logger.info("Channel: Exit Successfully.")
                except Exception as e:
                    self.error(e)
            elif (state == ChannelStates.INIT):
                try:
                    logger.info("Channel: Initialize.")
                    self.init()
                    self.progressbar += 20
                except Exception as e:
                    self.error(e)
            elif (state == ChannelStates.CHARGE):
                try:
                    logger.info("Channel: Charge DUT.")
                    self.charge_dut()
                    self.progressbar += 20
                except Exception as e:
                    self.error(e)
            elif (state == ChannelStates.LOAD_DISCHARGE):
                try:
                    logger.info("Channel: Discharge DUT.")
                    self.discharge_dut()
                    self.progressbar += 30
                    time.sleep(1)
                except Exception as e:
                    self.error(e)
            elif (state == ChannelStates.PROGRAM_VPD):
                try:
                    logger.info("Channel: Program VPD.")
                    self.program_dut()
                    self.progressbar += 10
                except Exception as e:
                    self.error(e)
            elif (state == ChannelStates.CHECK_ENCRYPTED_IC):
                try:
                    logger.info("Channel: Check Encrypted IC.")
                    self.check_encryptedic_dut()
                    self.progressbar += 5
                except Exception as e:
                    self.error(e)
            elif (state == ChannelStates.CHECK_TEMP):
                try:
                    logger.info("Channel: Check Temperature")
                    self.check_temperature_dut()
                    self.progressbar += 5
                except Exception as e:
                    self.error(e)
            elif (state == ChannelStates.CHECK_CAPACITANCE):
                try:
                    logger.info("Channel: Check Capacitor Value")
                    self.calculate_capacitance()
                    self.progressbar += 5
                except Exception as e:
                    self.error(e)
            elif (state == ChannelStates.DUT_DISCHARGE):
                try:
                    logger.info("Channel: Self Mesaured Capacitor")
                    self.check_dut_discharge()
                    self.progressbar += 10
                except Exception as e:
                    self.error(e)
            elif (state == ChannelStates.CHECK_POWER_FAIL):
                try:
                    logger.info("Channel: Check Power Fail Interrupt")
                    self.check_power_fail()
                    self.progressbar += 10
                except Exception as e:
                    self.error(e)
            else:
                logger.error("unknown dut state, exit...")
                self.exit = True

    def auto_test(self):
        self.queue.put(ChannelStates.INIT)
        self.queue.put(ChannelStates.CHARGE)
        self.queue.put(ChannelStates.PROGRAM_VPD)
        self.queue.put(ChannelStates.CHECK_ENCRYPTED_IC)
        self.queue.put(ChannelStates.CHECK_TEMP)
        self.queue.put(ChannelStates.CHECK_POWER_FAIL)
        # self.queue.put(ChannelStates.DUT_DISCHARGE)
        self.queue.put(ChannelStates.LOAD_DISCHARGE)
        self.queue.put(ChannelStates.CHECK_CAPACITANCE)
        self.queue.put(ChannelStates.EXIT)
        self.start()

    def empty(self):
        for i in range(self.queue.qsize()):
            self.queue.get()

    def error(self, e):
        exc = sys.exc_info()
        logger.error(traceback.format_exc(exc))
        self.exit = True
        raise e

    def quit(self):
        self.empty()
        self.queue.put(ChannelStates.EXIT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # barcode = ["AGIGA9603-004BCA02144800000002-06",
    #            "AGIGA9603-004BCA02144800000002-06",
    #            "AGIGA9603-004BCA02144800000002-06",
    #            "AGIGA9603-004BCA02144800000002-06"]
    barcode = ["AGIGA9811-001BCA02143900000228-01"]
    ch = Channel(barcode_list=barcode, channel_id=0,
                 name="UFT_CHANNEL", cable_barcodes_list=[""])
    # ch.start()
    # ch.queue.put(ChannelStates.INIT)
    # ch.queue.put(ChannelStates.CHARGE)
    # ch.queue.put(ChannelStates.PROGRAM_VPD)
    # ch.queue.put(ChannelStates.CHECK_ENCRYPTED_IC)
    # ch.queue.put(ChannelStates.CHECK_TEMP)
    # ch.queue.put(ChannelStates.LOAD_DISCHARGE)
    # ch.queue.put(ChannelStates.CHECK_CAPACITANCE)
    # ch.queue.put(ChannelStates.EXIT)
    ch.auto_test()
    # ch.switch_to_mb()
    # ch.switch_to_dut(0)
    # ch.init()
    # ch.charge_dut()
    # ch.discharge_dut()
