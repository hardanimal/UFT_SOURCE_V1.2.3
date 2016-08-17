#!/usr/bin/env python
# encoding: utf-8
"""Description:
"""

__version__ = "0.1"
__author__ = "@boqiling"

from UFT.fsm import FiniteStateMachine, States
import logging

TestStates = 0xA0


class MainFunc(FiniteStateMachine):
    def __init__(self):
        self.progress = 0
        super(MainFunc, self).__init__()

    def init(self):
        self.progress += 1
        print "init"

    def idle(self):
        print "idle"

    def work(self, states):
        self.progress += 1
        if(self.progress >= 50):
            self.quit()     # quit() will call close()
        if(states == TestStates):
            print "work"

    def error(self):
        print "error"

    def close(self):
        print "exit"

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import time
    m = MainFunc()

    m.en_queue(States.INIT)
    m.run()

    while(m.is_alive):
        print m.progress
        time.sleep(1)
        m.en_queue(TestStates)
