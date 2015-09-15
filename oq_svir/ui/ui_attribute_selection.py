# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/ui_attribute_selection.ui'
#
# Created: Sun Feb 22 18:30:10 2015
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

class Ui_AttributeSelctionDialog(object):
    def setupUi(self, AttributeSelctionDialog):
        AttributeSelctionDialog.setObjectName(_fromUtf8("AttributeSelctionDialog"))
        AttributeSelctionDialog.setWindowModality(QtCore.Qt.WindowModal)
        AttributeSelctionDialog.resize(700, 377)
        AttributeSelctionDialog.setModal(True)
        self.verticalLayout = QtGui.QVBoxLayout(AttributeSelctionDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(AttributeSelctionDialog)
        self.label.setWordWrap(True)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.loss_attrs_multisel = ListMultiSelectWidget(AttributeSelctionDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.loss_attrs_multisel.sizePolicy().hasHeightForWidth())
        self.loss_attrs_multisel.setSizePolicy(sizePolicy)
        self.loss_attrs_multisel.setObjectName(_fromUtf8("loss_attrs_multisel"))
        self.verticalLayout.addWidget(self.loss_attrs_multisel)
        self.groupBox = QtGui.QGroupBox(AttributeSelctionDialog)
        self.groupBox.setTitle(_fromUtf8(""))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.formLayout = QtGui.QFormLayout(self.groupBox)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.zone_id_attr_name_loss_cbox = QtGui.QComboBox(self.groupBox)
        self.zone_id_attr_name_loss_cbox.setObjectName(_fromUtf8("zone_id_attr_name_loss_cbox"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.zone_id_attr_name_loss_cbox)
        self.zone_id_attr_name_loss_lbl = QtGui.QLabel(self.groupBox)
        self.zone_id_attr_name_loss_lbl.setObjectName(_fromUtf8("zone_id_attr_name_loss_lbl"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.zone_id_attr_name_loss_lbl)
        self.verticalLayout.addWidget(self.groupBox)
        self.groupBox_2 = QtGui.QGroupBox(AttributeSelctionDialog)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.formLayout_2 = QtGui.QFormLayout(self.groupBox_2)
        self.formLayout_2.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout_2.setObjectName(_fromUtf8("formLayout_2"))
        self.zone_id_attr_name_zone_lbl = QtGui.QLabel(self.groupBox_2)
        self.zone_id_attr_name_zone_lbl.setObjectName(_fromUtf8("zone_id_attr_name_zone_lbl"))
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.LabelRole, self.zone_id_attr_name_zone_lbl)
        self.zone_id_attr_name_zone_cbox = QtGui.QComboBox(self.groupBox_2)
        self.zone_id_attr_name_zone_cbox.setObjectName(_fromUtf8("zone_id_attr_name_zone_cbox"))
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.FieldRole, self.zone_id_attr_name_zone_cbox)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.buttonBox = QtGui.QDialogButtonBox(AttributeSelctionDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(AttributeSelctionDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), AttributeSelctionDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), AttributeSelctionDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(AttributeSelctionDialog)

    def retranslateUi(self, AttributeSelctionDialog):
        AttributeSelctionDialog.setWindowTitle(_translate("AttributeSelctionDialog", "Aggregate loss by zone", None))
        self.label.setText(_translate("AttributeSelctionDialog", "For each zone, the plugin will calculate the count of loss points and (for each of the selected loss variables) the sum and average values", None))
        self.loss_attrs_multisel.setTitle(_translate("AttributeSelctionDialog", "Loss Layer", None))
        self.zone_id_attr_name_loss_lbl.setText(_translate("AttributeSelctionDialog", "Zone ID attribute name", None))
        self.groupBox_2.setTitle(_translate("AttributeSelctionDialog", "Zonal Layer", None))
        self.zone_id_attr_name_zone_lbl.setText(_translate("AttributeSelctionDialog", "Zone ID attriubute name", None))

from oq_svir.ui.list_multiselect_widget import ListMultiSelectWidget
