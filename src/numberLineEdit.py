import math
from PyQt5.QtWidgets import QLineEdit, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from spectrumObject import SpectrumObject
from dataTypes import DataTypes, FileTypes


class NumberLineEdit(QLineEdit):
    signalUpdateNumber = pyqtSignal(float)

    def __init__(self, *args, **kwargs):
        QLineEdit.__init__(self, *args, **kwargs)
        self.setContentsMargins(0, 0, 0, 0)
        self.setMaximumWidth(180)
        self.value = 0
        self.textChanged.connect(self.onTextChanged)

    def resetSpectrum(self, spectrum):
        dataType = spectrum.dataType
        value = 1
        if dataType == DataTypes.Trf:
            value = 1
        elif dataType == DataTypes.Phf:
            value = 0
        elif dataType == DataTypes.SignalH:
            value = 1
        elif dataType == DataTypes.MirrorH:
            value = 0
        self.value = value
        self.setText(f"{self.value:.8f}")

    def resetValue(self, value):
        self.value = value
        self.setText(f"{self.value:.8f}")

    def onTextChanged(self, text):
        curPos = self.cursorPosition()
        try:
            num = float(text)
            if not math.isnan(num) and not math.isinf(num):
                self.value = num
        except ValueError:
            pass
        self.setText(f"{self.value:.8f}")
        self.setCursorPosition(curPos)
        self.signalUpdateNumber.emit(self.value)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            direction = 1
        else:
            direction = -1
        text = self.text()
        dotPos = self.text().find(".")
        curPos = self.cursorPosition()
        # ePos = self.text().find("E")
        # if curPos >= ePos:
        #     curPos = ePos

        # if curPos <= 2:
        #     self.value += direction * 10 ** float(text[ePos + 1:])
        # elif curPos > 2:
        #     self.value += direction * 10 ** -(curPos - dotPos - 1) * 10 ** float(text[ePos + 1:])
        # if math.isnan(self.value) or math.isinf(self.value):
        #     self.value = 0
        # self.setText(f"{self.value:.8f}")

        if curPos == dotPos:
            self.value += direction
        elif curPos < dotPos:
            self.value += direction * 10 ** -(curPos - dotPos)
        elif curPos > dotPos:
            self.value += direction * 10 ** -(curPos - dotPos - 1)
        if math.isnan(self.value) or math.isinf(self.value):
            self.value = 0
        self.setText(f"{self.value:.8f}")

        # if self.value == 0:
        #     curPos = 1

        self.setCursorPosition(curPos - dotPos + self.text().find("."))

        # if self.isKeyPressed:
        #     delta = 1 if event.angleDelta().y() > 0 else -1
        #     fn = self.font()
        #     fn.setPointSize(fn.pointSize() +  delta)
        #     self.setFont(fn)
        #     event.accept()
