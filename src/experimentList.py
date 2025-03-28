from PyQt5.QtWidgets import QListWidget, QMenu, QListWidgetItem, QAction, QAbstractItemView, QFileDialog, \
    QItemDelegate, QLineEdit
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from theoryTypes import TheoryType
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QRegExp
from modelsList import ModelsListWidget
from fileManager import saveTheory
from PyQt5.QtGui import QRegExpValidator, QColor, QFont
from spectraTable import SpectraTable


# class TreeWidgetDelegate(QItemDelegate):
#     def __init__(self, parent=None):
#         QItemDelegate.__init__(self, parent=parent)
#
#     def createEditor(self, parent, option, index):
#         editor = QLineEdit(parent)
#         # reg = QRegExp('[A-z0-9\[\]_-]+')
#         reg = QRegExp("^[\w\-. ()#,]+$")
#         regV = QRegExpValidator(reg)
#         editor.setValidator(regV)
#         return editor


class ExperimentListWidget(QListWidget):
    signalSelect = pyqtSignal()
    theoryDefaultPath = None

    def __init__(self, plotByType, tables):
        super(QListWidget, self).__init__()
        self.tables = tables
        self.itemSelectionChanged.connect(self.itemSelected)
        self.plotByType = plotByType
        self.currentTable = None

        context = QMenu(self)
        action = QAction("Remove all", self)
        context.addAction(action)
        action.triggered.connect(self.onRemoveAll)
        actionRemoveSelected = QAction("Remove selected", self)
        context.addAction(actionRemoveSelected)
        actionRemoveSelected.triggered.connect(self.onRemoveSelected)
        self.contex = context

    def contextMenuEvent(self, e):
        self.contex.exec(e.globalPos())

    def addTable(self, table):
        table.listItem = QListWidgetItem(table.experimentName)

        # font = QFont()
        # font.setBold(True)
        # table.listItem.setFont(font)

        self.addItem(table.listItem)
        self.clearSelection()
        self.setCurrentItem(table.listItem)
        self.signalSelect.emit()

    def getTableByListItem(self, listItem):
        for table in self.tables:
            if table.listItem == listItem:
                return table

    @pyqtSlot()
    def itemSelected(self):
        for table in self.tables:
            table.container.setVisible(False)
        if len(self.selectedItems()) > 0:
            listItem = self.selectedItems()[0]
            self.currentTable = self.getTableByListItem(listItem)
        else:
            self.currentTable = None
        if self.currentTable is not None:
            self.currentTable.container.setVisible(True)
        self.signalSelect.emit()

    @pyqtSlot()
    def onRemoveAll(self):
        print("experimentList > onRemoveAll " + str(len(self.tables)))
        for table in self.tables:
            table.onClearTable()
            table.clearSelectedSpectraPlots()
            table.signalCellClick.disconnect()
            table.container.deleteLater()
            # self.removeTable(table)
        self.clear()
        self.tables.clear()

    @pyqtSlot()
    def onRemoveSelected(self):
        if len(self.selectedItems()) > 0:
            listItem = self.selectedItems()[0]
            table = self.getTableByListItem(listItem)
            # table.onClearTable()
            # table.clearSelectedSpectraPlots()
            # table.signalCellClick.disconnect()
            # table.container.deleteLater()
            # self.tables.remove(table)
            self.removeTable(table)
            self.takeItem(self.row(listItem))

    def removeTable(self, table):
        print("experimentList > removeTable " + table.fileType)
        table.onClearTable()
        table.clearSelectedSpectraPlots()
        table.signalCellClick.disconnect()
        table.container.deleteLater()
        self.tables.remove(table)