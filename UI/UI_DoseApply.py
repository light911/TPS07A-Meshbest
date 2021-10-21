# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'DoseApply.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.resize(377, 201)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.label_2 = QtWidgets.QLabel(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.ConsiderOrder = QtWidgets.QComboBox(Dialog)
        self.ConsiderOrder.setObjectName("ConsiderOrder")
        self.ConsiderOrder.addItem("")
        self.ConsiderOrder.addItem("")
        self.ConsiderOrder.addItem("")
        self.verticalLayout.addWidget(self.ConsiderOrder)
        self.doubleSpinBox = QtWidgets.QDoubleSpinBox(Dialog)
        self.doubleSpinBox.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.doubleSpinBox.sizePolicy().hasHeightForWidth())
        self.doubleSpinBox.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(20)
        self.doubleSpinBox.setFont(font)
        self.doubleSpinBox.setMinimum(0.01)
        self.doubleSpinBox.setMaximum(1000.0)
        self.doubleSpinBox.setProperty("value", 10.0)
        self.doubleSpinBox.setObjectName("doubleSpinBox")
        self.verticalLayout.addWidget(self.doubleSpinBox)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Apply|QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        self.verticalLayout.setStretch(2, 50)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.label.setText(_translate("Dialog", "Item"))
        self.label_2.setText(_translate("Dialog", "Consider order"))
        self.ConsiderOrder.setItemText(0, _translate("Dialog", "BeamSize"))
        self.ConsiderOrder.setItemText(1, _translate("Dialog", "Atten-Time"))
        self.ConsiderOrder.setItemText(2, _translate("Dialog", "TotalRange"))
        self.doubleSpinBox.setSuffix(_translate("Dialog", "Mgy"))
