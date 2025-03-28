import array

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import QObject, pyqtSignal, Qt, pyqtSlot
from PyQt5.QtWidgets import QTableView, QStyledItemDelegate, QMenu, \
    QWidget, QAction, QVBoxLayout, QLabel, \
    QPushButton, QTableWidgetItem
from numberLineEdit import NumberLineEdit
from fileManager import FileManager, getFileType, saveExperimentFiles
import clipboard
from dataTypes import DataTypes

import numpy as np


class SpectraTable(QWidget):
    signalCellClick = pyqtSignal(int, int, str)

    # signalClearSelection = pyqtSignal()

    def __init__(self, tableWidget, fileType, buttonsLayout, plotByType, container, experimentName):
        super(QObject, self).__init__()
        self.menu = None
        self.tableWidget = tableWidget
        self.plotByType = plotByType
        self.labels = [self.tableWidget.horizontalHeaderItem(col).text() for col in
                       range(self.tableWidget.columnCount())]
        self.fileType = fileType
        self.spectra = []
        self.selectedPlotsBySpectra = {}
        self.currentSelectedSpectrum = None
        self.newSpectraAdded = False
        self.rightClickSpectrum = None
        self.container = container
        self.experimentName = experimentName
        self.listItem = None


        # ###################### BUTTONS ####################
        clearTableButton = QPushButton("Clear table")
        clearTableButton.setFixedWidth(200)
        buttonsLayout.addWidget(clearTableButton)
        clearTableButton.clicked.connect(self.onClearTable)

        clearSelectionButton = QPushButton("Clear selection")
        clearSelectionButton.setFixedWidth(200)
        buttonsLayout.addWidget(clearSelectionButton)
        clearSelectionButton.clicked.connect(self.onClearSelection)

        saveAllButton = QPushButton("Save all")
        saveAllButton.setFixedWidth(200)
        buttonsLayout.addWidget(saveAllButton)
        saveAllButton.clicked.connect(self.onSaveAll)
        # ###################### BUTTONS ####################

        # ###################### NUMBER EDITOR ####################
        w = QWidget()
        w.setVisible(False)
        buttonsLayout.addWidget(w)
        vBoxLayout = QVBoxLayout(w)
        vBoxLayout.setContentsMargins(0, 0, 0, 0)
        label = QLabel("Correction")
        # label.setFont(QFont('Times', 10))
        vBoxLayout.addWidget(label)
        numberEdit = NumberLineEdit()
        vBoxLayout.addWidget(numberEdit)
        # numberEdit.reset()
        self.numberEdit = numberEdit
        self.correctionWidget = w
        self.correctionLabel = label

        self.correctionType = "Y+"  # "*"

        def updateNumber(num):
            spectrum = self.currentSelectedSpectrum
            if spectrum and spectrum in self.selectedPlotsBySpectra:
                newXValues, newYValues = self.getRangeCorrectionValues(spectrum)
                if spectrum.dataType == DataTypes.Trf:
                    xValues = newXValues
                    yValues = newYValues
                elif spectrum.dataType == DataTypes.Phf:
                    xValues = newXValues
                    yValues = [newYValues[i] / spectrum.xValues[i] for i in range(spectrum.numPoints)]
                elif spectrum.dataType == DataTypes.SignalH:
                    xValues = [newXValues[i] * 1e4 for i in range(spectrum.numPoints)]
                    yValues = newYValues
                elif spectrum.dataType == DataTypes.MirrorH:
                    xValues = [newXValues[i] * 1e4 for i in range(spectrum.numPoints)]
                    yValues = [-newYValues[i] for i in range(spectrum.numPoints)]
                # if spectrum in self.selectedPlotsBySpectra:
                self.selectedPlotsBySpectra[spectrum].setData(xValues, yValues)
                spectrum.plot.plotSelectionRange()

        numberEdit.signalUpdateNumber.connect(updateNumber)
        # ###################### NUMBER EDITOR ####################

        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(self.labels.index("File name"), QtWidgets.QHeaderView.Stretch)
        if "File name" in self.labels:
            header.setSectionResizeMode(self.labels.index("File name"), QtWidgets.QHeaderView.Stretch)
        header.setDefaultAlignment(Qt.AlignLeft)

        # self.tableWidget.verticalHeader().setVisible(False)

        self.tableWidget.setSelectionBehavior(QTableView.SelectRows)

        self.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        self.tableWidget.itemClicked.connect(self.onClickTableItem)
        self.tableWidget.horizontalHeader().sectionClicked.connect(self.onColHeaderClicked)
        self.tableWidget.verticalHeader().sectionClicked.connect(self.onRowHeaderClicked)

        delegate = ReadOnlyDelegate(self.tableWidget)
        self.tableWidget.setItemDelegateForColumn(self.labels.index("Color"), delegate)  # readonly for column
        self.tableWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tableWidget.customContextMenuRequested.connect(self.generateMenu)
        self.tableWidget.viewport().installEventFilter(self)

    @pyqtSlot()
    def onClearTable(self):
        self.clearSelectedSpectraPlots()
        fileType = self.fileType
        self.tableWidget.setRowCount(0)
        self.spectra = []
        FileManager.files = [filePath for filePath in FileManager.files if getFileType(filePath) != fileType]
        self.correctionWidget.setVisible(False)

    @pyqtSlot()
    def onClearSelection(self):
        self.clearSelectedSpectraPlots()
        self.correctionWidget.setVisible(False)

    @pyqtSlot()
    def onSaveAll(self):
        self.saveCorrection()
        saveExperimentFiles(self.spectra, self.fileType, self)

    def clearSelectedSpectraPlots(self):
        for spectrum in self.selectedPlotsBySpectra:
            if spectrum in self.spectra:
                spectrumIndex = self.spectra.index(spectrum)
                self.setRowColor(spectrumIndex, False, 0x000000)
            plot = self.plotByType[spectrum.dataType]
            plot.removePlotItem(self.selectedPlotsBySpectra[spectrum])
        self.selectedPlotsBySpectra.clear()
        font = QFont()
        font.setBold(len(self.selectedPlotsBySpectra) > 0)
        self.listItem.setFont(font)

    def fillTable(self):
        row = 0
        self.tableWidget.setRowCount(len(self.spectra))
        for spectrum in self.spectra:
            self.setItem(row, "Sample name", spectrum.sampleName)
            self.setItem(row, "Spectrum name", spectrum.spectrumName)
            self.setItem(row, "Temperature", str(spectrum.temperature))
            self.setItem(row, "Thickness", str(spectrum.thickness))
            self.setItem(row, "Date", spectrum.date)
            self.setItem(row, "File name", spectrum.fileName)
            self.setItem(row, "Color", None)

            self.setItem(row, "Start", str(spectrum.pStart))
            self.setItem(row, "End", str(spectrum.pEnd))
            self.setItem(row, "Points", str(spectrum.numPoints))
            self.setItem(row, "Type", spectrum.dataType)

            self.tableWidget.setVerticalHeaderItem(row, QtWidgets.QTableWidgetItem(str(spectrum.inFileNum)))

            row += 1
        self.clearSelectedSpectraPlots()

    def setItem(self, row, headerName, value):
        self.tableWidget.setItem(row, self.labels.index(headerName), QtWidgets.QTableWidgetItem(value))

    @pyqtSlot(QTableWidgetItem)
    def onClickTableItem(self, item):
        self.signalCellClick.emit(item.row(), item.column(), self.fileType)

    def setRowColor(self, row, select, color):
        if select:
            for col in range(len(self.labels)):
                self.tableWidget.item(row, col).setBackground(QColor(0xeeffee))
            self.tableWidget.item(row, self.labels.index("Color")).setBackground(QColor(color))
        else:
            for col in range(len(self.labels)):
                self.tableWidget.item(row, col).setBackground(QColor(0xFFFFFF))

    @pyqtSlot(int)
    def onColHeaderClicked(self, logicalIndex):
        print("Col " + str(logicalIndex))

    @pyqtSlot()
    def onRowHeaderClicked(self, logicalIndex=None):
        if logicalIndex is not None:
            self.signalCellClick.emit(logicalIndex, 0)

    def updateCorrection(self, xValues, yValues, num):
        newXValues = xValues[:]
        newYValues = yValues[:]
        for i in range(len(xValues)):
            if self.correctionType == "Y+":
                newYValues[i] = yValues[i] + num
            elif self.correctionType == "Y*":
                newYValues[i] = yValues[i] * num
            elif self.correctionType == "Y+X*":
                newYValues[i] = yValues[i] + xValues[i] * num
            elif self.correctionType == "X+":
                newXValues[i] = xValues[i] + num
        return newXValues, newYValues

    def getRangeCorrectionValues(self, spectrum):
        x, y = self.updateCorrection(spectrum.xValues, spectrum.yValues, self.numberEdit.value)
        if spectrum.plot.selectionRange[0] is not None and spectrum.plot.selectionRange[1] is not None:
            x_min = spectrum.plot.selectionRange[0]
            x_max = spectrum.plot.selectionRange[1]
            if spectrum.dataType == DataTypes.Trf:
                pass
            elif spectrum.dataType == DataTypes.Phf:
                pass
            elif spectrum.dataType == DataTypes.SignalH:
                x_min = spectrum.plot.selectionRange[0] * 1e-4
                x_max = spectrum.plot.selectionRange[1] * 1e-4
            elif spectrum.dataType == DataTypes.MirrorH:
                x_min = spectrum.plot.selectionRange[0] * 1e-4
                x_max = spectrum.plot.selectionRange[1] * 1e-4

            corr_x = np.where((x >= x_min) & (x <= x_max), x, spectrum.xValues)
            corr_y = np.where((x >= x_min) & (x <= x_max), y, spectrum.yValues)
        else:
            corr_x = x
            corr_y = y
        return corr_x, corr_y

    def saveCorrection(self):
        spectrum = self.currentSelectedSpectrum
        if spectrum and self.correctionWidget.isVisible():
            # tup = self.updateCorrection(spectrum.xValues, spectrum.yValues, self.numberEdit.value)
            tup = self.getRangeCorrectionValues(spectrum)
            spectrum.xValues = tup[0]
            spectrum.yValues = tup[1]
            self.currentSelectedSpectrum = None
            self.correctionWidget.setVisible(False)

    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.MouseButtonPress and
                event.buttons() == QtCore.Qt.RightButton and
                source is self.tableWidget.viewport()):
            item = self.tableWidget.itemAt(event.pos())
            if item is not None:
                self.rightClickSpectrum = self.spectra[item.row()]
                self.menu = QMenu(self)
                copyAction = QAction('Copy', self)
                copyAction.triggered.connect(self.onCopyToClipboard)
                self.menu.addAction(copyAction)
                self.menu.addSeparator()
                shiftYAction = QAction('Correction Y: add', self)
                shiftYAction.triggered.connect(self.onCorrectionYShift)
                self.menu.addAction(shiftYAction)
                multiplyYAction = QAction('Correction Y: multiply', self)
                multiplyYAction.triggered.connect(self.onCorrectionYMultiply)
                linearYAction = QAction('Correction Y: add linear X', self)
                linearYAction.triggered.connect(self.onCorrectionYLinear)
                self.menu.addAction(linearYAction)
                self.menu.addAction(multiplyYAction)
                shiftXAction = QAction('Correction X: add', self)
                shiftXAction.triggered.connect(self.onCorrectionXShift)
                self.menu.addAction(shiftXAction)

        return super(SpectraTable, self).eventFilter(source, event)

    def generateMenu(self, pos):
        self.menu.exec_(self.tableWidget.mapToGlobal(pos))

    @pyqtSlot()
    def onCopyToClipboard(self):
        if self.rightClickSpectrum:
            spectrumStr = ""
            for i in range(len(self.rightClickSpectrum.xValues)):
                spectrumStr += str(self.rightClickSpectrum.xValues[i]) + "\t" + str(
                    self.rightClickSpectrum.yValues[i]) + "\n"
            clipboard.copy(spectrumStr)

    @pyqtSlot()
    def onCorrectionYShift(self):
        if self.rightClickSpectrum in self.selectedPlotsBySpectra:
            self.saveCorrection()
            self.correctionWidget.setVisible(True)
            self.correctionType = "Y+"
            self.numberEdit.resetValue(0)
            text = self.rightClickSpectrum.dataType + " Y+"
            self.correctionLabel.setText(text)
            self.currentSelectedSpectrum = self.rightClickSpectrum

    @pyqtSlot()
    def onCorrectionYMultiply(self):
        if self.rightClickSpectrum in self.selectedPlotsBySpectra:
            self.saveCorrection()
            self.correctionWidget.setVisible(True)
            self.correctionType = "Y*"
            self.numberEdit.resetValue(1)
            text = self.rightClickSpectrum.dataType + " Y*"
            self.correctionLabel.setText(text)
            self.currentSelectedSpectrum = self.rightClickSpectrum

    @pyqtSlot()
    def onCorrectionYLinear(self):
        if self.rightClickSpectrum in self.selectedPlotsBySpectra:
            self.saveCorrection()
            self.correctionWidget.setVisible(True)
            self.correctionType = "Y+X*"
            self.numberEdit.resetValue(0)
            text = self.rightClickSpectrum.dataType + " Y+X*"
            self.correctionLabel.setText(text)
            self.currentSelectedSpectrum = self.rightClickSpectrum

    @pyqtSlot()
    def onCorrectionXShift(self):
        if self.rightClickSpectrum in self.selectedPlotsBySpectra:
            self.saveCorrection()
            self.correctionWidget.setVisible(True)
            self.correctionType = "X+"
            self.numberEdit.resetValue(0)
            text = self.rightClickSpectrum.dataType + " X+"
            self.correctionLabel.setText(text)
            self.currentSelectedSpectrum = self.rightClickSpectrum


class ReadOnlyDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return  # do nothing
