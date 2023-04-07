import math
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QListWidgetItem
from theoryModels import Theory, TheoryParameter, TheoryCurve, Model
from dataTypes import DataTypes, FileTypes


class TheoryLangasite(Theory):
    LIGHT_SPEED = 2.998e10  # cm/s
    PI = math.pi
    name = "Theory Ho langasite"

    def __init__(self):
        Theory.__init__(self)
        self.listItem = QListWidgetItem(self.name)
        self.numPoints = 500

        ################### v PARAMETERS v ###################
        self.d = TheoryParameter(1.756 * 0.1, 'd', "cm")  # thickness
        self.epsInf1 = TheoryParameter(14, '\u03B5\'<sub>\u221E</sub>', "")  # epsilon1 inf
        self.epsInf2 = TheoryParameter(0.05, '\u03B5\"<sub>\u221E</sub>', "")  # epsilon2 inf
        self.muInf1 = TheoryParameter(1, '\u03BC\'<sub>\u221E</sub>', "")  # mu1 inf
        self.Hext = TheoryParameter(40000, 'H<sub>ext</sub>', "Oe")  # H external
        # self.fFix = TheoryParameter(80 / 30, '\u03BD<sub>fix</sub>', "cm<sup>-1</sup>")  # nu fixed
        self.fFix = TheoryParameter(80, 'f<sub>fix</sub>', "GHz")  # f fixed

        self.Temperature = TheoryParameter(1.8, "Temperature", "K")
        self.deltaCF = TheoryParameter(1.005, '\u0394<sub>CF</sub>', "cm<sup>-1</sup>")  # delta CF splitting, cm-1
        self.gamma = TheoryParameter(1.0, '\u03B3', "cm<sup>-1</sup>")  # gamma
        self.axis_h = TheoryParameter(1.0, 'h<sup>ac</sup><sub>i</sub>', "i = 1(x), 2(y), 3(z)")  # gamma
        self.axis_Hext = TheoryParameter(1.0, 'H<sup>ext</sup><sub>i</sub>', "i = 1(x), 2(y), 3(z)")  # gamma

        self.f_Start = TheoryParameter(2, '\u03BD<sub>start</sub>', "cm<sup>-1</sup>", False)  # nu start
        self.f_End = TheoryParameter(5, '\u03BD<sub>end</sub>', "cm<sup>-1</sup>", False)  # nu end
        self.H_Start = TheoryParameter(0, 'H<sub>start</sub>', "Oe", False)  # H start
        self.H_End = TheoryParameter(60000, 'H<sub>end</sub>', "Oe", False)  # H end

        self.parameters = [self.d, self.epsInf1, self.epsInf2, self.muInf1, self.Hext, self.fFix,
                           self.Temperature, self.deltaCF, self.gamma, self.axis_h, self.axis_Hext,
                           self.f_Start, self.f_End, self.H_Start, self.H_End]
        ################### ^ PARAMETERS ^ ###################

        ################### v PLOT VALUES v ###################
        self.f = None  # frequencies array, cm
        self.H = None  # magnetic fields array, kOe
        self.tr_f = None  # transmittance
        self.ph_f = None  # phase/frequency, rad/cm-1
        self.tr_H = None  # transmittance
        self.ph_H = None  # mirror (optical length), mm
        # self.f_H_6m = None ##############################################################
        ################### ^ PLOT VALUES ^ ###################

        self.modelTypes = [Model.OSCILLATOR, Model.MAGNET_OSCILLATOR]

        ################### v UTILS v ###################
        # self.modes = []
        self.modesD = []
        self.modesDmu_x = []
        self.modesDmu_y = []
        self.modesDmu_z = []

        self.modes = []  # 6x position modes 1p, 1m, 2p, 2m, 3p, 3m
        for i in range(6):
            self.modes.append(Model(Model.MAGNET_OSCILLATOR))
        ################### ^ UTILS ^ ###################

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
                if model.name == Model.MAGNET_OSCILLATOR:
                    f0 = model.f0.value
                    mu_i += model.deltaMu.value * f0 ** 2 / (
                            f0 ** 2 - self.f[i] ** 2 - complex(0, model.gamma.value * self.f[i]))
            ########### !!! No 6x modes calculation in Tr(f)
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

        eps_H0 = 0
        mu_H0 = 0
        f = self.fFix.value / 30
        for model in self.models:
            if model.name == Model.OSCILLATOR:
                f0 = model.f0.value
                eps_H0 += model.deltaEps.value * f0 ** 2 / (
                          f0 ** 2 - f ** 2 - complex(0, model.gamma.value * f))
            if model.name == Model.MAGNET_OSCILLATOR:
                f0 = model.f0.value
                mu_H0 += model.deltaMu.value * f0 ** 2 / (
                         f0 ** 2 - f ** 2 - complex(0, model.gamma.value * f))

        eps = []
        mu = []
        for j in range(self.numPoints):
            eps_i = complex(self.epsInf1.value, self.epsInf2.value) + eps_H0
            mu_i = complex(self.muInf1.value, 0) + mu_H0

            self.calcUtils(self.H[j])
            # for model in self.modes:
            for i in range(6):
                model = self.modes[i]
                model.f0.value = self.modesD[i]
                if self.axis_h.value == 1:
                    model.deltaMu.value = self.modesDmu_x[i]
                elif self.axis_h.value == 2:
                    model.deltaMu.value = self.modesDmu_y[i]
                elif self.axis_h.value == 3:
                    model.deltaMu.value = self.modesDmu_z[i]
                else:
                    self.axis_h.numberEdit.resetValue(1)
                    model.deltaMu.value = self.modesDmu_x[i]
                model.gamma.value = self.gamma.value

                f0 = model.f0.value
                mu_i += model.deltaMu.value * f0 ** 2 / (f0 ** 2 - f ** 2 - complex(0, model.gamma.value * f))

            # self.f_H_6m = []  ####################################################
            # self.f_H_6m.append(self.modesD[5])  ####################################################

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

        # self.curves[DataTypes.Test] = TheoryCurve(self.H, self.f_H_6m)  ####################################################

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

    def calcUtils(self, H):
        PI1 = math.pi
        h = 6.6260755E-27 / (2 * PI1)
        kB = 1.380658E-16
        NA = 6.022E23
        kcm = 2 * PI1 * h * 3.0E10
        kGHz = 30
        muB = 0.927401549E-20
        ro = 5.2

        # Magnetization, frequencies and magnetic contributions for a distorted crystal: six sites
        cc = 0.015  # Ho concentration
        MvHoLang = (138.90 * (1 - cc) + 164.93 * cc) * 3 + 69.72 * 5 + 28.08 + 16 * 14
        Dcf = self.deltaCF.value
        ma = 1.0 * 3.5 * muB
        mb = 6.8 * muB
        mc = 5.4 * 0.94 * muB

        T = self.Temperature.value


        al2 = 120 * PI1 / 180
        cosal2 = math.cos(al2)
        sinal2 = math.sin(al2)
        al3 = -120 * PI1 / 180
        cosal3 = math.cos(al3)
        sinal3 = math.sin(al3)

        # Magnetic field dependence along a-, b and c-axes
        if self.axis_Hext.value == 1:
            # H||a
            TH = 90 * PI1 / 180
            fiH = 0 * PI1 / 180
        elif self.axis_Hext.value == 2:
            # H||b
            TH = 90 * PI1 / 180
            fiH = 90 * PI1 / 180
        elif self.axis_Hext.value == 3:
            # H||c
            TH = 0 * PI1 / 180
            fiH = 90 * PI1 / 180
        else:
            # H||a
            TH = 90 * PI1 / 180
            fiH = 0 * PI1 / 180

        cosTH = math.cos(TH)
        sinTH = math.sin(TH)
        cosfiH = math.cos(fiH)
        sinfiH = math.sin(fiH)

        def D1p(H): return 2 * math.sqrt(Dcf ** 2 + (1 / kcm * H * abs(ma * sinTH * cosfiH + mb * sinTH * sinfiH + mc * cosTH)) ** 2)
        def D1m(H): return 2 * math.sqrt(Dcf ** 2 + (1 / kcm * H * abs(-ma * sinTH * cosfiH + mb * sinTH * sinfiH + mc * cosTH)) ** 2)
        def D2p(H): return 2 * math.sqrt(Dcf ** 2 + (1 / kcm * H * abs(ma * sinTH * math.cos(fiH - al2) + mb * sinTH * math.sin(fiH - al2) + mc * cosTH)) ** 2)
        def D2m(H): return 2 * math.sqrt(Dcf ** 2 + (1 / kcm * H * abs(-ma * sinTH * math.cos(fiH - al2) + mb * sinTH * math.sin(fiH - al2) + mc * cosTH)) ** 2)
        def D3p(H): return 2 * math.sqrt(Dcf ** 2 + (1 / kcm * H * abs(ma * sinTH * math.cos(fiH - al3) + mb * sinTH * math.sin(fiH - al3) + mc * cosTH)) ** 2)
        def D3m(H): return 2 * math.sqrt(Dcf ** 2 + (1 / kcm * H * abs(-ma * sinTH * math.cos(fiH - al3) + mb * sinTH * math.sin(fiH - al3) + mc * cosTH)) ** 2)

        self.modesD = [D1p(H), D1m(H), D2p(H), D2m(H), D3p(H), D3m(H)]

        # frequencies and magnetic mode contributions
        def Dmux1p(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * ma ** 2 / D1p(H) / kcm * math.tanh(D1p(H) * kcm / 2 / kB / T) * (2 * Dcf / D1p(H)) ** 2
        def Dmux1m(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * ma ** 2 / D1m(H) / kcm * math.tanh(D1m(H) * kcm / 2 / kB / T) * (2 * Dcf / D1m(H)) ** 2
        def Dmux2p(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * (ma * cosal2 - mb * sinal2) ** 2 / D2p( H) / kcm * math.tanh(D2p(H) * kcm / 2 / kB / T) * (2 * Dcf / D2p(H)) ** 2
        def Dmux2m(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * (-ma * cosal2 - mb * sinal2) ** 2 / D2m(H) / kcm * math.tanh(D2m(H) * kcm / 2 / kB / T) * (2 * Dcf / D2m(H)) ** 2
        def Dmux3p(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * (ma * cosal3 - mb * sinal3) ** 2 / D3p(H) / kcm * math.tanh(D3p(H) * kcm / 2 / kB / T) * (2 * Dcf / D3p(H)) ** 2
        def Dmux3m(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * (-ma * cosal3 - mb * sinal3) ** 2 / D3m(H) / kcm * math.tanh(D3m(H) * kcm / 2 / kB / T) * (2 * Dcf / D3m(H)) ** 2
        self.modesDmu_x = [Dmux1p(H), Dmux1m(H), Dmux2p(H), Dmux2m(H), Dmux3p(H), Dmux3m(H)]

        def Dmuy1p(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * mb ** 2 / D1p(H) / kcm * math.tanh(D1p(H) * kcm / 2 / kB / T) * (2 * Dcf / D1p(H)) ** 2
        def Dmuy1m(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * mb ** 2 / D1m(H) / kcm * math.tanh(D1m(H) * kcm / 2 / kB / T) * (2 * Dcf / D1m(H)) ** 2
        def Dmuy2p(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * (ma * sinal2 + mb * cosal2) ** 2 / D2p(H) / kcm * math.tanh(D2p(H) * kcm / 2 / kB / T) * (2 * Dcf / D2p(H)) ** 2
        def Dmuy2m(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * (-ma * sinal2 + mb * cosal2) ** 2 / D2m(H) / kcm * math.tanh(D2m(H) * kcm / 2 / kB / T) * (2 * Dcf / D2m(H)) ** 2
        def Dmuy3p(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * (ma * sinal3 + mb * cosal3) ** 2 / D3p(H) / kcm * math.tanh(D3p(H) * kcm / 2 / kB / T) * (2 * Dcf / D3p(H)) ** 2
        def Dmuy3m(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * (-ma * sinal3 + mb * cosal3) ** 2 / D3m(H) / kcm * math.tanh(D3m(H) * kcm / 2 / kB / T) * (2 * Dcf / D3m(H)) ** 2
        self.modesDmu_y = [Dmuy1p(H), Dmuy1m(H), Dmuy2p(H), Dmuy2m(H), Dmuy3p(H), Dmuy3m(H)]

        def Dmuz1p(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * mc ** 2 / D1p(H) / kcm * math.tanh(D1p(H) * kcm / 2 / kB / T) * (2 * Dcf / D1p(H)) ** 2
        def Dmuz1m(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * mc ** 2 / D1m(H) / kcm * math.tanh(D1m(H) * kcm / 2 / kB / T) * (2 * Dcf / D1m(H)) ** 2
        def Dmuz2p(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * mc ** 2 / D2p(H) / kcm * math.tanh(D2p(H) * kcm / 2 / kB / T) * (2 * Dcf / D2p(H)) ** 2
        def Dmuz2m(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * mc ** 2 / D2m(H) / kcm * math.tanh(D2m(H) * kcm / 2 / kB / T) * (2 * Dcf / D2m(H)) ** 2
        def Dmuz3p(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * mc ** 2 / D3p(H) / kcm * math.tanh(D3p(H) * kcm / 2 / kB / T) * (2 * Dcf / D3p(H)) ** 2
        def Dmuz3m(H): return 4 * PI1 * ro / 6 * (3 * cc * NA / MvHoLang) * mc ** 2 / D3m(H) / kcm * math.tanh(D3m(H) * kcm / 2 / kB / T) * (2 * Dcf / D3m(H)) ** 2
        self.modesDmu_z = [Dmuz1p(H), Dmuz1m(H), Dmuz2p(H), Dmuz2m(H), Dmuz3p(H), Dmuz3m(H)]

