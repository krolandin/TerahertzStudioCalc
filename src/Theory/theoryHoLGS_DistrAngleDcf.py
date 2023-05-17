import math
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QListWidgetItem
from PyQt5.QtGui import QColor
from theoryModels import Theory, TheoryParameter, TheoryCurve, Model
from dataTypes import DataTypes, FileTypes
import numpy as np

from numba import vectorize, cuda, jit, float32, float64, int8, uint8, int16, prange, njit, complex64
from numba.types import UniTuple


class TheoryHoLGS_DistrAngleDcf(Theory):
    name = "Ho LGS DistrAngleDcf"

    def __init__(self):
        Theory.__init__(self)

        self.color = QColor(0x0000FF)

        ################### v PARAMETERS v ###################
        self.d = TheoryParameter(1.756 * 0.1, 'd', "cm")  # thickness
        self.epsInf1 = TheoryParameter(14, '\u03B5\'<sub>\u221E</sub>', "")  # epsilon1 inf
        self.epsInf2 = TheoryParameter(0.05, '\u03B5\"<sub>\u221E</sub>', "")  # epsilon2 inf
        self.muInf1 = TheoryParameter(1, '\u03BC\'<sub>\u221E</sub>', "")  # mu1 inf
        self.fFix = TheoryParameter(100, 'f<sub>fix</sub>', "GHz")  # f fixed

        # self.Temperature = TheoryParameter(1.8, "Temperature", "K")
        # self.deltaCF = TheoryParameter(1.005, '\u0394<sub>CF</sub>', "cm<sup>-1</sup>")  # delta CF splitting, cm-1
        # self.gamma = TheoryParameter(1.0, '\u03B3', "cm<sup>-1</sup>")  # gamma
        self.axis_Hext = TheoryParameter(1.0, 'H<sup>ext</sup><sub>i</sub>', "i = 1(x), 2(y), 3(z)")  # gamma
        self.axis_h = TheoryParameter(1.0, 'h<sup>ac</sup><sub>i</sub>', "i = 1(x), 2(y), 3(z)")  # gamma

        self.H_Start = TheoryParameter(0, 'H<sub>start</sub>', "Oe", False)  # H start
        self.H_End = TheoryParameter(30000, 'H<sub>end</sub>', "Oe", False)  # H end

        self.parameters = [self.d, self.epsInf1, self.epsInf2, self.muInf1, self.fFix,
                           self.axis_Hext, self.axis_h,
                           self.H_Start, self.H_End]
        ################### ^ PARAMETERS ^ ###################

        ################### v PLOT VALUES v ###################
        self.H = None  # magnetic fields array, kOe
        self.tr_H = None  # transmittance
        self.ph_H = None  # mirror (optical length), mm
        self.f_H_6m = [None for i in range(6)]
        self.dMu_H_6m = [None for i in range(6)]
        ################### ^ PLOT VALUES ^ ###################

        self.modelTypes = [Model.OSCILLATOR]

        self.curves.append(TheoryCurve(self.H, self.tr_H, DataTypes.SignalH))
        self.curves.append(TheoryCurve(self.H, self.ph_H, DataTypes.MirrorH))

        self.initParameters()

    def update(self):
        self.calcData_H()

    def calcData_H(self):
        H = np.array([self.H_Start.value + i * (self.H_End.value - self.H_Start.value) / numPoints for i in range(numPoints)], dtype=np.float32)
        eps_H0 = 0
        f = self.fFix.value / 30
        for model in self.models:
            if model.name == Model.OSCILLATOR:
                f0 = model.f0.value
                eps_H0 += model.deltaEps.value * f0 ** 2 / (f0 ** 2 - f ** 2 - complex(0, model.gamma.value * f))
        mu = calcDmu_H_f(H, f, int8(self.axis_Hext.value), int8(self.axis_h.value))

        self.tr_H = []
        self.ph_H = []
        epsH = complex(self.epsInf1.value, self.epsInf2.value) + eps_H0
        for i in range(numPoints):
            Tr, fiT = self.calcTrPh(mu[i], epsH, f)
            self.tr_H.append(Tr)
            self.ph_H.append(fiT / (2 * PI * f) * 10)  # mirror (optical depth), mm
        self.updateCurvePoints(H, self.tr_H, DataTypes.SignalH)
        self.updateCurvePoints(H, self.ph_H, DataTypes.MirrorH)

    def calcTrPh(self, mu, eps, f):
        nk = (mu * eps) ** 0.5
        n = nk.real
        k = nk.imag
        ab = (mu / eps) ** 0.5
        a = ab.real
        b = ab.imag
        A = 2 * PI * n * self.d.value * f  # w_Hz = w_cm-1 * LIGHT_SPEED
        E = np.exp(-4 * PI * k * self.d.value * f)  # w_Hz = w_cm-1 * LIGHT_SPEED
        R = ((a - 1) ** 2 + b ** 2) / ((a + 1) ** 2 + b ** 2)
        fiR = np.arctan((2 * b) / (a ** 2 + b ** 2 - 1))
        T = E * ((1 - R) ** 2 + 4 * R * (np.sin(fiR)) ** 2) / (
                (1 - R * E) ** 2 + 4 * R * E * (np.sin(A + fiR)) ** 2)
        fiT = A - np.arctan(b * (a ** 2 + b ** 2 - 1) / ((a ** 2 + b ** 2) * (2 + a) + a)) + np.arctan(
            (R * E * np.sin(2 * A + 2 * fiR)) / (1 - R * E * np.cos(2 * A + 2 * fiR)))
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
cc = 0.0445  # Ho concentration 0.0156 0.0445
numPoints = 60
oneSidePointsNum = 30
T = 1.8
# ma = 3.75 * muB  # 3.75
# mb = 7.13 * muB  # 7.13
# mc = 5.05 * muB  # 5.05
mIon = 9.4 * muB
tetaIon = PI * 58 / 180  # math.acos(mc / mIon)  # PI * 58 / 180
fiIon = PI * 60 / 180  # math.atan(mb / ma)  # PI * 60 / 180
sigmaTeta = PI * 12 / 180  # 128
sigmaFi = PI * 12 / 180  # 12
Dcf0 = 1  # 1.005
sigmaDcf2 = 1
gamma = 1
############## PARAMS
MvHoLang = (138.90 * (1 - cc) + 164.93 * cc) * 3 + 69.72 * 5 + 28.08 + 16 * 14
# mIon = math.sqrt(ma ** 2 + mb ** 2 + mc ** 2)  # 9 .51 * self.muB
pi23 = 2 * PI / 3
dTeta = 3 * 2 * sigmaTeta / (2 * oneSidePointsNum + 1)
dFi = 3 * 2 * sigmaFi / (2 * oneSidePointsNum + 1)
dDcf2 = 12 / (2 * oneSidePointsNum)  # normalX
nPos4PI = 4 * PI * ro / 6 * (3 * cc * NA / MvHoLang) * dTeta * dFi * dDcf2


@jit(float32(float32, float32), nopython=True, nogil=True)
def normal(x, sigma):
    return math.exp(- 0.5 * (x / sigma) ** 2) / math.sqrt(2 * PI) / sigma


@jit(float32(float32, float32, float32, float32), nopython=True, nogil=True)
def normalX(x, sigma, mu, normFactor):
    # sigma = 1.5  # 1  # 0.8  # 1.5
    # maxPos = 2.01
    # mu = maxPos - sigma ** 2 / maxPos
    # normFactor = 0.2608647801  # 0.2608647801  # 0.2959205746  # 0.2343407348
    return normFactor * math.exp(- 0.5 * ((x - mu) / sigma) ** 2) * x


@jit(float32(float32, float32), nopython=True, nogil=True)
def calcNormFactor(sigma, mu):
    p = math.sqrt(0.5 * PI) * mu / math.sqrt(1 / sigma ** 2) + \
        math.exp(-mu ** 2 / (2 * sigma ** 2)) * sigma ** 2 + \
        math.sqrt(0.5 * PI) * mu * sigma * math.erf(mu / (math.sqrt(2) * sigma))
    return 1 / p


# @jit(float32(float32, float32, float32, float32, float32, float32, float32), nopython=True, nogil=True)
# def getDPos(vectHx, vectHy, vectHz, vectMx, vectMy, vectMz, _Dcf):  # cm^-1
#     return 2 * np.sqrt(_Dcf ** 2 + (1 / kcm * (vectHx * vectMx + vectHy * vectMy + vectHz * vectMz)) ** 2)


@jit(float32(float32, float32, float32, float32, float32, float32, float32), nopython=True, nogil=True)
def getEPos(vectHx, vectHy, vectHz, vectMx, vectMy, vectMz, _Dcf):  # cm^-1
    return np.sqrt(_Dcf ** 2 + (1 / kcm * (vectHx * vectMx + vectHy * vectMy + vectHz * vectMz)) ** 2)


@jit(UniTuple(float32, 3)(uint8, float32, float32), nopython=True, nogil=True)
def getVectM(pos, deltaTeta, deltaFi):
    teta = tetaIon + deltaTeta
    if pos == 0:  # 1p
        fiPos = 0
    elif pos == 1:  # 1m
        fiPos = PI - 2 * fiIon
    if pos == 2:  # 2p
        fiPos = pi23
    elif pos == 3:  # 2m
        fiPos = PI - 2 * fiIon + pi23
    if pos == 4:  # 3p
        fiPos = - pi23
    elif pos == 5:  # 3m
        fiPos = PI - 2 * fiIon - pi23
    fi = fiIon + fiPos + deltaFi
    return mIon * math.cos(fi) * math.sin(teta), mIon * math.sin(fi) * math.sin(teta), mIon * math.cos(teta)


@jit(float32(float32, float32, float32), nopython=True, nogil=True)
def getDMuPosE(EPos, m, _Dcf):
    th = math.tanh(EPos * kcm / kB / T)
    dMuPos = nPos4PI * m**2 * (th * (_Dcf/EPos)**2 / (EPos * kcm) + (1 - th**2) * (EPos**2 - _Dcf**2)/(EPos**2 * kB * T))
    # dMuPos = nPos4PI * m ** 2 / (EPos * kcm) * math.tanh(EPos * kcm / kB / T) * (_Dcf / EPos) ** 2
    return dMuPos


@vectorize([complex64(float32, float32, int8, int8)], target='parallel')
def calcDmu_H_f(H_i, f_i, axis_Hext, axis_h):
    maxPos = 2 * Dcf0
    mu = maxPos - sigmaDcf2 ** 2 / maxPos
    normFactor = calcNormFactor(sigmaDcf2, mu)

    mu_i = 1
    for iFi in prange(-oneSidePointsNum, oneSidePointsNum):
        for iTeta in prange(-oneSidePointsNum, oneSidePointsNum):
            for iDcf in prange(0, 2 * oneSidePointsNum):
            #iDcf = 1
                for pos in prange(6):
                    vectMx, vectMy, vectMz = getVectM(pos, float32(iTeta * dTeta), float32(iFi * dFi))

                    if axis_Hext == 1:  # H||a
                        Hx, Hy, Hz = H_i, 0, 0
                    elif axis_Hext == 2:  # H||b
                        Hx, Hy, Hz = 0, H_i, 0
                    elif axis_Hext == 3:  # H||c
                        Hx, Hy, Hz = 0, 0, H_i
                    else:  # H||a
                        Hx, Hy, Hz = H_i, 0, 0

                    EPos = getEPos(Hx, Hy, Hz, vectMx, vectMy, vectMz, float32(iDcf * dDcf2 * 0.5))
                    if EPos == 0:
                        EPos = 0.00001
                    f0 = 2 * EPos

                    if axis_h == 1:  # h||a
                        vectM = vectMx
                    elif axis_h == 2:  # h||b
                        vectM = vectMy
                    elif axis_h == 3:  # h||c
                        vectM = vectMz
                    else:  # h||a
                        vectM = vectMx

                    dMu = getDMuPosE(EPos, vectM, iDcf * dDcf2 * 0.5) * \
                                    normal(iTeta * dTeta, sigmaTeta) * \
                                    normal(iFi * dFi, sigmaFi) * \
                                    normalX(iDcf * dDcf2, sigmaDcf2, mu, normFactor)

                    r = f0 ** 2 - f_i ** 2 - 1j * gamma * f_i
                    if r != 0:
                        mu_i += (dMu * f0 ** 2 / r)
    return mu_i

