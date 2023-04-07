from PyQt5.QtWidgets import QListWidget, QMenu, QListWidgetItem, QAction, QAbstractItemView, QFileDialog, \
    QItemDelegate, QLineEdit
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from theoryTypes import TheoryType
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QRegExp
from modelsList import ModelsListWidget
from fileManager import saveTheory
from PyQt5.QtGui import QRegExpValidator, QColor


class TreeWidgetDelegate(QItemDelegate):
    def __init__(self, parent=None):
        QItemDelegate.__init__(self, parent=parent)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        # reg = QRegExp('[A-z0-9\[\]_-]+')
        reg = QRegExp("^[\w\-. ()#,]+$")
        regV = QRegExpValidator(reg)
        editor.setValidator(regV)
        return editor


class TheoriesListWidget(QListWidget):
    signalTheorySelected = pyqtSignal()
    theoryDefaultPath = None

    def __init__(self, plotByType, tables):
        super(QListWidget, self).__init__()
        self.tables = tables
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.actions = {}
        self.theories = []
        self.theoryTypes = TheoryType.types
        self.itemSelectionChanged.connect(self.itemSelected)
        self.currentTheory = None

        self.plotByType = plotByType

        context = QMenu(self)
        action = QAction("Save all as...", self)
        context.addAction(action)
        action.triggered.connect(self.onSaveAll)
        action = QAction("Save selected", self)
        context.addAction(action)
        action.triggered.connect(self.onSaveSelected)
        context.addSeparator()
        action = QAction("Remove all", self)
        context.addAction(action)
        action.triggered.connect(self.onRemoveAll)
        actionRemoveSelected = QAction("Remove selected", self)
        context.addAction(actionRemoveSelected)
        actionRemoveSelected.triggered.connect(self.onRemoveSelected)
        context.addSeparator()
        for theoryName in self.theoryTypes:
            action = QAction(theoryName, self)
            self.actions[theoryName] = action
            context.addAction(action)
            action.triggered.connect(self.onTheoryAdded)
        self.contex = context

        delegate = TreeWidgetDelegate()
        self.setItemDelegate(delegate)
        # self.itemChanged.connect(self.checkName, Qt.QueuedConnection)

    # def checkName(self, item):
    #     text = item.text()
    #     print('checkName: slibings:', text)

    def getTheoryByListItem(self, listItem):
        for theory in self.theories:
            if theory.listItem == listItem:
                return theory

    def addNewTheory(self, theory):
        self.createTheoryListItem(theory)
        theory.modelsList = ModelsListWidget(theory)
        # self.currentTheory = theory
        self.addTheory(theory)
        self.setCurrentItem(theory.listItem)

    def createTheoryListItem(self, theory):
        if theory.text is None:
            num = 1
            for t in self.theories:
                if t.name == theory.name:
                    num += 1
            theory.text = theory.name + " #" + str(num)
        theory.listItem = QListWidgetItem(theory.text)
        theory.listItem.setFlags(theory.listItem.flags() | QtCore.Qt.ItemIsEditable)

    def addTheory(self, theory):
        self.theories.append(theory)
        self.addItem(theory.listItem)
        theory.update()
        for curve in theory.curves:
            if theory.color is None:
                color = QColor(0xFF0000)
            else:
                color = theory.color
            curve.plotItem = self.plotByType[curve.dataType].plotWidget.plot(curve.x,
                                                                             curve.y,
                                                                             name=theory.text,
                                                                             pen=pg.mkPen(color))
            # self.plotByType[dataType].showPlotWidget()
            self.signalTheorySelected.emit()

    def contextMenuEvent(self, e):
        self.contex.exec(e.globalPos())

    @pyqtSlot()
    def onTheoryAdded(self):
        action = self.sender()
        theory = self.theoryTypes[action.text()]()
        self.addNewTheory(theory)

    @pyqtSlot()
    def onSaveAll(self):
        if len(self.theories) > 0:
            directory = str(QFileDialog.getExistingDirectory(self, "Select Directory", "theories"))
            # directory = str(
            #     QFileDialog.getExistingDirectory(self, "Select Directory", "theories", QFileDialog.ShowDirsOnly))
        for theory in self.theories:
            saveTheory(theory, directory, self.tables)

    @pyqtSlot()
    def onSaveSelected(self):
        if len(self.selectedItems()) > 0:
            listItem = self.selectedItems()[0]
            theory = self.getTheoryByListItem(listItem)
            if self.theoryDefaultPath is None:
                self.theoryDefaultPath = "theories"
            if theory.directory is None:
                directory = str(QFileDialog.getExistingDirectory(self, "Select Directory", self.theoryDefaultPath))
            else:
                directory = theory.directory
            self.theoryDefaultPath = directory
            saveTheory(theory, directory, self.tables)

    @pyqtSlot()
    def onRemoveAll(self):
        for theory in self.theories:
            for parameter in theory.parameters:
                parameter.widget.deleteLater()
            for curve in theory.curves:
                self.plotByType[curve.dataType].removePlotItem(curve.plotItem)
        self.clear()
        self.theories.clear()

    @pyqtSlot()
    def onRemoveSelected(self):
        if len(self.selectedItems()) > 0:
            listItem = self.selectedItems()[0]
            theory = self.getTheoryByListItem(listItem)
            for curve in theory.curves:
                self.plotByType[curve.dataType].removePlotItem(curve.plotItem)
            self.theories.remove(theory)
            self.takeItem(self.row(listItem))

    @pyqtSlot()
    def itemSelected(self):
        if len(self.selectedItems()) > 0:
            listItem = self.selectedItems()[0]
            self.currentTheory = self.getTheoryByListItem(listItem)
        else:
            self.currentTheory = None
        self.signalTheorySelected.emit()

