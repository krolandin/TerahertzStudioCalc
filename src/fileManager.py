import struct
from pathlib import Path
from spectrumObject import SpectrumObject
import os
import datetime as dt
import pickle
# from theoriesList import TheoriesListWidget
from theoryModels import Model
from dataTypes import DataTypes, FileTypes
from theoryTypes import TheoryType


class FileManager:
    files = []

    # def __init__(self):
    #     pass


def readFloat(file):
    tup = struct.unpack('<f', file.read(4))  # little endian float tuple
    value = float('.'.join(str(ele) for ele in tup))  # Convert tuple to float
    return round(value, 6)


def readSpectraFile(f):
    fileExt = Path(f).suffix.upper()
    if fileExt == ".DAT":
        return readDatFile(f)
    elif fileExt == ".FDP":
        return readFdpFile(f)
    elif fileExt == ".MH":
        return readMH(f)
    elif fileExt == ".MT":
        return readMT(f)
    elif fileExt == ".MANG":
        return readMANG(f)
    elif fileExt == ".IRR":
        return readBrukerReflection(f)
    else:
        return None
    # self.statusbar.showMessage("Loaded: " + Path(f).name)


def getFileType(f):
    fileExt = Path(f).suffix.upper()
    if fileExt == ".DAT":
        return FileTypes.TrPhf
    elif fileExt == ".FDP":
        return FileTypes.TrPhH
    elif fileExt == ".MH":
        return FileTypes.MH
    elif fileExt == ".MT":
        return FileTypes.MT
    elif fileExt == ".MANG":
        return FileTypes.MTeta
    elif fileExt == ".IRR":
        return FileTypes.RPhRf
    else:
        return None


def readDatFile(f):
    spectra = []
    fileType = FileTypes.TrPhf
    try:
        file = open(f, "rb")
    except FileNotFoundError:
        return []
    readBytes = file.read(1)  # first step without reading
    inFileNum = 1
    while readBytes:
        readBytes = file.read(1)
        nextTextLength = int.from_bytes(readBytes, byteorder='little',
                                        signed=True)  # next text length/ little endian int
        if nextTextLength == 0:
            break
        readBytes = file.read(2)
        header = readBytes.decode("utf-8")
        if header == "hd":
            numPoints = int.from_bytes(file.read(2), byteorder='little', signed=True)  # 2 bytes int
            nextTextLength = int.from_bytes(file.read(1), byteorder='little', signed=True)  # next text length
            spectrumName = file.read(64).decode("utf-8")[:nextTextLength]  # read>decode>get substring
            nextTextLength = int.from_bytes(file.read(1), byteorder='little', signed=True)  # next text length
            date = file.read(14).decode("utf-8")[:nextTextLength]
            frequencies = []
            for frNum in range(numPoints):
                frequency = readFloat(file)
                frequencies.append(frequency)
        else:
            nextTextLength = int.from_bytes(file.read(1), byteorder='little', signed=True)  # next text length
            sampleName = file.read(14).decode("utf-8")[:nextTextLength]
            temperature = readFloat(file)
            d = readFloat(file)
            values = []
            for frNum in range(numPoints):
                value = readFloat(file)
                values.append(value)
            if header == "tr":
                dataType = DataTypes.Trf
            elif header == "pt":
                dataType = DataTypes.Phf
            else:
                dataType = header
            spectrum = SpectrumObject(sampleName, spectrumName, temperature, d, date, Path(f).stem,
                                      dataType, numPoints, frequencies[0], frequencies[len(frequencies) - 1],
                                      fileType)
            spectrum.filePath = os.path.relpath(f, start=os.curdir)
            spectrum.inFileNum = inFileNum
            inFileNum += 1
            for pointNum in range(numPoints):
                spectrum.xValues.append(frequencies[pointNum])
                spectrum.yValues.append(values[pointNum])

            spectra.append(spectrum)
    file.close
    return spectra


def readFdpFile(f):
    spectra = []
    fileType = FileTypes.TrPhH
    try:
        file = open(f, "rb")
    except FileNotFoundError:
        return []
    headerString = str(file.readline())
    if not ("Field" in headerString and "Signal" in headerString):
        return []
    hasMirror = "Mirror[MM]" in headerString
    sampleName = Path(f).parts[-2]
    spectrumName = Path(f).stem
    file_time = dt.datetime.fromtimestamp(os.path.getmtime(f))
    date = file_time.strftime("%d.%m.%Y")
    lines = file.readlines()
    numPoints = len(lines)
    signal = SpectrumObject(sampleName, spectrumName, 0, 0, date,
                            Path(f).stem,
                            dataType=DataTypes.SignalH, numPoints=numPoints, pStart=0, pEnd=0,
                            fileType=fileType)
    signal.filePath = os.path.relpath(f, start=os.curdir)
    signal.inFileNum = 1
    signal.xValues = []
    signal.yValues = []
    if hasMirror:
        mirror = SpectrumObject(sampleName, spectrumName, 0, 0, date,
                                Path(f).stem,
                                dataType=DataTypes.MirrorH, numPoints=numPoints, pStart=0, pEnd=0,
                                fileType=fileType)
        mirror.filePath = os.path.relpath(f, start=os.curdir)
        mirror.inFileNum = 2
        mirror.xValues = []
        mirror.yValues = []
    minH = 10000
    maxH = -10000
    temperatureSmpl = 0
    temperatureCntr = 0
    for line in lines:
        values = [float(strVal) for strVal in str(line.decode("utf-8")).split()]
        if values[0] < minH:
            minH = values[0]
        if values[0] > maxH:
            maxH = values[0]
        signal.xValues.append(values[0])
        signalYValue = values[3]
        if hasMirror:
            mirror.xValues.append(values[0])
            mirror.yValues.append(values[4])
            if not ("SignalIntensity" in headerString):
                signalYValue = signalYValue ** 2
        signal.yValues.append(signalYValue)
        temperatureSmpl += values[1]
        temperatureCntr += values[2]
    signal.pStart = minH
    signal.pEnd = maxH
    signal.temperature = round((0.75 * temperatureSmpl + 0.25 * temperatureCntr) / numPoints, 2)
    spectra.append(signal)
    if hasMirror:
        mirror.pStart = minH
        mirror.pEnd = maxH
        mirror.temperature = signal.temperature
        spectra.append(mirror)
    return spectra


def readMH(f):
    return readTwoColText(f, FileTypes.MH, DataTypes.M_H)


def readMT(f):
    return readTwoColText(f, FileTypes.MT, DataTypes.M_T)


def readMANG(f):
    return readTwoColText(f, FileTypes.MTeta, DataTypes.M_teta)


def readBrukerReflection(f):
    return readMultipleColText(f, FileTypes.RPhRf, [DataTypes.R_f, DataTypes.PhR_f])


def readMultipleColText(f, fileType, dataTypes):
    spectra = []
    try:
        file = open(f, "rb")
    except FileNotFoundError:
        return []
    sampleName = Path(f).parts[-2]
    spectrumName = Path(f).stem
    file_time = dt.datetime.fromtimestamp(os.path.getmtime(f))
    date = file_time.strftime("%d.%m.%Y")
    lines = file.readlines()
    numPoints = len(lines)
    for i in range(len(dataTypes)):
        spectrum = SpectrumObject(sampleName, spectrumName, 0, 0, date,
                                  Path(f).stem,
                                  dataType=dataTypes[i], numPoints=numPoints, pStart=0, pEnd=0,
                                  fileType=fileType)
        spectrum.filePath = os.path.relpath(f, start=os.curdir)
        spectrum.inFileNum = 1
        spectrum.xValues = []
        spectrum.yValues = []
        minX = 10000000
        maxX = -10000000
        for line in lines:
            lineStr = str(line.decode("utf-8")).replace(",", ".")
            values = [float(strVal) for strVal in lineStr.split()]
            if len(values) < 2:
                continue
            if values[0] < minX:
                minX = values[0]
            if values[0] > maxX:
                maxX = values[0]
            spectrum.xValues.append(values[0])
            spectrum.yValues.append(values[1 + i])
        spectrum.pStart = minX
        spectrum.pEnd = maxX
        spectrum.temperature = 0
        spectra.append(spectrum)
    return spectra


def readTwoColText(f, fileType, dataType):
    spectra = []
    try:
        file = open(f, "rb")
    except FileNotFoundError:
        return []
    sampleName = Path(f).parts[-2]
    spectrumName = Path(f).stem
    file_time = dt.datetime.fromtimestamp(os.path.getmtime(f))
    date = file_time.strftime("%d.%m.%Y")
    lines = file.readlines()
    numPoints = len(lines)
    spectrum = SpectrumObject(sampleName, spectrumName, 0, 0, date,
                              Path(f).stem,
                              dataType=dataType, numPoints=numPoints, pStart=0, pEnd=0,
                              fileType=fileType)
    spectrum.filePath = os.path.relpath(f, start=os.curdir)
    spectrum.inFileNum = 1
    spectrum.xValues = []
    spectrum.yValues = []
    minX = 10000000
    maxX = -10000000
    for line in lines:
        lineStr = str(line.decode("utf-8")).replace(",", ".")
        values = [float(strVal) for strVal in lineStr.split()]
        if len(values) < 2:
            continue
        if values[0] < minX:
            minX = values[0]
        if values[0] > maxX:
            maxX = values[0]
        spectrum.xValues.append(values[0])
        spectrum.yValues.append(values[1])
    spectrum.pStart = minX
    spectrum.pEnd = maxX
    spectrum.temperature = 0
    spectra.append(spectrum)
    return spectra


def saveExperimentFiles(spectra, fileType):
    spectraByFile = {}
    for spectrum in spectra:
        if spectrum.fileType == fileType:
            try:
                spectraByFile[spectrum.filePath].append(spectrum)
            except KeyError:
                spectraByFile[spectrum.filePath] = [spectrum]

    for filePath in spectraByFile:
        if spectraByFile[filePath][0].fileType == fileType:
            spectraSignal = spectraByFile[filePath][0]
            spectraMirror = None
            if len(spectraByFile[filePath]) > 1:
                spectraMirror = spectraByFile[filePath][1]
            if spectraSignal.dataType == DataTypes.SignalH:
                p = Path(filePath)
                parent = p.parents[0]
                stem = p.stem
                ext = p.suffix
                with open(str(parent) + "\\" + str(stem) + str(ext), 'w') as file:
                    file.write(" Field[T] Tsmpl[K] Tcntr[K] SignalIntensity" +
                               ("   Mirror[MM]" if spectraMirror is not None else "") +
                               "\n")
                    for i in range(len(spectraSignal.xValues)):
                        file.write(" " + f"{spectraSignal.xValues[i]:.5f}" +
                                   "    " + f"{spectraSignal.temperature:.2f}" +
                                   "     " + f"{spectraSignal.temperature:.2f}" +
                                   "   " + f"{spectraSignal.yValues[i]:.5f}" +
                                   ("  " + f"{spectraMirror.yValues[i]:.4f}" if spectraMirror is not None else "") +
                                   "\n")
                    file.close()
        if spectraSignal.dataType == DataTypes.Trf:
            p = Path(filePath)
            parent = p.parents[0]
            stem = p.stem
            ext = p.suffix
            fileBytes = bytearray()
            with open(str(parent) + "\\" + str(stem) + str(ext), 'wb') as file:
                fileBytes.append(10)  # byte. first step
                for spectrum in spectra:
                    fileBytes.append(2)  # byte
                    fileBytes.extend(bytes("hd", 'UTF-8'))  # string. Header
                    fileBytes.extend(bytearray(struct.pack("h", len(spectrum.xValues))))  # short. Number of points
                    spectrum.spectrumName = spectrum.spectrumName[0:64]  # only first 64 symbols
                    fileBytes.append(len(spectrum.spectrumName))  # byte. spectrumName length
                    fileBytes.extend(bytes(spectrum.spectrumName, 'UTF-8'))  # string. spectrumName
                    fileBytes.extend(bytearray(64 - len(spectrum.spectrumName)))  # bytes. spectrumName empty space
                    fileBytes.append(10)  # byte. step
                    spectrum.date = spectrum.date[0:14]  # only first 14 symbols
                    # fileBytes.append(len(spectrum.date))  # byte. date length
                    fileBytes.extend(bytes(spectrum.date, 'UTF-8'))  # string. date
                    fileBytes.extend(bytearray(14 - len(spectrum.date)))  # bytes. date empty space
                    for xValue in spectrum.xValues:
                        fileBytes.extend(bytearray(struct.pack("f", xValue)))  # float. Frequency
                    fileBytes.append(2)  # byte
                    if spectrum.dataType == DataTypes.Trf:
                        hd = "tr"
                    elif spectrum.dataType == DataTypes.Phf:
                        hd = "pt"
                    fileBytes.extend(bytes(hd, 'UTF-8'))  # string. Header data type
                    spectrum.sampleName = spectrum.sampleName[0:14]  # only first 14 symbols
                    fileBytes.append(len(spectrum.sampleName))  # byte. sampleName length
                    fileBytes.extend(bytes(spectrum.sampleName, 'UTF-8'))  # string. sampleName
                    fileBytes.extend(bytearray(14 - len(spectrum.sampleName)))  # bytes. sampleName empty space
                    fileBytes.extend(bytearray(struct.pack("f", spectrum.temperature)))  # float. temperature
                    fileBytes.extend(bytearray(struct.pack("f", spectrum.thickness)))  # float. thickness
                    for yValue in spectrum.yValues:
                        fileBytes.extend(bytearray(struct.pack("f", yValue)))  # float. Tr or Ph

                file.write(fileBytes)
                file.close()
        # save file for ".DAT" and ".FDP" only


def saveTheory(theory, directory, tables):
    if len(directory) == 0:
        return
    with open(directory + "/" + theory.listItem.text() + ".theory", 'wb') as file:
        for table in tables:
            table.onSaveAll()

        parameters = []
        for parameter in theory.parameters:
            parameters.append(parameter.value)
        models = []
        for model in theory.models:
            modelParameters = []
            for parameter in model.parameters:
                modelParameters.append(parameter.value)
            models.append({"name": model.name, "text": model.listItem.text(), "parameters": modelParameters})
        experiments = []
        for table in tables:
            for spectra in table.selectedPlotsBySpectra:
                experiments.append({"filePath": spectra.filePath, "inFileNum": spectra.inFileNum})
        theoryObject = {"name": theory.name, "parameters": parameters, "models": models, "experiments": experiments}
        pickle.dump(theoryObject, file)


def loadTheory(filePath):
    if Path(filePath).is_file():
        with open(filePath, 'rb') as file:
            theoryDict = pickle.load(file)
            theory = TheoryType.types[theoryDict["name"]]()
            theory.directory = os.path.relpath(os.path.dirname(filePath), start=os.curdir)
            theory.text = Path(filePath).stem
            for i in range(len(theoryDict["parameters"])):
                theory.parameters[i].value = theoryDict["parameters"][i]
                theory.parameters[i].numberEdit.resetValue(theory.parameters[i].value)
            for modelDict in theoryDict["models"]:
                model = Model(modelDict["name"])
                model.text = modelDict["text"]
                for i in range(len(modelDict["parameters"])):
                    model.parameters[i].value = modelDict["parameters"][i]
                    model.parameters[i].numberEdit.resetValue(model.parameters[i].value)
                theory.models.append(model)
            experiments = []
            for experiment in theoryDict["experiments"]:
                experiments.append({"filePath": experiment["filePath"], "inFileNum": experiment["inFileNum"]})
            return theory, experiments
    else:
        return None
