#!/usr/bin/env python
# encoding: utf-8
"""Base Model for Cororado PGEM I2C functions
"""
__version__ = "0.1"
__author__ = "@fanmuzhi, @boqiling"
__all__ = ["PGEMBase"]

import logging
import struct
import re
from dut import DUT

logger = logging.getLogger(__name__)

# EEPROM dict for coronado
EEP_MAP = [{"name": "TEMPHIST", "addr": 0x000, "length": 2, "type": "int"},
           {"name": "CAPHIST", "addr": 0x021, "length": 32, "type": "int"},
           {"name": "CHARGER", "addr": 0x041, "length": 1, "type": "int"},
           {"name": "CAPACITANCE", "addr": 0x042, "length": 1, "type": "int"},
           {"name": "CHARGEVOL", "addr": 0x043, "length": 2, "type": "int"},
           {"name": "CHGMAXVAL", "addr": 0x045, "length": 2, "type": "int"},
           {"name": "POWERDET", "addr": 0x047, "length": 1, "type": "int"},
           {"name": "CHARGECUR", "addr": 0x048, "length": 2, "type": "int"},
           {"name": "HWVER", "addr": 0x04A, "length": 2, "type": "str"},
           {"name": "CAPPN", "addr": 0x04C, "length": 16, "type": "str"},
           # SN, need program, id
           {"name": "SN", "addr": 0x05C, "length": 8, "type": "str"},
           {"name": "PCBVER", "addr": 0x064, "length": 2, "type": "str"},
           # MFDATE, need program, yyww
           {"name": "MFDATE", "addr": 0x066, "length": 4, "type": "str"},
           # ENDUSR, need program, vv
           {"name": "ENDUSR", "addr": 0x06A, "length": 2, "type": "str"},
           # PCA, need program, default all 0
           {"name": "PCA", "addr": 0x06C, "length": 11, "type": "str"},
           {"name": "INITIALCAP", "addr": 0x077, "length": 1, "type": "int"},
           {"name": "PGEMID", "addr": 0x0DA, "length": 1, "type": "str"},
           ]

# PGEM ID write to saphire.
PGEM_ID = {0: "A", 1: "B", 2: "C", 3: "D"}

BARCODE_PATTERN = re.compile(
    r'^(?P<SN>(?P<PN>AGIGA\d{4}-\d{3}\w{3})(?P<VV>\d{2})(?P<YY>[1-2][0-9])'
    r'(?P<WW>[0-4][0-9]|5[0-3])(?P<ID>\d{8})-(?P<RR>\d{2}))$')


class PGEMException(Exception):
    """PGEM Exception
    """
    pass


class PGEMBase(DUT):
    """PGEM Base Class, All models should be inheret from this base class.
    """
    TEMP_SENSRO_ADDR = 0x1B

    def __init__(self, device, barcode, **kvargs):
        # slot number for dut on fixture location.
        # from 0 to 3, totally 4 slots in UFT
        self.slotnum = kvargs.get("slot", 0)

        # I2C adapter device
        self.device = device

        # barcode
        self.barcode = barcode
        r = BARCODE_PATTERN.search(barcode)
        if r:
            self.barcode_dict = r.groupdict()
            self.partnumber = self.barcode_dict["PN"]
            self.revision = self.barcode_dict["RR"]
        else:
            raise PGEMException("Unvalide barcode.")

    @staticmethod
    def _query_map(mymap, **kvargs):
        """method to search the map (the list of dict, [{}, {}])
        :params mymap:  the map to search
                kvargs: query conditon key=value, key should be in the dict.
        :return: the dict match the query contdtion or None.
        """
        r = mymap
        for k, v in kvargs.items():
            r = filter(lambda row: row[k] == v, r)
        return r

    def read_vpd_byname(self, reg_name):
        """method to read eep_data according to eep_name
        eep is one dict in eep_map, for example:
        {"name": "CINT", "addr": 0x02B3, "length": 1, "type": "int"}
        :param reg_name: register name, e.g. "PCA"
        :return value of the register
        """
        eep = self._query_map(EEP_MAP, name=reg_name)[0]
        start = eep["addr"]  # start_address
        length = eep["length"]  # length
        typ = eep["type"]  # type

        self.device.slave_addr = 0x53
        datas = self.device.read_reg(start, length)

        if (typ == "word"):
            val = 0
            for i in range(0, len(datas)):
                val += datas[i] << 8 * i
        if (typ == "str"):
            val = ''.join(chr(i) for i in datas)
        if (typ == "int"):
            val = 0
            for i in range(0, len(datas)):
                val += datas[i] << 8 * i
        return val

    def read_vpd_byaddress(self, address):
        """method to read eep_data according to eep_address
        :return value of the register
        added by pzho
        """
        self.device.slave_addr = 0x53
        datas = self.device.read_reg(address, 1)
        val = datas[0]
        '''for i in range(0, len(datas)):
            val += datas[i] << 8 * i'''
        return val

    def read_vpd(self):
        """method to read out EEPROM info from dut
        :return a dict of vpd names and values.
        """
        dut = {}
        for eep in EEP_MAP:
            reg_name = eep["name"]
            dut.update({reg_name.lower(): self.read_vpd_byname(reg_name)})
        # set self.values to write to database later.
        for k, v in dut.items():
            setattr(self, k, v)

        return dut

    @staticmethod
    def load_bin_file(filepath):
        """read a file and transfer to a binary list
        :param filepath: file path to load
        """
        datas = []
        f = open(filepath, 'rb')
        s = f.read()
        for x in s:
            rdata = struct.unpack("B", x)[0]
            datas.append(rdata)
        return datas

    def write_vpd(self, filepath, write_id):
        """method to write barcode information to PGEM EEPROM
        :param filepath: the ebf file location.
        """
        buffebf = self.load_bin_file(filepath)
        # [ord(x) for x in string]
        id = [ord(x) for x in self.barcode_dict['ID']]
        yyww = [ord(x) for x in (self.barcode_dict['YY'] +
                                 self.barcode_dict['WW'])]
        vv = [ord(x) for x in self.barcode_dict['VV']]

        # id == SN == Product Serial Number
        eep = self._query_map(EEP_MAP, name="SN")[0]
        buffebf[eep["addr"]: eep["addr"] + eep["length"]] = id

        # yyww == MFDATE == Manufacture Date YY WW
        eep = self._query_map(EEP_MAP, name="MFDATE")[0]
        buffebf[eep["addr"]: eep["addr"] + eep["length"]] = yyww

        # vv == ENDUSR == Manufacturer Name
        eep = self._query_map(EEP_MAP, name="ENDUSR")[0]
        buffebf[eep["addr"]: eep["addr"] + eep["length"]] = vv

        if (int(write_id)):
            eep = self._query_map(EEP_MAP, name="PGEMID")[0]
            buffebf[eep["addr"]: eep["addr"] + eep["length"]] = \
                [ord(PGEM_ID[self.slotnum])]
        # write to VPD
        self.device.slave_addr = 0x53
        # can be start with 0x41, 0x00 for ensurance.
        for i in range(0x00, len(buffebf)):
            self.device.write_reg(i, buffebf[i])
            self.device.sleep(5)

        # readback to check
        assert self.barcode_dict["ID"] == self.read_vpd_byname("SN")
        assert (self.barcode_dict["YY"] + self.barcode_dict["WW"]) == \
               self.read_vpd_byname("MFDATE")
        assert self.barcode_dict["VV"] == self.read_vpd_byname("ENDUSR")

        if (int(write_id)):
            assert PGEM_ID[self.slotnum] == self.read_vpd_byname("PGEMID")

    def control_led(self, status="off"):
        """method to control the LED on DUT chip PCA9536DP
        :param status: status=1, LED off, default. staus=0, LED on.
        """
        LOGIC = {"on": 0, "off": 1}
        status = LOGIC.get(status)
        logger.debug("LED: {0}".format(status))
        if (status is None):
            raise PGEMException("wrong LED status is set")

        self.device.slave_addr = 0x41
        REG_OUTPUT = 0x01
        REG_CONFIG = 0x03

        # config PIO to output
        wdata = [REG_CONFIG, 0x00]
        self.device.write(wdata)

        # set LED status
        out = status << 1
        wdata = [REG_OUTPUT, out]
        self.device.write(wdata)

    def self_discharge(self, status=False):
        """PGEM self discharge, controlled by I/O expander IC, address 0x41
        :param status: status=False, not discharge; status=True, discharge.
        """
        if (status):
            IO = 1
        else:
            IO = 0

        self.device.slave_addr = 0x41
        REG_OUTPUT = 0x01
        REG_CONFIG = 0x03

        # config PIO to output
        wdata = [REG_CONFIG, 0x00]
        self.device.write(wdata)

        # set IO status
        wdata = [REG_OUTPUT, IO]
        self.device.write(wdata)

    def encrypted_ic(self):
        """Check if encypted ic is working.
        :return: True for valid data.
        """
        val = self.device.read_reg(0x00, length=128)
        logger.debug("encrypted data: {0}".format(val))
        # valid data in 0x00 to 0x80 (address 0 to 127)
        # 0xFF in 0x80 to 0xFF (address 128 to 256)
        try:
            for v in val:
                assert v == 255
        except AssertionError:
            # good
            return True
        return False

    def write_bq24707(self, reg_addr, wata):
        """ write regsiter value to charge IC BQ24707
        :param reg_addr: register address of BQ24707
        :param wdata: data to write
        """
        self.device.slave_addr = 0x09

        # write first low 8bits, then high 8bits
        self.device.write_reg(reg_addr, [wata & 0x00FF, wata >> 8])

    def read_bq24707(self, reg_addr):
        """read register value from charge IC BQ24707
        :param reg_addr: register address
        :return: value of the register address
        """
        self.device.slave_addr = 0x09
        ata_in = self.device.read_reg(reg_addr, length=2)

        # first low 8bits then high 8bits
        val = (ata_in[1] << 8) + ata_in[0]
        return val

    def charge(self, status=True, **kvargs):
        """Send charge option to charge IC to start the charge.
        Charge IC BQ24707 is used as default.
        Override this function is use other IC instead.
        :param kvargs: option dict of charge option, charge voltage, etc.
        :param status: status=True, start charge; status=False, stop charge.
        """
        # BQ24707 register address
        CHG_OPT_ADDR = 0x12
        CHG_CUR_ADDR = 0x14
        CHG_VOL_ADDR = 0x15
        INPUT_CUR_ADDR = 0x3F
        MAN_ID_ADDR = 0xFE
        DEV_ID_ADDR = 0xFF

        # check IC
        logger.debug("BQ24707 ID {0} {1}".format(self.read_bq24707(
            MAN_ID_ADDR), self.read_bq24707(DEV_ID_ADDR)))

        if status:
            option = kvargs.get("option")
            # start charge
            # convert options from string to int
            for k, v in option.items():
                if k in ["ChargeCurrent", "ChargeVoltage",
                         "ChargeOption", "InputCurrent"]:
                    option[k] = int(v, 0)

            # write options
            charge_option = option["ChargeOption"]  # 0x1990
            charge_option &= ~(0x01)  # clear last bit

            self.write_bq24707(CHG_OPT_ADDR, charge_option)
            self.write_bq24707(CHG_CUR_ADDR, option["ChargeCurrent"])  # 0x01C0
            self.write_bq24707(CHG_VOL_ADDR, option["ChargeVoltage"])  # 0x1200
            self.write_bq24707(INPUT_CUR_ADDR, option["InputCurrent"])  # 0x0400

            # read back to check if written successfully
            assert self.read_bq24707(CHG_OPT_ADDR) == charge_option
            assert self.read_bq24707(CHG_CUR_ADDR) == option["ChargeCurrent"]
            assert self.read_bq24707(CHG_VOL_ADDR) == option["ChargeVoltage"]
            assert self.read_bq24707(INPUT_CUR_ADDR) == option["InputCurrent"]
        else:
            charge_option = self.read_bq24707(CHG_OPT_ADDR)
            # stop charge
            charge_option |= 0x01  # set last bit
            self.write_bq24707(CHG_OPT_ADDR, charge_option)

    @staticmethod
    def _calc_temp(temp):
        # method to caculate the temp sensor value of chip SE97BTP
        if (int(temp) & (0x01 << 12)):
            # check 12 bit, 1 for negative , 0 for positive
            result = (~(int(temp) >> 1) & 0xFFF) * 0.125
            # 0.125 for resolution
            result += 0.125  # since FFFF = -0.125, not 0.
            result = -result
        else:
            result = ((int(temp) >> 1) & 0xFFF) * 0.125
            # 0.125 for resolution
        return result

    def check_temp(self):
        """check temperature on SE97B of DUT.
        :return: temperature value
        """
        # self.device.slave_addr = self.TEMP_SENSRO_ADDR
        self.device.slave_addr = 0x1B
        # self.device.slave_addr = 0x1A
        # check device id
        # val = self.device.read_reg(0x07, length=2)
        # val = (val[0] << 8) + val[1]
        # assert val == 0xA203

        # check temp value
        val = self.device.read_reg(0x05, length=2)
        val = (val[0] << 8) + val[1]

        temp = self._calc_temp(val)
        logger.debug("temp value: {0}".format(temp))
        return temp


class Diamond4(PGEMBase):
    """
    PGEM with LTC3350 Charge IC used instead of BQ24707 class.
    """

    def __init__(self, device, barcode, **kvargs):
        super(Diamond4, self).__init__(device, barcode, **kvargs)
        logger.debug("LTC3350 Charge IC used instead of BQ24707, unknown ID")
        # self.TEMP_SENSRO_ADDR = 0x1A

    def write_ltc3350(self, reg_addr, wata):
        """ write regsiter value to charge IC LTC3350
        :param reg_addr: register address of LTC3350
        :param wdata: data to write
        """
        self.device.slave_addr = 0x09

        # write first low 8bits, then high 8bits
        self.device.write_reg(reg_addr, [wata & 0x00FF, wata >> 8])

    def start_cap_meas(self):
        self.device.slave_addr = 0x09
        self.device.write_reg(0x17, 0x01)

    def read_ltc3350(self, reg_addr):
        """read register value from charge IC LTC3350
        :param reg_addr: register address
        :return: value of the register address
        """
        self.device.slave_addr = 0x09
        ata_in = self.device.read_reg(reg_addr, length=2)

        # first low 8bits then high 8bits
        val = (ata_in[1] << 8) + ata_in[0]
        return val

    def charge(self, status=True, **kvargs):
        """
        Charge IC LTC3350 used instead of BQ24707.
        :param kvargs: option dict of charge option, charge voltage, etc.
        :param status: status=True, start charge; status=False, stop charge.
        """
        VCAPFB_DAC_ADDR = 0x05
        VSHUNT_ADDR = 0x06
        CTL_REG_ADDR = 0x17
        NUM_CAPS_ADDR = 0x1A
        CHRG_STATUS_ADDR = 0x1B

        # VCAPFB_DAC = 0xD

        # self.write_ltc3350(CTL_REG_ADDR, 0x01)
        # check IC
        # logger.debug("LTC3350 Charge IC used instead of BQ24707, unknown ID")
        if status:
            option = kvargs.get("option")
            # start charge
            # convert options from string to int
            for k, v in option.items():
                if k in ["vcapfb_dac", "vshunt", ]:
                    option[k] = int(v, 0)
            # write options
            vcapfb_dac = option["vcapfb_dac"]  # 0xC or 0xD or 0xE
            vshunt = option["vshunt"]  # 0x3998
            self.write_ltc3350(VSHUNT_ADDR, vshunt)
            self.write_ltc3350(VCAPFB_DAC_ADDR, vcapfb_dac)
            # self.write_ltc3350(0x02, 0x78)
            # self.write_ltc3350(0x17, 0x01)
        else:
            # stop charge
            self.write_ltc3350(VSHUNT_ADDR, 0x0000)
            self.write_ltc3350(VCAPFB_DAC_ADDR, 0x0)

    def meas_vcap(self):
        val = self.read_ltc3350(0x26) * 0.001465
        # print val
        return val

    def meas_capacitor(self):
        MEAS_CAP_ADDR = 0x1E
        val = self.read_ltc3350(MEAS_CAP_ADDR) * 591 * 330
        # print val
        return val


if __name__ == "__main__":
    import time

    logging.basicConfig(level=logging.DEBUG)

    from UFT.devices.aardvark import pyaardvark

    adk = pyaardvark.Adapter()
    adk.slave_addr = 0x70 + 0x00  # 0111 0000
    wdata = [0x01 << 0]
    adk.write(wdata)

    print adk.unique_id()

    barcode = "AGIGA9811-001BCA02143900000228-01"
    # # ch.init([barcode, "", "", ""])      # first one is valid.
    #
    # bq24704_option = {"ChargeOption": 0x1990,
    #                   "ChargeCurrent": 0x01C0, "ChargeVoltage": 0x1200,
    #                   "InputCurrent": 0x0400}

    # dut = PGEMBase(device=adk, slot=0, barcode=barcode)
    dut = Diamond4(device=adk, slot=0, barcode=barcode)
    # dut.charge(option=bq24704_option, status=True)
    #
    # print dut.read_vpd()
    # dut.control_led(status="on")
    #
    # path = "./101-40028-01-Rev02 Crystal2 VPD.ebf"
    # dut.write_vpd(path)
    #
    # print dut.read_vpd()
    # print dut.check_temp()
    #
    # dut.charge(option=bq24704_option, status=False)
    # dut.self_discharge(True)

    # print dut.check_power_fail()
    # dut.auto_discharge(True)

    VCAPFB_DAC_ADDR = 0x05
    VSHUNT_ADDR = 0x06
    # dut.charge(status=False)
    # dut.write_ltc3350(0x02, 0x78)
    # dut.write_ltc3350(0x17, 0x01)
    # dut.start_cap_meas()
    print "ctl_reg:", bin(dut.read_ltc3350(0x17))
    # print "per:", dut.read_ltc3350(0x04)*10, "s"
    print "vshunt:", dut.read_ltc3350(VSHUNT_ADDR)
    # print "num_caps:", dut.read_ltc3350(0x1A)
    print "vcapfb_dac:", dut.read_ltc3350(VCAPFB_DAC_ADDR)
    print "meas_cap", dut.read_ltc3350(0x1E) * 591 * 330, "uF"
    print "meas_Vin:", dut.read_ltc3350(0x25) * 0.00221, " V"
    print "meas_Vout:", dut.read_ltc3350(0x27) * 0.00221, " V"
    print "meas_Vcap1:", dut.read_ltc3350(0x20) * 0.0001835, " V"
    print "meas_Vcap2:", dut.read_ltc3350(0x21) * 0.0001835, " V"
    print "meas_Vcap3:", dut.read_ltc3350(0x22) * 0.0001835, " V"
    print "meas_Vcap:", dut.read_ltc3350(0x26) * 0.001476, " V"

    print "chrg_status", bin(dut.read_ltc3350(0x1B))

    temp = dut.check_temp()
    print "temp: ", temp
    adk.close()
