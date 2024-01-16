from PyQt5.QtWidgets import QMenu, QAction, QDialog, QApplication, QMainWindow, QTableView, QColorDialog, QStyledItemDelegate, \
    QLineEdit, QLabel, QListWidget, QVBoxLayout, QWidget, QFileSystemModel, QTreeView, QAbstractItemView, QItemDelegate
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, pyqtSignal, Qt, pyqtSlot, QModelIndex, QDir, QRegExp
from pathlib import Path
import os
import clipboard
from PyQt5.QtGui import QRegExpValidator
from fileManager import loadTheory

class TheoryFileTree(QTreeView):
    signalOpenFiles = pyqtSignal(str)

    def __init__(self, layout):
        super(QTreeView, self).__init__()

        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        self.model.setNameFilters(["*.theory"])

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index("theories"))
        self.tree.setAnimated(False)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setIndentation(20)
        # self.tree.setSortingEnabled(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        self.tree.hideColumn(1)
        self.tree.hideColumn(2)
        self.tree.setColumnWidth(0, 500)
        self.tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree.setModel(self.model)
        # self.tree.setWindowTitle("Dir View")
        # self.tree.resize(840, 480)
        self.tree.clicked.connect(self.onTreeClicked)
        self.tree.doubleClicked.connect(self.onTreeDoubleClicked)

        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.openMenu)

        layout.addWidget(self.tree)

    @pyqtSlot(QtCore.QPoint)
    def openMenu(self, position):
        index = self.tree.currentIndex()
        indexItem = self.model.index(index.row(), 0, index.parent())
        filePath = self.model.filePath(indexItem)
        menu = QMenu(self)
        if os.path.isdir(filePath):
            action = QAction("Copy table of models", self)
            menu.addAction(action)
            action.triggered.connect(self.onCopyModelsTable)
            menu.addSeparator()
            action = QAction("Show in Explorer", self)
            menu.addAction(action)
            action.triggered.connect(self.onExplore)
        elif os.path.isfile(filePath):
            action = QAction("Delete", self)
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap("picts/delete.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            action.setIcon(icon)
            menu.addAction(action)
            action.triggered.connect(self.onDeleteTheory)

        menu.exec_(self.tree.mapToGlobal(position))

    @pyqtSlot()
    def onCopyModelsTable(self):
        index = self.tree.currentIndex()
        indexItem = self.model.index(index.row(), 0, index.parent())
        filePath = self.model.filePath(indexItem)
        if os.path.isdir(filePath):
            files = os.listdir(filePath)
            modelParametersStr = ""
            for f in files:
                file = filePath + "/" + f
                if os.path.isfile(file) and Path(file).suffix.upper() == ".THEORY":
                    tup = loadTheory(file)
                    theory = tup[0]
                    modelParametersStr += self.getTheoryModelsString(theory)
                    modelParametersStr += "\n"
            clipboard.copy(modelParametersStr)

    def getTheoryModelsString(self, theory):
        theoryStr = ""
        if theory.name == "NgLGS TrPh(f,H)":
            theoryStr += theory.text
            # theoryStr += "\t" + str(theory.fFix.value)
            # theoryStr += "\t" + str(theory.Hext.value)
            # theoryStr += "\t" + str(theory.Temperature.value)
            for m in theory.models:
                if m.name == m.MAGNET_OSCILLATOR_ND:
                    tup = theory.getModeDeltaMu(m)
                    theoryStr += "\t" + str(tup[0])
                    theoryStr += "\t" + str(tup[1])
                    theoryStr += "\t" + str(tup[2])
                    theoryStr += "\t" + str(m.gamma.value)
                if m.name == m.OSCILLATOR_ND:
                    tup = theory.getModeDeltaEps(m)
                    theoryStr += "\t" + str(tup[0])
                    theoryStr += "\t" + str(tup[1])
                    theoryStr += "\t" + str(tup[2])
                    theoryStr += "\t" + str(m.gamma.value)
                if m.name == m.OSCILLATOR:
                    theoryStr += "\t" + str(m.deltaEps.value)
                    theoryStr += "\t" + str(m.f0.value)
                    theoryStr += "\t" + str(m.gamma.value)
        if theory.name == "Ho LGS DistrAngleDcf":
            theoryStr += str(theory.fFix.value)
            # theoryStr += "\t" + str(theory.axis_Hext.value)
            theoryStr += theory.getResonanceFields(theory.axis_Hext.value)
            print(theoryStr)
        else:
            for p in theory.parameters:
                if p.isMain:
                    theoryStr += "\t" + str(p.value)
            for m in theory.models:
                ################  Only for magnet oscillators!!!
                ################  Only for magnet oscillators!!!
                ################  Only for magnet oscillators!!!
                if m.name == m.MAGNET_OSCILLATOR:
                    for mp in m.parameters:
                        if mp.isMain:
                            theoryStr += "\t" + str(mp.value)
        return theoryStr

    @pyqtSlot()
    def onExplore(self):
        index = self.tree.currentIndex()
        indexItem = self.model.index(index.row(), 0, index.parent())
        filePath = self.model.filePath(indexItem)
        if os.path.isdir(filePath):
            path = os.path.realpath(filePath)
            os.startfile(path)

    @pyqtSlot()
    def onDeleteTheory(self):
        index = self.tree.currentIndex()
        indexItem = self.model.index(index.row(), 0, index.parent())
        filePath = self.model.filePath(indexItem)
        os.remove(filePath)

    @pyqtSlot(QModelIndex)
    def onTreeClicked(self, index):
        indexItem = self.model.index(index.row(), 0, index.parent())
        fileName = self.model.fileName(indexItem)
        filePath = self.model.filePath(indexItem)
        # self.tree.expandAll()

    @pyqtSlot(QModelIndex)
    def onTreeDoubleClicked(self, index):
        indexItem = self.model.index(index.row(), 0, index.parent())
        fileName = self.model.fileName(indexItem)
        filePath = self.model.filePath(indexItem)
        fileExt = Path(filePath).suffix.upper()

        if os.path.isdir(filePath):
            return  # cancel opening all files from a directory
            # files = os.listdir(filePath)
            # for f in files:
            #     file = filePath + "/" + f
            #     if os.path.isfile(file) and Path(file).suffix.upper() == ".THEORY":
            #         self.signalOpenFiles.emit(file)
        elif os.path.isfile(filePath) and fileExt == ".THEORY":
            self.signalOpenFiles.emit(filePath)
        else:
            pass

