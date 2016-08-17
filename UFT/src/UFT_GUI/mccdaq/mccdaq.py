from param import *
import _mccdaq


class MCCDAQ:
    def __init__(self):
        # Declare UL Revision Level 
        self.RevLevel = CURRENTREVNUM
        # Initiate error handling
        # Parameters:
        #      PRINTALL :all warnings and errors encountered will be printed
        #      DONTSTOP :program will continue even if error occurs.
        #                Note that STOPALL and STOPFATAL are only effective in 
        #                Windows applications, not Console applications. 
        self.status = _mccdaq.ErrHandling(PRINTALL, DONTSTOP)

    def getDeclareRevision(self):
        return self.RevLevel

    def getStatus(self):
        return (self.status)

    def AIn(self, BoardNum=0, Chan=0, Gain=BIP5VOLTS):
        (self.status, data) = _mccdaq.AIn(BoardNum, Chan, Gain)
        return data

    def AInScan(self, BoardNum=0, LowChan=0, HighChan=4, Count=20, Rate=3125, Gain=BIP5VOLTS, Options=CONVERTDATA):
        self.status = _mccdaq.AInScan(BoardNum, LowChan, HighChan, Count, Rate, Gain, Options)

    def AOut(self, BoardNum=0, Chan=0, Gain=BIP5VOLTS, DataValue=0):
        self.status = _mccdaq.AOut(BoardNum, Chan, Gain, DataValue)

    def ToEngUnits(self, BoardNum=0, Gain=BIP5VOLTS, DataValue=0):
        (self.status, EngUnits) = _mccdaq.ToEngUnits(BoardNum, Gain, DataValue)
        return EngUnits

    def FromEngUnits(self, BoardNum=0, Gain=BIP5VOLTS, EngUnits=0.0):
        (self.status, DataValue) = _mccdaq.FromEngUnits(BoardNum, Gain, EngUnits)
        return DataValue

    def DConfigPort(self, BoardNum=0, PortNum=FIRSTPORTA, Direction=DIGITALIN):
        self.status = _mccdaq.DConfigPort(BoardNum, PortNum, Direction)

    def DIn(self, BoardNum=0, PortNum=FIRSTPORTA):
        (self.status, data) = _mccdaq.DIn(BoardNum, PortNum)
        return data

    def DBitIn(self, BoardNum=0, PortType=FIRSTPORTA, BitNum=0):
        (self.status, data) = _mccdaq.DBitIn(BoardNum, PortType, BitNum)
        return data

    def DOut(self, BoardNum=0, PortNum=FIRSTPORTA, DataValue=0):
        self.status = _mccdaq.DOut(BoardNum, PortNum, DataValue)

    def DBitOut(self, BoardNum=0, PortType=FIRSTPORTA, BitNum=0, BitValue=0):
        self.status = _mccdaq.DBitOut(BoardNum, PortType, BitNum, BitValue)

    def C8254Config(self, BoardNum=0, CounterNum=1, Config=HIGHONLASTCOUNT):
        self.status = _mccdaq.C8254Config(BoardNum, CounterNum, Config)

    def CLoad(self, BoardNum=0, RegName=LOADREG1, LoadValue=1000):
        self.status = _mccdaq.CLoad(BoardNum, RegName, LoadValue)

    def CLoad32(self, BoardNum=0, RegName=LOADREG1, LoadValue=1000):
        self.status = _mccdaq.CLoad32(BoardNum, RegName, LoadValue)

    def CIn(self, BoardNum=0, CounterNum=1):
        (self.status, data) = _mccdaq.CIn(BoardNum, CounterNum)
        return data

    def CIn32(self, BoardNum=0, CounterNum=1):
        (self.status, data) = _mccdaq.CIn32(BoardNum, CounterNum)
        return data

    def CFreqIn(self, BoardNum=0, SigSource=CTRINPUT1, GateInterval=100):
        (self.status, Count, Freq) = _mccdaq.CFreqIn(BoardNum, SigSource, GateInterval)
        return (Count, Freq)

    def C9513Init(self, BoardNum=0, ChipNum=1, FOutDivider=0, FOutSource=FREQ4, Compare1=DISABLED, Compare2=DISABLED,
                  TimeOfDay=DISABLED):
        self.status = _mccdaq.C9513Init(BoardNum, ChipNum, FOutDivider, FOutSource, Compare1, Compare2, TimeOfDay)

    def GetBoardName(self, BoardNum=0):
        Name = _mccdaq.GetBoardName(BoardNum)
        return Name

    def GetErrMsg(self, ErrCode=0):
        ErrMsg = _mccdaq.GetErrMsg(ErrCode)
        return ErrMsg

    def GetConfig(self, InfoType=DIGITALINFO, BoardNum=0, DevNum=0, ConfigItem=DIDEVTYPE):
        (self.status, ConfigVal) = _mccdaq.GetConfig(InfoType, BoardNum, DevNum, ConfigItem)
        return ConfigVal

    def SetConfig(self, InfoType=BOARDINFO, BoardNum=0, DevNum=0, ConfigItem=BIDACUPDATEMODE,
                  ConfigVal=UPDATEONCOMMAND):
        self.status = _mccdaq.SetConfig(InfoType, BoardNum, DevNum, ConfigItem, ConfigVal)

    def FlashLED(self, BoardNum=0):
        self.status = _mccdaq.FlashLED(BoardNum)

