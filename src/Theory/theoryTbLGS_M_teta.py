import math
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QListWidgetItem
from PyQt5.QtGui import QColor
from theoryModels import Theory, TheoryParameter, TheoryCurve, Model
from dataTypes import DataTypes, FileTypes
import numpy as np

from numba import vectorize, guvectorize, cuda, jit, float32, float64, int8, uint8, int16, prange, njit, complex64
from numba.types import UniTuple


class TheoryTbLGS_M_teta(Theory):
    name = "Tb LGS M(teta)"

    def __init__(self):
        Theory.__init__(self)

        self.color = QColor(0x0000FF)

        ################### v PARAMETERS v ###################
        self.Temperature = TheoryParameter(1.9, "Temperature", "K")

        self.Concentration1 = TheoryParameter(0.0445, "Concentration 1", "")
        self.mIon1 = TheoryParameter(9.51, "mIon 1", "muB")
        self.tetaIon1 = TheoryParameter(58.16, "tetaIon 1", "deg")
        self.fiIon1 = TheoryParameter(63.43, "fiIon 1", "deg")
        self.sigmaTeta1 = TheoryParameter(8, "sigmaTeta 1", "deg")
        self.sigmaFi1 = TheoryParameter(14, "sigmaFi 1", "deg")
        self.Dcf01 = TheoryParameter(1, "Dcf0 1", "cm-1")

        self.Concentration2 = TheoryParameter(0.0445, "Concentration 2", "")
        self.mIon2 = TheoryParameter(9.51, "mIon 2", "muB")
        self.tetaIon2 = TheoryParameter(58.16, "tetaIon 2", "deg")
        self.fiIon2 = TheoryParameter(63.43, "fiIon 2", "deg")
        self.sigmaTeta2 = TheoryParameter(8, "sigmaTeta 2", "deg")
        self.sigmaFi2 = TheoryParameter(14, "sigmaFi 2", "deg")
        self.Dcf02 = TheoryParameter(1, "Dcf0 2", "cm-1")

        # self.sigmaDcf2 = TheoryParameter(2.5, "sigmaDcf2", "cm-1")
        self.hiVVc = TheoryParameter(3.5E-6, "hiVVc", "")
        self.hiVVab = TheoryParameter(4.2E-6, "hiVVab", "")

        self.H_Rot = TheoryParameter(20000, 'H<sub>rot</sub>', "Oe", False)  # H end

        self.shiftYZ = TheoryParameter(0, "shiftYZ", "deg")
        self.shiftXZ = TheoryParameter(0, "shiftXZ", "deg")
        self.shiftXY = TheoryParameter(0, "shiftXY", "deg")

        self.parameters = [self.Temperature,
                           self.Concentration1, self.mIon1, self.tetaIon1, self.fiIon1, self.sigmaTeta1, self.sigmaFi1, self.Dcf01,
                           self.Concentration2, self.mIon2, self.tetaIon2, self.fiIon2, self.sigmaTeta2, self.sigmaFi2, self.Dcf02,
                           self.hiVVc, self.hiVVab,
                           self.H_Rot,
                           self.shiftXY, self.shiftYZ, self.shiftXZ]
        ################### ^ PARAMETERS ^ ###################

        ################### v PLOT VALUES v ###################
        teta = None  # magnetic fields array, kOe
        self.M_teta = [None for i in range(3)]
        ################### ^ PLOT VALUES ^ ###################

        for k in range(3):
            self.curves.append(TheoryCurve(teta, self.M_teta[k], DataTypes.M_teta, "H rot " + str(k)))
        self.curves[0].color = QColor(0xFF0000)
        self.curves[1].color = QColor(0x00FF00)
        self.curves[2].color = QColor(0x0000FF)

        self.initParameters()

    def update(self):
        print("update Ho LGS M(H)")
        self.calcData_H()

    def calcData_H(self):
        teta = np.array([i * (180) / 180 for i in range(180)], dtype=np.float32)
        Mxy, Myz, Mxz = calcM_Angle(teta,
                                    self.Temperature.value,

                                    self.Concentration1.value, self.mIon1.value * muB,
                                    self.tetaIon1.value * PI / 180, self.fiIon1.value * PI / 180,
                                    self.sigmaTeta1.value * PI / 180, self.sigmaFi1.value * PI / 180, self.Dcf01.value,

                                    self.Concentration2.value, self.mIon2.value * muB,
                                    self.tetaIon2.value * PI / 180, self.fiIon2.value * PI / 180,
                                    self.sigmaTeta2.value * PI / 180, self.sigmaFi2.value * PI / 180, self.Dcf02.value,

                                    self.hiVVc.value, self.hiVVab.value,
                                    self.shiftXY.value, self.shiftYZ.value, self.shiftXZ.value,
                                    self.H_Rot.value
                                    )
        M_teta = [Myz, Mxz, Mxy]
        for k in range(3):
            self.updateCurvePoints(np.append(teta, 180 + teta), np.append(M_teta[k], M_teta[k]), DataTypes.M_teta,
                                   "H rot " + str(k))


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
numPoints = 30
oneSidePointsNum = 10

# Hrot = 20000

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


@guvectorize([
    "void(float32[:], "
    "float32, "
    "float32, float32, float32, float32, float32, float32, float32, "
    "float32, float32, float32, float32, float32, float32, float32, "
    "float32, float32, "
    "float32, float32, float32, "
    "float32, "
    "float32[:], float32[:], float32[:])"],

    "(n),"
    "(),"
    "(),(),(),(),(),(),(),"
    "(),(),(),(),(),(),(),"
    "(),(),"
    "(),(),(),"
    "()->(n),(n),(n)",
    target='parallel')
# def calcM_H(H, Mx, My, Mz):
def calcM_Angle(alpha,
                T,
                cc1, mIon1, tetaIon1, fiIon1, sigmaTeta1, sigmaFi1, Dcf01,
                cc2, mIon2, tetaIon2, fiIon2, sigmaTeta2, sigmaFi2, Dcf02,
                hiVVc, hiVVab,
                shiftXY, shiftYZ, shiftXZ,
                Hrot,
                Mxy, Myz, Mxz):
    Mxy[:] = [0 for i in range(len(alpha))]
    Myz[:] = [0 for i in range(len(alpha))]
    Mxz[:] = [0 for i in range(len(alpha))]

    MvHoLang = (138.90 * (1 - cc1 - cc2) + 164.93 * (cc1 + cc2)) * 3 + 69.72 * 5 + 28.08 + 16 * 14

    dTeta1 = 3 * 2 * sigmaTeta1 / (2 * oneSidePointsNum + 1)
    dFi1 = 3 * 2 * sigmaFi1 / (2 * oneSidePointsNum + 1)
    nPos1 = 1 / 6 * (3 * cc1 * NA / MvHoLang) * dTeta1 * dFi1

    dTeta2 = 3 * 2 * sigmaTeta2 / (2 * oneSidePointsNum + 1)
    dFi2 = 3 * 2 * sigmaFi2 / (2 * oneSidePointsNum + 1)
    nPos2 = 1 / 6 * (3 * cc2 * NA / MvHoLang) * dTeta2 * dFi2

    # maxPos = 2 * Dcf0
    # mu = maxPos - sigmaDcf2 ** 2 / maxPos
    # normFactor = calcNormFactor(sigmaDcf2, mu)

    for i in prange(len(alpha)):
        for iFi in prange(-oneSidePointsNum, oneSidePointsNum):
            for iTeta in prange(-oneSidePointsNum, oneSidePointsNum):
                for pos in prange(6):
                    # if pos != 0 and pos != 1: continue
                    vectMx, vectMy, vectMz = getVectM(pos, float32(iTeta * dTeta1), float32(iFi * dFi1),
                                                      tetaIon1, fiIon1, mIon1)
                    dFactor = normal(iTeta * dTeta1, sigmaTeta1) * normal(iFi * dFi1, sigmaFi1)
                    angle = PI * i / 180

                    teta = angle + shiftXY * PI / 180
                    EPos = getEPos(Hrot * math.sin(teta), Hrot * math.cos(teta), 0, vectMx, vectMy, vectMz, Dcf01)
                    vectMH = vectMx * Hrot * math.sin(teta) + vectMy * Hrot * math.cos(teta)
                    Mxy[i] += nPos1 * (vectMH ** 2 / Hrot) * math.tanh(EPos * kcm / kB / T) / (EPos * kcm) * dFactor

                    teta = angle + shiftYZ * PI / 180
                    EPos = getEPos(0, Hrot * math.sin(teta), Hrot * math.cos(teta), vectMx, vectMy, vectMz, Dcf01)
                    vectMH = vectMy * Hrot * math.sin(teta) + vectMz * Hrot * math.cos(teta)
                    Myz[i] += nPos1 * (vectMH ** 2 / Hrot) * math.tanh(EPos * kcm / kB / T) / (EPos * kcm) * dFactor

                    teta = angle + shiftXZ * PI / 180
                    EPos = getEPos(Hrot * math.sin(teta), 0, Hrot * math.cos(teta), vectMx, vectMy, vectMz, Dcf01)
                    vectMH = vectMx * Hrot * math.sin(teta) + vectMz * Hrot * math.cos(teta)
                    Mxz[i] += nPos1 * (vectMH ** 2 / Hrot) * math.tanh(EPos * kcm / kB / T) / (EPos * kcm) * dFactor

                for pos in prange(6):
                    # if pos != 0 and pos != 1: continue
                    vectMx, vectMy, vectMz = getVectM(pos, float32(iTeta * dTeta2), float32(iFi * dFi2),
                                                      tetaIon2, fiIon2, mIon2)
                    dFactor = normal(iTeta * dTeta2, sigmaTeta2) * normal(iFi * dFi2, sigmaFi2)
                    angle = PI * i / 180

                    teta = angle + shiftXY * PI / 180
                    EPos = getEPos(Hrot * math.sin(teta), Hrot * math.cos(teta), 0, vectMx, vectMy, vectMz, Dcf02)
                    vectMH = vectMx * Hrot * math.sin(teta) + vectMy * Hrot * math.cos(teta)
                    Mxy[i] += nPos2 * (vectMH ** 2 / Hrot) * math.tanh(EPos * kcm / kB / T) / (EPos * kcm) * dFactor

                    teta = angle + shiftYZ * PI / 180
                    EPos = getEPos(0, Hrot * math.sin(teta), Hrot * math.cos(teta), vectMx, vectMy, vectMz, Dcf02)
                    vectMH = vectMy * Hrot * math.sin(teta) + vectMz * Hrot * math.cos(teta)
                    Myz[i] += nPos2 * (vectMH ** 2 / Hrot) * math.tanh(EPos * kcm / kB / T) / (EPos * kcm) * dFactor

                    teta = angle + shiftXZ * PI / 180
                    EPos = getEPos(Hrot * math.sin(teta), 0, Hrot * math.cos(teta), vectMx, vectMy, vectMz, Dcf02)
                    vectMH = vectMx * Hrot * math.sin(teta) + vectMz * Hrot * math.cos(teta)
                    Mxz[i] += nPos2 * (vectMH ** 2 / Hrot) * math.tanh(EPos * kcm / kB / T) / (EPos * kcm) * dFactor

        Mxy[i] += hiVVab * Hrot * math.cos(teta) ** 2 + hiVVab * Hrot * math.sin(teta) ** 2
        Myz[i] += hiVVc * Hrot * math.cos(teta) ** 2 + hiVVab * Hrot * math.sin(teta) ** 2
        Mxz[i] += hiVVc * Hrot * math.cos(teta) ** 2 + hiVVab * Hrot * math.sin(teta) ** 2
