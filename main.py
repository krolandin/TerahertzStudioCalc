import sys
from PyQt5.QtGui import QColor
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QColorDialog, QVBoxLayout, QWidget, QTabWidget, QTableWidget, \
    QStatusBar, QTabBar
from pathlib import Path
from fileManager import FileManager, readSpectraFile, loadTheory
from spectraTable import SpectraTable
from spectraPlot import SpectraPlot
import pickle
from spectrumObject import SpectrumObject
from theoryUI import TheoryUI
from theoryFileTree import TheoryFileTree
from PyQt5.QtCore import pyqtSlot, Qt, QSize
import clipboard
from dataTypes import DataTypes, FileTypes
from screenSettings import screenSize
import numpy as np


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        # ##################### MAIN UI #########################
        mainWidget = QWidget(self)
        self.setCentralWidget(mainWidget)
        mainWidget.layout = QVBoxLayout(self)
        mainWidget.setLayout(mainWidget.layout)
        mainSplitter = QtWidgets.QSplitter(self)
        mainSplitter.setOrientation(QtCore.Qt.Vertical)
        mainWidget.layout.addWidget(mainSplitter)
        # ##################### MAIN UI #########################

        # ##################### STATUS BAR #########################
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        # ##################### STATUS BAR #########################

        # ##################### UPPER BLOCK #########################
        plotsContainer = QWidget(self)
        mainSplitter.addWidget(plotsContainer)
        # ##################### UPPER BLOCK #########################

        # ##################### BOTTOM BLOCK #########################
        bottomContainer = QWidget(self)
        mainSplitter.addWidget(bottomContainer)
        bottomContainer.layout = QtWidgets.QHBoxLayout(bottomContainer)
        # bottomContainer.layout.setContentsMargins(0,0,0,0)
        self.tabs = QTabWidget()

        # self.tabs.setTabBar(TabBar())
        self.tabs.setTabsClosable(True)
        # self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        # self.tabs.setElideMode(Qt.ElideRight)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.tabCloseRequested.connect(self.closeTab)

        bottomContainer.layout.addWidget(self.tabs)
        rightMenuContainer = QWidget(self)
        bottomContainer.layout.addWidget(rightMenuContainer)
        rightMenuContainer.layout = QtWidgets.QVBoxLayout(rightMenuContainer)
        rightMenuContainer.layout.setAlignment(Qt.AlignTop)
        # ##################### BOTTOM BLOCK #########################

        # ##################### UPPER BLOCK > PLOTS #########################
        self.plotColors = [0xFF1700, 0xFF8E00, 0xFFE400, 0x06FF00, 0x23049D, 0xAA2EE6, 0xFF79CD, 0xFFDF6B]
        self.plotColorsNum = 0
        self.plotByType = {}
        self.currentPlotWithCursor = None
        for dataType in DataTypes.types:
            self.plotByType[dataType] = SpectraPlot(dataType, rightMenuContainer.layout)
            self.plotByType[dataType].signalPlotClick.connect(self.onPlotClick)
            self.plotByType[dataType].signalCopyTheory.connect(self.onCopyTheory)
            self.plotByType[dataType].signalCopyExp.connect(self.onCopyExp)
        plotsContainer.layout = QtWidgets.QHBoxLayout(plotsContainer)
        plotsSplitter = QtWidgets.QSplitter(plotsContainer)
        plotsSplitter.setOrientation(QtCore.Qt.Horizontal)
        for dataType in DataTypes.types:
            plotsSplitter.addWidget(self.plotByType[dataType])
        plotsSplitter.setChildrenCollapsible(False)
        plotsContainer.layout.addWidget(plotsSplitter)
        # ##################### UPPER BLOCK > PLOTS #########################

        # ##################### BOTTOM BLOCK > TABLES #########################
        self.tables = []
        # ##################### BOTTOM BLOCK > TABLES #########################

        # ############## BOTTOM BLOCK > THEORY FILES ###############
        tabTheoryFiles = QWidget(self)
        self.tabs.addTab(tabTheoryFiles, "Theory files")
        tabTheoryFiles.layout = QtWidgets.QHBoxLayout(tabTheoryFiles)
        self.theoryFileTree = TheoryFileTree(tabTheoryFiles.layout)

        self.tabs.tabBar().setTabButton(0, QTabBar.RightSide, None)

        def onOpenTheory(filePath):
            tup = loadTheory(filePath)
            theory = tup[0]
            for t in self.theoryUI.theoryList.theories:
                if t.text == theory.text:
                    return
            self.theoryUI.theoryList.addNewTheory(theory)
            experiments = tup[1]
            for experiment in experiments:
                self.loadExpFiles([experiment["filePath"]])
            for experiment in experiments:
                for table in self.tables:
                    for row in range(len(table.spectra)):
                        if experiment["filePath"] == table.spectra[row].filePath and \
                                experiment["inFileNum"] == table.spectra[row].inFileNum:
                            self.selectLoadedSpectra(row, table)
                            break

        self.theoryFileTree.signalOpenFiles.connect(onOpenTheory)
        # ############## BOTTOM BLOCK > THEORY FILES ###############

        # ############## BOTTOM BLOCK > THEORY ###############
        tabTheory = QWidget(self)
        self.tabs.addTab(tabTheory, "Theory")
        self.tabs.tabBar().setTabButton(1, QTabBar.RightSide, None)
        tabTheory.layout = QtWidgets.QHBoxLayout(tabTheory)
        theoryContainer = QWidget(self)
        tabTheory.layout.addWidget(theoryContainer)
        theoryContainer.layout = QtWidgets.QHBoxLayout(theoryContainer)
        tabTheory.layout.setAlignment(theoryContainer, Qt.AlignLeft)
        self.theoryUI = TheoryUI(theoryContainer.layout, self.plotByType, self.tables)
        # ############## BOTTOM BLOCK > THEORY ###############

        # ##################### INIT #########################
        self.setAcceptDrops(True)
        # self.loadExpFiles(self.loadDataOnStart())
        self.currentTableSpectrum = None
        mainSplitter.setSizes([600, 300])
        # ##################### INIT #########################

    ################# TABLES #################
    def addNewTable(self, fileType, newSpectra, tabName):
        tabExp = QWidget(self)
        self.tabs.addTab(tabExp, "[" + fileType + "] " + tabName)
        tableWidget = QTableWidget()
        for i in range(11):
            tableWidget.insertColumn(i)
        tableWidget.setHorizontalHeaderLabels(["Sample name", "Spectrum name", "Temperature", "Thickness",
                                               "Date", "File name", "Color", "Start", "End", "Points",
                                               "Type"])
        tabExp.layout = QtWidgets.QHBoxLayout(tabExp)
        tabExp.layout.addWidget(tableWidget)
        tabExp_rt = QWidget(self)
        tabExp.layout.addWidget(tabExp_rt)
        tabExp_rt.setMaximumWidth(220)
        tabExp_rt.layout = QtWidgets.QVBoxLayout(tabExp_rt)
        tabExp_rt.layout.setAlignment(Qt.AlignTop)
        table = SpectraTable(tableWidget, fileType, tabExp_rt.layout, self.plotByType)
        table.spectra.extend(newSpectra)
        table.newSpectraAdded = True
        self.tables.append(table)

        def onSignalCellClick(row, col, tableFileType):
            self.selectRow(row, col, table)

        table.signalCellClick.connect(onSignalCellClick)

    def closeAllExpTabsAndTheories(self):
        for i in range(len(self.tables)):
            index = 1 + len(self.tables) - i
            self.tables[i].onClearTable()
            tab = self.tabs.widget(index)
            tab.deleteLater()
            self.tabs.removeTab(index)
            self.tables[i].signalCellClick.disconnect()
        self.tables.clear()
        self.theoryUI.theoryList.onRemoveAll()

    def closeExpTable(self, index):
        pass

    @pyqtSlot(int)
    def closeTab(self, index):
        if index < 2:
            return
        tab = self.tabs.widget(index)
        tab.deleteLater()
        self.tabs.removeTab(index)
        i = index - 2
        self.tables[i].onClearTable()
        self.tables[i].signalCellClick.disconnect()
        self.tables.remove(self.tables[i])

    ################# TABLES #################

    ################# PLOTS #################
    @pyqtSlot(str)
    def onPlotClick(self, plotDataType):
        self.currentPlotWithCursor = self.plotByType[plotDataType]

    @pyqtSlot(str)
    def onCopyTheory(self, plotDataType):
        # self.plotByType[plotDataType]
        theory = self.theoryUI.theoryList.currentTheory
        if theory is not None:
            curves = []
            for curve in theory.curves:
                if curve.dataType == plotDataType:
                    curves.append(curve)
            if len(curves) == 0:
                return
            spectrumStr = ""
            for i in range(len(curves[0].x)):
                xValue = curves[0].x[i]
                if curve.dataType == DataTypes.SignalH:
                    xValue = curves[0].x[i] * 1e-4  # Oe to T
                spectrumStr += str(xValue)
                for curve in curves:
                    spectrumStr += "\t" + str(curve.y[i])
                spectrumStr += "\n"
            clipboard.copy(spectrumStr)
            self.statusbar.showMessage("Copy theory to clipboard: " + theory.name + " > " + plotDataType)

    @pyqtSlot(str)
    def onCopyExp(self, plotDataType):
        spectrumStr = ""
        for table in self.tables:
            for spectrum in table.selectedPlotsBySpectra:
                if spectrum.dataType == plotDataType:
                    for i in range(len(spectrum.xValues)):
                        xValue = spectrum.xValues[i]
                        yValue = spectrum.yValues[i]
                        if spectrum.dataType == DataTypes.Phf:
                            yValue = spectrum.yValues[i] / spectrum.xValues[i]
                        if spectrum.dataType == DataTypes.MirrorH:
                            yValue = -yValue
                        spectrumStr += str(xValue) + "\t" + str(yValue) + "\n"
        clipboard.copy(spectrumStr)
        self.statusbar.showMessage("Copy experiment to clipboard: " + plotDataType)

    ################# PLOTS #################

    ################# SELECTION #################
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

    def checkClosePlot(self, plot):
        theories = self.theoryUI.theoryList.theories
        for table in self.tables:
            for spectrum in table.selectedPlotsBySpectra:
                if spectrum.dataType == plot.dataType:
                    return
        for theory in theories:
            for curveDataType in theory.curves:
                if curveDataType == plot.dataType:
                    return
        plot.hidePlotWidget()

    def plotSpectra(self, spectrum, table, row, plot):
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

    def setSpectrumColor(self, spectrum: SpectrumObject):
        if spectrum.color:
            return
        spectrum.color = self.plotColors[self.plotColorsNum]
        self.plotColorsNum += 1
        if self.plotColorsNum > len(self.plotColors) - 1:
            self.plotColorsNum = 0

    ################# SELECTION #################

    ################# DRAG AND DROP FILES #################
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        self.loadExpFiles(files)

    def loadExpFiles(self, files):
        fileNames = ""
        for table in self.tables:
            table.newSpectraAdded = False
        for f in files:
            if f in FileManager.files:
                continue
            newSpectra = readSpectraFile(f)
            if len(newSpectra) == 0:
                return
            self.addNewTable(newSpectra[0].fileType, newSpectra, Path(f).name)
            fileNames += Path(f).name + " "
            FileManager.files.append(f)
        self.statusbar.showMessage("Loaded: " + fileNames)
        for table in self.tables:
            if table.newSpectraAdded:
                table.fillTable()

    ################# DRAG AND DROP FILES #################

    def saveDataOnExit(self):
        pass
        # with open('expFiles.pkl', 'wb') as file:
        #     pickle.dump(FileManager.files, file)

    def loadDataOnStart(self):
        pass
        # if Path('expFiles.pkl').is_file():
        #     with open('expFiles.pkl', 'rb') as file:
        #         return pickle.load(file)

    ##################### Key pressed #####################
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.closeAllExpTabsAndTheories()
        if event.key() == Qt.Key_Left:
            if self.currentPlotWithCursor:
                self.currentPlotWithCursor.setCursorToPrev()
        if event.key() == Qt.Key_Right:
            if self.currentPlotWithCursor:
                self.currentPlotWithCursor.setCursorToNext()
        if event.key() == Qt.Key_Space:
            print("Space")
        if event.key() == Qt.Key_Q:
            if self.theoryUI.currentTheory is not None:
                self.theoryUI.currentTheory.update()
                self.theoryUI.currentTheory.plotCurves()
                if self.theoryUI.currentTheory.name == "Ho LGS DistrAngleDcf" or \
                    self.theoryUI.currentTheory.name == "Ho LGS DistrAngleMu" or \
                    self.theoryUI.currentTheory.name == "Ho LGS DistrAngleMuDcf":
                    for spectrum in self.tables[0].spectra:
                        v = spectrum.xValues
                        maximum = np.max(v)
                        minimum = np.min(v)
                        index_of_maximum = np.where(v == maximum)
                        index_of_minimum = np.where(v == minimum)

                        # print(index_of_maximum[0][0])
                        # print(index_of_minimum[0][0])

                        if spectrum.dataType == DataTypes.SignalH:
                            self.tables[0].rightClickSpectrum = self.tables[0].currentSelectedSpectrum = spectrum
                            self.tables[0].onCorrectionYMultiply()
                            value = self.theoryUI.currentTheory.curves[0].y[0] / spectrum.yValues[index_of_minimum[0][0]]
                            self.tables[0].numberEdit.resetValue(value)
                            self.tables[0].saveCorrectionForAutoShift()
                        if spectrum.dataType == DataTypes.MirrorH:
                            self.tables[0].rightClickSpectrum = self.tables[0].currentSelectedSpectrum = spectrum
                            self.tables[0].onCorrectionYShift()
                            value = - self.theoryUI.currentTheory.curves[1].y[0] - spectrum.yValues[index_of_minimum[0][0]]
                            self.tables[0].numberEdit.setText(f"{value:.8f}")
                        if spectrum.dataType == DataTypes.dMu_H:
                            self.tables[0].rightClickSpectrum = self.tables[0].currentSelectedSpectrum = spectrum
                            self.tables[0].onCorrectionYShift()
                            value = self.theoryUI.currentTheory.curves[1].y[0]
                            self.tables[0].numberEdit.setText(f"{value:.8f}")

        if event.key() == Qt.Key_Return:
            if self.theoryUI.currentTheory is not None:
                self.theoryUI.currentTheory.update()
                self.theoryUI.currentTheory.plotCurves()
    ##################### Key pressed #####################

class TabBar(QTabBar):
    def tabSizeHint(self, index):
        size = QTabBar.tabSizeHint(self, index)
        w = int(self.width() / self.count())
        return QSize(w, size.height())


# main
# QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons
app = QApplication(sys.argv)
mainWindow = MainWindow()
widget = QtWidgets.QStackedWidget()
widget.addWidget(mainWindow)
widget.setMinimumWidth(int(screenSize()[0] * 0.4))
widget.setMinimumHeight(int(screenSize()[1] * 0.4))
widget.showMaximized()
widget.show()
try:
    sys.exit(app.exec_())
except SystemExit:
    mainWindow.saveDataOnExit()
