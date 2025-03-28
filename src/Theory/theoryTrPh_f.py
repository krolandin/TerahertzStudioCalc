import math
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QListWidgetItem
from PyQt5.QtGui import QColor
from theoryModels import Theory, TheoryParameter, TheoryCurve, Model
from dataTypes import DataTypes, FileTypes
import numpy as np
import time
from numba import vectorize, cuda, jit, float32, float64, int8, int16, prange


class TheoryTrPh_f(Theory):
    LIGHT_SPEED = 2.998e10  # cm/s
    PI = math.pi
    name = "Tr,Ph(f)"

    def __init__(self):
        Theory.__init__(self)
        self.listItem = QListWidgetItem(self.name)

        self.d = TheoryParameter(1.756 * 0.1, 'd', "cm")  # thickness
        self.epsInf1 = TheoryParameter(14, '\u03B5\'<sub>\u221E</sub>', "")  # epsilon1 inf
        self.epsInf2 = TheoryParameter(0.05, '\u03B5\"<sub>\u221E</sub>', "")  # epsilon2 inf
        self.muInf1 = TheoryParameter(1, '\u03BC\'<sub>\u221E</sub>', "")  # mu1 inf
        self.f_Start = TheoryParameter(2, '\u03BD<sub>start</sub>', "cm<sup>-1</sup>", False)  # nu start
        self.f_End = TheoryParameter(5, '\u03BD<sub>end</sub>', "cm<sup>-1</sup>", False)  # nu end

        self.parameters = [self.d, self.epsInf1, self.epsInf2, self.muInf1,
                           self.f_Start, self.f_End]

        self.modelTypes = [Model.OSCILLATOR, Model.MAGNET_OSCILLATOR, Model.RELAXATOR, Model.DRUDE]

        self.f = None  # frequencies array, cm
        self.tr_f = None  # transmittance
        self.ph_f = None  # phase/frequency, rad/cm-1

        self.curves.append(TheoryCurve(self.f, self.tr_f, DataTypes.Trf))
        self.curves.append(TheoryCurve(self.f, self.ph_f, DataTypes.Phf))

        self.initParameters()

    def update(self):
        self.calc_f()

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
                if model.name == Model.MAGNET_OSCILLATOR:
                    f0 = model.f0.value
                    mu_i += model.deltaMu.value * f0 ** 2 / (
                            f0 ** 2 - self.f[i] ** 2 - complex(0, model.gamma.value * self.f[i]))
                if model.name == Model.RELAXATOR:
                    eps_i += model.deltaEps.value / (1 - complex(0, self.f[i]/model.f0.value))
                if model.name == Model.DRUDE:
                    eps_i += 1j*4*math.pi*model.sigma.value*model.gamma.value/(self.f[i]*(model.gamma.value-1j*self.f[i]))
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
        if T < 1e-6:  # value limitation for logarithmic scale use
            T = 1e-6
        fiT = A - math.atan(b * (a ** 2 + b ** 2 - 1) / ((a ** 2 + b ** 2) * (2 + a) + a)) + math.atan(
            (R * E * math.sin(2 * A + 2 * fiR)) / (1 - R * E * math.cos(2 * A + 2 * fiR)))
        return T, fiT

    def getModelsString(self):
        theoryStr = ""
        theoryStr += "\t" + str(self.d.value)
        theoryStr += "\t" + str(self.epsInf1.value)
        theoryStr += "\t" + str(self.epsInf2.value)
        theoryStr += "\t" + str(self.muInf1.value)

        for m in self.models:
            if m.name == m.MAGNET_OSCILLATOR:
                theoryStr += "\t" + str(m.deltaMu.value)
                theoryStr += "\t" + str(m.f0.value)
                theoryStr += "\t" + str(m.gamma.value)
            if m.name == m.OSCILLATOR:
                theoryStr += "\t" + str(m.deltaEps.value)
                theoryStr += "\t" + str(m.f0.value)
                theoryStr += "\t" + str(m.gamma.value)

        return theoryStr