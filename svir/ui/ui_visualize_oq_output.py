# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_visualize_oq_output.ui'
#
# Created: Wed Jun 15 15:36:33 2016
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

class Ui_VisualizeOqOutputDialog(object):
    def setupUi(self, VisualizeOqOutputDialog):
        VisualizeOqOutputDialog.setObjectName(_fromUtf8("VisualizeOqOutputDialog"))
        VisualizeOqOutputDialog.resize(586, 309)
        self.buttonBox = QtGui.QDialogButtonBox(VisualizeOqOutputDialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.layoutWidget = QtGui.QWidget(VisualizeOqOutputDialog)
        self.layoutWidget.setGeometry(QtCore.QRect(30, 20, 531, 211))
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.hdf5_lbl = QtGui.QLabel(self.layoutWidget)
        self.hdf5_lbl.setObjectName(_fromUtf8("hdf5_lbl"))
        self.horizontalLayout.addWidget(self.hdf5_lbl)
        self.file_browser_tbn = QtGui.QToolButton(self.layoutWidget)
        self.file_browser_tbn.setObjectName(_fromUtf8("file_browser_tbn"))
        self.horizontalLayout.addWidget(self.file_browser_tbn)
        self.hdf5_path_le = QtGui.QLineEdit(self.layoutWidget)
        self.hdf5_path_le.setEnabled(False)
        self.hdf5_path_le.setObjectName(_fromUtf8("hdf5_path_le"))
        self.horizontalLayout.addWidget(self.hdf5_path_le)
        self.open_hdfview_btn = QtGui.QPushButton(self.layoutWidget)
        self.open_hdfview_btn.setObjectName(_fromUtf8("open_hdfview_btn"))
        self.horizontalLayout.addWidget(self.open_hdfview_btn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.rlz_lbl = QtGui.QLabel(self.layoutWidget)
        self.rlz_lbl.setObjectName(_fromUtf8("rlz_lbl"))
        self.verticalLayout.addWidget(self.rlz_lbl)
        self.rlz_cbx = QtGui.QComboBox(self.layoutWidget)
        self.rlz_cbx.setObjectName(_fromUtf8("rlz_cbx"))
        self.verticalLayout.addWidget(self.rlz_cbx)
        self.imt_lbl = QtGui.QLabel(self.layoutWidget)
        self.imt_lbl.setObjectName(_fromUtf8("imt_lbl"))
        self.verticalLayout.addWidget(self.imt_lbl)
        self.imt_cbx = QtGui.QComboBox(self.layoutWidget)
        self.imt_cbx.setObjectName(_fromUtf8("imt_cbx"))
        self.verticalLayout.addWidget(self.imt_cbx)
        self.poe_lbl = QtGui.QLabel(self.layoutWidget)
        self.poe_lbl.setObjectName(_fromUtf8("poe_lbl"))
        self.verticalLayout.addWidget(self.poe_lbl)
        self.poe_cbx = QtGui.QComboBox(self.layoutWidget)
        self.poe_cbx.setObjectName(_fromUtf8("poe_cbx"))
        self.verticalLayout.addWidget(self.poe_cbx)

        self.retranslateUi(VisualizeOqOutputDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), VisualizeOqOutputDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), VisualizeOqOutputDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(VisualizeOqOutputDialog)

    def retranslateUi(self, VisualizeOqOutputDialog):
        VisualizeOqOutputDialog.setWindowTitle(_translate("VisualizeOqOutputDialog", "Visualize oq-engine output", None))
        self.hdf5_lbl.setText(_translate("VisualizeOqOutputDialog", "Hdf5 file", None))
        self.file_browser_tbn.setText(_translate("VisualizeOqOutputDialog", "...", None))
        self.open_hdfview_btn.setText(_translate("VisualizeOqOutputDialog", "Open with HDFView", None))
        self.rlz_lbl.setText(_translate("VisualizeOqOutputDialog", "Realization", None))
        self.imt_lbl.setText(_translate("VisualizeOqOutputDialog", "Intensity Measure Type", None))
        self.poe_lbl.setText(_translate("VisualizeOqOutputDialog", "Probability of Exceedance", None))

