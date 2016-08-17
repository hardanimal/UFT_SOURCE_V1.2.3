#!/usr/bin/env python
# encoding: utf-8
"""Description:
"""

__version__ = "0.1"
__author__ = "@boqiling"

import threading
from Queue import Queue
import logging

logger = logging.getLogger(__name__)


class States(object):
    EXIT = -1


class FiniteStateMachine(threading.Thread):
    def __init__(self, name=None):
        self.queue = Queue()
        self.exit = False
        super(FiniteStateMachine, self).__init__(name=name)

    def run(self):
        logger.debug(self.name)
        while (not self.exit):
            s = self.queue.get()
            if (s == States.EXIT):
                self.exit = True
            else:
                self.work(s)

    def empty(self):
        for i in range(self.queue.qsize()):
            self.queue.get()

    def work(self, state):
        logger.debug("In Work State: {0}".format(state))
        # raise NotImplementedError

    def quit(self):
        self.empty()
        self.queue.put(States.EXIT)


if __name__ == "__main__":
    Format = "(%(threadName)-10s) %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=Format)

    fsm = FiniteStateMachine(name="FSM")
    fsm.start()

    fsm.queue.put("initialize")
    fsm.queue.put("debug")
    fsm.queue.put("exit....")

    # import time
    #time.sleep(0.1)
    logger.debug("end.")
    fsm.quit()
