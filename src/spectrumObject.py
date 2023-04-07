from array import array


class SpectrumObject:
    def __init__(self, sampleName, spectrumName, temperature, thickness, date, fileName="",
                 dataType="", numPoints=0, pStart=0, pEnd=0, fileType=""):
        self.sampleName = sampleName
        self.spectrumName = spectrumName
        self.temperature = temperature
        self.thickness = thickness
        self.date = date
        self.fileName = fileName
        self.filePath = ""
        # self.abscissaType = abscissaType  # "f", "H"
        self.fileType = fileType
        self.inFileNum = 0

        self.dataType = dataType
        self.numPoints = numPoints
        self.pStart = pStart
        self.pEnd = pEnd

        self.xValues = array('f', [])  # frequency in cm-1 # magnetic field in Tesla
        self.yValues = array('f', [])  # Tr(f), Ph(f), Signal(H), Mirror(H)

        self.yMultiplier = 1

        self.color = None
        self.dataRow = 0



