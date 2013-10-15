# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'selection_dialog.ui'
#
# Created: Tue Oct 15 03:04:38 2013
#      by: PyQt4 UI code generator 4.10.3
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

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(658, 397)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.selectionTool = QtGui.QGroupBox(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.selectionTool.sizePolicy().hasHeightForWidth())
        self.selectionTool.setSizePolicy(sizePolicy)
        self.selectionTool.setMinimumSize(QtCore.QSize(470, 200))
        self.selectionTool.setObjectName(_fromUtf8("selectionTool"))
        self.selectionToolLayout = QtGui.QVBoxLayout(self.selectionTool)
        self.selectionToolLayout.setObjectName(_fromUtf8("selectionToolLayout"))
        self.selectorLayout = QtGui.QHBoxLayout()
        self.selectorLayout.setObjectName(_fromUtf8("selectorLayout"))
        self.selectorList = QtGui.QListWidget(self.selectionTool)
        self.selectorList.setObjectName(_fromUtf8("selectorList"))
        self.selectorLayout.addWidget(self.selectorList)
        self.selectorFormLayout = QtGui.QVBoxLayout()
        self.selectorFormLayout.setObjectName(_fromUtf8("selectorFormLayout"))
        self.selectorSummaryLabel = QtGui.QLabel(self.selectionTool)
        self.selectorSummaryLabel.setObjectName(_fromUtf8("selectorSummaryLabel"))
        self.selectorFormLayout.addWidget(self.selectorSummaryLabel)
        self.removeFromRuleListButton = QtGui.QPushButton(self.selectionTool)
        self.removeFromRuleListButton.setObjectName(_fromUtf8("removeFromRuleListButton"))
        self.selectorFormLayout.addWidget(self.removeFromRuleListButton)
        self.purgeUnselectedEventsButton = QtGui.QPushButton(self.selectionTool)
        self.purgeUnselectedEventsButton.setObjectName(_fromUtf8("purgeUnselectedEventsButton"))
        self.selectorFormLayout.addWidget(self.purgeUnselectedEventsButton)
        self.invertSelectionButton = QtGui.QPushButton(self.selectionTool)
        self.invertSelectionButton.setObjectName(_fromUtf8("invertSelectionButton"))
        self.selectorFormLayout.addWidget(self.invertSelectionButton)
        self.selectorLayout.addLayout(self.selectorFormLayout)
        self.selectionToolLayout.addLayout(self.selectorLayout)
        self.selectorFormLayout_2 = QtGui.QHBoxLayout()
        self.selectorFormLayout_2.setObjectName(_fromUtf8("selectorFormLayout_2"))
        self.selectorComboBox = QtGui.QComboBox(self.selectionTool)
        self.selectorComboBox.setEditable(False)
        self.selectorComboBox.setObjectName(_fromUtf8("selectorComboBox"))
        self.selectorComboBox.addItem(_fromUtf8(""))
        self.selectorComboBox.setItemText(0, _fromUtf8(""))
        self.selectorComboBox.addItem(_fromUtf8(""))
        self.selectorComboBox.addItem(_fromUtf8(""))
        self.selectorComboBox.addItem(_fromUtf8(""))
        self.selectorComboBox.addItem(_fromUtf8(""))
        self.selectorComboBox.addItem(_fromUtf8(""))
        self.selectorComboBox.addItem(_fromUtf8(""))
        self.selectorComboBox.addItem(_fromUtf8(""))
        self.selectorComboBox.addItem(_fromUtf8(""))
        self.selectorFormLayout_2.addWidget(self.selectorComboBox)
        self.selectButton = QtGui.QPushButton(self.selectionTool)
        self.selectButton.setObjectName(_fromUtf8("selectButton"))
        self.selectorFormLayout_2.addWidget(self.selectButton)
        self.selectionToolLayout.addLayout(self.selectorFormLayout_2)
        self.verticalLayout.addWidget(self.selectionTool)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.selectionTool.setTitle(_translate("Dialog", "Select Events", None))
        self.selectorSummaryLabel.setText(_translate("Dialog", "All events selected", None))
        self.removeFromRuleListButton.setText(_translate("Dialog", "Remove from List", None))
        self.purgeUnselectedEventsButton.setText(_translate("Dialog", "Delete unselected events", None))
        self.invertSelectionButton.setText(_translate("Dialog", "Invert Selection", None))
        self.selectorComboBox.setItemText(1, _translate("Dialog", "Within Polyhedra", None))
        self.selectorComboBox.setItemText(2, _translate("Dialog", "Within J/B distance of source", None))
        self.selectorComboBox.setItemText(3, _translate("Dialog", "Within Rupture distance", None))
        self.selectorComboBox.setItemText(4, _translate("Dialog", "Within a square centered on", None))
        self.selectorComboBox.setItemText(5, _translate("Dialog", "Within a distance from", None))
        self.selectorComboBox.setItemText(6, _translate("Dialog", "J/B within from point", None))
        self.selectorComboBox.setItemText(7, _translate("Dialog", "Time between", None))
        self.selectorComboBox.setItemText(8, _translate("Dialog", "Field between", None))
        self.selectButton.setText(_translate("Dialog", "Select", None))

