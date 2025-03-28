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
        if self.name == "Ho LGS DistrAngleDcf" or self.name == "Ho LGS M(teta)" or self.name == "Ho LGS M(H)":
            pass
        else:
            self.update()
        self.plotCurves()

    def updateCurvePoints(self, x, y, dataType, comment=""):
        for curve in self.curves:
            if curve.dataType == dataType and curve.comment == comment:
                curve.x = x
                curve.y = y


# class TheoryTrPh_f(Theory):
#     LIGHT_SPEED = 2.998e10  # cm/s
#     PI = math.pi
#     name = "Tr,Ph(f)"
#
#     def __init__(self):
#         Theory.__init__(self)
#         self.listItem = QListWidgetItem(self.name)
#
#         self.d = TheoryParameter(1.756 * 0.1, 'd', "cm")  # thickness
#         self.epsInf1 = TheoryParameter(14, '\u03B5\'<sub>\u221E</sub>', "")  # epsilon1 inf
#         self.epsInf2 = TheoryParameter(0.05, '\u03B5\"<sub>\u221E</sub>', "")  # epsilon2 inf
#         self.muInf1 = TheoryParameter(1, '\u03BC\'<sub>\u221E</sub>', "")  # mu1 inf
#         self.f_Start = TheoryParameter(2, '\u03BD<sub>start</sub>', "cm<sup>-1</sup>", False)  # nu start
#         self.f_End = TheoryParameter(5, '\u03BD<sub>end</sub>', "cm<sup>-1</sup>", False)  # nu end
#
#         self.parameters = [self.d, self.epsInf1, self.epsInf2, self.muInf1,
#                            self.f_Start, self.f_End]
#
#         self.modelTypes = [Model.OSCILLATOR, Model.MAGNET_OSCILLATOR]
#
#         self.f = None  # frequencies array, cm
#         self.tr_f = None  # transmittance
#         self.ph_f = None  # phase/frequency, rad/cm-1
#
#         self.curves.append(TheoryCurve(self.f, self.tr_f, DataTypes.Trf))
#         self.curves.append(TheoryCurve(self.f, self.ph_f, DataTypes.Phf))
#
#         self.initParameters()
#
#     def update(self):
#         self.calc_f()
#
#     def calc_f(self):
#         self.f = [self.f_Start.value + i * (self.f_End.value - self.f_Start.value) / self.numPoints for i in
#                   range(self.numPoints)]  # frequencies array, cm
#         eps = []
#         mu = []
#         for i in range(self.numPoints):
#             eps_i = complex(self.epsInf1.value, self.epsInf2.value)
#             mu_i = complex(self.muInf1.value, 0)
#             for model in self.models:
#                 if model.name == Model.OSCILLATOR:
#                     eps_i += model.deltaEps.value * model.f0.value ** 2 / (
#                             model.f0.value ** 2 - self.f[i] ** 2 - complex(0, model.gamma.value * self.f[i]))
#                 if model.name == Model.MAGNET_OSCILLATOR:
#                     f0 = model.f0.value
#                     mu_i += model.deltaMu.value * f0 ** 2 / (
#                             f0 ** 2 - self.f[i] ** 2 - complex(0, model.gamma.value * self.f[i]))
#             eps.append(eps_i)
#             mu.append(mu_i)
#         self.tr_f = []
#         self.ph_f = []
#         for i in range(self.numPoints):
#             TrPh = self.calcTrPh(mu[i], eps[i], self.f[i])
#             T = TrPh[0]
#             fiT = TrPh[1]
#             self.tr_f.append(T)
#             self.ph_f.append(fiT / self.f[i])
#         self.updateCurvePoints(self.f, self.tr_f, DataTypes.Trf)
#         self.updateCurvePoints(self.f, self.ph_f, DataTypes.Phf)
#
#     def calcTrPh(self, mu, eps, f):
#         # sigma = 0  # [0.5*self.epsInf2*self.w[i] for i in range(self.numPoints)] # cond
#         # nk = (mu * (self.eps[i] + complex(0, 2 * sigma / self.f[i] / self.LIGHT_SPEED))) ** 0.5
#         nk = (mu * eps) ** 0.5
#         n = nk.real
#         k = nk.imag
#         # ab = (mu / (self.eps[i] + complex(0, 2 * sigma / self.f[i] / self.LIGHT_SPEED))) ** 0.5
#         ab = (mu / eps) ** 0.5
#         a = ab.real
#         b = ab.imag
#         A = 2 * self.PI * n * self.d.value * f  # w_Hz = w_cm-1 * LIGHT_SPEED
#         E = math.exp(-4 * self.PI * k * self.d.value * f)  # w_Hz = w_cm-1 * LIGHT_SPEED
#         R = ((a - 1) ** 2 + b ** 2) / ((a + 1) ** 2 + b ** 2)
#         fiR = math.atan((2 * b) / (a ** 2 + b ** 2 - 1))
#         T = E * ((1 - R) ** 2 + 4 * R * (math.sin(fiR)) ** 2) / (
#                 (1 - R * E) ** 2 + 4 * R * E * (math.sin(A + fiR)) ** 2)
#         if T < 1e-6:  # value limitation for logarithmic scale use
#             T = 1e-6
#         fiT = A - math.atan(b * (a ** 2 + b ** 2 - 1) / ((a ** 2 + b ** 2) * (2 + a) + a)) + math.atan(
#             (R * E * math.sin(2 * A + 2 * fiR)) / (1 - R * E * math.cos(2 * A + 2 * fiR)))
#         return T, fiT


# class TheoryTrPh_fH(Theory):
#     LIGHT_SPEED = 2.998e10  # cm/s
#     PI = math.pi
#     name = "Tr,Ph(f), Tr,Ph(H(f))"
#
#     def __init__(self):
#         Theory.__init__(self)
#         self.listItem = QListWidgetItem(self.name)
#
#         self.d = TheoryParameter(1.756 * 0.1, 'd', "cm")  # thickness
#         self.epsInf1 = TheoryParameter(14, '\u03B5\'<sub>\u221E</sub>', "")  # epsilon1 inf
#         self.epsInf2 = TheoryParameter(0.05, '\u03B5\"<sub>\u221E</sub>', "")  # epsilon2 inf
#         self.muInf1 = TheoryParameter(1, '\u03BC\'<sub>\u221E</sub>', "")  # mu1 inf
#         self.Hext = TheoryParameter(40000, 'H<sub>ext</sub>', "Oe")  # H external
#         self.fFix = TheoryParameter(100, 'f<sub>fix</sub>', "GHz")  # f fixed
#         self.f_Start = TheoryParameter(2, '\u03BD<sub>start</sub>', "cm<sup>-1</sup>", False)  # nu start
#         self.f_End = TheoryParameter(5, '\u03BD<sub>end</sub>', "cm<sup>-1</sup>", False)  # nu end
#         self.H_Start = TheoryParameter(0, 'H<sub>start</sub>', "Oe", False)  # H start
#         self.H_End = TheoryParameter(60000, 'H<sub>end</sub>', "Oe", False)  # H end
#
#         self.parameters = [self.d, self.epsInf1, self.epsInf2, self.muInf1, self.Hext, self.fFix,
#                            self.f_Start, self.f_End, self.H_Start, self.H_End]
#
#         self.modelTypes = [Model.OSCILLATOR, Model.MAGNET_OSCILLATOR_H]
#
#         self.f = None  # frequencies array, cm
#         self.H = None  # magnetic fields array, kOe
#         self.tr_f = None  # transmittance
#         self.ph_f = None  # phase/frequency, rad/cm-1
#         self.tr_H = None  # transmittance
#         self.ph_H = None  # mirror (optical length), mm
#
#         # QFontDatabase.addApplicationFont("../fonts/Montserrat-ThinItalic.ttf")
#
#         self.curves.append(TheoryCurve(self.f, self.tr_f, DataTypes.Trf))
#         self.curves.append(TheoryCurve(self.f, self.ph_f, DataTypes.Phf))
#         self.curves.append(TheoryCurve(self.H, self.tr_H, DataTypes.SignalH))
#         self.curves.append(TheoryCurve(self.H, self.ph_H, DataTypes.MirrorH))
#
#         self.initParameters()
#
#     def update(self):
#         self.calc_f()
#         self.calc_H()
#
#     def calc_f(self):
#         self.f = [self.f_Start.value + i * (self.f_End.value - self.f_Start.value) / self.numPoints for i in
#                   range(self.numPoints)]  # frequencies array, cm
#         eps = []
#         mu = []
#         for i in range(self.numPoints):
#             eps_i = complex(self.epsInf1.value, self.epsInf2.value)
#             mu_i = complex(self.muInf1.value, 0)
#             for model in self.models:
#                 if model.name == Model.OSCILLATOR:
#                     eps_i += model.deltaEps.value * model.f0.value ** 2 / (
#                             model.f0.value ** 2 - self.f[i] ** 2 - complex(0, model.gamma.value * self.f[i]))
#                 if model.name == Model.MAGNET_OSCILLATOR_H:
#                     f0 = model.f0_H(self.Hext.value)
#                     mu_i += model.deltaMu.value * f0 ** 2 / (
#                             f0 ** 2 - self.f[i] ** 2 - complex(0, model.gamma.value * self.f[i]))
#             eps.append(eps_i)
#             mu.append(mu_i)
#         self.tr_f = []
#         self.ph_f = []
#         for i in range(self.numPoints):
#             TrPh = self.calcTrPh(mu[i], eps[i], self.f[i])
#             T = TrPh[0]
#             fiT = TrPh[1]
#             self.tr_f.append(T)
#             self.ph_f.append(fiT / self.f[i])
#         self.updateCurvePoints(self.f, self.tr_f, DataTypes.Trf)
#         self.updateCurvePoints(self.f, self.ph_f, DataTypes.Phf)
#
#     def calc_H(self):
#         self.H = [self.H_Start.value + i * (self.H_End.value - self.H_Start.value) / self.numPoints for i in
#                   range(self.numPoints)]  # magnetic fields array, Oe
#         eps = []
#         mu = []
#         f = self.fFix.value / 30
#         for i in range(self.numPoints):
#             eps_i = complex(self.epsInf1.value, self.epsInf2.value)
#             mu_i = complex(self.muInf1.value, 0)
#             for model in self.models:
#                 if model.name == Model.OSCILLATOR:
#                     eps_i += model.deltaEps.value * model.f0.value ** 2 / (
#                             model.f0.value ** 2 - f ** 2 - complex(0, model.gamma.value * f))
#                 if model.name == Model.MAGNET_OSCILLATOR_H:
#                     f0 = model.f0_H(self.H[i])
#                     mu_i += model.deltaMu.value * f0 ** 2 / (
#                             f0 ** 2 - f ** 2 - complex(0, model.gamma.value * f))
#             eps.append(eps_i)
#             mu.append(mu_i)
#         self.tr_H = []
#         self.ph_H = []
#         for i in range(self.numPoints):
#             TrPh = self.calcTrPh(mu[i], eps[i], f)
#             T = TrPh[0]
#             fiT = TrPh[1]
#             self.tr_H.append(T)
#             self.ph_H.append(fiT / (2 * self.PI * f) * 10)  # mirror (optical depth), mm
#         self.updateCurvePoints(self.H, self.tr_H, DataTypes.SignalH)
#         self.updateCurvePoints(self.H, self.ph_H, DataTypes.MirrorH)
#
#     def calcTrPh(self, mu, eps, f):
#         # sigma = 0  # [0.5*self.epsInf2*self.w[i] for i in range(self.numPoints)] # cond
#         # nk = (mu * (self.eps[i] + complex(0, 2 * sigma / self.f[i] / self.LIGHT_SPEED))) ** 0.5
#         nk = (mu * eps) ** 0.5
#         n = nk.real
#         k = nk.imag
#         # ab = (mu / (self.eps[i] + complex(0, 2 * sigma / self.f[i] / self.LIGHT_SPEED))) ** 0.5
#         ab = (mu / eps) ** 0.5
#         a = ab.real
#         b = ab.imag
#         A = 2 * self.PI * n * self.d.value * f  # w_Hz = w_cm-1 * LIGHT_SPEED
#         E = math.exp(-4 * self.PI * k * self.d.value * f)  # w_Hz = w_cm-1 * LIGHT_SPEED
#         R = ((a - 1) ** 2 + b ** 2) / ((a + 1) ** 2 + b ** 2)
#         fiR = math.atan((2 * b) / (a ** 2 + b ** 2 - 1))
#         T = E * ((1 - R) ** 2 + 4 * R * (math.sin(fiR)) ** 2) / (
#                 (1 - R * E) ** 2 + 4 * R * E * (math.sin(A + fiR)) ** 2)
#         fiT = A - math.atan(b * (a ** 2 + b ** 2 - 1) / ((a ** 2 + b ** 2) * (2 + a) + a)) + math.atan(
#             (R * E * math.sin(2 * A + 2 * fiR)) / (1 - R * E * math.cos(2 * A + 2 * fiR)))
#         return T, fiT


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
    RELAXATOR = "Relaxator"
    DRUDE = "Drude"

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
        if self.name == self.RELAXATOR:
            self.deltaEps = TheoryParameter(0.3, 'Δε', "")  # delta epsilon
            self.f0 = TheoryParameter(20, 'ω<sub>0</sub>=1/τ', "cm<sup>-1</sup>")  # nu 0
            self.parameters = [self.deltaEps, self.f0]
        if self.name == self.DRUDE:
            self.sigma = TheoryParameter(5, 'σ<sub>0</sub>', "S ⋅ cm<sup>-1</sup>")  # delta epsilon
            self.gamma = TheoryParameter(20, 'Γ', "cm<sup>-1</sup>")  # nu 0
            self.parameters = [self.sigma, self.gamma]

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



