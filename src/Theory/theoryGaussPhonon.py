import math
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QListWidgetItem
from PyQt5.QtGui import QColor
from theoryModels import Theory, TheoryParameter, TheoryCurve, Model
from dataTypes import DataTypes, FileTypes
import numpy as np

from numba import vectorize, cuda, jit, float32, float64, int8, uint8, int16, prange, njit, complex64
from numba.types import UniTuple


class TheoryGaussPhonon(Theory):
    name = "Gauss phonon"

    def __init__(self):
        Theory.__init__(self)

        self.color = QColor(0x0000FF)

        ################### v PARAMETERS v ###################
        self.d = TheoryParameter(1.756 * 0.1, 'd', "cm")  # thickness
        self.epsInf1 = TheoryParameter(14, '\u03B5\'<sub>\u221E</sub>', "")  # epsilon1 inf
        self.epsInf2 = TheoryParameter(0.05, '\u03B5\"<sub>\u221E</sub>', "")  # epsilon2 inf
        self.muInf1 = TheoryParameter(1, '\u03BC\'<sub>\u221E</sub>', "")  # mu1 inf
        self.f_Start = TheoryParameter(2, '\u03BD<sub>start</sub>', "cm<sup>-1</sup>", False)  # nu start
        self.f_End = TheoryParameter(5, '\u03BD<sub>end</sub>', "cm<sup>-1</sup>", False)  # nu end

        self.deltaEps = TheoryParameter(0.3, '\u0394\u03B5<sub>Phonon</sub>', "")  # delta epsilon
        self.f0 = TheoryParameter(6, '\u03BD<sub>0</sub>', "cm<sup>-1</sup>")  # nu 0
        self.gamma = TheoryParameter(0.2, '\u03B3', "cm<sup>-1</sup>")  # gamma
        self.sigma2 = TheoryParameter(0.2, '2σ', "cm<sup>-1</sup>")  # 2 sigma

        self.parameters = [self.d, self.epsInf1, self.epsInf2, self.muInf1,
                           self.f_Start, self.f_End,
                           self.deltaEps, self.f0, self.sigma2, self.gamma]
        ################### ^ PARAMETERS ^ ###################

        ################### v PLOT VALUES v ###################
        self.f = None  # frequencies array, cm
        self.tr_f = None  # transmittance
        self.ph_f = None  # phase/frequency, rad/cm-1
        self.r_f = None  # Reflectivity
        self.rph_f = None  # Reflectivity phase, rad
        ################### ^ PLOT VALUES ^ ###################

        self.modelTypes = [Model.OSCILLATOR, Model.MAGNET_OSCILLATOR]

        self.curves.append(TheoryCurve(self.f, self.tr_f, DataTypes.Trf))
        self.curves.append(TheoryCurve(self.f, self.ph_f, DataTypes.Phf))
        self.curves.append(TheoryCurve(self.f, self.r_f, DataTypes.R_f))
        self.curves.append(TheoryCurve(self.f, self.rph_f, DataTypes.PhR_f))

        self.initParameters()

    def update(self):
        self.calc_f()

    def calc_f(self):
        self.f = np.array([self.f_Start.value + i * (self.f_End.value - self.f_Start.value) / numPoints for i in
                           range(numPoints)], dtype=np.float32)  # frequencies array, cm

        eps = calcDEps_f_GaussPhonon(self.f, float32(self.deltaEps.value),
                                     float32(self.f0.value),
                                     float32(self.sigma2.value),
                                     float32(self.gamma.value))

        # eps = []
        mu = []
        for i in range(numPoints):
            eps[i] += complex(self.epsInf1.value, self.epsInf2.value)
            mu_i = complex(self.muInf1.value, 0)
            for model in self.models:
                if model.name == Model.OSCILLATOR:
                    eps[i] += model.deltaEps.value * model.f0.value ** 2 / (
                            model.f0.value ** 2 - self.f[i] ** 2 - complex(0, model.gamma.value * self.f[i]))
                if model.name == Model.MAGNET_OSCILLATOR:
                    f0 = model.f0.value
                    mu_i += model.deltaMu.value * f0 ** 2 / (
                            f0 ** 2 - self.f[i] ** 2 - complex(0, model.gamma.value * self.f[i]))
            # eps.append(eps_i)
            mu.append(mu_i)
            # np.append(eps, eps_i)

        self.tr_f = []
        self.ph_f = []
        self.r_f = []
        self.rph_f = []
        for i in range(numPoints):
            # TrPh = self.calcTrPh(mu[i], eps[i], self.f[i])
            # Tr = TrPh[0]
            # fiTr = TrPh[1]
            # self.tr_f.append(Tr)
            # self.ph_f.append(fiTr / self.f[i])

            TrRPh = self.calcTrRPh(mu[i], eps[i], self.f[i])
            T = TrRPh[0]
            fiT = TrRPh[1]
            R = TrRPh[2]
            fiR = TrRPh[3]
            self.tr_f.append(T)
            self.ph_f.append(fiT / self.f[i])
            self.r_f.append(R)
            self.rph_f.append(fiR)


        self.updateCurvePoints(self.f, self.tr_f, DataTypes.Trf)
        self.updateCurvePoints(self.f, self.ph_f, DataTypes.Phf)
        self.updateCurvePoints(self.f, self.r_f, DataTypes.R_f)
        self.updateCurvePoints(self.f, self.rph_f, DataTypes.PhR_f)

    def calcTrRPh(self, mu, eps, f):
        nk = (mu * eps) ** 0.5
        n = nk.real
        k = nk.imag
        ab = (mu / eps) ** 0.5
        a = ab.real
        b = ab.imag
        A = 2 * PI * n * self.d.value * f  # w_Hz = w_cm-1 * LIGHT_SPEED
        E = math.exp(-4 * PI * k * self.d.value * f)  # w_Hz = w_cm-1 * LIGHT_SPEED
        R = ((a - 1) ** 2 + b ** 2) / ((a + 1) ** 2 + b ** 2)
        fiR = math.atan((2 * b) / (a ** 2 + b ** 2 - 1))
        T = E * ((1 - R) ** 2 + 4 * R * (math.sin(fiR)) ** 2) / (
                (1 - R * E) ** 2 + 4 * R * E * (math.sin(A + fiR)) ** 2)
        if T < 1e-6:  # value limitation for logarithmic scale use
            T = 1e-6
        fiT = A - math.atan(b * (a ** 2 + b ** 2 - 1) / ((a ** 2 + b ** 2) * (2 + a) + a)) + math.atan(
            (R * E * math.sin(2 * A + 2 * fiR)) / (1 - R * E * math.cos(2 * A + 2 * fiR)))
        return T, fiT, R, fiR


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
def normal(x, sigma):
    return math.exp(- 0.5 * (x / sigma) ** 2) / math.sqrt(2 * PI) / sigma


@vectorize([complex64(float32, float32, float32, float32, float32)], target='parallel')
def calcDEps_f_GaussPhonon(f_i, deltaEps, f0, sigma2, gamma):
    dFPos = 1.5 * 3 * sigma2 / (2 * oneSidePointsNum + 1)
    # gammaLorentz = 4 * gamma / oneSidePointsNum
    eps_i = 0
    for iFPos in prange(-oneSidePointsNum, oneSidePointsNum):

        dEpsPos = normal(iFPos * dFPos, sigma2 * 0.5) * deltaEps * dFPos
        f = f0 + iFPos * dFPos

        r = f ** 2 - f_i ** 2 - 1j * gamma * f_i
        if r != 0:
            eps_i += (dEpsPos * f ** 2 / r)
    return eps_i
