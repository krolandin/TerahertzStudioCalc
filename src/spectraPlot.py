from PyQt5.QtGui import QColor
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QPoint
from PyQt5.QtWidgets import QPushButton, QLabel, QAction, QWidget, QHBoxLayout
import pyqtgraph as pg
from pyqtgraph import ScatterPlotItem
from dataTypes import DataTypes, getDataTypeAttributes
from screenSettings import screenSize


class SpectraPlot(QWidget):
    signalPlotClick = pyqtSignal(str)
    signalCopyTheory = pyqtSignal(str)
    signalCopyExp = pyqtSignal(str)

    def __init__(self, dataType, rightMenuContainerLayout):
        super(QObject, self).__init__()

        self.dataType = dataType
        self.plotWidget = pg.PlotWidget(self)
        self.btnPlot = QPushButton(dataType)
        rightMenuContainerLayout.addWidget(self.btnPlot)

        layout_box = QHBoxLayout(self)
        layout_box.setContentsMargins(0, 0, 0, 0)
        layout_box.addWidget(self.plotWidget)

        self.currentItem = None
        self.currentItemId = None

        actionCopyTheory = QAction('Copy theory', self)
        actionCopyExp = QAction('Copy experiment', self)
        self.plotWidget.plot().scene().contextMenu.remove(self.plotWidget.plot().scene().contextMenu[0])
        self.plotWidget.plotItem.vb.menu.addSeparator()
        self.plotWidget.plotItem.vb.menu.addAction(actionCopyTheory)
        self.plotWidget.plotItem.vb.menu.addAction(actionCopyExp)
        actionCopyTheory.triggered.connect(self.onCopyTheory)
        actionCopyExp.triggered.connect(self.onCopyExp)

        # self.plotWidget.plotItem.vb.setLimits(minYRange=0.000001, yMin=0.0000001)
        self.plotWidget.plotItem.vb.setRange(rect=None, xRange=None, yRange=(10, 0.000001), padding=None, update=True)

        # ################ PLOT #################
        plotTitle = dataType
        attributes = getDataTypeAttributes(DataTypes.types, dataType)
        nameY = attributes.nameY
        nameX = attributes.nameX
        logY = attributes.logY

        self.plotWidget.setBackground('w')  # Add Background colour to white
        self.plotWidget.setTitle(plotTitle, color="b", size="24px")  # in pt or px
        styles = {"color": "#f00", "font-size": "20px"}  # in px only
        self.plotWidget.setLabel("left", nameY, **styles)
        self.plotWidget.setLabel("bottom", nameX, **styles)  # <sub>13</sub>
        self.plotWidget.addLegend()  # Add legend
        self.plotWidget.showGrid(x=True, y=True)  # Add grid
        self.plotWidget.setXRange(0, 10, padding=0)  # Set Range
        self.plotWidget.setYRange(20, 55, padding=0)
        self.plotWidget.setLogMode(False, logY)
        self.plotWidget.enableAutoRange()

        self.plotWidget.scene().sigMouseClicked.connect(self.onMouseClick)
        # ####################### PLOT BUTTON ####################
        self.btnPlot.setCheckable(True)
        self.btnPlot.clicked.connect(self.onBtnPlotClick)
        self.hidePlotWidget()
        # ####################### PLOT BUTTON ####################

        # ####################### CURSOR ####################
        pen = pg.mkPen(None)
        self.cursorItem = self.plotWidget.plot([0], [0],
                                               name=None, pen=pen,
                                               symbol='x', symbolSize=12,
                                               symbolPen=pen, symbolBrush=QColor(0x000000))
        self.plotWidget.removeItem(self.cursorItem)
        # self.cursorLabel = QLabel("")

        self.cursorLabel = QLabel(self)
        # pos = 0.15 * self.cursorLabel.parent().rect().bottomRight() #- 0.1 * self.cursorLabel.rect().bottomRight()
        pos = self.geometry().topLeft() - self.cursorLabel.geometry().topLeft() + QPoint(80, 40)
        self.cursorLabel.move(pos)
        self.cursorLabel.setText('')
        self.cursorLabel.setStyleSheet("QLabel{font-size: 14pt; color:rgba(0, 0, 255, 127)}")
        self.cursorLabel.setMinimumWidth(int(screenSize()[0] * 0.12))
        # rightMenuContainerLayout.addWidget(self.cursorLabel)
        # ####################### CURSOR ####################

    def plot(self, spectrum):
        plotName = spectrum.spectrumName + ", " + spectrum.sampleName + ", " + str(spectrum.temperature) + " K"
        if self.dataType == DataTypes.Trf:
            xValues = spectrum.xValues
            yValues = spectrum.yValues
        elif self.dataType == DataTypes.Phf:
            xValues = spectrum.xValues
            yValues = [spectrum.yValues[i] / spectrum.xValues[i] for i in range(spectrum.numPoints)]
        elif self.dataType == DataTypes.SignalH:
            xValues = [spectrum.xValues[i] * 1e4 for i in range(spectrum.numPoints)]
            yValues = spectrum.yValues
        elif self.dataType == DataTypes.MirrorH:
            xValues = [spectrum.xValues[i] * 1e4 for i in range(spectrum.numPoints)]
            yValues = [-spectrum.yValues[i] for i in range(spectrum.numPoints)]
        else:
            xValues = spectrum.xValues
            yValues = spectrum.yValues

        plotDataItem = self.plotWidget.plot(xValues, yValues,
                                            name=plotName, pen=None,
                                            symbol='o', symbolSize=6,
                                            symbolPen=None, symbolBrush=QColor(spectrum.color))
        self.plotWidget.removeItem(self.cursorItem)
        return plotDataItem

    def removePlotItem(self, plot):
        self.plotWidget.removeItem(self.cursorItem)
        self.cursorLabel.setText("")
        self.currentItem = None
        self.plotWidget.removeItem(plot)

    def showPlotWidget(self):
        self.btnPlot.setChecked(True)
        self.btnPlot.setStyleSheet("background-color : lightBlue")
        self.show()

    def hidePlotWidget(self):
        self.btnPlot.setChecked(False)
        self.btnPlot.setStyleSheet("background-color : lightGrey")
        self.hide()

    @pyqtSlot()
    def onBtnPlotClick(self):
        sender = self.sender()
        if sender.isChecked():
            sender.setStyleSheet("background-color : lightBlue")
            self.show()
        else:
            sender.setStyleSheet("background-color : lightGrey")
            self.hide()

    @pyqtSlot(object)
    def onMouseClick(self, event):
        p = self.plotWidget
        pos = event.scenePos()
        xLog = p.plotItem.ctrl.logXCheck.isChecked()
        yLog = p.plotItem.ctrl.logYCheck.isChecked()
        vx = p.getViewBox().mapSceneToView(pos).x()
        vy = p.getViewBox().mapSceneToView(pos).y()
        x = 10 ** vx if xLog else vx
        y = 10 ** vy if yLog else vy
        if pos.x() > 50:
            p.removeItem(self.cursorItem)
            self.cursorItem.setData([x], [y])
            self.cursorLabel.setText(f"{x:.5}" + "; " + f"{y:.5}")
            p.addItem(self.cursorItem)
            for item in p.plotItem.allChildItems():
                if type(item) is ScatterPlotItem:
                    if len(item.getData()[0]) > 1:
                        for i in range(len(item.getData()[0])):
                            ppx = item.getData()[0][i]
                            ppy = item.getData()[1][i]
                            px = 10 ** ppx if xLog else ppx
                            py = 10 ** ppy if yLog else ppy
                            dataPoint = pg.Point(ppx, ppy)
                            delta = p.getViewBox().mapViewToScene(dataPoint) - pos
                            if delta.length() < 10:
                                p.removeItem(self.cursorItem)
                                self.cursorItem.setData([px], [py])
                                self.cursorLabel.setText("[" + str(i + 1) + "] " + f"{px:.5}" + "; " + f"{py:.5}")
                                p.addItem(self.cursorItem)
                                self.currentItem = item
                                self.currentItemId = i
                                self.signalPlotClick.emit(self.dataType)
                                return

    def setCursorToId(self, dataId):
        if self.currentItem:
            ppx = self.currentItem.getData()[0][dataId]
            ppy = self.currentItem.getData()[1][dataId]
            p = self.plotWidget
            xLog = p.plotItem.ctrl.logXCheck.isChecked()
            yLog = p.plotItem.ctrl.logYCheck.isChecked()
            px = 10 ** ppx if xLog else ppx
            py = 10 ** ppy if yLog else ppy
            p.removeItem(self.cursorItem)
            self.cursorItem.setData([px], [py])
            self.cursorLabel.setText("[" + str(dataId + 1) + "] " + f"{px:.5}" + "; " + f"{py:.5}")
            p.addItem(self.cursorItem)
            self.currentItemId = dataId

    def setCursorToNext(self):
        if self.currentItem and self.currentItemId is not None:
            newId = self.currentItemId + 1
            if newId > len(self.currentItem.getData()[0]) - 1:
                newId = len(self.currentItem.getData()[0]) - 1
            self.setCursorToId(newId)

    def setCursorToPrev(self):
        if self.currentItem and self.currentItemId:
            newId = self.currentItemId - 1
            if newId < 0:
                newId = 0
            self.setCursorToId(newId)

    @pyqtSlot()
    def onCopyTheory(self):
        self.signalCopyTheory.emit(self.dataType)

    @ pyqtSlot()
    def onCopyExp(self):
        self.signalCopyExp.emit(self.dataType)