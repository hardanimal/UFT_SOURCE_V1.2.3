#!/usr/bin/env python
# encoding: utf-8
"""Base Model for Cororado PGEM I2C functions
"""
__version__ = "0.1"
__author__ = "@fanmuzhi, @boqiling"
__all__ = ["PGEMBase"]

import logging
from logger_handler import init_logger

formatter = logging.Formatter('[ %(asctime)s ] (%(threadName)s  %(thread)d)'
                              ' %(module)s : %(message)s')
logger = logging.getLogger(__name__)
init_logger(logger, formatter, logging.INFO)
