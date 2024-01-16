class DataTypes:
    Trf = "Tr(f)"
    Phf = "Ph(f)"
    SignalH = "Tr(H)"
    MirrorH = "Ph(H)"
    M_H = "M(H)"
    M_T = "M(T)"
    M_teta = "M(\u03B8)"
    f_H = "f(H)"
    dMu_H = "dMu(H)"
    Test = "Test"
    R_f = "R(f)"
    PhR_f = "PhR(f)"
    types = [Trf, Phf, SignalH, MirrorH, M_H, M_T, M_teta, f_H, dMu_H, R_f, PhR_f]


def getDataTypeAttributes(types, dataType):
    attributes = None
    if dataType in types:
        if dataType == DataTypes.Trf:
            attributes = DataTypeAttributes(nameY="Transmittance", nameX="Frequency, cm<sup>-1</sup>", logY=True)
        elif dataType == DataTypes.Phf:
            attributes = DataTypeAttributes(nameY="Phase/Frequency, rad/cm<sup>-1</sup>", nameX="Frequency, cm<sup>-1</sup>")
        elif dataType == DataTypes.SignalH:
            attributes = DataTypeAttributes(nameY="Transmittance", nameX="Magnetic field, Oe")
        elif dataType == DataTypes.MirrorH:
            attributes = DataTypeAttributes(nameY="Optical path length, mm", nameX="Magnetic field, Oe")
        elif dataType == DataTypes.M_H:
            attributes = DataTypeAttributes(nameY="Magnetization, emu/g", nameX="Magnetic field, Oe")
        elif dataType == DataTypes.M_T:
            attributes = DataTypeAttributes(nameY="Magnetization, emu/g", nameX="Temperature, K")
        elif dataType == DataTypes.M_teta:
            attributes = DataTypeAttributes(nameY="Magnetization, emu/g", nameX="Angle, degrees")
        elif dataType == DataTypes.R_f:
            attributes = DataTypeAttributes(nameY="Reflectivity", nameX="Frequency, cm<sup>-1</sup>")
        elif dataType == DataTypes.PhR_f:
            attributes = DataTypeAttributes(nameY="Phase, rad", nameX="Frequency, cm<sup>-1</sup>")
        elif dataType == DataTypes.dMu_H:
            attributes = DataTypeAttributes(nameY="Δμ''", nameX="Magnetic field, Oe")
        else:
            attributes = DataTypeAttributes(nameY="TestY, units", nameX="TestX, units")
    else:
        print("getDataTypeAttributes error: dataType " + dataType)
    return attributes


class DataTypeAttributes:
    def __init__(self, nameY, nameX, logY=False):
        self.nameY = nameY
        self.nameX = nameX
        self.logY = logY


class FileTypes:
    TrPhf = "TrPh_f"
    TrPhH = "TrPh_H"
    MH = "M_H"
    MT = "M_T"
    MTeta = "M_Teta"
    RPhRf = "RPhR_f"
    types = [TrPhf, TrPhH, MH, MT, MTeta, RPhRf]
