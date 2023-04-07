import math
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QListWidgetItem
from PyQt5.QtGui import QColor
from theoryModels import Theory, TheoryParameter, TheoryCurve, Model
from dataTypes import DataTypes, FileTypes
import numpy as np
import time
from numba import vectorize, cuda, jit, float32, float64, int8, int16, prange


class TheoryLangasite_Dmu_f_H(Theory):
    name = "Ho LGS Dmu(f,H)"

    LIGHT_SPEED = 2.998e10  # cm/s
    PI = math.pi
    h = 6.6260755E-27 / (2 * PI)
    kB = 1.380658E-16
    NA = 6.022E23
    kcm = 2 * PI * h * 3.0E10  # cm^-1 to erg
    kGHz = 30
    muB = 0.927401549E-20
    ro = 5.2

    # Magnetization, frequencies and magnetic contributions for a distorted crystal: six sites
    cc = 0.0156  # Ho concentration
    MvHoLang = (138.90 * (1 - cc) + 164.93 * cc) * 3 + 69.72 * 5 + 28.08 + 16 * 14
    # ma = 1.0 * 3.5 * muB
    # mb = 6.8 * muB
    # mc = 5.4 * 0.94 * muB
    mIon = 9.3 * muB
    tetaIon = PI * 54.9 / 180
    fiIon = PI * 62.7 / 180
    pi23 = 2 * PI / 3

    def __init__(self):
        Theory.__init__(self)
        self.sigmaDcf = None
        self.dDcf = None
        self.dFi = None
        self.dTeta = None
        self.sigmaFi = None
        self.sigmaTeta = None
        self.hAxisIndex = None
        self.vectH = None
        self.T = None
        self.Dcf = None
        self.nPos4PI = None
        self.listItem = QListWidgetItem(self.name)
        self.numPoints = 5

        self.color = QColor(0x0000FF)

        ################### v PARAMETERS v ###################

        self.Temperature = TheoryParameter(1.8, "Temperature", "K")
        self.deltaCF = TheoryParameter(1.005, '\u0394<sub>CF</sub>', "cm<sup>-1</sup>")  # delta CF splitting, cm-1
        # self.gamma = TheoryParameter(1.0, '\u03B3', "cm<sup>-1</sup>")  # gamma
        self.axis_h = TheoryParameter(1.0, 'h<sup>ac</sup><sub>i</sub>', "i = 1(x), 2(y), 3(z)")  # gamma
        self.axis_Hext = TheoryParameter(1.0, 'H<sup>ext</sup><sub>i</sub>', "i = 1(x), 2(y), 3(z)")  # gamma

        self.H_Start = TheoryParameter(0, 'H<sub>start</sub>', "Oe", False)  # H start
        self.H_End = TheoryParameter(30000, 'H<sub>end</sub>', "Oe", False)  # H end
        self.f_Start = TheoryParameter(0, '\u03BD<sub>start</sub>', "cm<sup>-1</sup>", False)  # nu start
        self.f_End = TheoryParameter(10, '\u03BD<sub>end</sub>', "cm<sup>-1</sup>", False)  # nu end

        self.parameters = [self.Temperature, self.deltaCF, self.axis_h, self.axis_Hext,
                           self.H_Start, self.H_End, self.f_Start, self.f_End, self.f_Start, self.f_End]
        ################### ^ PARAMETERS ^ ###################

        ################### v PLOT VALUES v ###################
        self.H = None  # magnetic fields array, kOe
        self.f = None
        self.DmuTot = None
        ################### ^ PLOT VALUES ^ ###################

        self.curves.append(TheoryCurve(self.H, self.f, DataTypes.dMu_H, "f"))
        self.curves.append(TheoryCurve(self.H, self.DmuTot, DataTypes.dMu_H, "Dmu"))

        self.initParameters()

    def update(self):
        print("update TheoryLangasite_v2")
        start = time.time()

        self.calcConstants()
        self.H = np.array([self.H_Start.value + i * (self.H_End.value - self.H_Start.value) / self.numPoints for j in
                           range(self.numPoints) for i in range(self.numPoints)], dtype=np.float32)
        self.f = np.array([self.f_Start.value + i * (self.f_End.value - self.f_Start.value) / self.numPoints for i in
                           range(self.numPoints) for j in range(self.numPoints)], dtype=np.float32)
        print(self.H)
        print(self.f)

        self.updateCurvePoints(self.H, self.f, DataTypes.dMu_H, "f")
        self.updateCurvePoints(self.H, self.calcData_H(), DataTypes.dMu_H, "Dmu")

        function_time = time.time() - start
        print("Calc in %s seconds" % function_time)

    def calcData_H(self):
        # muIm = []
        muIm = np.zeros_like(self.H, dtype=self.H.dtype)
        gamma = 0.5

        for i in range(self.numPoints):
            self.calcH(self.H[i])
            for j in range(self.numPoints):
                f = self.f[self.numPoints * j]
                muIm_j = 0
                for iFi in range(-self.oneSidePointsNum, self.oneSidePointsNum):
                    for iTeta in range(-self.oneSidePointsNum, self.oneSidePointsNum):
                        for iDcf in range(-self.oneSidePointsNum, self.oneSidePointsNum):
                            # for pos in range(6):
                            pos = 0
                            vectM = self.getVectM(pos, iTeta * self.dTeta, iFi * self.dFi)
                            # DPos = self.getDPos(vectM, self.Dcf)
                            DPos = self.getDPos(vectM, self.Dcf + iDcf * self.dDcf)
                            f0 = DPos
                            dMu = self.getDMu(DPos, vectM, self.Dcf + iDcf * self.dDcf) * \
                                  self.normal(iTeta * self.dTeta, self.sigmaTeta) * \
                                  self.normal(iFi * self.dFi, self.sigmaFi) * \
                                  self.normal(iDcf * self.dDcf, self.sigmaDcf)

                            muIm_j += (dMu * f0 ** 2 / (f0 ** 2 - f ** 2 - complex(0, gamma * f))).imag

                # muIm.append(muIm_j)
                muIm[self.numPoints * j + i] = muIm_j
                print("-", self.H[i], f, muIm_j)
                print("=", self.H[i+j], self.f[i+j], muIm[i+j])
        return muIm
        # self.updateCurvePoints(self.H, self.f, DataTypes.dMu_H, "f")
        # self.updateCurvePoints(self.H, muIm, DataTypes.dMu_H, "Dmu")

    def calcConstants(self):
        self.oneSidePointsNum = 5
        self.Dcf = self.deltaCF.value
        self.T = self.Temperature.value
        ma = 3.75 * self.muB  # 3.75
        mb = 7.13 * self.muB  # 7.13
        mc = 5.05 * self.muB  # 5.05
        self.mIon = np.sqrt(ma ** 2 + mb ** 2 + mc ** 2)  # 9 .51 * self.muB
        self.tetaIon = np.arccos(mc / self.mIon)  # self.PI * 58.16 / 180
        self.fiIon = np.arctan(mb / ma)  # self.PI * 63.43 / 180
        print(
            "mIon = " + str(self.mIon / self.muB) + "; tetaIon " + str(self.tetaIon / self.PI * 180) + "; fiIon " + str(
                self.fiIon / self.PI * 180))
        self.sigmaTeta = self.PI * 8 / 180
        self.sigmaFi = self.PI * 14 / 180
        self.dTeta = 3 * 2 * self.sigmaTeta / (2 * self.oneSidePointsNum + 1)
        self.dFi = 3 * 2 * self.sigmaFi / (2 * self.oneSidePointsNum + 1)
        self.sigmaDcf = self.Dcf * 0.5
        self.dDcf = 3 * 2 * self.sigmaDcf / (2 * self.oneSidePointsNum + 1)
        self.nPos4PI = 4 * self.PI * self.ro / 6 * (
                3 * self.cc * self.NA / self.MvHoLang) * self.dTeta * self.dFi * self.dDcf

    def calcH(self, H):
        # External magnetic field dependence along a-, b and c-axes
        if self.axis_Hext.value == 1:  # H||a
            self.vectH = np.array([H, 0, 0])
        elif self.axis_Hext.value == 2:  # H||b
            self.vectH = np.array([0, H, 0])
        elif self.axis_Hext.value == 3:  # H||c
            self.vectH = np.array([0, 0, H])
        else:  # H||a
            # self.axis_Hext.numberEdit.resetValue(1)
            self.vectH = np.array([H, 0, 0])

        # AC magnetic field dependence along a-, b and c-axes
        if self.axis_h.value == 1:  # h||a
            self.hAxisIndex = 0
        elif self.axis_h.value == 2:  # h||b
            self.hAxisIndex = 1
        elif self.axis_h.value == 3:  # h||c
            self.hAxisIndex = 2
        else:  # h||a
            self.axis_h.numberEdit.resetValue(1)
            self.hAxisIndex = 0

    def normal(self, x, sigma):
        return math.exp(- 0.5 * (x / sigma) ** 2) / math.sqrt(2 * self.PI) / sigma

    def getDPos(self, vectM, Dcf):  # cm^-1
        return 2 * math.sqrt(Dcf ** 2 + (1 / self.kcm * np.dot(self.vectH, vectM)) ** 2)

    def getVectM(self, i, deltaTeta, deltaFi):
        teta = self.tetaIon + deltaTeta
        if i == 0:  # 1p
            fiPos = 0
        elif i == 1:  # 1m
            fiPos = self.PI - 2 * self.fiIon
        if i == 2:  # 2p
            fiPos = self.pi23
        elif i == 3:  # 2m
            fiPos = self.PI - 2 * self.fiIon + self.pi23
        if i == 4:  # 3p
            fiPos = - self.pi23
        elif i == 5:  # 3m
            fiPos = self.PI - 2 * self.fiIon - self.pi23
        fi = self.fiIon + fiPos + deltaFi
        vectM = self.mIon * np.array([math.cos(fi) * math.sin(teta), math.sin(fi) * math.sin(teta), math.cos(teta)])
        return vectM

    def getDMu(self, DPos, vectM, Dcf):
        m = vectM[self.hAxisIndex]
        dMuPos = self.nPos4PI * m ** 2 / DPos / self.kcm * math.tanh(DPos * self.kcm / 2 / self.kB / self.T) * (
                2 * Dcf / DPos) ** 2
        return dMuPos


LIGHT_SPEED = 2.998e10  # cm/s
PI = math.pi
h = 6.6260755E-27 / (2 * PI)
kB = 1.380658E-16
NA = 6.022E23
kcm = 2 * PI * h * 3.0E10  # cm^-1 to erg
kGHz = 30
muB = 0.927401549E-20
ro = 5.2
cc = 0.0156  # Ho concentration
MvHoLang = (138.90 * (1 - cc) + 164.93 * cc) * 3 + 69.72 * 5 + 28.08 + 16 * 14
mIon = 9.3 * muB
tetaIon = PI * 54.9 / 180
fiIon = PI * 62.7 / 180
pi23 = 2 * PI / 3

oneSidePointsNum = 25
Dcf = 1.005
T = 1.8
ma = 3.75 * muB  # 3.75
mb = 7.13 * muB  # 7.13
mc = 5.05 * muB  # 5.05
mIon = math.sqrt(ma ** 2 + mb ** 2 + mc ** 2)  # 9 .51 * self.muB
tetaIon = math.acos(mc / mIon)  # self.PI * 58.16 / 180
fiIon = math.atan(mb / ma)  # self.PI * 63.43 / 180
sigmaTeta = PI * 8 / 180
sigmaFi = PI * 14 / 180
dTeta = 3 * 2 * sigmaTeta / (2 * oneSidePointsNum + 1)
dFi = 3 * 2 * sigmaFi / (2 * oneSidePointsNum + 1)
sigmaDcf = Dcf * 0.5
dDcf = 3 * 2 * sigmaDcf / (2 * oneSidePointsNum + 1)
nPos4PI = 4 * PI * ro / 6 * (3 * cc * NA / MvHoLang) * dTeta * dFi * dDcf

axis_Hext = 1
axis_h = 1
gamma = 0.5
numPoints = 30


@jit(float32(float32, float32), nopython=True, nogil=True)
def normal(x, sigma):
    return math.exp(- 0.5 * (x / sigma) ** 2) / math.sqrt(2 * PI) / sigma


# @jit(forceobj=True)
@jit(float32(float32, float32, float32), nopython=True, nogil=True)
def getDPos(vectH, vectM, _Dcf):  # cm^-1
    # return 2 * np.sqrt(_Dcf ** 2 + (1 / kcm * np.dot(vectH, vectM)) ** 2)
    return 2 * np.sqrt(_Dcf ** 2 + (1 / kcm * vectH * vectM) ** 2)


@jit(float32(float32, float32, float32), nopython=True, nogil=True, parallel=False)
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
    # vectM = [mIon * math.cos(fi) * math.sin(teta), mIon * math.sin(fi) * math.sin(teta), mIon * math.cos(teta)]
    vectM = mIon * math.cos(fi) * math.sin(teta)
    return vectM


@jit(float32(float32, float32, float32), nopython=True, nogil=True)
def getDMu(DPos, m, _Dcf):
    # m = vectM[hAxisIndex]
    dMuPos = nPos4PI * m ** 2 / DPos / kcm * math.tanh(DPos * kcm / 2 / kB / T) * (2 * Dcf / DPos) ** 2
    return dMuPos


# @vectorize(['float32(float32, float32)'], target='cpu')
@vectorize(['float32(float32, float32)'], target='parallel')
def calcData_H(H_i, f_i):
    # vectH = np.array([H_i, 0, 0], dtype=np.float32)
    # vectH = np.array([H_i, 0, 0])
    # hAxisIndex = 0;
    muIm_i = 0
    for iFi in range(-oneSidePointsNum, oneSidePointsNum):
        for iTeta in range(-oneSidePointsNum, oneSidePointsNum):
            for iDcf in range(-oneSidePointsNum, oneSidePointsNum):
                # for pos in range(6):
                pos = int16(0)
                vectM = getVectM(pos, float32(iTeta * dTeta), float32(iFi * dFi))


                DPos = getDPos(H_i, vectM, Dcf + iDcf * dDcf)
                if DPos == 0:
                    continue
                f0 = DPos
                dMu = getDMu(DPos, vectM, Dcf + iDcf * dDcf) * \
                      normal(iTeta * dTeta, sigmaTeta) * \
                      normal(iFi * dFi, sigmaFi) * \
                      normal(iDcf * dDcf, sigmaDcf)

                r = f0 ** 2 - f_i ** 2 - 1j * gamma * f_i
                if r != 0:
                    muIm_i += (dMu * f0 ** 2 / r).imag
                # muIm_i += calcPosMu2(H_i, f_i, iTeta, iFi, iDcf)
    return muIm_i
