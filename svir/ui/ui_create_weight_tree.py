# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_create_weight_tree.ui'
#
# Created: Tue Aug 19 14:39:18 2014
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_CreateWeightTreeDialog(object):
    def setupUi(self, CreateWeightTreeDialog):
        CreateWeightTreeDialog.setObjectName(_fromUtf8("CreateWeightTreeDialog"))
        CreateWeightTreeDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        CreateWeightTreeDialog.resize(512, 418)
        self.verticalLayout = QtGui.QVBoxLayout(CreateWeightTreeDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(CreateWeightTreeDialog)
        self.label.setWordWrap(True)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.scrollArea = QtGui.QScrollArea(CreateWeightTreeDialog)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 492, 291))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.gridLayout = QtGui.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.grid_layout = QtGui.QGridLayout()
        self.grid_layout.setObjectName(_fromUtf8("grid_layout"))
        self.label_4 = QtGui.QLabel(self.scrollAreaWidgetContents)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.grid_layout.addWidget(self.label_4, 0, 2, 1, 1, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.label_3 = QtGui.QLabel(self.scrollAreaWidgetContents)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.grid_layout.addWidget(self.label_3, 0, 1, 1, 1, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.label_2 = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.grid_layout.addWidget(self.label_2, 0, 0, 1, 1, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.gridLayout.addLayout(self.grid_layout, 0, 0, 1, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.buttonBox = QtGui.QDialogButtonBox(CreateWeightTreeDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(CreateWeightTreeDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), CreateWeightTreeDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), CreateWeightTreeDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CreateWeightTreeDialog)

    def retranslateUi(self, CreateWeightTreeDialog):
        CreateWeightTreeDialog.setWindowTitle(_translate("CreateWeightTreeDialog", "Define model structure", None))
        self.label.setText(_translate("CreateWeightTreeDialog", "Create your indices by defining which fields appartain to which theme. Attributes need both a theme and a name to be considered in the index calculation. You can generate a flat index (with no themes) by not entering any theme.", None))
        self.label_4.setText(_translate("CreateWeightTreeDialog", "Name", None))
        self.label_3.setText(_translate("CreateWeightTreeDialog", "Theme", None))
        self.label_2.setText(_translate("CreateWeightTreeDialog", "Attribute", None))

