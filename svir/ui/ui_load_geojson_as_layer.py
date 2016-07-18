# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_load_geojson_as_layer.ui'
#
# Created: Mon Jul 18 10:44:19 2016
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

class Ui_LoadGeoJsonAsLayerDialog(object):
    def setupUi(self, LoadGeoJsonAsLayerDialog):
        LoadGeoJsonAsLayerDialog.setObjectName(_fromUtf8("LoadGeoJsonAsLayerDialog"))
        LoadGeoJsonAsLayerDialog.resize(586, 309)
        self.buttonBox = QtGui.QDialogButtonBox(LoadGeoJsonAsLayerDialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.layoutWidget = QtGui.QWidget(LoadGeoJsonAsLayerDialog)
        self.layoutWidget.setGeometry(QtCore.QRect(30, 20, 531, 211))
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.geojson_lbl = QtGui.QLabel(self.layoutWidget)
        self.geojson_lbl.setObjectName(_fromUtf8("geojson_lbl"))
        self.horizontalLayout.addWidget(self.geojson_lbl)
        self.file_browser_tbn = QtGui.QToolButton(self.layoutWidget)
        self.file_browser_tbn.setObjectName(_fromUtf8("file_browser_tbn"))
        self.horizontalLayout.addWidget(self.file_browser_tbn)
        self.geojson_path_le = QtGui.QLineEdit(self.layoutWidget)
        self.geojson_path_le.setEnabled(False)
        self.geojson_path_le.setObjectName(_fromUtf8("geojson_path_le"))
        self.horizontalLayout.addWidget(self.geojson_path_le)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.rlz_lbl = QtGui.QLabel(self.layoutWidget)
        self.rlz_lbl.setObjectName(_fromUtf8("rlz_lbl"))
        self.verticalLayout.addWidget(self.rlz_lbl)
        self.rlz_cbx = QtGui.QComboBox(self.layoutWidget)
        self.rlz_cbx.setEnabled(False)
        self.rlz_cbx.setObjectName(_fromUtf8("rlz_cbx"))
        self.verticalLayout.addWidget(self.rlz_cbx)
        self.imt_lbl = QtGui.QLabel(self.layoutWidget)
        self.imt_lbl.setObjectName(_fromUtf8("imt_lbl"))
        self.verticalLayout.addWidget(self.imt_lbl)
        self.imt_cbx = QtGui.QComboBox(self.layoutWidget)
        self.imt_cbx.setEnabled(False)
        self.imt_cbx.setObjectName(_fromUtf8("imt_cbx"))
        self.verticalLayout.addWidget(self.imt_cbx)
        self.poe_lbl = QtGui.QLabel(self.layoutWidget)
        self.poe_lbl.setObjectName(_fromUtf8("poe_lbl"))
        self.verticalLayout.addWidget(self.poe_lbl)
        self.poe_cbx = QtGui.QComboBox(self.layoutWidget)
        self.poe_cbx.setEnabled(False)
        self.poe_cbx.setObjectName(_fromUtf8("poe_cbx"))
        self.verticalLayout.addWidget(self.poe_cbx)

        self.retranslateUi(LoadGeoJsonAsLayerDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), LoadGeoJsonAsLayerDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), LoadGeoJsonAsLayerDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(LoadGeoJsonAsLayerDialog)

    def retranslateUi(self, LoadGeoJsonAsLayerDialog):
        LoadGeoJsonAsLayerDialog.setWindowTitle(_translate("LoadGeoJsonAsLayerDialog", "Load GeoJson as layer", None))
        self.geojson_lbl.setText(_translate("LoadGeoJsonAsLayerDialog", "Geojson file or archive", None))
        self.file_browser_tbn.setText(_translate("LoadGeoJsonAsLayerDialog", "...", None))
        self.rlz_lbl.setText(_translate("LoadGeoJsonAsLayerDialog", "Realization", None))
        self.imt_lbl.setText(_translate("LoadGeoJsonAsLayerDialog", "Intensity Measure Type", None))
        self.poe_lbl.setText(_translate("LoadGeoJsonAsLayerDialog", "Probability of Exceedance", None))

