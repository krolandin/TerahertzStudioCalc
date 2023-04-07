import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout
from theoriesList import TheoriesListWidget
from PyQt5.QtCore import pyqtSlot, QObject


class TheoryUI(QObject):

    def __init__(self, layout, plotByType, tables):
        super(QObject, self).__init__()

        layout.setContentsMargins(0, 0, 0, 0)
        self.plotByType = plotByType
        self.currentTheory = None
        self.currentModel = None

        # ##################### THEORY LIST BLOCK #########################
        theoriesListContainer = QWidget()
        theoriesListContainer.setMinimumWidth(400)
        layout.addWidget(theoriesListContainer)
        theoriesListLayout = QVBoxLayout(theoriesListContainer)
        label = QLabel("Theories")
        theoriesListLayout.addWidget(label)
        self.theoryList = TheoriesListWidget(plotByType, tables)
        theoriesListLayout.addWidget(self.theoryList)
        self.theoryList.signalTheorySelected.connect(self.onTheorySelected)
        # ##################### THEORY LIST BLOCK #########################

        # ##################### THEORY PARAMETERS BLOCK #########################
        self.theoryParametersContainer = QWidget()
        layout.addWidget(self.theoryParametersContainer)
        # theoryParametersLayout = QVBoxLayout(theoryParametersContainer)
        self.theoryParametersLayout = QGridLayout(self.theoryParametersContainer)
        label = QLabel("Theory parameters")
        self.theoryParametersLayout.addWidget(label)
        self.theoryParametersContainer.setVisible(False)
        # ##################### THEORY PARAMETERS BLOCK #########################

        # ##################### MODEL LIST BLOCK #########################
        self.modelsListContainer = QWidget()
        self.modelsListContainer.setMinimumWidth(400)
        layout.addWidget(self.modelsListContainer)
        self.modelsListLayout = QVBoxLayout(self.modelsListContainer)
        label = QLabel("Models")
        self.modelsListLayout.addWidget(label)
        self.modelsListContainer.setVisible(False)
        # ##################### MODEL LIST BLOCK #########################

        # ##################### MODEL PARAMETERS BLOCK #########################
        self.modelsParametersContainer = QWidget()
        layout.addWidget(self.modelsParametersContainer)
        self.modelParametersLayout = QGridLayout(self.modelsParametersContainer)
        label = QLabel("Model parameters")
        self.modelParametersLayout.addWidget(label)
        self.modelsParametersContainer.setVisible(False)
        # ##################### MODEL PARAMETERS BLOCK #########################

    def clearTheoryParameters(self):
        if self.currentTheory is None:
            return
        if self.currentTheory.modelsList is None:
            return
        for parameter in self.currentTheory.parameters:
            if parameter is not None:
                parameter.widget.setVisible(False)
        self.theoryParametersContainer.setVisible(False)
        self.modelsListContainer.setVisible(False)
        self.modelsParametersContainer.setVisible(False)
        self.currentTheory.modelsList.setVisible(False)
        # self.currentTheory.modelsList.disconnect()

    def showTheoryParameters(self):
        self.theoryParametersContainer.setVisible(True)
        i = 0
        l = math.ceil(len(self.currentTheory.parameters) * 0.5)
        for parameter in self.currentTheory.parameters:
            self.theoryParametersLayout.addWidget(parameter.widget, 1 + i % l, math.floor(i / l))
            parameter.widget.setVisible(True)
            i += 1
        self.theoryParametersLayout.setRowStretch(self.theoryParametersLayout.rowCount(), 1)

        if len(self.currentTheory.modelTypes) == 0:
            return
        self.modelsListLayout.addWidget(self.currentTheory.modelsList)
        self.currentTheory.modelsList.setVisible(True)
        self.modelsListContainer.setVisible(True)
        self.currentTheory.modelsList.signalModelSelected.connect(self.onModelSelected)
        self.updateModels()

    def clearModelParameters(self):
        self.modelsParametersContainer.setVisible(False)
        model = self.currentModel
        if model is None:
            return
        for parameter in model.parameters:
            parameter.widget.setVisible(False)

    def showModelParameters(self):
        self.modelsParametersContainer.setVisible(True)
        model = self.currentModel
        i = 0
        # l = math.ceil(len(self.currentTheory.parameters) * 0.5)
        for parameter in model.parameters:
            self.modelParametersLayout.addWidget(parameter.widget, 1 + i, 0)
            parameter.widget.setVisible(True)
            i += 1
        self.modelParametersLayout.setRowStretch(self.modelParametersLayout.rowCount(), 1)

    @pyqtSlot()
    def onTheorySelected(self):
        self.clearTheoryParameters()
        self.currentTheory = self.theoryList.currentTheory
        if self.currentTheory is not None:
            self.showTheoryParameters()

    @pyqtSlot()
    def onModelSelected(self):
        self.updateModels()

    def updateModels(self):
        self.clearModelParameters()
        self.currentModel = self.currentTheory.modelsList.currentModel
        if self.currentModel is not None:
            self.showModelParameters()

