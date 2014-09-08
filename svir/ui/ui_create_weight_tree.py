# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_create_weight_tree.ui'
#
# Created: Mon Sep  8 17:11:33 2014
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
        CreateWeightTreeDialog.resize(570, 220)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(CreateWeightTreeDialog.sizePolicy().hasHeightForWidth())
        CreateWeightTreeDialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QtGui.QVBoxLayout(CreateWeightTreeDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label_2 = QtGui.QLabel(CreateWeightTreeDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout.addWidget(self.label_2)
        self.risk_field_cbx = QtGui.QComboBox(CreateWeightTreeDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.risk_field_cbx.sizePolicy().hasHeightForWidth())
        self.risk_field_cbx.setSizePolicy(sizePolicy)
        self.risk_field_cbx.setObjectName(_fromUtf8("risk_field_cbx"))
        self.horizontalLayout.addWidget(self.risk_field_cbx)
        self.merge_risk_btn = QtGui.QPushButton(CreateWeightTreeDialog)
        self.merge_risk_btn.setObjectName(_fromUtf8("merge_risk_btn"))
        self.horizontalLayout.addWidget(self.merge_risk_btn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.label = QtGui.QLabel(CreateWeightTreeDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setWordWrap(True)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.scrollArea = QtGui.QScrollArea(CreateWeightTreeDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 550, 75))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.gridLayout = QtGui.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.grid_layout = QtGui.QGridLayout()
        self.grid_layout.setObjectName(_fromUtf8("grid_layout"))
        self.gridLayout.addLayout(self.grid_layout, 0, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.buttonBox = QtGui.QDialogButtonBox(CreateWeightTreeDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Reset)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(CreateWeightTreeDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), CreateWeightTreeDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), CreateWeightTreeDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CreateWeightTreeDialog)

    def retranslateUi(self, CreateWeightTreeDialog):
        CreateWeightTreeDialog.setWindowTitle(_translate("CreateWeightTreeDialog", "Define model structure", None))
        self.label_2.setText(_translate("CreateWeightTreeDialog", "Risk field", None))
        self.merge_risk_btn.setText(_translate("CreateWeightTreeDialog", "Copy risk field from another layer", None))
        self.label.setText(_translate("CreateWeightTreeDialog", "Create your indices by defining which fields appartain to which theme. Attributes need both a theme and a name to be considered in the index calculation. You can generate a flat index (with no themes) by not entering any theme.", None))

