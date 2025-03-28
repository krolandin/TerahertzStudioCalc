from array import array
import numpy as np


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

        self.plot = None

        # self.dataPointSizes = None

    # def setDataPointSizes(self, xValues, yValues):
    #     self.xValues = xValues
    #     self.yValues = yValues
    #
    #     # x = np.linspace(0, 10, 100)
    #     # y = np.sin(x)
    #     x_min, x_max = 30, 70
    #     mask = (xValues >= x_min) & (xValues <= x_max)
    #
    #     self.dataPointSizes = np.ones(len(xValues)) * 6  # Базовый размер
    #     self.dataPointSizes[mask] = 10  # Увеличенный размер
