import math
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QListWidgetItem
from PyQt5.QtGui import QColor
from theoryModels import Theory, TheoryParameter, TheoryCurve, Model
from dataTypes import DataTypes, FileTypes
import numpy as np

from numba import vectorize, guvectorize, cuda, jit, float32, float64, int8, uint8, int16, prange, njit, complex64
from numba.types import UniTuple


class TheoryTbLangasite_M_H(Theory):
    name = "Tb LGS M(H) 3 + 3 pos"

    def __init__(self):
        Theory.__init__(self)

        self.color = QColor(0x0000FF)

        ################### v PARAMETERS v ###################
        self.Concentration = TheoryParameter(0.0445, "Concentration", "")
        self.Temperature = TheoryParameter(1.9, "Temperature", "K")
        self.mIon = TheoryParameter(9.51, "mIon", "muB")
        self.tetaIon = TheoryParameter(58.16, "tetaIon", "deg")
        self.fiIon = TheoryParameter(63.43, "fiIon", "deg")
        self.sigmaTeta = TheoryParameter(8, "sigmaTeta", "deg")
        self.sigmaFi = TheoryParameter(14, "sigmaFi", "deg")
        self.Dcf0 = TheoryParameter(1, "Dcf0", "cm-1")
        self.sigmaDcf2 = TheoryParameter(2.5, "sigmaDcf2", "cm-1")
        self.hiVVc = TheoryParameter(3.5E-6, "hiVVc", "")
        self.hiVVab = TheoryParameter(4.2E-6, "hiVVab", "")

        self.H_Start = TheoryParameter(0, 'H<sub>start</sub>', "Oe", False)  # H start
        self.H_End = TheoryParameter(30000, 'H<sub>end</sub>', "Oe", False)  # H end

        self.parameters = [self.Concentration, self.Temperature, self.mIon, self.tetaIon, self.fiIon, self.sigmaTeta,
                           self.sigmaFi, self.Dcf0, self.sigmaDcf2, self.hiVVc, self.hiVVab,
                           self.H_Start, self.H_End]
        ################### ^ PARAMETERS ^ ###################

        ################### v PLOT VALUES v ###################
        H = None  # magnetic fields array, kOe
        self.M_H = [None for i in range(3)]
        ################### ^ PLOT VALUES ^ ###################

        for k in range(3):
            self.curves.append(TheoryCurve(H, self.M_H[k], DataTypes.M_H, "H axis " + str(k)))

        self.initParameters()

    def update(self):
        print("update Ho LGS M(H)")
        self.calcData_H()

    def calcData_H(self):
        H = np.array(
            [self.H_Start.value + i * (self.H_End.value - self.H_Start.value) / numPoints for i in range(numPoints)],
            dtype=np.float32)

        Mx, My, Mz = calcM_H(H,
                             self.Concentration.value, self.Temperature.value, self.mIon.value * muB,
                             self.tetaIon.value * PI / 180, self.fiIon.value * PI / 180, self.sigmaTeta.value * PI / 180,
                             self.sigmaFi.value * PI / 180, self.Dcf0.value, self.sigmaDcf2.value,
                             self.hiVVc.value, self.hiVVab.value,
                             )
        M_H = [Mx, My, Mz]
        for k in range(3):
            self.updateCurvePoints(H, M_H[k], DataTypes.M_H, "H axis " + str(k))


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
numPoints = 40
oneSidePointsNum = 20

# cc = 0.0445  # Ho concentration 0.0156
# T = 1.9
# # ma = 3.5 * muB  # 3.75
# # mb = 7.13 * muB  # 7.13
# # mc = 5.05 * muB  # 5.05
# # mIon = math.sqrt(ma ** 2 + mb ** 2 + mc ** 2)  # 9 .51 * self.muB
# mIon = 9.51 * muB  # 9 .51 * self.muB
# tetaIon = PI * 58 / 180  # math.acos(mc / mIon)  # PI * 58.16 / 180
# fiIon = PI * 60 / 180  # math.atan(mb / ma)  # PI * 63.43 / 180
# sigmaTeta = PI * 8 / 180  # 8
# sigmaFi = PI * 14 / 180  # 14
# Dcf0 = 0.5  # 1.005
# sigmaDcf2 = 2.5
#
# hiVVc = 3.5E-6
# hiVVab = 4.2E-6
############## PARAMS
pi23 = 2 * PI / 3
# dTeta = 3 * 2 * sigmaTeta / (2 * oneSidePointsNum + 1)
# dFi = 3 * 2 * sigmaFi / (2 * oneSidePointsNum + 1)
# dDcf2 = 7 / (2 * oneSidePointsNum + 1)  # normalX


# MvHoLang = (138.90 * (1 - cc) + 164.93 * cc) * 3 + 69.72 * 5 + 28.08 + 16 * 14
# nPos = 1 / 6 * (3 * cc * NA / MvHoLang) * dTeta * dFi * dDcf2


@jit(float32(float32, float32), nopython=True, nogil=True)
def normal(x, sigma):
    return math.exp(- 0.5 * (x / sigma) ** 2) / math.sqrt(2 * PI) / sigma


@jit(float32(float32, float32, float32, float32), nopython=True, nogil=True)
def normalX(x, sigma, mu, normFactor):
    return normFactor * math.exp(- 0.5 * ((x - mu) / sigma) ** 2) * x


@jit(float32(float32, float32), nopython=True, nogil=True)
def calcNormFactor(sigma, mu):
    p = math.sqrt(0.5 * PI) * mu / math.sqrt(1 / sigma ** 2) + \
        math.exp(-mu ** 2 / (2 * sigma ** 2)) * sigma ** 2 + \
        math.sqrt(0.5 * PI) * mu * sigma * math.erf(mu / (math.sqrt(2) * sigma))
    return 1 / p


@jit(float32(float32, float32, float32, float32, float32, float32, float32), nopython=True, nogil=True)
def getEPos(vectHx, vectHy, vectHz, vectMx, vectMy, vectMz, _Dcf):  # cm^-1
    return np.sqrt(_Dcf ** 2 + (1 / kcm * (vectHx * vectMx + vectHy * vectMy + vectHz * vectMz)) ** 2)


@jit(UniTuple(float32, 3)(uint8, float32, float32, float32, float32, float32), nopython=True, nogil=True)
def getVectM(pos, deltaTeta, deltaFi, tetaIon, fiIon, mIon):
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


@guvectorize(["void(float32[:], float32, float32, float32, float32, float32, float32, float32, float32, float32, float32, float32, float32[:], float32[:], float32[:])"],
             "(n),(),(),(),(),(),(),(),(),(),(),()->(n),(n),(n)",
             target='parallel')
# def calcM_H(H, Mx, My, Mz):
def calcM_H(H,
            cc, T, mIon, tetaIon, fiIon, sigmaTeta, sigmaFi, Dcf0, sigmaDcf2, hiVVc, hiVVab,
            Mx, My, Mz):
    Mx[:] = [0 for i in range(len(H))]
    My[:] = [0 for i in range(len(H))]
    Mz[:] = [0 for i in range(len(H))]

    maxPos = 2 * Dcf0
    mu = maxPos - sigmaDcf2 ** 2 / maxPos
    normFactor = calcNormFactor(sigmaDcf2, mu)
    dDcf2 = (Dcf0 + 3 * sigmaDcf2 * 0.5) / (2 * oneSidePointsNum + 1)  # normalX

    dTeta = 3 * sigmaTeta / (2 * oneSidePointsNum + 1)
    dFi = 3 * sigmaFi / (2 * oneSidePointsNum + 1)
    MvHoLang = (138.90 * (1 - cc) + 164.93 * cc) * 3 + 69.72 * 5 + 28.08 + 16 * 14
    nPos = 1 / 6 * (3 * cc * NA / MvHoLang) * dTeta * dFi * dDcf2

    for i in prange(len(H)):
        for iFi in prange(-oneSidePointsNum, oneSidePointsNum):
            for iTeta in prange(-oneSidePointsNum, oneSidePointsNum):
                for iDcf in prange(0, 2 * oneSidePointsNum + 1):
                    for pos in prange(6):
                        vectMx, vectMy, vectMz = getVectM(pos, float32(iTeta * dTeta), float32(iFi * dFi),
                                                          tetaIon, fiIon, mIon)
                        dFactor = normal(iTeta * dTeta, sigmaTeta) * normal(iFi * dFi, sigmaFi) * normalX(iDcf * dDcf2, sigmaDcf2, mu, normFactor)

                        EPos = getEPos(H[i], 0, 0, vectMx, vectMy, vectMz, float32(iDcf * dDcf2 * 0.5))
                        # EPos = getEPos(H[i], 0, 0, vectMx, vectMy, vectMz, Dcf0)
                        if EPos == 0: EPos = 0.0000001
                        Mx[i] += nPos * (vectMx ** 2 * H[i]) * math.tanh(EPos * kcm / kB / T) / (EPos * kcm) * dFactor

                        EPos = getEPos(0, H[i], 0, vectMx, vectMy, vectMz, float32(iDcf * dDcf2 * 0.5))
                        if EPos == 0: EPos = 0.0000001
                        My[i] += nPos * (vectMy ** 2 * H[i]) * math.tanh(EPos * kcm / kB / T) / (EPos * kcm) * dFactor

                        EPos = getEPos(0, 0, H[i], vectMx, vectMy, vectMz, float32(iDcf * dDcf2 * 0.5))
                        if EPos == 0: EPos = 0.0000001
                        Mz[i] += nPos * (vectMz ** 2 * H[i]) * math.tanh(EPos * kcm / kB / T) / (EPos * kcm) * dFactor
        Mx[i] += hiVVab * H[i]
        My[i] += hiVVab * H[i]
        Mz[i] += hiVVc * H[i]

#
# @guvectorize(["void(float32[:], float32, float32, float32, float32, float32, float32, float32, float32, float32, float32, float32, float32[:], float32[:], float32[:])"],
#              "(n),(),(),(),(),(),(),(),(),(),(),()->(n),(n),(n)",
#              target='parallel')
# # def calcM_H(H, Mx, My, Mz):
# def calcM_Angle(H,
#                 cc, T, mIon, tetaIon, fiIon, sigmaTeta, sigmaFi, Dcf0, sigmaDcf2, hiVVc, hiVVab,
#                 Mxy, Myz, Mxz):
#     Mxy[:] = [0 for i in range(len(H))]
#     Myz[:] = [0 for i in range(len(H))]
#     Mxz[:] = [0 for i in range(len(H))]
#
#     dTeta = 3 * 2 * sigmaTeta / (2 * oneSidePointsNum + 1)
#     dFi = 3 * 2 * sigmaFi / (2 * oneSidePointsNum + 1)
#     MvHoLang = (138.90 * (1 - cc) + 164.93 * cc) * 3 + 69.72 * 5 + 28.08 + 16 * 14
#     nPos = 1 / 6 * (3 * cc * NA / MvHoLang) * dTeta * dFi * dDcf2
#
#     maxPos = 2 * Dcf0
#     mu = maxPos - sigmaDcf2 ** 2 / maxPos
#     normFactor = calcNormFactor(sigmaDcf2, mu)
#
#     for i in prange(len(H)):
#         for iFi in prange(-oneSidePointsNum, oneSidePointsNum):
#             for iTeta in prange(-oneSidePointsNum, oneSidePointsNum):
#                 for iDcf in prange(0, 2 * oneSidePointsNum):
#                     for pos in prange(6):
#                         vectMx, vectMy, vectMz = getVectM(pos, float32(iTeta * dTeta), float32(iFi * dFi),
#                                                           tetaIon, fiIon, mIon)
#                         dFactor = normal(iTeta * dTeta, sigmaTeta) * normal(iFi * dFi, sigmaFi) * normalX(iDcf * dDcf2,
#                                                                                                           sigmaDcf2, mu,
#                                                                                                           normFactor)
#
#                         EPos = getEPos(H[i], 0, 0, vectMx, vectMy, vectMz, float32(iDcf * dDcf2 * 0.5))
#                         # EPos = getEPos(H[i], 0, 0, vectMx, vectMy, vectMz, Dcf0)
#                         if EPos == 0: EPos = 0.0000001
#                         Mxy[i] += nPos * (vectMx ** 2 * H[i]) * math.tanh(EPos * kcm / kB / T) / (EPos * kcm) * dFactor
#
#                         EPos = getEPos(0, H[i], 0, vectMx, vectMy, vectMz, float32(iDcf * dDcf2 * 0.5))
#                         if EPos == 0: EPos = 0.0000001
#                         Myz[i] += nPos * (vectMy ** 2 * H[i]) * math.tanh(EPos * kcm / kB / T) / (EPos * kcm) * dFactor
#
#                         EPos = getEPos(0, 0, H[i], vectMx, vectMy, vectMz, float32(iDcf * dDcf2 * 0.5))
#                         if EPos == 0: EPos = 0.0000001
#                         Mxz[i] += nPos * (vectMz ** 2 * H[i]) * math.tanh(EPos * kcm / kB / T) / (EPos * kcm) * dFactor
#         Mxy[i] += hiVVab * H[i]
#         Myz[i] += hiVVab * H[i]
#         Mxz[i] += hiVVc * H[i]
