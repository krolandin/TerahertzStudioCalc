import math
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QListWidgetItem
from PyQt5.QtGui import QColor
from theoryModels import Theory, TheoryParameter, TheoryCurve, Model
from dataTypes import DataTypes, FileTypes
import numpy as np

from numba import vectorize, cuda, jit, float32, float64, int8, uint8, int16, prange, njit, complex64, guvectorize
from numba.types import UniTuple


class TheoryHoLGS_DistrAngleMu(Theory):
    name = "Ho LGS DistrAngleMu"

    def __init__(self):
        Theory.__init__(self)

        self.color = QColor(0x0000FF)

        ################### v PARAMETERS v ###################
        self.d = TheoryParameter(1.756 * 0.1, 'd', "cm")  # thickness
        self.epsInf1 = TheoryParameter(14, '\u03B5\'<sub>\u221E</sub>', "")  # epsilon1 inf
        self.epsInf2 = TheoryParameter(0.0, '\u03B5\"<sub>\u221E</sub>', "")  # epsilon2 inf
        self.muInf1 = TheoryParameter(1, '\u03BC\'<sub>\u221E</sub>', "")  # mu1 inf
        self.fFix = TheoryParameter(100, 'f<sub>fix</sub>', "GHz")  # f fixed

        self.Temperature = TheoryParameter(1.8, "Temperature", "K")
        self.cc = TheoryParameter(0.0445, "Concentration", "")

        self.mIon = TheoryParameter(9, 'μ<sub>ion</sub>', "μ<sub>B</sub>")
        self.sigmaMIon = TheoryParameter(9.4, 'sigma μ', "μ<sub>B</sub>")
        self.alphaIon = TheoryParameter(58, 'α<sub>ion</sub>', "deg")
        self.sigmaAlpha = TheoryParameter(12, 'sigma α', "deg")
        self.betaIon = TheoryParameter(60, 'β<sub>ion</sub>', "deg")
        self.sigmaBeta = TheoryParameter(12, 'sigma β', "deg")

        self.deltaCF = TheoryParameter(1, 'Δ<sub>CF</sub>', "cm<sup>-1</sup>")
        # self.deltaCF2MaxPos = TheoryParameter(1, '2\u0394<sub>CF</sub> max pos', "cm<sup>-1</sup>")
        # self.deltaCF2Sigma = TheoryParameter(1, 'sigma 2\u0394<sub>CF</sub> max pos', "cm<sup>-1</sup>")
        self.gamma = TheoryParameter(1.0, 'γ', "cm<sup>-1</sup>")

        self.axis_Hext = TheoryParameter(1.0, 'H<sup>ext</sup><sub>i</sub>', "i = 1(x), 2(y), 3(z)")
        self.axis_h = TheoryParameter(1.0, 'h<sup>ac</sup><sub>i</sub>', "i = 1(x), 2(y), 3(z)")

        self.H_Start = TheoryParameter(0, 'H<sub>start</sub>', "Oe", False)  # H start
        self.H_End = TheoryParameter(30000, 'H<sub>end</sub>', "Oe", False)  # H end

        self.parameters = [self.d, self.epsInf1, self.epsInf2, self.muInf1, self.fFix,
                           self.axis_Hext, self.axis_h,
                           self.H_Start, self.H_End,
                           self.Temperature, self.cc,
                           self.mIon, self.sigmaMIon,
                           self.alphaIon, self.sigmaAlpha,
                           self.betaIon, self.sigmaBeta,
                           # self.deltaCF2MaxPos, self.deltaCF2Sigma,
                           self.deltaCF,
                           self.gamma,
                           ]
        ################### ^ PARAMETERS ^ ###################

        ################### v PLOT VALUES v ###################
        self.H = None  # magnetic fields array, kOe
        self.tr_H = None  # transmittance
        self.ph_H = None  # mirror (optical length), mm
        self.dMu_H = None
        self.f_H_6m = [None for i in range(6)]
        self.dMu_H_6m = [None for i in range(6)]
        ################### ^ PLOT VALUES ^ ###################

        self.modelTypes = [Model.OSCILLATOR]

        self.curves.append(TheoryCurve(self.H, self.tr_H, DataTypes.SignalH))
        self.curves.append(TheoryCurve(self.H, self.ph_H, DataTypes.MirrorH))
        self.curves.append(TheoryCurve(self.H, self.dMu_H, DataTypes.dMu_H))

        self.initParameters()

    def update(self):
        self.calcData_H()

    def calcData_H(self):
        H = np.array(
            [self.H_Start.value + i * (self.H_End.value - self.H_Start.value) / numPoints for i in range(numPoints)],
            dtype=np.float32)
        eps_H0 = 0
        f = self.fFix.value / 30
        for model in self.models:
            if model.name == Model.OSCILLATOR:
                f0 = model.f0.value
                eps_H0 += model.deltaEps.value * f0 ** 2 / (f0 ** 2 - f ** 2 - complex(0, model.gamma.value * f))
        mu = calcDmu_H_f(H, f,
                         self.Temperature.value, self.cc.value,
                         self.mIon.value * muB, self.sigmaMIon.value * muB,
                         self.alphaIon.value * PI / 180, self.sigmaAlpha.value * PI / 180,
                         self.betaIon.value * PI / 180, self.sigmaBeta.value * PI / 180,
                         # self.deltaCF2MaxPos.value, self.deltaCF2Sigma.value,
                         self.deltaCF.value,
                         self.gamma.value,
                         int8(self.axis_Hext.value), int8(self.axis_h.value)
                         )

        self.tr_H = []
        self.ph_H = []
        self.dMu_H = []
        epsH = complex(self.epsInf1.value, self.epsInf2.value) + eps_H0
        for i in range(numPoints):
            self.dMu_H.append(mu[i].imag)
            Tr, fiT = self.calcTrPh(mu[i], epsH, f)
            self.tr_H.append(Tr)
            self.ph_H.append(fiT / (2 * PI * f) * 10)  # mirror (optical depth), mm
        self.updateCurvePoints(H, self.tr_H, DataTypes.SignalH)
        self.updateCurvePoints(H, self.ph_H, DataTypes.MirrorH)
        self.updateCurvePoints(H, self.dMu_H, DataTypes.dMu_H)

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

    def getVectM(self, pos, deltaTeta, deltaFi, mIon, tetaIon, fiIon):
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
        return abs(mIon * math.cos(fi) * math.sin(teta)), abs(mIon * math.sin(fi) * math.sin(teta)), abs(
            mIon * math.cos(teta))

    def getEPos(self, vectHx, vectHy, vectHz, vectMx, vectMy, vectMz, _Dcf):  # cm^-1
        return np.sqrt(_Dcf ** 2 + (1 / kcm * (vectHx * vectMx + vectHy * vectMy + vectHz * vectMz)) ** 2)

    def getResonanceFields(self, axis_Hext):
        theoryStr = ""
        for pos in range(6):
            vectMx, vectMy, vectMz = self.getVectM(pos, 0, 0, self.mIon.value, self.tetaIon.value * PI / 180,
                                                   self.fiIon.value * PI / 180)
            if axis_Hext == 1:  # H||a
                theoryStr += "\t" + str(
                    kcm * np.sqrt((self.fFix.value / 30 / 2) ** 2 - (self.deltaCF2Sigma.value / 2) ** 2) / (
                            vectMx * muB))
            elif axis_Hext == 2:  # H||b
                theoryStr += "\t" + str(
                    kcm * np.sqrt((self.fFix.value / 30 / 2) ** 2 - (self.deltaCF2Sigma.value / 2) ** 2) / (
                            vectMy * muB))
            elif axis_Hext == 3:  # H||c
                theoryStr += "\t" + str(
                    kcm * np.sqrt((self.fFix.value / 30 / 2) ** 2 - (self.deltaCF2Sigma.value / 2) ** 2) / (
                            vectMz * muB))
        return theoryStr


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
numPoints = 60
oneSidePointsNum = 12
############## PARAMS
pi23 = 2 * PI / 3


@jit(float32(float32, float32), nopython=True, nogil=True)
def normal(x, sigma):
    return math.exp(- 0.5 * (x / sigma) ** 2) / math.sqrt(2 * PI) / sigma


@jit(float32(float32, float32), nopython=True, nogil=True)
def rayleigh(x, sigma):
    return x * math.exp(-0.5 * (x / sigma) ** 2) / sigma ** 2


@jit(float32(float32, float32), nopython=True, nogil=True)
def malkin(x, sigma):
    return sigma * x / ((sigma ** 2 + x ** 2) ** (3 / 2))


@jit(float32(float32, float32, float32, float32), nopython=True, nogil=True)
def normalX(x, sigma, mu, normFactor):  # x * normal(x) Rice
    return normFactor * math.exp(- 0.5 * ((x - mu) / sigma) ** 2) * x


@jit(float32(float32, float32), nopython=True, nogil=True)
def calcNormFactor(sigma, mu):
    p = math.sqrt(0.5 * PI) * mu / math.sqrt(1 / sigma ** 2) + \
        math.exp(-mu ** 2 / (2 * sigma ** 2)) * sigma ** 2 + \
        math.sqrt(0.5 * PI) * mu * sigma * math.erf(mu / (math.sqrt(2) * sigma))
    return 1 / p


@jit(float32(float32, float32, float32, float32, float32, float32, float32), nopython=True, nogil=True)
def getEPos(vectHx, vectHy, vectHz, vectMx, vectMy, vectMz, deltaCF):  # cm^-1
    return np.sqrt(deltaCF ** 2 + (1 / kcm * (vectHx * vectMx + vectHy * vectMy + vectHz * vectMz)) ** 2)


# @jit(UniTuple(float32, 3)(uint8, float32, float32, float32, float32, float32), nopython=True, nogil=True)
# def getVectM(pos, deltaTeta, deltaFi, mIon, tetaIon, fiIon):
#     teta = tetaIon + deltaTeta
#     if pos == 0:  # 1p
#         fiPos = 0
#     elif pos == 1:  # 1m
#         fiPos = PI - 2 * fiIon
#     if pos == 2:  # 2p
#         fiPos = pi23
#     elif pos == 3:  # 2m
#         fiPos = PI - 2 * fiIon + pi23
#     if pos == 4:  # 3p
#         fiPos = - pi23
#     elif pos == 5:  # 3m
#         fiPos = PI - 2 * fiIon - pi23
#     fi = fiIon + fiPos + deltaFi
#     return mIon * math.cos(fi) * math.sin(teta), mIon * math.sin(fi) * math.sin(teta), mIon * math.cos(teta)


@jit(UniTuple(float32, 3)(uint8, float32, float32, float32), nopython=True, nogil=True)
def getVectMAlpha(pos, mIon, alpha, beta):
    if pos == 0:  # 1p
        return mIon * math.cos(alpha), \
               -mIon * math.sin(alpha) * math.sin(beta), \
               mIon * math.sin(alpha) * math.cos(beta)
    elif pos == 1:  # 1m
        beta -= PI
        return mIon * math.cos(alpha), \
               -mIon * math.sin(alpha) * math.sin(beta), \
               mIon * math.sin(alpha) * math.cos(beta)
    elif pos == 2:  # 2p
        return mIon * (-0.5 * math.cos(alpha) + 0.8660254040 * math.sin(alpha) * math.sin(beta)), \
               mIon * (0.8660254040 * math.cos(alpha) + 0.5 * math.sin(alpha) * math.sin(beta)), \
               mIon * math.sin(alpha) * math.cos(beta)
    elif pos == 3:  # 2m
        beta -= PI
        return mIon * (-0.5 * math.cos(alpha) + 0.8660254040 * math.sin(alpha) * math.sin(beta)), \
               mIon * (0.8660254040 * math.cos(alpha) + 0.5 * math.sin(alpha) * math.sin(beta)), \
               mIon * math.sin(alpha) * math.cos(beta)
    elif pos == 4:  # 3p
        return mIon * (-0.5 * math.cos(alpha) - 0.8660254040 * math.sin(alpha) * math.sin(beta)), \
               mIon * (-0.8660254040 * math.cos(alpha) + 0.5 * math.sin(alpha) * math.sin(beta)), \
               mIon * math.sin(alpha) * math.cos(beta)
    elif pos == 5:  # 3m
        beta -= PI
        return mIon * (-0.5 * math.cos(alpha) - 0.8660254040 * math.sin(alpha) * math.sin(beta)), \
               mIon * (-0.8660254040 * math.cos(alpha) + 0.5 * math.sin(alpha) * math.sin(beta)), \
               mIon * math.sin(alpha) * math.cos(beta)
    return 0, 0, 0


@jit(float32(float32, float32, float32, float32, float32), nopython=True, nogil=True)
def getDMuPosE(EPos, m, deltaCF, T, nPos4PI):
    # th = math.tanh(EPos * kcm / kB / T)
    # dMuPos = nPos4PI * m**2 * (th * (deltaCF/EPos)**2 / (EPos * kcm) + (1 - th**2) * (EPos**2 - deltaCF**2)/(EPos**2 * kB * T))
    dMuPos = nPos4PI * m ** 2 / (EPos * kcm) * math.tanh(EPos * kcm / kB / T) * (deltaCF / EPos) ** 2
    return dMuPos


@vectorize([complex64(float32, float32,  # H, f
                      float32, float32,  # Temperature, cc
                      float32, float32,  # mIon, sigmaMIon
                      float32, float32,  # alphaIon, sigmaAlpha
                      float32, float32,  # betaIon, sigmaBeta
                      # float32, float32,  # deltaCF2MaxPos, deltaCF2Sigma
                      float32,  # deltaCF
                      float32,  # gamma
                      int8, int8,  # axis_Hext, axis_h
                      )], target='parallel')
def calcDmu_H_f(H_i, f_i,
                Temperature, cc,
                mIon, sigmaMIon,
                alphaIon, sigmaAlpha,
                betaIon, sigmaBeta,
                # deltaCF2MaxPos, deltaCF2Sigma,
                deltaCF,
                gamma,
                axis_Hext, axis_h,
                ):
    MvHoLang = (138.90 * (1 - cc) + 164.93 * cc) * 3 + 69.72 * 5 + 28.08 + 16 * 14
    dMIon = 3 * 2 * sigmaMIon / (2 * oneSidePointsNum + 1)
    dAlpha = 3 * 2 * sigmaAlpha / (2 * oneSidePointsNum + 1)
    dBeta = 3 * 2 * sigmaBeta / (2 * oneSidePointsNum + 1)

    # normMu = deltaCF2MaxPos - deltaCF2Sigma ** 2 / deltaCF2MaxPos
    # normFactor = calcNormFactor(deltaCF2Sigma, normMu)
    # dDcf2 = (deltaCF2MaxPos + deltaCF2Sigma * 3) / (2 * oneSidePointsNum)  # normalX (Rice)
    dDcf2 = (4 * deltaCF) / (2 * oneSidePointsNum)  # rayleigh

    nPos4PI = 4 * PI * ro / 6 * (3 * cc * NA / MvHoLang) * dMIon * dAlpha * dBeta #* dDcf2

    mu_i = 1
    for iAlpha in prange(-oneSidePointsNum, oneSidePointsNum):
        for iBeta in prange(-oneSidePointsNum, oneSidePointsNum):
            for iMIon in prange(-oneSidePointsNum, oneSidePointsNum):
                # for iDcf in prange(2 * oneSidePointsNum):
                    for pos in prange(6):
                        vectMx, vectMy, vectMz = getVectMAlpha(pos,
                                                               mIon + float32(iMIon * dMIon),
                                                               alphaIon + float32(iAlpha * dAlpha),
                                                               betaIon + float32(iBeta * dBeta)
                                                               )

                        if axis_Hext == 1:  # H||a
                            Hx, Hy, Hz = H_i, 0, 0
                        elif axis_Hext == 2:  # H||b
                            Hx, Hy, Hz = 0, H_i, 0
                        elif axis_Hext == 3:  # H||c
                            Hx, Hy, Hz = 0, 0, H_i
                        else:  # H||a
                            Hx, Hy, Hz = H_i, 0, 0

                        # EPos = getEPos(Hx, Hy, Hz, vectMx, vectMy, vectMz, float32(iDcf * dDcf2 * 0.5))
                        EPos = getEPos(Hx, Hy, Hz, vectMx, vectMy, vectMz, deltaCF)
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

                        # dMu = getDMuPosE(EPos, vectM, iDcf * dDcf2 * 0.5, Temperature, nPos4PI) * \
                        dMu = getDMuPosE(EPos, vectM, deltaCF, Temperature, nPos4PI) * \
                              normal(iMIon * dMIon, sigmaMIon) * \
                              normal(iAlpha * dAlpha, sigmaAlpha) * \
                              normal(iBeta * dBeta, sigmaBeta) #* \
                              # normalX(iDcf * dDcf2, deltaCF2Sigma, normMu, normFactor)
                              # rayleigh(iDcf * dDcf2, deltaCF2MaxPos)

                        r = f0 ** 2 - f_i ** 2 - 1j * gamma * f_i
                        if r != 0:
                            mu_i += (dMu * f0 ** 2 / r)
    return mu_i
