#!/usr/bin/env python
# encoding: utf-8
"""Model for PGEM config
"""
__version__ = "0.1"
__author__ = "@fanmuzhi, @boqiling"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.sqlite.base import dialect


class SessionManager(object):
    def __init__(self):
        self.engine = {}
        self.session = {}

    def get_engine(self, connectString):
        if (connectString in self.engine):
            engine = self.engine[connectString]
        else:
            engine = create_engine(connectString)
            self.engine[connectString] = engine
        return engine

    def prepare_db(self, connectString, models):
        engine = self.get_engine(connectString)
        for model in models:
            model.metadata.create_all(engine)

    def get_session(self, connectString):
        if (connectString in self.session):
            session = self.session[connectString]
        else:
            engine = self.get_engine(connectString)
            session = sessionmaker(bind=engine)
            self.session[connectString] = session
        return session()
