from PyQt5.QtWidgets import QApplication


def screenSize():
    rec = QApplication.desktop().screenGeometry()
    height = rec.height()
    width = rec.width()
    return width, height
