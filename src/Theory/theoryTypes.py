from theoryModels import TheoryTrPh_fH
# from temp.theoryLangasite_GaussDirection import TheoryLangasite_GaussDirection
from theoryLangasite_M_H import TheoryLangasite_M_H
from theoryLangasite_M_teta import TheoryLangasite_M_teta
from theoryHoLGS_DistrAngleDcf import TheoryHoLGS_DistrAngleDcf
from theoryNdLGS_TrPh_fH import theoryNdLGS_TrPh_fH
from theoryTrPh_f import TheoryTrPh_f
from theoryTrPh_f_RPh_f import TheoryTrPh_f_RPh_f
from theoryTbLGS_M_teta import TheoryTbLGS_M_teta
from theoryGaussPhonon import TheoryGaussPhonon


class TheoryType:
    types = {TheoryTrPh_fH.name: TheoryTrPh_fH,
             TheoryTrPh_f.name: TheoryTrPh_f,
             # TheoryLangasite_GaussDirection.name: TheoryLangasite_GaussDirection,
             TheoryLangasite_M_H.name: TheoryLangasite_M_H,
             TheoryLangasite_M_teta.name: TheoryLangasite_M_teta,
             TheoryHoLGS_DistrAngleDcf.name: TheoryHoLGS_DistrAngleDcf,
             theoryNdLGS_TrPh_fH.name: theoryNdLGS_TrPh_fH,
             TheoryTrPh_f_RPh_f.name: TheoryTrPh_f_RPh_f,
             TheoryTbLGS_M_teta.name: TheoryTbLGS_M_teta,
             TheoryGaussPhonon.name:TheoryGaussPhonon,
             }
