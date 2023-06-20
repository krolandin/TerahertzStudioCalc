import math
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QListWidgetItem
from PyQt5.QtGui import QColor
from theoryModels import Theory, TheoryParameter, TheoryCurve, Model
from dataTypes import DataTypes, FileTypes
import numpy as np
from numba import vectorize, cuda, jit, float32, float64, int8, uint8, int16, prange, njit, complex64


class TheoryPrLGS_TrPh_f(Theory):
    name = "PrLGS TrPh(f)"

    LIGHT_SPEED = 2.998e10  # cm/s
    PI = math.pi
    h = 0.66260755e-26
    muB = 0.927401549e-20
    kcm = h * LIGHT_SPEED
    ro = 5.1269
    kB = 1.380658E-16
    NA = 6.022E23
    MvNdLang = 144.242 * 3 + 69.72 * 5 + 28.086 + 15.9994 * 14  # g/mol
    Vcell = 3.347009702e-22  # cm3

    def __init__(self):
        Theory.__init__(self)

        self.color = QColor(0x0000FF)
        self.listItem = QListWidgetItem(self.name)

        ################### v PARAMETERS v ###################
        self.d = TheoryParameter(1.0 * 0.1, 'd', "cm")  # thickness
        self.epsInf1 = TheoryParameter(14, '\u03B5\'<sub>\u221E</sub>', "")  # epsilon1 inf
        self.muInf1 = TheoryParameter(1, '\u03BC\'<sub>\u221E</sub>', "")  # mu1 inf
        self.Temperature = TheoryParameter(1.8, 'T', "K")
        self.f_Start = TheoryParameter(2, '\u03BD<sub>start</sub>', "cm<sup>-1</sup>", False)  # nu start
        self.f_End = TheoryParameter(5, '\u03BD<sub>end</sub>', "cm<sup>-1</sup>", False)  # nu end

        self.deltaMu = TheoryParameter(0.02, 'Δμ', "")  # delta mu
        self.gamma = TheoryParameter(0.5, 'γ', "cm<sup>-1</sup>")  # gamma
        self.sigma = TheoryParameter(8, 'σ<sub>Rayleigh</sub>', "cm<sup>-1</sup>")

        self.parameters = [self.d, self.epsInf1, self.muInf1, self.Temperature,
                           self.f_Start, self.f_End,
                           self.deltaMu, self.gamma, self.sigma]
        ################### ^ PARAMETERS ^ ###################

        self.modelTypes = [Model.OSCILLATOR]

        ################### v PLOT VALUES v ###################
        self.f = None  # frequencies array, cm
        self.tr_f = None  # transmittance
        self.ph_f = None  # phase/frequency, rad/cm-1
        ################### ^ PLOT VALUES ^ ###################

        self.curves.append(TheoryCurve(self.f, self.tr_f, DataTypes.Trf))
        self.curves.append(TheoryCurve(self.f, self.ph_f, DataTypes.Phf))

        self.initParameters()

    def update(self):
        self.calc_f()

    def calc_f(self):
        self.f = np.array([self.f_Start.value + i * (self.f_End.value - self.f_Start.value) / numPoints for i in
                           range(numPoints)], dtype=np.float32)
        eps = []
        # mu = []
        mu = calcDMu_f_RayleighDistr(self.f,
                                     float32(self.deltaMu.value),
                                     float32(self.gamma.value),
                                     float32(self.sigma.value))

        for i in range(self.numPoints):
            eps_i = complex(self.epsInf1.value, 0)
            mu[i] += complex(self.muInf1.value, 0)
            for model in self.models:
                if model.name == Model.OSCILLATOR:
                    eps_i += model.deltaEps.value * model.f0.value ** 2 / (
                            model.f0.value ** 2 - self.f[i] ** 2 - complex(0, model.gamma.value * self.f[i]))
            eps.append(eps_i)

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
        nk = (mu * eps) ** 0.5
        n = nk.real
        k = nk.imag
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


LIGHT_SPEED = 2.998e10  # cm/s
PI = math.pi
h = 6.6260755E-27 / (2 * PI)
kB = 1.380658E-16
NA = 6.022E23
kcm = 2 * PI * h * LIGHT_SPEED  # cm^-1 to erg
kGHz = 30
muB = 0.927401549E-20
ro = 5.2
# Magnetization, frequencies and magnetic contributions for a distorted crystal: six sites

############## PARAMS
numPoints = 1000
oneSidePointsNum = 300


@jit(float32(float32, float32), nopython=True, nogil=True)
def rayleigh(x, sigma):
    return x * math.exp(-0.5 * (x / sigma) ** 2) / sigma ** 2


@vectorize([complex64(float32, float32, float32, float32)], target='parallel')
def calcDMu_f_RayleighDistr(f_i, deltaMu, gamma, sigma):
    dFPos = 4 * sigma / (oneSidePointsNum + 1)
    mu_i = 0
    for iFPos in prange(oneSidePointsNum):
        dMuPos = rayleigh(iFPos * dFPos, sigma) * deltaMu * dFPos
        f = iFPos * dFPos
        r = f ** 2 - f_i ** 2 - 1j * gamma * f_i
        if r != 0:
            mu_i += (dMuPos * f ** 2 / r)
    return mu_i
