#!/usr/bin/env python
# encoding: utf-8
"""test code for UFT test process
"""
__version__ = "0.1"
__author__ = "@boqiling"

from UFT.models import PGEMBase, DUT_STATUS, DUT, Cycle
from UFT.backend.session import SessionManager
from UFT.backend import load_config, load_test_item
from UFT.devices import pwr
from UFT.devices import load
from UFT.devices import aardvark
from UFT.config import *
import time

# barcode list for test purpose only
barcode_list = ["AGIGA9601-002BCA02143500000001-04",
                "AGIGA9603-004BCA02144800000002-06",
                "AGIGA9711-004BCA02143500000003-09",
                "AGIGA9601-002BCA02143500000004-04"]


def run():
    # aardvark
    adk = aardvark.Adapter()
    adk.open(portnum=ADK_PORT)

    # setup dut_list
    dut_list = []
    config_list = []
    for slot in range(TOTAL_SLOTNUM):
        dut = PGEMBase(device=adk, slot=slot, barcode=barcode_list[slot])
        dut.status = DUT_STATUS.Idle
        dut_list.append(dut)

        # load config
        dut_config = load_config(CONFIG_DB, dut.partnumber, dut.revision)
        config_list.append(dut_config)

    # setup load
    ld = load.DCLoad(port=LD_PORT, timeout=LD_DELAY)
    for slot in range(TOTAL_SLOTNUM):
        ld.select_channel(slot)
        ld.input_off()
        ld.protect_on()
        ld.change_func(load.DCLoad.ModeCURR)
        #ld.set_curr(0.8)    # discharge current, should be in dut config.

    # setup main power 12V
    ps = pwr.PowerSupply()
    ps.selectChannel(node=PS_ADDR, ch=PS_CHAN)

    setting = {"volt": PS_VOLT, "curr": PS_CURR,
               "ovp": PS_OVP, "ocp": PS_OCP}
    ps.set(setting)
    ps.activateOutput()
    time.sleep(1)
    volt = ps.measureVolt()
    curr = ps.measureCurr()
    assert (PS_VOLT-1) < volt < (PS_VOLT+1)
    assert curr >= 0

    # setup database
    sm = SessionManager()
    my_session = sm.get_session(RESULT_DB)
    sm.prepare_db(RESULT_DB, [DUT, Cycle])

    # charging
    #TODO add time out gauge here.

    counter = 0     # counter for whole charging and discharging

    for slot in range(TOTAL_SLOTNUM):
        charge_config = load_test_item(config_list[slot], "Charge")

        dut_list[slot].switch()   # to dut
        dut_list[slot].charge(option=charge_config, status=True)
        dut_list[slot].slotnum = slot

    all_charged = False
    while(not all_charged):
        all_charged = True
        for slot in range(TOTAL_SLOTNUM):
            charge_config = load_test_item(config_list[slot], "Charge")

            this_cycle = Cycle()
            this_cycle.vin = ps.measureVolt()
            this_cycle.temp = dut_list[slot].check_temp()
            this_cycle.time = counter
            counter += 1

            ld.select_channel(slot)
            this_cycle.vcap = ld.read_volt()

            threshold = float(charge_config["Threshold"].strip("aAvV"))
            if(this_cycle.vcap > threshold):
                all_charged &= True
                dut_list[slot].status = DUT_STATUS.Charged
            else:
                all_charged &= False
            dut_list[slot].cycles.append(this_cycle)
        time.sleep(INTERVAL)

    # programming
    for slot in range(TOTAL_SLOTNUM):
        program_config = load_test_item(config_list[slot], "Program_VPD")
        dut_list[slot].write_vpd(program_config["File"])
        dut_list[slot].read_vpd()

    # discharging
    #TODO add time out gauge here.
    for slot in range(TOTAL_SLOTNUM):
        charge_config = load_test_item(config_list[slot], "Charge")
        discharge_config = load_test_item(config_list[slot], "Discharge")

        dut_list[slot].switch()   # to dut
        dut_list[slot].charge(option=charge_config, status=False)

        ld.select_channel(slot)

        current = float(discharge_config["Current"].strip("aAvV"))
        ld.set_curr(current)  # set discharge current
        ld.input_on()

    all_discharged = False
    while(not all_discharged):
        all_discharged = True
        for slot in range(TOTAL_SLOTNUM):
            discharge_config = load_test_item(config_list[slot], "Discharge")

            this_cycle = Cycle()
            this_cycle.vin = ps.measureVolt()
            this_cycle.temp = dut_list[slot].check_temp()
            this_cycle.time = counter
            counter += 1

            ld.select_channel(slot)
            this_cycle.vcap = ld.read_volt()

            threshold = float(discharge_config["Threshold"].strip("aAvV"))
            if(this_cycle.vcap <= threshold):
                all_discharged &= True
                dut_list[slot].status = DUT_STATUS.Discharged
            else:
                all_discharged &= False
            dut_list[slot].cycles.append(this_cycle)
        time.sleep(INTERVAL)

    # save to database
    for dut in dut_list:
        if(dut.status != DUT_STATUS.Blank):
            my_session.add(dut)
            my_session.commit()


if __name__ == "__main__":
    run()
