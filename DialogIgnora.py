# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialog_ignora.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Janelinha(object):
    def setupUi(self, Janelinha):
        Janelinha.setObjectName("Janelinha")
        Janelinha.resize(240, 349)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icones/epe"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Janelinha.setWindowIcon(icon)
        self.groupBox = QtWidgets.QGroupBox(Janelinha)
        self.groupBox.setGeometry(QtCore.QRect(10, 0, 221, 341))
        self.groupBox.setObjectName("groupBox")
        self.lineEdit_nbarra = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit_nbarra.setGeometry(QtCore.QRect(173, 40, 43, 20))
        self.lineEdit_nbarra.setText("")
        self.lineEdit_nbarra.setPlaceholderText("")
        self.lineEdit_nbarra.setClearButtonEnabled(False)
        self.lineEdit_nbarra.setObjectName("lineEdit_nbarra")
        self.pushButton_incluir = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_incluir.setGeometry(QtCore.QRect(110, 70, 101, 23))
        self.pushButton_incluir.setObjectName("pushButton_incluir")
        self.pushButton_removerselec = QtWidgets.QPushButton(self.groupBox)
        self.pushButton_removerselec.setGeometry(QtCore.QRect(110, 280, 101, 23))
        self.pushButton_removerselec.setObjectName("pushButton_removerselec")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setGeometry(QtCore.QRect(110, 41, 61, 16))
        self.label.setObjectName("label")
        self.listView = QtWidgets.QListView(self.groupBox)
        self.listView.setGeometry(QtCore.QRect(10, 20, 91, 311))
        self.listView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.listView.setObjectName("listView")

        self.retranslateUi(Janelinha)
        QtCore.QMetaObject.connectSlotsByName(Janelinha)

    def retranslateUi(self, Janelinha):
        _translate = QtCore.QCoreApplication.translate
        Janelinha.setWindowTitle(_translate("Janelinha", "Lista IGNORA"))
        self.groupBox.setTitle(_translate("Janelinha", "Barras a serem ignoradas"))
        self.lineEdit_nbarra.setWhatsThis(_translate("Janelinha", "Campo para inserção de barras na lista ignora. Apenas números inteiros positivos."))
        self.pushButton_incluir.setText(_translate("Janelinha", "Incluir"))
        self.pushButton_removerselec.setText(_translate("Janelinha", "Remover Seleção"))
        self.label.setText(_translate("Janelinha", "Nº da barra:"))
        self.listView.setWhatsThis(_translate("Janelinha", "Lista de barras que serão ignoradas na criação do arquivo Monitora.dat e da lista de contingências."))

