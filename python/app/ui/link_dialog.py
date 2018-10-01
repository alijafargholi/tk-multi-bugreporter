# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'link_form.ui',
# licensing of 'link_form.ui' applies.
#
# Created: Sun Sep 30 20:43:10 2018
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_link_form(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Ui_link_form, self).__init__(parent)
        self.setObjectName("link_form")
        self.resize(632, 89)
        self.setMaximumSize(QtCore.QSize(16777215, 100))
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtGui.QLabel('Link:')
        self.label.setStyleSheet("font-weight: bold; color: #3399ff;")
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.link = QtGui.QLineEdit(self)
        self.link.setObjectName("link")
        self.horizontalLayout_2.addWidget(self.link)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.cancel = QtGui.QPushButton("Cancel")
        self.cancel.setObjectName("cancel")
        self.horizontalLayout.addWidget(self.cancel)
        self.ok = QtGui.QPushButton("Ok")
        self.ok.setObjectName("ok")
        self.horizontalLayout.addWidget(self.ok)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.cancel.clicked.connect(self.close)
        self.ok.clicked.connect(self.accept)
