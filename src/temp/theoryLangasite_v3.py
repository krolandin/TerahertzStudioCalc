import math
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QListWidgetItem
from theoryModels import Theory, TheoryParameter, TheoryCurve, Model
from dataTypes import DataTypes, FileTypes
import numpy as np


class TheoryLangasite_v3(Theory):
    name = "Theory Ho langasite v3"

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
    cc = 0.015  # Ho concentration
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
        self.hAxisIndex = None
        self.vectH = None
        self.T = None
        self.Dcf = None
        self.dDcf = None
        self.sigmaDcf = None
        self.nPos4PI = None
        self.listItem = QListWidgetItem(self.name)
        self.numPoints = 200

        ################### v PARAMETERS v ###################
        self.d = TheoryParameter(1.756 * 0.1, 'd', "cm")  # thickness
        self.epsInf1 = TheoryParameter(14, '\u03B5\'<sub>\u221E</sub>', "")  # epsilon1 inf
        self.epsInf2 = TheoryParameter(0.05, '\u03B5\"<sub>\u221E</sub>', "")  # epsilon2 inf
        self.muInf1 = TheoryParameter(1, '\u03BC\'<sub>\u221E</sub>', "")  # mu1 inf
        self.fFix = TheoryParameter(100, 'f<sub>fix</sub>', "GHz")  # f fixed

        self.Temperature = TheoryParameter(1.8, "Temperature", "K")
        self.deltaCF = TheoryParameter(1.005, '\u0394<sub>CF</sub>', "cm<sup>-1</sup>")  # delta CF splitting, cm-1
        self.gamma = TheoryParameter(1.0, '\u03B3', "cm<sup>-1</sup>")  # gamma
        self.axis_h = TheoryParameter(1.0, 'h<sup>ac</sup><sub>i</sub>', "i = 1(x), 2(y), 3(z)")  # gamma
        self.axis_Hext = TheoryParameter(1.0, 'H<sup>ext</sup><sub>i</sub>', "i = 1(x), 2(y), 3(z)")  # gamma

        self.H_Start = TheoryParameter(1, 'H<sub>start</sub>', "Oe", False)  # H start
        self.H_End = TheoryParameter(30000, 'H<sub>end</sub>', "Oe", False)  # H end

        self.parameters = [self.d, self.epsInf1, self.epsInf2, self.muInf1, self.fFix,
                           self.Temperature, self.deltaCF, self.gamma, self.axis_h, self.axis_Hext,
                           self.H_Start, self.H_End]
        ################### ^ PARAMETERS ^ ###################

        ################### v PLOT VALUES v ###################
        self.H = None  # magnetic fields array, kOe
        self.tr_H = None  # transmittance
        self.ph_H = None  # mirror (optical length), mm
        # self.f_H_6m = None ##############################################################
        ################### ^ PLOT VALUES ^ ###################

        self.modelTypes = [Model.OSCILLATOR]

        ################### v DISTRIBUTION v ###################
        self.oneSidePointsNum = 20

        # self.modes = []
        # self.modesD = []
        # self.modesDmu_x = []
        # self.modesDmu_y = []
        # self.modesDmu_z = []

        # self.modes = []  # 6x position modes 1p, 1m, 2p, 2m, 3p, 3m
        # for i in range(6):
        #     self.modes.append([])
        #     for iFi in range(self.oneSidePointsNum*2 + 1):
        #         self.modes[i].append([])
        #         for iTeta in range(self.oneSidePointsNum*2 + 1):
        #             self.modes[i][iFi].append(PositionMode)
        ################### ^ DISTRIBUTION ^ ###################

        self.curves.append(TheoryCurve(self.H, self.tr_H, DataTypes.SignalH))
        self.curves.append(TheoryCurve(self.H, self.ph_H, DataTypes.MirrorH))

        self.initParameters()

    def update(self):
        print("update TheoryLangasite_v2")
        self.calcConstants()
        self.calc_H()

    def calc_H(self):
        self.H = [self.H_Start.value + i * (self.H_End.value - self.H_Start.value) / self.numPoints for i in
                  range(self.numPoints)]  # magnetic fields array, Oe
        eps_H0 = 0
        f = self.fFix.value / 30
        for model in self.models:
            if model.name == Model.OSCILLATOR:
                f0 = model.f0.value
                eps_H0 += model.deltaEps.value * f0 ** 2 / (
                        f0 ** 2 - f ** 2 - complex(0, model.gamma.value * f))

        eps = []
        mu = []
        gamma = self.gamma.value

        for j in range(self.numPoints):
            eps_j = complex(self.epsInf1.value, self.epsInf2.value) + eps_H0
            mu_j = complex(self.muInf1.value, 0)

            self.calcH(self.H[j])

            for i in range(6):
                vectM = self.getVectM(i)
                # for iDcf in range(-self.oneSidePointsNum, self.oneSidePointsNum):
                for iDcf in range(0, self.oneSidePointsNum):
                    Dcf = iDcf * self.dDcf
                    DPos = self.getDPos(vectM, Dcf)
                    # if self.H[j] < 5000: print(Dcf/self.Dcf, self.H[j])
                    f0 = DPos
                    dMu = self.getDMu(DPos, vectM, Dcf) * self.maxwell(Dcf/self.Dcf)
                    # dMu = self.getDMu(DPos, vectM, Dcf) * self.normal(Dcf, self.sigmaDcf, self.Dcf)
                    # gamma = 0.1
                    mu_j += dMu * f0 ** 2 / (f0 ** 2 - f ** 2 - complex(0, gamma * f))

            eps.append(eps_j)
            mu.append(mu_j)

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

        # self.curves[DataTypes.Test] = TheoryCurve(self.H, self.f_H_6m)  ####################################################

    def calcTrPh(self, mu, eps, f):
        nk = (mu * eps) ** 0.5
        n = nk.real
        k = nk.imag
        ab = (mu / eps) ** 0.5
        a = ab.real
        b = ab.imag
        A = 2 * self.PI * n * self.d.value * f  # w_Hz = w_cm-1 * LIGHT_SPEED
        E = np.exp(-4 * self.PI * k * self.d.value * f)  # w_Hz = w_cm-1 * LIGHT_SPEED
        R = ((a - 1) ** 2 + b ** 2) / ((a + 1) ** 2 + b ** 2)
        fiR = np.arctan((2 * b) / (a ** 2 + b ** 2 - 1))
        T = E * ((1 - R) ** 2 + 4 * R * (np.sin(fiR)) ** 2) / (
                (1 - R * E) ** 2 + 4 * R * E * (np.sin(A + fiR)) ** 2)
        fiT = A - np.arctan(b * (a ** 2 + b ** 2 - 1) / ((a ** 2 + b ** 2) * (2 + a) + a)) + np.arctan(
            (R * E * np.sin(2 * A + 2 * fiR)) / (1 - R * E * np.cos(2 * A + 2 * fiR)))
        return T, fiT

    def calcConstants(self):
        self.oneSidePointsNum = 100
        self.Dcf = self.deltaCF.value
        self.T = self.Temperature.value
        ma = 1.0 * 3.5 * self.muB
        mb = 6.8 * self.muB
        mc = 5.4 * 0.94 * self.muB
        self.mIon = np.sqrt(ma**2+mb**2+mc**2)  # 9 .51 * self.muB
        self.tetaIon = np.arccos(mc/self.mIon)  # self.PI * 58.16 / 180
        self.fiIon = np.arctan(mb/ma)  # self.PI * 63.43 / 180
        # self.sigmaDcf = 2.05
        # self.dDcf = 3 * 2 * self.sigmaDcf / (self.oneSidePointsNum * 2 + 1)
        self.dDcf = 3 * self.Dcf / self.oneSidePointsNum
        self.nPos4PI = 4 * self.PI * self.ro / 6 * (3 * self.cc * self.NA / self.MvHoLang) * self.dDcf

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

    def normal(self, x, sigma, mu):
        return np.exp(- 0.5 * ((x-mu)/sigma) ** 2) / np.sqrt(2 * self.PI) / sigma

    def maxwell(self, x):
        return 4 / np.sqrt(self.PI) * x ** 2 * np.exp(- x ** 2)

    def getDPos(self, vectM, Dcf):  # cm^-1
        return 2 * np.sqrt(Dcf ** 2 + (1 / self.kcm * np.dot(self.vectH, vectM)) ** 2)

    def getVectM(self, i):
        teta = self.tetaIon
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
        fi = self.fiIon + fiPos
        vectM = self.mIon * np.array([np.cos(fi) * np.sin(teta), np.sin(fi) * np.sin(teta), np.cos(teta)])
        return vectM

    def getDMu(self, DPos, vectM, Dcf):
        m = vectM[self.hAxisIndex]
        dMuPos = self.nPos4PI * m ** 2 / DPos / self.kcm * np.tanh(DPos * self.kcm / 2 / self.kB / self.T) * (2 * Dcf / DPos) ** 2
        return dMuPos


