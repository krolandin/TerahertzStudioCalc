import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QTableWidget, QColorDialog
from PyQt5.QtCore import pyqtSlot, QObject, Qt
from experimentList import *
from spectrumObject import SpectrumObject
from PyQt5.QtGui import QRegExpValidator, QColor, QFont


class ExperimentUI(QObject):

    def __init__(self, layout, plotByType, tables):
        super(QObject, self).__init__()

        layout.setContentsMargins(0, 0, 0, 0)
        self.plotByType = plotByType
        self.tables = tables
        self.layout = layout

        self.plotColors = [0xFF1700, 0xFF8E00, 0xFFE400, 0x06FF00, 0x23049D, 0xAA2EE6, 0xFF79CD, 0xFFDF6B]
        self.plotColorsNum = 0

        self.currentTableSpectrum = None

        # self.experimentContainer = QWidget()
        # layout.addWidget(self.experimentContainer)
        # listLayout = QHBoxLayout(self.experimentContainer)

        # ##################### EXP LIST #########################
        # listContainer = QWidget()
        # listContainer.setMinimumWidth(400)
        # # listContainer.setMaximumWidth(600)
        # listLayout.addWidget(listContainer)
        # listLayout = QVBoxLayout(listContainer)

        # label = QLabel("Experiment tables")
        # listLayout.addWidget(label)

        self.experimentList = ExperimentListWidget(plotByType, tables)
        self.experimentList.setMinimumWidth(500)
        self.experimentList.setMaximumWidth(600)
        self.layout.addWidget(self.experimentList)
        self.layout.setAlignment(self.experimentList, Qt.AlignLeft)
        # self.experimentList.signalSelect.connect(self.onSelect)
        # ##################### EXP LIST #########################

    @pyqtSlot()
    # def onSelect(self):
    #     print("experimentUI > onSelect")

    def addTable(self, table):
        self.layout.addWidget(table.container)
        self.experimentList.addTable(table)

    def addNewTable(self, fileType, newSpectra, experimentName):
        container = QWidget()
        # self.tabs.addTab(container, "[" + fileType + "] " + tabName)
        tableWidget = QTableWidget()
        for i in range(11):
            tableWidget.insertColumn(i)
        tableWidget.setHorizontalHeaderLabels(["Sample name", "Spectrum name", "Temperature", "Thickness",
                                               "Date", "File name", "Color", "Start", "End", "Points",
                                               "Type"])
        container.layout = QHBoxLayout(container)
        container.layout.addWidget(tableWidget)
        container_rt = QWidget()
        container.layout.addWidget(container_rt)
        container_rt.setMaximumWidth(220)
        container_rt.layout = QVBoxLayout(container_rt)
        container_rt.layout.setAlignment(Qt.AlignTop)
        table = SpectraTable(tableWidget, fileType, container_rt.layout, self.plotByType, container, experimentName)
        table.spectra.extend(newSpectra)
        table.newSpectraAdded = True

        self.addTable(table)

        self.tables.append(table)
        print("experimUI > addNewTable " + table.fileType)

        def onSignalCellClick(row, col, tableFileType):
            self.selectRow(row, col, table)

        table.signalCellClick.connect(onSignalCellClick)

    def selectRow(self, row, col, table):
        spectrum = table.spectra[row]
        plot = self.plotByType[spectrum.dataType]
        table.saveCorrection()
        if spectrum in table.selectedPlotsBySpectra:
            if col == table.labels.index("Color"):
                startColor = QColor(spectrum.color)  # opening color dialog
                color = QColorDialog.getColor(startColor)
                if not (color.isValid()):
                    return
                spectrum.color = int(color.name().replace("#", ""), 16)
                table.selectedPlotsBySpectra[spectrum].setSymbolBrush(color)
                table.setRowColor(row, True, spectrum.color)
                return
            # plot.clearCursor()
            # plot.plotWidget.removeItem(table.selectedPlotsBySpectra[spectrum])
            plot.removePlotItem(table.selectedPlotsBySpectra[spectrum])
            del table.selectedPlotsBySpectra[spectrum]
            table.setRowColor(row, False, 0x000000)
            table.currentSelectedSpectrum = None
            table.correctionWidget.setVisible(False)
            self.currentTableSpectrum = None
            self.checkClosePlot(plot)
        else:
            self.plotSpectra(spectrum, table, row, plot)
            self.currentTableSpectrum = spectrum
            plot.showPlotWidget()

        font = QFont()
        font.setBold(len(table.selectedPlotsBySpectra) > 0)
        table.listItem.setFont(font)


    def checkClosePlot(self, plot):
        # theories = self.theoryUI.theoryList.theories
        for table in self.tables:
            for spectrum in table.selectedPlotsBySpectra:
                if spectrum.dataType == plot.dataType:
                    return
        # for theory in theories:
        #     for curveDataType in theory.curves:
        #         if curveDataType == plot.dataType:
        #             return
        plot.hidePlotWidget()

    def plotSpectra(self, spectrum, table, row, plot):
        spectrum.plot = plot
        self.setSpectrumColor(spectrum)
        table.setRowColor(row, True, spectrum.color)
        table.currentSelectedSpectrum = spectrum
        table.numberEdit.resetSpectrum(spectrum)
        table.selectedPlotsBySpectra[spectrum] = plot.plot(spectrum)

    def selectLoadedSpectra(self, row, table):
        spectrum = table.spectra[row]
        plot = self.plotByType[spectrum.dataType]
        table.saveCorrection()
        if spectrum in table.selectedPlotsBySpectra:
            pass
        else:
            self.plotSpectra(spectrum, table, row, plot)
            self.currentTableSpectrum = spectrum
            plot.showPlotWidget()
        font = QFont()
        font.setBold(len(table.selectedPlotsBySpectra) > 0)
        table.listItem.setFont(font)

    def setSpectrumColor(self, spectrum: SpectrumObject):
        if spectrum.color:
            return
        spectrum.color = self.plotColors[self.plotColorsNum]
        self.plotColorsNum += 1
        if self.plotColorsNum > len(self.plotColors) - 1:
            self.plotColorsNum = 0
