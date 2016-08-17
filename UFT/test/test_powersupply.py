from UFT.devices import pwr
import threading


class Test_Thread(threading.Thread):
    ps = pwr.PowerSupply()

    def __init__(self):
        super(Test_Thread, self).__init__()

    def run(self):
        print self.ps.instr.ask("*IDN?")

if __name__ == "__main__":
    while 1:
        var = raw_input("please enter s: \n")
        if var == "s":
            t = Test_Thread()
            t.start()
            t.join()
    #t2 = Test_Thread()
    #t2.start()