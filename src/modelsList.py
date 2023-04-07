from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QListWidget, QMenu, QListWidgetItem, QAction
from theoryModels import Model


class ModelsListWidget(QListWidget):
    signalModelSelected = pyqtSignal()

    def __init__(self, theory):
        super(QListWidget, self).__init__()

        self.theory = theory
        self.currentModel = None
        self.actions = {}

        self.itemSelectionChanged.connect(self.itemSelected)

        context = QMenu(self)
        actionRemoveAll = QAction("Remove all", self)
        context.addAction(actionRemoveAll)
        actionRemoveAll.triggered.connect(self.onRemoveAll)
        actionRemoveSelected = QAction("Remove selected", self)
        context.addAction(actionRemoveSelected)
        actionRemoveSelected.triggered.connect(self.onRemoveSelected)
        context.addSeparator()
        for madelType in theory.modelTypes:
            action = QAction(madelType, self)
            self.actions[madelType] = action
            context.addAction(action)
            action.triggered.connect(self.onModelAdded)
        self.contex = context

        self.initModels()

    def initModels(self):
        for model in self.theory.models:
            model.listItem = QListWidgetItem(model.text)
            self.addItem(model.listItem)
            # self.theory.update()
            # self.theory.plotCurves()
            for parameter in model.parameters:
                parameter.numberEdit.signalUpdateNumber.connect(self.updateNumber)

    def addNewModel(self, model):
        self.theory.models.append(model)
        num = 0
        for m in self.theory.models:
            if m.name == model.name:
                num += 1
        model.text = model.name + " #" + str(num)
        model.listItem = QListWidgetItem(model.text)
        self.addItem(model.listItem)
        self.theory.update()
        self.theory.plotCurves()
        for parameter in model.parameters:
            parameter.numberEdit.signalUpdateNumber.connect(self.updateNumber)

    @pyqtSlot(float)
    def updateNumber(self, num):
        self.theory.update()
        self.theory.plotCurves()

    def getModelByListItem(self, listItem):
        for model in self.theory.models:
            if model.listItem == listItem:
                return model

    def contextMenuEvent(self, e):
        self.contex.exec(e.globalPos())

    @pyqtSlot()
    def onModelAdded(self):
        action = self.sender()
        model = Model(action.text())
        self.addNewModel(model)

    @pyqtSlot()
    def onRemoveAll(self):
        for model in self.theory.models:
            for parameter in model.parameters:
                parameter.widget.deleteLater()
        self.clear()
        self.theory.models.clear()
        self.theory.update()
        self.theory.plotCurves()

    @pyqtSlot()
    def onRemoveSelected(self):
        if len(self.selectedItems()) > 0:
            listItem = self.selectedItems()[0]
            model = self.getModelByListItem(listItem)
            self.theory.models.remove(model)
            self.takeItem(self.row(listItem))
            self.theory.update()
            self.theory.plotCurves()

    @pyqtSlot()
    def itemSelected(self):
        if len(self.selectedItems()) > 0:
            listItem = self.selectedItems()[0]
            self.currentModel = self.getModelByListItem(listItem)
        else:
            self.currentModel = None
        self.signalModelSelected.emit()

