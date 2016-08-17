#!/usr/bin/env python
# encoding: utf-8
"""command line interface for UFT
"""
__version__ = "0.1"
__author__ = "@fanmuzhi, @boqiling"
import time
import argparse
import logging

logger = logging.getLogger(__name__)

# pass args
def parse_args():
    parser = argparse.ArgumentParser(description="Universal Functional Test "
                                                 "Program for Agigatech PGEM. "
                                                 "@boqiling 2014.")
    parser.add_argument('-l', '--list-config',
                        dest='listconfig',
                        action='store_true',
                        help='list current configuration of UFT',
                        default=False)
    parser.add_argument('--run',
                        dest='run',
                        action='store_true',
                        help='run test automatically',
                        default=False)
    parser.add_argument('--syncdb',
                        dest='syncdb',
                        action='store',
                        help='synchronize the configuration file with '
                             'configuration database',
                        default=False)
    parser.add_argument('--debug',
                        dest='debug',
                        action='store_true',
                        help='start debug hardware and hardware connections',
                        default=False)
    parser.add_argument('-v', '--verbose',
                        dest='verbose',
                        action='store_true',
                        help='print debug information on the screen',
                        default=False)

    args = parser.parse_args()
    return args


# cli command to synchronize the dut config
def synchronize_db(directory):
    from UFT import config
    from UFT.backend import sync_config
    import os

    if os.path.isdir(directory):
        db_uri = "sqlite:///" + config.CONFIG_DB
        sync_config(db_uri, directory)
    else:
        logger.error("Not valid path: {0}".format(directory))


# cli command to debug hardware

# cli command to run single test
def single_test():
    from UFT.channel import ChannelStates, Channel
    from UFT import config

    # barcode = "AGIGA9601-002BCA02143500000002-04"
    barcode_list = []
    for i in range(config.TOTAL_SLOTNUM):
        barcode_list.append(raw_input("please scan the barcode of dut{"
                                      "0}".format(i)) or "")
    ch = Channel(barcode_list=barcode_list, channel_id=0,
                 name="UFT_CHANNEL")
    ch.auto_test()
    while (ch.is_alive):
        print "test progress: {0}%".format(ch.progressbar)
        time.sleep(2)


# TODO cli command to generate test reports

#TODO cli command to generate dut charts

def main():
    logging.basicConfig(level=logging.INFO)

    args = parse_args()
    if args.verbose:
        from UFT import logger

        logger.setLevel(level=logging.DEBUG)
    if args.debug:
        pass
    if args.listconfig:
        pass
    if args.syncdb:
        synchronize_db(args.syncdb)
    if args.run:
        single_test()


if __name__ == "__main__":
    main()
