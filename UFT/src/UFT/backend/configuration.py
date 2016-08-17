#!/usr/bin/env python
# encoding: utf-8
"""PGEM test configuration model.
Default connect to configuration.db which save the test items settings.
"""

__version__ = "0.1"
__author__ = "@fanmuzhi, @boqiling"
__all__ = ["PGEMConfig", "TestItem"]

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Boolean
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

SQLBase = declarative_base()


class PGEMConfig(SQLBase):
    __tablename__ = "configuration"

    id = Column(Integer, primary_key=True)
    partnumber = Column(String(20), nullable=False)
    description = Column(String(50))
    revision = Column(String(5), nullable=False)

    testitems = relationship("TestItem", backref="configuration",
                             cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint('partnumber',
                                       'revision',
                                       name='_partnumber_revision_uc_'),)

    def to_dict(self):
        items_list = {}
        for item in self.testitems:
            items_list.update(item.to_dict())
        # items_list = {"ITEM": items_list}
        return {"partnumber": self.partnumber,
                "description": self.description,
                "revision": self.revision,
                "testitems": items_list}


class TestItem(SQLBase):
    __tablename__ = "test_item"

    id = Column(Integer, primary_key=True)
    configid = Column(Integer, ForeignKey("configuration.id"))

    name = Column(String(10), nullable=False)
    description = Column(String(30))
    enable = Column(Boolean, nullable=False)
    min = Column(Float)
    max = Column(Float)
    stoponfail = Column(Boolean, default=True)
    misc = Column(String(50))

    def to_dict(self):
        return {
            self.name: {
                "description": self.description,
                "enable": int(self.enable),
                "min": self.min,
                "max": self.max,
                "stoponfail": int(self.stoponfail),
                "misc": self.misc
            }
        }


if __name__ == "__main__":
    from session import SessionManager

    dburi = "sqlite:///configuration.db"
    sm = SessionManager()
    session = sm.get_session(dburi)
    sm.prepare_db(dburi, [PGEMConfig, TestItem])

    # Insert Example
    CrystalConfig = PGEMConfig()
    CrystalConfig.partnumber = "AGIGA9601-002BCA"
    CrystalConfig.description = "Crystal"
    CrystalConfig.revision = "04"

    CheckTemp = TestItem()
    CheckTemp.name = "Check_Temp"
    CheckTemp.description = "Check Temperature on chip SE97BTP, data in degree"
    CheckTemp.enable = True
    CheckTemp.min = 5.0
    CheckTemp.max = 30.0
    CheckTemp.stoponfail = False

    Charge = TestItem()
    Charge.name = "Charge"
    Charge.description = "Charge DUT with BQ24707, limition in seconds"
    Charge.enable = True
    Charge.min = 30.0
    Charge.max = 120.0
    Charge.stoponfail = True

    try:
        CrystalConfig.testitems.append(CheckTemp)
        CrystalConfig.testitems.append(Charge)
        session.add(CrystalConfig)
        session.commit()
    except Exception as e:
        print e
        session.rollback()

    # Query Example
    crystal = session.query(PGEMConfig).filter(
        PGEMConfig.partnumber == "AGIGA9601-002BCA",
        PGEMConfig.revision == "04").first()
    for testitem in crystal.testitems:
        if testitem.name == "Charge":
            print testitem.name
            print testitem.description
            print testitem.max

    print crystal.to_dict()
