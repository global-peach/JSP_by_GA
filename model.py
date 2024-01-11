 
class JSPGAInput:
    def __init__(self, dict) -> None:
        self.ProcessingTime = []
        self.ProcessingGroup = []
        self.MachineStartTime = []
        self.TimeEfficent = []
        self.MachineBuffer = []
        self.Itertion = 10
        self.IsWorst = False
        self.__dict__.update(dict)

class HFSPGAInput:
    def __init__(self, dict) -> None:
        self.ProcessingTime = []
        self.ProcessingGroup = []
        self.MachineStartTime = []
        self.ProcessingWeight: list[list[str]] = []
        self.ProcessingNameList = []
        self.WorkStationNameList = []
        self.ResourceConfig: object = {}
        self.TimeEfficent = []
        self.MachineBuffer = []
        self.IsWorst = False
        self.WeightExchangeTime = 5
        self.__dict__.update(dict)
