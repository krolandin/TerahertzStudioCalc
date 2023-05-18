import math
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QListWidgetItem
from theoryModels import Theory, TheoryParameter, TheoryCurve, Model
from dataTypes import DataTypes, FileTypes


class TheoryTrPh_fH(Theory):
    LIGHT_SPEED = 2.998e10  # cm/s
    PI = math.pi
    name = "Tr,Ph(f), Tr,Ph(H(f))"

    def __init__(self):
        Theory.__init__(self)
        self.listItem = QListWidgetItem(self.name)

        self.d = TheoryParameter(1.756 * 0.1, 'd', "cm")  # thickness
        self.epsInf1 = TheoryParameter(14, '\u03B5\'<sub>\u221E</sub>', "")  # epsilon1 inf
        self.epsInf2 = TheoryParameter(0.05, '\u03B5\"<sub>\u221E</sub>', "")  # epsilon2 inf
        self.muInf1 = TheoryParameter(1, '\u03BC\'<sub>\u221E</sub>', "")  # mu1 inf
        self.Hext = TheoryParameter(40000, 'H<sub>ext</sub>', "Oe")  # H external
        self.fFix = TheoryParameter(100, 'f<sub>fix</sub>', "GHz")  # f fixed
        self.f_Start = TheoryParameter(2, '\u03BD<sub>start</sub>', "cm<sup>-1</sup>", False)  # nu start
        self.f_End = TheoryParameter(5, '\u03BD<sub>end</sub>', "cm<sup>-1</sup>", False)  # nu end
        self.H_Start = TheoryParameter(0, 'H<sub>start</sub>', "Oe", False)  # H start
        self.H_End = TheoryParameter(60000, 'H<sub>end</sub>', "Oe", False)  # H end

        self.parameters = [self.d, self.epsInf1, self.epsInf2, self.muInf1, self.Hext, self.fFix,
                           self.f_Start, self.f_End, self.H_Start, self.H_End]

        self.modelTypes = [Model.OSCILLATOR, Model.MAGNET_OSCILLATOR_H]

        self.f = None  # frequencies array, cm
        self.H = None  # magnetic fields array, kOe
        self.tr_f = None  # transmittance
        self.ph_f = None  # phase/frequency, rad/cm-1
        self.tr_H = None  # transmittance
        self.ph_H = None  # mirror (optical length), mm

        # QFontDatabase.addApplicationFont("../fonts/Montserrat-ThinItalic.ttf")

        self.curves.append(TheoryCurve(self.f, self.tr_f, DataTypes.Trf))
        self.curves.append(TheoryCurve(self.f, self.ph_f, DataTypes.Phf))
        self.curves.append(TheoryCurve(self.H, self.tr_H, DataTypes.SignalH))
        self.curves.append(TheoryCurve(self.H, self.ph_H, DataTypes.MirrorH))

        self.initParameters()

    def update(self):
        self.calc_f()
        self.calc_H()

    def calc_f(self):
        self.f = [self.f_Start.value + i * (self.f_End.value - self.f_Start.value) / self.numPoints for i in
                  range(self.numPoints)]  # frequencies array, cm
        eps = []
        mu = []
        for i in range(self.numPoints):
            eps_i = complex(self.epsInf1.value, self.epsInf2.value)
            mu_i = complex(self.muInf1.value, 0)
            for model in self.models:
                if model.name == Model.OSCILLATOR:
                    eps_i += model.deltaEps.value * model.f0.value ** 2 / (
                            model.f0.value ** 2 - self.f[i] ** 2 - complex(0, model.gamma.value * self.f[i]))
                if model.name == Model.MAGNET_OSCILLATOR_H:
                    f0 = model.f0_H(self.Hext.value)
                    mu_i += model.deltaMu.value * f0 ** 2 / (
                            f0 ** 2 - self.f[i] ** 2 - complex(0, model.gamma.value * self.f[i]))
            eps.append(eps_i)
            mu.append(mu_i)
        self.tr_f = []
        self.ph_f = []
        for i in range(self.numPoints):
            TrPh = self.calcTrPh(mu[i], eps[i], self.f[i])
            T = TrPh[0]
            fiT = TrPh[1]
            self.tr_f.append(T)
            self.ph_f.append(fiT / self.f[i])
        self.updateCurvePoints(self.f, self.tr_f, DataTypes.Trf)
        self.updateCurvePoints(self.f, self.ph_f, DataTypes.Phf)

    def calc_H(self):
        self.H = [self.H_Start.value + i * (self.H_End.value - self.H_Start.value) / self.numPoints for i in
                  range(self.numPoints)]  # magnetic fields array, Oe
        eps = []
        mu = []
        f = self.fFix.value / 30
        for i in range(self.numPoints):
            eps_i = complex(self.epsInf1.value, self.epsInf2.value)
            mu_i = complex(self.muInf1.value, 0)
            for model in self.models:
                if model.name == Model.OSCILLATOR:
                    eps_i += model.deltaEps.value * model.f0.value ** 2 / (
                            model.f0.value ** 2 - f ** 2 - complex(0, model.gamma.value * f))
                if model.name == Model.MAGNET_OSCILLATOR_H:
                    f0 = model.f0_H(self.H[i])
                    mu_i += model.deltaMu.value * f0 ** 2 / (
                            f0 ** 2 - f ** 2 - complex(0, model.gamma.value * f))
            eps.append(eps_i)
            mu.append(mu_i)
        self.tr_H = []
        self.ph_H = []
        for i in range(self.numPoints):
            TrPh = self.calcTrPh(mu[i], eps[i], f)
            T = TrPh[0]
            fiT = TrPh[1]
            self.tr_H.append(T)
            self.ph_H.append(fiT / (2 * self.PI * f) * 10)  # mirror (optical depth), mm
        self.updateCurvePoints(self.H, self.tr_H, DataTypes.SignalH)
        self.updateCurvePoints(self.H, self.ph_H, DataTypes.MirrorH)

    def calcTrPh(self, mu, eps, f):
        # sigma = 0  # [0.5*self.epsInf2*self.w[i] for i in range(self.numPoints)] # cond
        # nk = (mu * (self.eps[i] + complex(0, 2 * sigma / self.f[i] / self.LIGHT_SPEED))) ** 0.5
        nk = (mu * eps) ** 0.5
        n = nk.real
        k = nk.imag
        # ab = (mu / (self.eps[i] + complex(0, 2 * sigma / self.f[i] / self.LIGHT_SPEED))) ** 0.5
        ab = (mu / eps) ** 0.5
        a = ab.real
        b = ab.imag
        A = 2 * self.PI * n * self.d.value * f  # w_Hz = w_cm-1 * LIGHT_SPEED
        E = math.exp(-4 * self.PI * k * self.d.value * f)  # w_Hz = w_cm-1 * LIGHT_SPEED
        R = ((a - 1) ** 2 + b ** 2) / ((a + 1) ** 2 + b ** 2)
        fiR = math.atan((2 * b) / (a ** 2 + b ** 2 - 1))
        T = E * ((1 - R) ** 2 + 4 * R * (math.sin(fiR)) ** 2) / (
                (1 - R * E) ** 2 + 4 * R * E * (math.sin(A + fiR)) ** 2)
        fiT = A - math.atan(b * (a ** 2 + b ** 2 - 1) / ((a ** 2 + b ** 2) * (2 + a) + a)) + math.atan(
            (R * E * math.sin(2 * A + 2 * fiR)) / (1 - R * E * math.cos(2 * A + 2 * fiR)))
        return T, fiT