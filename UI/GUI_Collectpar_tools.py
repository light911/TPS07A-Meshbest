#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  3 16:31:21 2020

@author: blctl
"""


from xmlrpc.client import Boolean
import PyQt5
from PyQt5 import QtWidgets, uic, QtGui, QtCore

from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QGraphicsScene,QDialogButtonBox,QAbstractButton,QTableWidget
from PyQt5.QtGui import QPixmap,QPainter,QBrush,QPen,QColor,QFont
from PyQt5.QtCore import QRect,QPoint,QRectF,QPointF,Qt
from PyQt5.QtCore import QObject,QThread,pyqtSignal,pyqtSlot,QMutex,QMutexLocker
from UI.UI_NormalApply import Ui_Dialog as Ui_Dialog_NormalApply
from UI.UI_DoseApply import Ui_Dialog as Ui_Dialog_DoseApply
from UI.UI_DoseRelateApply import Ui_Dialog as Ui_Dialog_DoseRelateApply
from UI.UI_BoolApply import Ui_Dialog as Ui_Dialog_BoolApply
# qtCreatorFile = "/data/program/MeshBestGUI/UI/NormalApply.ui"  
# #print qtCreatorFile
# Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile) 

# qtCreatorFile2 = "/data/program/MeshBestGUI/UI/DoseApply.ui"  
# #print qtCreatorFile
# Ui_MainWindow2, QtBaseClass = uic.loadUiType(qtCreatorFile2) 

# qtCreatorFile3 = "/data/program/MeshBestGUI/UI/DoseRelateApply.ui"  

# Ui_MainWindow3, QtBaseClass = uic.loadUiType(qtCreatorFile3) 


     
class NormalApply(QtWidgets.QDialog, Ui_Dialog_NormalApply,QThread): 
    Done = pyqtSignal(float)
    def __init__(self):
        #reload init
        QtWidgets.QMainWindow.__init__(self)
        Ui_Dialog_NormalApply.__init__(self)
        self.setupUi(self)
#        self.title="item"
        self.DefaultValue=float()
#        print type(self.CollectInfo)
        
        self.initgui()
        self.initGuiEvent()
        
    def initgui(self):
        pass
    
    def initGuiEvent(self):
         self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.buttonBoxYesToAllClick)
         self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.buttonBoxCancelClick)
         
    def buttonBoxYesToAllClick(self):
        value = self.doubleSpinBox.value()
        self.Done.emit(value)
        self.close()
        
    def buttonBoxCancelClick(self):
        self.close()
    def updateDefaultValue(self,value):
        self.doubleSpinBox.setValue(value)
    def updateTitle(self,value):
        self.label.setText(value)
    def updateminValue(self,value):
        self.doubleSpinBox.setMinimum(value)

class DoseApply(QtWidgets.QDialog, Ui_Dialog_DoseApply,QThread): 
    DoseApplyDone = pyqtSignal(str,float)
    def __init__(self):
        #reload init
        QtWidgets.QMainWindow.__init__(self)
        Ui_Dialog_DoseApply.__init__(self)
        self.setupUi(self)
#        self.title="item"
        self.DefaultValue=float()
#        print type(self.CollectInfo)
        
        self.initgui()
        self.initGuiEvent()
        
    def initgui(self):
        pass
    
    def initGuiEvent(self):
         self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.buttonBoxYesToAllClick)
         self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.buttonBoxCancelClick)
         self.ConsiderOrder.currentIndexChanged.connect(self.ConsiderOrdervalueChanged)

    def ConsiderOrdervalueChanged(self):
        if self.ConsiderOrder.currentIndex() == 0:
            self.doubleSpinBox.setDisabled(True)
        else:
            self.doubleSpinBox.setEnabled(True)
        
    def buttonBoxYesToAllClick(self):
        value = self.doubleSpinBox.value()
        text = self.ConsiderOrder.currentText()
        self.DoseApplyDone.emit(text,value)
        self.close()
        
    def buttonBoxCancelClick(self):
        self.close()
    def updateDefaultValue(self,value):
        self.doubleSpinBox.setValue(value)
    def updateTitle(self,value):
        self.label.setText(value)
    def updateminValue(self,value):
        self.doubleSpinBox.setMinimum(value)
        
class DoseRelateApply(QtWidgets.QDialog, Ui_Dialog_DoseRelateApply,QThread): 
    DoseApplyDone = pyqtSignal(str,float)
    def __init__(self):
        #reload init
        QtWidgets.QMainWindow.__init__(self)
        Ui_Dialog_DoseRelateApply.__init__(self)
        self.setupUi(self)
#        self.title="item"
        self.DefaultValue=float()
#        print type(self.CollectInfo)
        
        self.initgui()
        self.initGuiEvent()
        
    def initgui(self):
        pass
    
    def initGuiEvent(self):
         self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.buttonBoxYesToAllClick)
         self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.buttonBoxCancelClick)
         
    def buttonBoxYesToAllClick(self):
        value = self.doubleSpinBox.value()
        text = self.ConsiderOrder.currentText()
        self.DoseApplyDone.emit(text,value)
        self.close()
        
    def buttonBoxCancelClick(self):
        self.close()
    def updateDefaultValue(self,value):
        self.doubleSpinBox.setValue(value)
    def updateTitle(self,value):
        self.label.setText(value)
    def updateConsiderOrder(self,value):
        self.ConsiderOrder.setCurrentIndex(value)
    def updateminValue(self,value):
        self.doubleSpinBox.setMinimum(value)        
    def changeNumberConsiderOrder(self,value):
        total = self.ConsiderOrder.count()+1
        for i in range(total):
#            print i
            self.ConsiderOrder.removeItem(total-i)
        if value == 3:
             self.ConsiderOrder.insertItems(1,['Don\'t keep Dose','Keep Dose &Change Range by Beamsize'])
        else:
             self.ConsiderOrder.insertItems(1,['Don\'t keep Dose'])

class BoolApply(QtWidgets.QDialog, Ui_Dialog_BoolApply,QThread): 
    Done = pyqtSignal(bool)
    def __init__(self):
        #reload init
        QtWidgets.QMainWindow.__init__(self)
        Ui_Dialog_NormalApply.__init__(self)
        self.setupUi(self)
#        self.title="item"
        self.DefaultValue=False
#        print type(self.CollectInfo)
        
        self.initgui()
        self.initGuiEvent()
        
    def initgui(self):
        pass
    
    def initGuiEvent(self):
         self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.buttonBoxYesToAllClick)
         self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.buttonBoxCancelClick)
         
    def buttonBoxYesToAllClick(self):
        #todo
        if self.comboBox.currentText() == 'True':
            value = True
        else:
            value = False
        self.Done.emit(value)
        self.close()
        
    def buttonBoxCancelClick(self):
        self.close()
    def updateDefaultValue(self,value):
        self.doubleSpinBox.setValue(value)
    def updateTitle(self,value):
        self.label.setText(value)
    def updateminValue(self,value):
        self.doubleSpinBox.setMinimum(value)            