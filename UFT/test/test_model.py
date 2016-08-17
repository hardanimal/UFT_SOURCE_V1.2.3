#!/usr/bin/env python
# encoding: utf-8
"""description:
"""
__version__ = "0.1"
__author__ = "@boqiling"


from UFT.backend.session import SessionManager
from UFT.models import DUT, Cycle, DUT_STATUS

sm = SessionManager()
session = sm.get_session("sqlite:///pgem.db")
sm.prepare_db("sqlite:///pgem.db", [DUT, Cycle])

dut = DUT()
dut.sn = "888888"
dut.partnumber = "crystal"
dut.status = DUT_STATUS.Idle

session.add(dut)
session.commit()

try:
    dut = session.query(DUT).filter(DUT.partnumber == "crystal").first()

    print dut.sn

    #dut.__dict__.update({"sn": "12345", "slotnum": 7})
    d = {"status": DUT_STATUS.Idle, "slotnum": 2}
    for k, v in d.items():
        setattr(dut, k, v)

    cycle = Cycle()
    c = {"vin": 47, "vcap": 43, "temp": 20}
    for k, v in c.items():
        setattr(cycle, k, v)
    dut.cycles.append(cycle)

    session.commit()
except Exception as e:
    print e
    session.rollback()
