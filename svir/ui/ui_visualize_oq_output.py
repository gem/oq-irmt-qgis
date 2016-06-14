# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_visualize_oq_output.ui'
#
# Created: Tue Jun 14 16:59:51 2016
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
        self.widget = QtGui.QWidget(VisualizeOqOutputDialog)
        self.widget.setGeometry(QtCore.QRect(30, 20, 531, 211))
        self.widget.setObjectName(_fromUtf8("widget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.widget)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.hdf5_lbl = QtGui.QLabel(self.widget)
        self.hdf5_lbl.setObjectName(_fromUtf8("hdf5_lbl"))
        self.horizontalLayout.addWidget(self.hdf5_lbl)
        self.file_browser_tbn = QtGui.QToolButton(self.widget)
        self.file_browser_tbn.setObjectName(_fromUtf8("file_browser_tbn"))
        self.horizontalLayout.addWidget(self.file_browser_tbn)
        self.hdf5_path_le = QtGui.QLineEdit(self.widget)
        self.hdf5_path_le.setEnabled(False)
        self.hdf5_path_le.setObjectName(_fromUtf8("hdf5_path_le"))
        self.horizontalLayout.addWidget(self.hdf5_path_le)
        self.open_hdfview_btn = QtGui.QPushButton(self.widget)
        self.open_hdfview_btn.setObjectName(_fromUtf8("open_hdfview_btn"))
        self.horizontalLayout.addWidget(self.open_hdfview_btn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.rlz_lbl = QtGui.QLabel(self.widget)
        self.rlz_lbl.setObjectName(_fromUtf8("rlz_lbl"))
        self.verticalLayout.addWidget(self.rlz_lbl)
        self.rlz_cbx = QtGui.QComboBox(self.widget)
        self.rlz_cbx.setObjectName(_fromUtf8("rlz_cbx"))
        self.verticalLayout.addWidget(self.rlz_cbx)
        self.imt_lbl = QtGui.QLabel(self.widget)
        self.imt_lbl.setObjectName(_fromUtf8("imt_lbl"))
        self.verticalLayout.addWidget(self.imt_lbl)
        self.imt_cbx = QtGui.QComboBox(self.widget)
        self.imt_cbx.setObjectName(_fromUtf8("imt_cbx"))
        self.verticalLayout.addWidget(self.imt_cbx)
        self.poe_lbl = QtGui.QLabel(self.widget)
        self.poe_lbl.setObjectName(_fromUtf8("poe_lbl"))
        self.verticalLayout.addWidget(self.poe_lbl)
        self.poe_cbx = QtGui.QComboBox(self.widget)
        self.poe_cbx.setObjectName(_fromUtf8("poe_cbx"))
        self.verticalLayout.addWidget(self.poe_cbx)

        self.retranslateUi(VisualizeOqOutputDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), VisualizeOqOutputDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), VisualizeOqOutputDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(VisualizeOqOutputDialog)

    def retranslateUi(self, VisualizeOqOutputDialog):
        VisualizeOqOutputDialog.setWindowTitle(_translate("VisualizeOqOutputDialog", "Dialog", None))
        self.hdf5_lbl.setText(_translate("VisualizeOqOutputDialog", "Hdf5 file", None))
        self.file_browser_tbn.setText(_translate("VisualizeOqOutputDialog", "...", None))
        self.open_hdfview_btn.setText(_translate("VisualizeOqOutputDialog", "Open with HDFView", None))
        self.rlz_lbl.setText(_translate("VisualizeOqOutputDialog", "Realization", None))
        self.imt_lbl.setText(_translate("VisualizeOqOutputDialog", "Intensity Measure Type", None))
        self.poe_lbl.setText(_translate("VisualizeOqOutputDialog", "Probability of Exceedance", None))

