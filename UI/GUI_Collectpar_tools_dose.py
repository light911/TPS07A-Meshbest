#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  3 16:31:21 2020

@author: blctl
"""


import PyQt5
from PyQt5 import QtWidgets, uic, QtGui, QtCore

from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QGraphicsScene,QDialogButtonBox,QAbstractButton,QTableWidget
from PyQt5.QtGui import QPixmap,QPainter,QBrush,QPen,QColor,QFont
from PyQt5.QtCore import QRect,QPoint,QRectF,QPointF,Qt
from PyQt5.QtCore import QObject,QThread,pyqtSignal,pyqtSlot,QMutex,QMutexLocker
from UI_DoseApply import Ui_Dialog as Ui_Dialog_DoseApply
# qtCreatorFile = "/data/program/MeshBestGUI/UI/DoseApply.ui"  
# #print qtCreatorFile
# Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile) 


class DoseApply(QtWidgets.QDialog, Ui_Dialog_DoseApply,QThread): 
    DoseApplyDone = pyqtSignal(int,float)
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
         
    def buttonBoxYesToAllClick(self):
        value = self.doubleSpinBox.value()
        
        self.DoseApplyDone.emit(value)
        self.close()
        
    def buttonBoxCancelClick(self):
        self.close()
    def updateDefaultValue(self,value):
        self.doubleSpinBox.setValue(value)
    def updateTitle(self,value):
        self.label.setText(value)