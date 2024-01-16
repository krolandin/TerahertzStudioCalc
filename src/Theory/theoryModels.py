import math
from spectrumObject import SpectrumObject
from numberLineEdit import NumberLineEdit
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QListWidgetItem
from PyQt5.QtGui import QColor, QDoubleValidator, QValidator, QFont, QFontDatabase
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, Qt
from dataTypes import DataTypes, FileTypes


class Theory(QObject):
    def __init__(self, numPoints=1000):
        super(QObject, self).__init__()
        self.text = None
        self.numPoints = numPoints
        self.curves = []
        # self.plotItems = []
        self.parameters = []
        self.listItem = None
        self.modelTypes = []
        self.directory = None

        self.color = None

        self.models = []
        self.modelsList = None

    def update(self):
        pass

    def plotCurves(self):
        for curve in self.curves:
            if curve.plotItem is not None:
                curve.plotItem.setData(curve.x, curve.y)

    def initParameters(self):
        for parameter in self.parameters:
            parameter.numberEdit.signalUpdateNumber.connect(self.updateNumber)

    @pyqtSlot(float)
    def updateNumber(self, num):
        if self.name == "Ho LGS DistrAngleDcf" \
                or self.name == "Ho LGS DistrAngleMu" \
                or self.name == "Ho LGS DistrAngleMuDcf" \
                or self.name == "Ho LGS M(teta)" \
                or self.name == "Ho LGS M(H)":
            pass
        else:
            self.update()
        self.plotCurves()

    def updateCurvePoints(self, x, y, dataType, comment=""):
        for curve in self.curves:
            if curve.dataType == dataType and curve.comment == comment:
                curve.x = x
                curve.y = y


class TheoryTest(Theory):
    name = "Test"

    def __init__(self):
        Theory.__init__(self)
        self.listItem = QListWidgetItem(self.name)

        self.p1 = TheoryParameter(2, "Parameter 1", "cm<sup>-1</sup>")
        self.p2 = TheoryParameter(5, "Parameter 2", "units", False)

        self.parameters = [self.p1, self.p2]

        self.modelTypes = []

        self.x = None
        self.y = None

        self.initParameters()

    def update(self):
        self.x = []
        self.y = []
        for i in range(self.numPoints):
            self.x.append(i)
            self.y.append(self.p1.value * math.sin(self.p2.value * self.x[i]))
        self.curves.append(TheoryCurve(self.x, self.y, DataTypes.Test))


class Model:
    LIGHT_SPEED = 2.998e10  # cm/s
    h = 0.66260755e-26
    muB = 0.927401549e-20

    OSCILLATOR = "Oscillator"
    MAGNET_OSCILLATOR = "Magnet oscillator"
    MAGNET_OSCILLATOR_H = "Magnet oscillator (H)"
    MAGNET_OSCILLATOR_ND = "Magnet oscillator f,mu(H)"
    OSCILLATOR_ND = "Oscillator dEps f(H) NdLGS"

    def __init__(self, name):
        self.name = name
        self.text = None
        self.parameters = []
        self.listItem = None

        if self.name == self.OSCILLATOR:
            self.deltaEps = TheoryParameter(0.3, '\u0394\u03B5', "")  # delta epsilon
            self.f0 = TheoryParameter(6, '\u03BD<sub>0</sub>', "cm<sup>-1</sup>")  # nu 0
            self.gamma = TheoryParameter(0.2, '\u03B3', "cm<sup>-1</sup>")  # gamma
            self.parameters = [self.deltaEps, self.f0, self.gamma]
        if self.name == self.MAGNET_OSCILLATOR:
            self.deltaMu = TheoryParameter(0.07, '\u0394\u03BC', "")  # delta mu
            self.f0 = TheoryParameter(7, '\u03BD<sub>0</sub>', "cm<sup>-1</sup>")  # nu 0
            self.gamma = TheoryParameter(0.1, '\u03B3', "cm<sup>-1</sup>")  # gamma
            self.parameters = [self.deltaMu, self.f0, self.gamma]
        if self.name == self.MAGNET_OSCILLATOR_H:
            self.deltaMu = TheoryParameter(0.07, '\u0394\u03BC', "")  # delta mu
            self.gamma = TheoryParameter(0.1, '\u03B3', "cm<sup>-1</sup>")  # gamma
            self.deltaCF = TheoryParameter(0.1, '\u0394<sub>CF</sub>', "cm<sup>-1</sup>")  # delta CF splitting, cm-1
            self.magneticMoment = TheoryParameter(0.825, '\u03BC<sub>trans</sub>',
                                                  "\u03BC<sub>B</sub>")  # transition magnetic moment, muB
            self.parameters = [self.deltaMu, self.gamma, self.deltaCF, self.magneticMoment]
        if self.name == self.MAGNET_OSCILLATOR_ND:
            self.A = TheoryParameter(0.07, 'A(Δμ = 4πρN<sub>A</sub>·A·th(E/T)/E)', "μ<sub>B</sub>")
            self.gamma = TheoryParameter(0.1, 'γ', "cm<sup>-1</sup>")  # gamma
            self.B = TheoryParameter(0.825, 'B(E = B·H)', "μ<sub>B</sub>")
            self.parameters = [self.A, self.gamma, self.B]
        if self.name == self.OSCILLATOR_ND:
            self.deltaEps = TheoryParameter(0.3, '\u0394\u03B5', "")  # delta epsilon
            self.gamma = TheoryParameter(0.2, '\u03B3', "cm<sup>-1</sup>")  # gamma
            self.mu = TheoryParameter(0.825, '\u03BC<sub>trans</sub>', "\u03BC<sub>B</sub>")
            self.parameters = [self.deltaEps, self.gamma, self.mu]

    def f0_H(self, H):
        kcm = self.h * self.LIGHT_SPEED
        mu = self.magneticMoment.value * self.muB  # delta CF splitting, cm-1; transition magnetic moment, muB
        f0 = 2 * math.sqrt(self.deltaCF.value ** 2 + (H * mu / kcm) ** 2)  # in cm-1
        return f0


class TheoryParameter:
    def __init__(self, value, name, unit, isMain=True, multiplier=1):
        self.value = value
        self.name = name
        self.unit = unit
        self.isMain = isMain
        self.multiplier = multiplier

        w = QWidget()
        hBoxLayout = QHBoxLayout(w)
        hBoxLayout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(self.name + (", " if len(self.unit) > 0 else "") + self.unit)
        # label.setText("<span style='font-size:18pt; font-weight:600; color:#aa0000;'>text1</span><span style='font-size:10pt; font-weight:600; color:#00aa00;'>text2</span>" )
        label.setFont(QFont('Times new roman', 12))
        label.setStyleSheet("color: #000000;" if self.isMain else "color: #888888;")
        hBoxLayout.addWidget(label)
        numberEdit = NumberLineEdit()
        numberEdit.multiplier = self.multiplier
        numberEdit.resetValue(self.value)
        hBoxLayout.addWidget(numberEdit)
        self.numberEdit = numberEdit
        self.widget = w

        # def updateNumber(num):
        #     self.value = num
        self.numberEdit.signalUpdateNumber.connect(self.updateNumber)

    # @pyqtSlot(float)
    def updateNumber(self, num):
        self.value = num


class TheoryCurve:
    def __init__(self, x, y, dataType, comment=""):
        self.plotItem = None
        self.x = x
        self.y = y
        self.dataType = dataType
        self.comment = comment



