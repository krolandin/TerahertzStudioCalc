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
from experimentUI import *
from theoryFileTree import TheoryFileTree
from PyQt5.QtCore import pyqtSlot, Qt, QSize
import clipboard
from dataTypes import DataTypes, FileTypes
from screenSettings import screenSize
from darktheme.widget_template import DarkApplication, DarkPalette
from ascManager import parse_asc_data


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
        self.tabs = QTabWidget()

        self.tabs.setTabsClosable(False)
        self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(True)

        bottomContainer.layout.addWidget(self.tabs)
        rightMenuContainer = QWidget(self)
        bottomContainer.layout.addWidget(rightMenuContainer)
        rightMenuContainer.layout = QtWidgets.QVBoxLayout(rightMenuContainer)
        rightMenuContainer.layout.setAlignment(Qt.AlignTop)
        # ##################### BOTTOM BLOCK #########################

        # ##################### UPPER BLOCK > PLOTS #########################
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

        self.tabs.tabBar().setTabButton(0, QTabBar.RightSide, None)  # Hide close button

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
                            self.experimentUI.selectLoadedSpectra(row, table)
                            break

        self.theoryFileTree.signalOpenFiles.connect(onOpenTheory)
        # ############## BOTTOM BLOCK > THEORY FILES ###############

        # ############## BOTTOM BLOCK > THEORY ###############
        tabTheory = QWidget(self)
        self.tabs.addTab(tabTheory, "Theory")
        self.tabs.tabBar().setTabButton(1, QTabBar.RightSide, None)  # Hide close button
        tabTheory.layout = QtWidgets.QHBoxLayout(tabTheory)
        theoryContainer = QWidget(self)
        tabTheory.layout.addWidget(theoryContainer)
        theoryContainer.layout = QtWidgets.QHBoxLayout(theoryContainer)
        tabTheory.layout.setAlignment(theoryContainer, Qt.AlignLeft)
        self.theoryUI = TheoryUI(theoryContainer.layout, self.plotByType, self.tables)
        # ############## BOTTOM BLOCK > THEORY ###############

        # ############## BOTTOM BLOCK > EXPERIMENT ###############
        tabExperiment = QWidget(self)
        self.tabs.addTab(tabExperiment, "Experiment")
        self.tabs.tabBar().setTabButton(2, QTabBar.RightSide, None)  # Hide close button
        tabExperiment.layout = QtWidgets.QHBoxLayout(tabExperiment)
        experimentContainer = QWidget(self)
        tabExperiment.layout.addWidget(experimentContainer)
        experimentContainer.layout = QtWidgets.QHBoxLayout(experimentContainer)
        self.experimentUI = ExperimentUI(experimentContainer.layout, self.plotByType, self.tables)
        # ############## BOTTOM BLOCK > EXPERIMENT ###############

        # ##################### INIT #########################
        self.setAcceptDrops(True)
        # self.loadExpFiles(self.loadDataOnStart())
        # self.currentTableSpectrum = None
        mainSplitter.setSizes([900, 200])
        # ##################### INIT #########################

    def closeAllExperimentAndTheories(self):
        self.theoryUI.theoryList.onRemoveAll()
        self.experimentUI.experimentList.onRemoveAll()

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
                        spectrumStr += str(xValue) + "\t" + str(yValue) + "\n"
        clipboard.copy(spectrumStr)
        self.statusbar.showMessage("Copy experiment to clipboard: " + plotDataType)
    ################# PLOTS #################

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
            self.experimentUI.addNewTable(newSpectra[0].fileType, newSpectra, Path(f).name)
            fileNames += Path(f).name + " "
            FileManager.files.append(f)
        self.statusbar.showMessage("Loaded: " + fileNames)
        for table in self.tables:
            if table.newSpectraAdded:
                table.fillTable()
    ################# DRAG AND DROP FILES #################

    ################# SAVE/LOAD DATA ON EXIT/START #################
    def saveDataOnExit(self):
        with open('expFiles.pkl', 'wb') as file:
            pickle.dump(FileManager.files, file)

    def loadDataOnStart(self):
        if Path('expFiles.pkl').is_file():
            with open('expFiles.pkl', 'rb') as file:
                return pickle.load(file)
    ################# SAVE/LOAD DATA ON EXIT/START #################

    ################# KEY PRESSED #################
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.closeAllExperimentAndTheories()
        if event.key() == Qt.Key_Left:
            if self.currentPlotWithCursor:
                self.currentPlotWithCursor.setCursorToPrev()
        if event.key() == Qt.Key_Right:
            if self.currentPlotWithCursor:
                self.currentPlotWithCursor.setCursorToNext()
        if event.key() == Qt.Key_Space:
            pass
            # self.copyTableSpectrumToClipboard()
        if event.key() == Qt.Key_Return:
            if self.theoryUI.currentTheory is not None:
                self.theoryUI.currentTheory.update()
                self.theoryUI.currentTheory.plotCurves()
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_V:
            clipboard = QApplication.clipboard()
            pasted_text = clipboard.text()
            self.pasteExpFromTPSCalc(pasted_text)
            # print(f'Pasted text: {pasted_text}')

    def pasteExpFromTPSCalc(self, pasted_text):
        for table in self.tables:
            table.newSpectraAdded = False
        newSpectra = parse_asc_data(pasted_text)
        if len(newSpectra) == 0:
            return
        self.experimentUI.addNewTable(newSpectra[0].fileType, newSpectra, "Pasted")
        self.statusbar.showMessage("Paste")
        for table in self.tables:
            if table.newSpectraAdded:
                table.fillTable()
    ################# KEY PRESSED #################

class TabBar(QTabBar):
    def tabSizeHint(self, index):
        size = QTabBar.tabSizeHint(self, index)
        w = int(self.width() / self.count())
        return QSize(w, size.height())


# main
# QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
# QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons
app = QApplication(sys.argv)
# app.setPalette(DarkPalette())
mainWindow = MainWindow()
widget = QtWidgets.QStackedWidget()
widget.addWidget(mainWindow)
widget.setMinimumWidth(int(screenSize()[0] * 0.7))
widget.setMinimumHeight(int(screenSize()[1] * 0.7))
# widget.showMaximized()
widget.show()
try:
    sys.exit(app.exec_())
except SystemExit:
    mainWindow.saveDataOnExit()
