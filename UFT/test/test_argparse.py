#!/usr/bin/env python
# encoding: utf-8
"""Description:
"""

__version__ = "0.1"
__author__ = "@boqiling"
__all__ = [""]

import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="example")

    parser.add_argument('-s', dest='singlevalue', action='store', help='store a value')
    parser.add_argument('-v', "--verbose", dest='verbose',
                        action='store_true', help='verbose', default=False)
    #parser.add_argument('word', action='store', help='word to action')

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    print args
    print args.singlevalue
    print args.verbose
    #print args.word
