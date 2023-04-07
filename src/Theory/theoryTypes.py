from theoryModels import TheoryTrPh_fH, TheoryTrPh_f
from temp.theoryLangasite_GaussDirection import TheoryLangasite_GaussDirection
from theoryLangasite_M_H import TheoryLangasite_M_H
from theoryLangasite_M_teta import TheoryLangasite_M_teta
from theoryHoLGS_DistrAngleDcf import TheoryHoLGS_DistrAngleDcf
from theoryNdLGS_TrPh_fH import theoryNdLGS_TrPh_fH


class TheoryType:
    types = {TheoryTrPh_fH.name: TheoryTrPh_fH,
             TheoryTrPh_f.name: TheoryTrPh_f,
             TheoryLangasite_GaussDirection.name: TheoryLangasite_GaussDirection,
             TheoryLangasite_M_H.name: TheoryLangasite_M_H,
             TheoryLangasite_M_teta.name: TheoryLangasite_M_teta,
             TheoryHoLGS_DistrAngleDcf.name: TheoryHoLGS_DistrAngleDcf,
             theoryNdLGS_TrPh_fH.name: theoryNdLGS_TrPh_fH,
             }
