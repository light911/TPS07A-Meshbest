#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  2 14:45:55 2020

@author: blctl
"""

import PyQt5,sys,os
from PyQt5 import QtWidgets, uic, QtGui, QtCore

from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QGraphicsScene,QDialogButtonBox,QAbstractButton,QTableWidget
from PyQt5.QtGui import QPixmap,QPainter,QBrush,QPen,QColor,QFont
from PyQt5.QtCore import QRect,QPoint,QRectF,QPointF,Qt
from PyQt5.QtCore import QObject,QThread,pyqtSignal,pyqtSlot,QMutex,QMutexLocker

from UI.GUI_Collectpar_tools import NormalApply,DoseApply,DoseRelateApply,BoolApply
from UI.UI_CollectPar import Ui_Dialog
#from GUIMain_collectpar_tools_dose import DoseApply
# qtCreatorFile = "/data/program/MeshBestGUI/UI/CollectPar.ui"  
# #print qtCreatorFile
# Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile) 


class collectparui(QtWidgets.QDialog, Ui_Dialog,QThread): 
    Done = pyqtSignal()
    def __init__(self,beamlineinfo,view):
        #reload init
        QtWidgets.QMainWindow.__init__(self)
        Ui_Dialog.__init__(self)
        self.setupUi(self)
        self.view = view
        

        self.beamlineinfo = beamlineinfo
        # self.CollectInfo=CollectInfo
        self.CollectInfo = self.beamlineinfo[self.view]['collectInfo']
#      
        self.NormalApply = NormalApply()
        self.NormalApply.Done.connect(self.afterNormalApplyDone)
        self.DoseApply = DoseApply()
        self.DoseApply.DoseApplyDone.connect(self.afterDoseApplyDone)
        self.DoseRelateApply = DoseRelateApply()
        self.DoseRelateApply.DoseApplyDone.connect(self.afterDoseRelateApplyApplyDone)
        self.BoolApply = BoolApply()
        self.BoolApply.Done.connect(self.afterBoolApplyDone)
#        self.AvailableBeamSizes=[50,30,20,10,5]
#        self.Flux=[3.31E12,1.4E12,7.56E11,1.71E11,7.5E10]
        self.currentbeamsize=10
        self.currentAtten = 0
        self.sampleFlux=0
        self.initgui()
        self.initGuiEvent()
#        print self.beamlineinfo['Fulx']
        
    def initgui(self):
        self.InfoTable.setColumnCount(12)
        self.InfoTable.setColumnWidth(0,40)
        self.InfoTable.setColumnWidth(1,40)
        self.InfoTable.setColumnWidth(2,70)
        self.InfoTable.setColumnWidth(3,200)
        self.InfoTable.setColumnWidth(4,200)
        self.InfoTable.setColumnWidth(5,100)
        self.InfoTable.setColumnWidth(6,100)
        self.InfoTable.setColumnWidth(7,200)
        self.InfoTable.setColumnWidth(8,100)
        self.InfoTable.setColumnWidth(9,100)
        self.InfoTable.setColumnWidth(10,100)
        self.InfoTable.setColumnWidth(11,100)
        item0=QtWidgets.QTableWidgetItem("X")
        item1=QtWidgets.QTableWidgetItem("Y")
        item2=QtWidgets.QTableWidgetItem("BeamSize")
        item3=QtWidgets.QTableWidgetItem("Rought dose(byHoton) MGy")
        item4=QtWidgets.QTableWidgetItem("Absorbed Dose (MGy)")
        item5=QtWidgets.QTableWidgetItem("Atten%")
        item6=QtWidgets.QTableWidgetItem("Exposed Time")
        item7=QtWidgets.QTableWidgetItem("Total collect range")
        item8=QtWidgets.QTableWidgetItem("Frame width")
        item9=QtWidgets.QTableWidgetItem("Distance")
        item10=QtWidgets.QTableWidgetItem("CollectDone")
        item11=QtWidgets.QTableWidgetItem("Energy")
        
        self.InfoTable.setHorizontalHeaderItem(0,item0)
        self.InfoTable.setHorizontalHeaderItem(1,item1)
        self.InfoTable.setHorizontalHeaderItem(2,item2)
        self.InfoTable.setHorizontalHeaderItem(3,item3)
        self.InfoTable.setHorizontalHeaderItem(4,item4)
        self.InfoTable.setHorizontalHeaderItem(5,item5)
        self.InfoTable.setHorizontalHeaderItem(6,item6)
        self.InfoTable.setHorizontalHeaderItem(7,item7)
        self.InfoTable.setHorizontalHeaderItem(8,item8)
        self.InfoTable.setHorizontalHeaderItem(9,item9)
        self.InfoTable.setHorizontalHeaderItem(10,item10)
        self.InfoTable.setHorizontalHeaderItem(11,item11)

    def initGuiEvent(self):
#        self.buttons={}
#        buttonlist = self.buttonBox.buttons()
#        for button in buttonlist:
#            '''
#            Cancel
#            Reset
#            Apply
#            '''
#            name=button.text()
#            self.buttons[name] = button
            
        self.buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.buttonBoxResetClick)
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.buttonBoxApplyClick)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.buttonBoxCancelClick)
        # self.buttonBox.button(QDialogButtonBox.YesToAll).clicked.connect(self.buttonBoxYesToAllClick)
        self.ApplytoAll.clicked.connect(self.buttonBoxYesToAllClick)
#        RoughHeaderItem=self.InfoTable.horizontalHeaderItem(3)
#        self.InfoTable.mouseDoubleClickEvent=self.RoughDoseDoubleClick
#        RoughHeaderItem.mouseDoubleClickEvent.connect(self.RoughDoseDoubleClick)
#        self.buttonBox.clicked(QAbstractButton).connect(self.buttonBoxClick)   
#        QTableWidget.a
        
    def RoughDoseDoubleClick(self,item):
        print (item)
        print ("RoughDoseDoubleClick")
        
    def buttonBoxYesToAllClick(self):
        if len((self.InfoTable.selectedRanges())) == 0:
            return
  
        if len((self.InfoTable.selectedRanges())) > 1:
            SelectedColumn = self.InfoTable.selectedRanges()[0].leftColumn()
            for item in self.InfoTable.selectedRanges():
                if item.leftColumn() != SelectedColumn:
                    return

        for item in self.InfoTable.selectedRanges():
            if item.columnCount() > 1:
                return
            
        #Everything Fine
        self.SelectedColumn = self.InfoTable.selectedRanges()[0].leftColumn()

        self.SelectedRow=[]            
        for item in self.InfoTable.selectedRanges():
            for i in range(item.topRow(),item.bottomRow()+1):
                self.SelectedRow.append(i)

        if self.SelectedColumn == 0 or self.SelectedColumn == 1 or self.SelectedColumn == 2:
            return
        
        elif self.SelectedColumn == 3 or self.SelectedColumn == 4:
            self.DoseApply.updateDefaultValue(float(self.InfoTable.item(self.SelectedRow[0], self.SelectedColumn).text()))
            self.DoseApply.updateTitle(self.InfoTable.horizontalHeaderItem(self.SelectedColumn).text())
            self.DoseApply.show()
#            print "Change Dose"
        elif self.SelectedColumn == 5 or self.SelectedColumn == 6 or self.SelectedColumn == 7 or self.SelectedColumn == 8:
            self.DoseRelateApply.updateDefaultValue(float(self.InfoTable.item(self.SelectedRow[0], self.SelectedColumn).text()))
            self.DoseRelateApply.updateTitle(self.InfoTable.horizontalHeaderItem(self.SelectedColumn).text())
            if self.SelectedColumn == 5 :
                #atten
                #for atten/Time set default to don't keep dose
                self.DoseRelateApply.changeNumberConsiderOrder(2)
                self.DoseRelateApply.updateConsiderOrder(1)
                
                self.DoseRelateApply.updateminValue(0)
                
            elif self.SelectedColumn == 6:
                #for atten/Time set default to don't keep dose
                self.DoseRelateApply.changeNumberConsiderOrder(2)
                self.DoseRelateApply.updateConsiderOrder(1)
                
                minExposedTime = self.beamlineinfo["minExposedTime"]
                self.DoseRelateApply.updateminValue(minExposedTime)
            elif self.SelectedColumn == 8:
                #for Framewidth should set default to keep dose
                self.DoseRelateApply.changeNumberConsiderOrder(2)
                self.DoseRelateApply.updateConsiderOrder(0)
                self.DoseRelateApply.updateminValue(0.01)
            else:
                #for TotalCollectrange should set default to keep dose
                self.DoseRelateApply.changeNumberConsiderOrder(2)
                self.DoseRelateApply.updateConsiderOrder(0)
                self.DoseRelateApply.updateminValue(0.01)
            
            self.DoseRelateApply.show()
        elif self.SelectedColumn == 10:
            self.BoolApply.show()
        else:
            self.NormalApply.updateDefaultValue(float(self.InfoTable.item(self.SelectedRow[0], self.SelectedColumn).text()))
            self.NormalApply.updateTitle(self.InfoTable.horizontalHeaderItem(self.SelectedColumn).text())
#            print float(self.InfoTable.item(self.SelectedRow[0], self.SelectedColumn).text())
            self.NormalApply.show()
            print ("normal change")
        
    def afterNormalApplyDone(self,value):
        print ("got",value)
#        print self.beamlineinfo["Flux"]
        for row in self.SelectedRow :
            additem = QTableWidgetItem(str(value))
            self.InfoTable.setItem(row,self.SelectedColumn,additem)
            
        self.updateDosebyTableinfo()
    def afterBoolApplyDone(self,value):
        if value == True:
            updatevalue="True"
        else:
            updatevalue="False"
        for row in self.SelectedRow :
            additem = QTableWidgetItem(updatevalue)
            self.InfoTable.setItem(row,self.SelectedColumn,additem)

    def afterDoseApplyDone(self,text,value):
        if self.SelectedColumn == 3:
            DoseSelect=0#for Hotlton cal
        elif self.SelectedColumn == 4:
            DoseSelect=1#for absorbedDose=Holton*dosefactor
        else:
            DoseSelect=0#for Hotlton cal
            
        
        
        for row in self.SelectedRow :
            beamsize = self.CorrectBeamsize(float(self.InfoTable.item(row,2).text()))
            Energy = float(self.InfoTable.item(row,11).text())
            TotalCollectRange = float(self.InfoTable.item(row,7).text())
            Distance = float(self.InfoTable.item(row,9).text())
            Delta = float(self.InfoTable.item(row,8).text())
            Atten = float(self.InfoTable.item(row,5).text())
            ExpTime = float(self.InfoTable.item(row,6).text())
            RoughtDose = float(self.InfoTable.item(row,3).text())
            EstimateDose = float(self.InfoTable.item(row,4).text())
            dose = float(value)
            flux = self.predict_flux(self.currentbeamsize,self.currentAtten,self.sampleFlux,beamsize,self.beamlineinfo)
            newHdose,newAdose,newAtten,newExptime,newTrange,newDelta,NewDistance,NewEnergy=\
            self.calDosePar(text,DoseSelect,beamsize,dose,RoughtDose,EstimateDose,Atten,ExpTime,TotalCollectRange,Delta,Distance,Energy,flux)
            newHdoseitem=QTableWidgetItem(str(newHdose))
            newAdoseitem=QTableWidgetItem(str(newAdose))
            newAttenitem=QTableWidgetItem(str(newAtten))
            newExpTimeitem=QTableWidgetItem(str(newExptime))
            newTrangeitem=QTableWidgetItem(str(newTrange))
            newDeltaitem=QTableWidgetItem(str(newDelta))
            newDistanceitem=QTableWidgetItem(str(NewDistance))
            newEnergyitem=QTableWidgetItem(str(NewEnergy))


            self.InfoTable.setItem(row,3,newHdoseitem)
            self.InfoTable.setItem(row,4,newAdoseitem)
            self.InfoTable.setItem(row,5,newAttenitem)
            self.InfoTable.setItem(row,6,newExpTimeitem)
            self.InfoTable.setItem(row,7,newTrangeitem)
            self.InfoTable.setItem(row,8,newDeltaitem)
            self.InfoTable.setItem(row,9,newDistanceitem)
            self.InfoTable.setItem(row,11,newEnergyitem)


    def afterDoseRelateApplyApplyDone(self,text,value):
        if text == "Keep Dose" :
            
            for row in self.SelectedRow :
                if self.SelectedColumn == 7:
                    TotalCollectRange = float(value)
                    Atten = float(self.InfoTable.item(row,5).text())
                    ExpTime = float(self.InfoTable.item(row,6).text())
                    Delta = float(self.InfoTable.item(row,8).text())
                    mode = "Atten-Time"
                elif self.SelectedColumn == 5:
                    TotalCollectRange = float(self.InfoTable.item(row,7).text())
                    Atten = float(value)
                    ExpTime = float(self.InfoTable.item(row,6).text())
                    Delta = float(self.InfoTable.item(row,8).text())
                    mode = "TotalRange"
                elif self.SelectedColumn == 6:                
                    mode = "TotalRange"
                    TotalCollectRange = float(self.InfoTable.item(row,7).text())
                    Atten = float(self.InfoTable.item(row,5).text())
                    Delta = float(self.InfoTable.item(row,8).text())
                    ExpTime = float(value)
                elif self.SelectedColumn == 8:                
                    mode = "Atten-Time"
                    TotalCollectRange = float(self.InfoTable.item(row,7).text())
                    Atten = float(self.InfoTable.item(row,5).text())
                    ExpTime = float(self.InfoTable.item(row,6).text())
                    Delta = float(value)
                else:
                    mode = "Atten-Time"
                    TotalCollectRange = float(self.InfoTable.item(row,7).text())
                    Atten = float(self.InfoTable.item(row,5).text())
                    ExpTime = float(self.InfoTable.item(row,6).text())
                    Delta = float(self.InfoTable.item(row,8).text())
                
                print(self.SelectedColumn,mode,TotalCollectRange,Atten,ExpTime)
                beamsize = self.CorrectBeamsize(float(self.InfoTable.item(row,2).text()))
                Energy = float(self.InfoTable.item(row,11).text())               
                Distance = float(self.InfoTable.item(row,9).text())
                
                RoughtDose = float(self.InfoTable.item(row,3).text())
                EstimateDose = float(self.InfoTable.item(row,4).text())
                newHdose,newAdose,newAtten,newExptime,newTrange,newDelta,NewDistance,NewEnergy=\
                self.calkeepDoseRelatedPar(mode,beamsize,RoughtDose,EstimateDose,Atten,ExpTime,TotalCollectRange,Delta,Distance,Energy)
                newHdoseitem=QTableWidgetItem(str(newHdose))
                newAdoseitem=QTableWidgetItem(str(newAdose))
                newAttenitem=QTableWidgetItem(str(newAtten))
                newExpTimeitem=QTableWidgetItem(str(newExptime))
                newTrangeitem=QTableWidgetItem(str(newTrange))
                newDeltaitem=QTableWidgetItem(str(newDelta))
                newDistanceitem=QTableWidgetItem(str(NewDistance))
                newEnergyitem=QTableWidgetItem(str(NewEnergy))
    
    
                self.InfoTable.setItem(row,3,newHdoseitem)
                self.InfoTable.setItem(row,4,newAdoseitem)
                self.InfoTable.setItem(row,5,newAttenitem)
                self.InfoTable.setItem(row,6,newExpTimeitem)
                self.InfoTable.setItem(row,7,newTrangeitem)
                self.InfoTable.setItem(row,8,newDeltaitem)
                self.InfoTable.setItem(row,9,newDistanceitem)
                self.InfoTable.setItem(row,11,newEnergyitem)
                
           
        elif text == "Don't keep Dose":
            for row in self.SelectedRow :
                additem = QTableWidgetItem(str(value))
                self.InfoTable.setItem(row,self.SelectedColumn,additem)
        else:
            pass
        self.updateDosebyTableinfo()
        
    def buttonBoxResetClick(self):
        self.update()
        print("click")

    def buttonBoxApplyClick(self):
        self.UpdatBaseonTable()

        # self.CollectInfo = beamlineinfo[self.view]['collectInfo']

#        self.CollectInfo = self.NewCollectInfo
        # for j in range(len(self.CollectInfo)):
        #             self.CollectInfo.pop()
        # for i in range(len(self.NewCollectInfo)):
        #             self.CollectInfo.append(self.NewCollectInfo[i])
        self.beamlineinfo[self.view]['collectInfo'] = self.NewCollectInfo
        
        self.Done.emit()
        self.close()
        pass
        
    def buttonBoxCancelClick(self):
        self.close()
        pass
    
    def update(self):
#        print "1"
        
#        print "2"
#        print self.CollectInfo
#        print type(self.CollectInfo)
        self.CollectInfo = self.beamlineinfo[self.view]['collectInfo']
        self.InfoTable.setRowCount(len(self.CollectInfo))
        row = 0
#                print self.CollectInfo
        for item in self.CollectInfo:
            self.addHeaditem(row,item['ViewX'],\
                             item['ViewY'],\
                             item['BeamSize'],\
                             item['RoughtDose'],\
                             item['EstimateDose'],\
                             item['Atten'],\
                             item['ExpTime'],\
                             item['TotalCollectRange'],\
                             item['Delta'],\
                             item['Distance'],\
                             item['CollectDone'],\
                             item['Energy']
                             )
            row = row + 1

    def addHeaditem(self,row,item1,item2,*args):
        worditem = QTableWidgetItem(str(item1))
        countitem = QTableWidgetItem(str(item2))
        self.InfoTable.setItem(row,0,worditem)
        self.InfoTable.setItem(row,1,countitem)
        i=1
        for arg in args:
            i = i + 1
            additem = QTableWidgetItem(str(arg))
            if i == 3 :
#                if arg == True:
#                    cs=2
#                else:
#                    cs=0
#                additem.setCheckState(cs)
                self.InfoTable.setItem(row,i,additem)
            else:
                self.InfoTable.setItem(row,i,additem)



    def UpdatBaseonTable(self):
        self.CollectInfo = self.beamlineinfo[self.view]['collectInfo']
        self.NewCollectInfo=[]
        for i in range(self.InfoTable.rowCount()) :
            posdata={}
            posdata['ViewX']=float(self.InfoTable.item(i,0).text())
            posdata['ViewY']=float(self.InfoTable.item(i,1).text())
            # posdata['View2X']=float(self.InfoTable.item(i,0).text())
            # posdata['View2Y']=float(self.InfoTable.item(i,1).text())
            posdata['CollectOrder']=int(i+1)
            posdata['CollectType']=0
            

            # posdata['CollectDone']=self.CollectInfo[i]['CollectDone']
            if self.InfoTable.item(i,10).text() == 'True':
                posdata['CollectDone']=True
            else:
                posdata['CollectDone']=False
            
            posdata['FileName']= self.CollectInfo[i]['FileName']
            posdata['FolderName']=self.CollectInfo[i]['FolderName']
            posdata['Distance']=float(self.InfoTable.item(i,9).text())
            posdata['BeamSize']=self.CorrectBeamsize(float(self.InfoTable.item(i,2).text()))
            posdata['Energy']=float(self.InfoTable.item(i,11).text())
            posdata['TotalCollectRange']=float(self.InfoTable.item(i,7).text())
            
            phiView=(self.CollectInfo[i]['StartPhi']+self.CollectInfo[i]['EndPhi'])/2.0   
            posdata['StartPhi']=phiView - float(self.InfoTable.item(i,7).text())/2.0
            posdata['EndPhi']=phiView + float(self.InfoTable.item(i,7).text())/2.0
            
            posdata['Delta']=float(self.InfoTable.item(i,8).text())
            posdata['Atten']=float(self.InfoTable.item(i,5).text())
            posdata['ExpTime']=float(self.InfoTable.item(i,6).text())

            posdata['RoughtDose']=float(self.InfoTable.item(i,3).text())
            posdata['EstimateDose']=float(self.InfoTable.item(i,4).text())
            self.NewCollectInfo.append(posdata)
        
        
    def CorrectBeamsize(self,beamsize):
        newbeamsize=min(self.beamlineinfo["AvailableBeamSizes"], key=lambda x:abs(x-beamsize))
        return newbeamsize

            
    def RoughDose(self,flux,energy,time,beamsizex=50,beamsizey=50,beamtype="Square"):
        '''
        flux for photons/sec/um^2
        energy for ev
        time for sec
        beamize for um
        '''
        fluxden=flux/beamsizex/beamsizey
        wave=12398.0/energy
        dose=fluxden*time*wave*wave/2000.0/1e6
#        print dose
        return dose
    def calDosePar(self,mode,DoseSelect,beamsize,Dose,Hdose,Adose,Atten,ExposedTime,Trange,Framewidth,Distance,Energy,flux=None):
#        print self.beamlineinfo['Flux']
        # dose is Mgy, in cal should change to gy
        
        index = self.beamlineinfo["AvailableBeamSizes"].index(beamsize)
        if flux:
            pass#has flux input
        else:
            # flux = self.beamlineinfo['Flux'][str(beamsize)]
            flux = self.predict_flux(self.currentbeamsize,self.currentAtten,self.sampleFlux,beamsize,self.beamlineinfo)
        # dosefactor = self.beamlineinfo["DoseFactor"][index]
        # bestdose = self.beamlineinfo["BestDose"][index]
        # BeamFWHM = self.beamlineinfo["BeamFWHM"][index]
        dosefactor = 1
        bestdose = 10
        if beamsize == 1:
            BeamFWHM = 2*2
        else:
            BeamFWHM = beamsize*beamsize
        minExposedTime = self.beamlineinfo["minExposedTime"]
#        Dose = Dose *1e6
        fluxden=flux/BeamFWHM
        wave = 12398.0/Energy
        
        if DoseSelect  == 0:#for Hotlton cal
            Hdose = Dose 
            Adose = Hdose * dosefactor
        elif DoseSelect  == 1:#for absorbedDose=Holton*dosefactor
            Adose = Dose
            Hdose = Dose/dosefactor
            
            
        if mode == "BeamSize" :#opt for single crystal
            Adose = bestdose
            Hdose = Adose/dosefactor
            
            TimeCanUse = Hdose * 1e6 / fluxden /wave/wave*2000.0
            ExposedTime = TimeCanUse/(Trange/Framewidth)
            if ExposedTime < minExposedTime:
                Atten = (1.0 - (ExposedTime/minExposedTime)) * 100.0
                ExposedTime = minExposedTime
                
            else:
                Atten = 0
        elif mode == "Atten-Time":#fix Dose/Total range/Frame width
            TimeCanUse = Hdose * 1e6 / fluxden / wave / wave * 2000
            ExposedTime = TimeCanUse/(Trange/Framewidth)
            
#            print "cal========="
#            print TimeCanUse,ExposedTime,Hdose,fluxden,wave
            if ExposedTime < minExposedTime:
                Atten = (1.0 - (ExposedTime/minExposedTime)) * 100.0
                ExposedTime = minExposedTime
            else:
                Atten = 0
            pass
        elif mode == "TotalRange" :#fix Dose/frame width/atten/time
            TimeCanUse = Hdose * 1e6 / fluxden /wave/wave*2000
            Trange = TimeCanUse / (ExposedTime * (1-Atten/100.0)) * Framewidth  
        else:
            pass
#        print TimeCanUse,ExposedTime,Hdose,fluxden,wave
        return Hdose,Adose,Atten,ExposedTime,Trange,Framewidth,Distance,Energy
    def predict_flux(self,currentBeamsize,currentAtten,sampleFlux,Targetbeamsize,par):
        # currentBeamsize =  float(self.bluiceData['string']['currentBeamsize'])
        # currentAtten = self.bluiceData['motor']['attenuation']#float
        # sampleFlux = float(self.bluiceData['string']['sampleFlux'])
        
        tr = (100-currentAtten)/100
        if tr <= 0:
            FullFlux = 0
        else:
            FullFlux = sampleFlux/tr
        if FullFlux == 0:
            #no beam or something else
            #using default
            if currentBeamsize >= 30:
                FullFlux=par['Flux'][100]
            else:
                FullFlux=par['Flux'][currentBeamsize]
            pass
        else:
            pass
        
        if currentBeamsize >= 30:
            #current factor at max
            factor1 = par['Flux'][100]
        else:
            factor1 = par['Flux'][currentBeamsize]

        if Targetbeamsize >= 30:
            #Targetbeamsize factor at max
            factor2 = par['Flux'][100]
        else:
            factor2 = par['Flux'][Targetbeamsize]
        
        flux = FullFlux / factor1 * factor2
        # if FullFlux == 0:
        #     #no beam or something else
        #     #using default
        #     if currentBeamsize >= 20:
        #         FullFlux=par['Flux'][100]
        #     else:
        #         FullFlux=par['Flux'][1]
        #     pass
        # else:
        #     pass
        
        # if currentBeamsize >= 20 and Targetbeamsize >= 20:
        #     # same
        #     flux = FullFlux
        # elif currentBeamsize < 20 and Targetbeamsize >= 20:
        #     # FullFlux is smaller
        #     flux = FullFlux / par['Fluxfactor']
        # elif currentBeamsize < 20 and Targetbeamsize < 20:
        #     flux = FullFlux
        # elif currentBeamsize > 20 and Targetbeamsize < 20:
        #     flux = FullFlux * par['Fluxfactor']
        # else:
        #     #shoud not got to here
        #         flux =FullFlux
        # # print(f'sampleFlux={sampleFlux}, predict_flux={flux},currentatten={currentAtten},tr={tr}')
        return flux
    def calkeepDoseRelatedPar(self,mode,beamsize,Hdose,Adose,Atten,ExposedTime,Trange,Framewidth,Distance,Energy,flux=None):
#        print self.beamlineinfo['Flux']
        # dose is Mgy, in cal should change to gy
        
        index = self.beamlineinfo["AvailableBeamSizes"].index(beamsize)
        if flux:
            pass#has flux input
        else:
            # flux = self.beamlineinfo['Flux'][str(beamsize)]
            flux = self.predict_flux(self.currentbeamsize,self.currentAtten,self.sampleFlux,beamsize,self.beamlineinfo)
        # dosefactor = self.beamlineinfo["DoseFactor"][index]
        # bestdose = self.beamlineinfo["BestDose"][index]
        # BeamFWHM = self.beamlineinfo["BeamFWHM"][index]
        dosefactor = 1
        bestdose = 10
        if beamsize == 1:
            BeamFWHM = 2*2
        else:
            BeamFWHM = beamsize*beamsize
        minExposedTime = self.beamlineinfo["minExposedTime"]
#        Dose = Dose *1e6
        fluxden=flux/BeamFWHM
        wave = 12398.0/Energy
        if mode == "Atten-Time":#fix Dose/Total range/Frame width
            TimeCanUse = Hdose * 1e6 / fluxden / wave / wave * 2000
            ExposedTime = TimeCanUse/(Trange/Framewidth)
            
#            print "cal========="
#            print TimeCanUse,ExposedTime,Hdose,fluxden,wave
            if ExposedTime < minExposedTime:
                Atten = (1.0 - (ExposedTime/minExposedTime)) * 100.0
                ExposedTime = minExposedTime
            else:
                Atten = 0
            pass
        elif mode == "TotalRange" :#fix Dose/frame width/atten/time
            TimeCanUse = Hdose * 1e6 / fluxden /wave/wave*2000
            Trange = TimeCanUse / (ExposedTime * (1-Atten/100.0)) * Framewidth  
        elif mode == "Keep Dose &Change Range by Beamsize":
            #Total Range us only
            ##setup beamsize vs total range
            
            
            TimeCanUse = Hdose * 1e6 / fluxden / wave / wave * 2000
            ExposedTime = TimeCanUse/(Trange/Framewidth)
            
#            print "cal========="
#            print TimeCanUse,ExposedTime,Hdose,fluxden,wave
            if ExposedTime < minExposedTime:
                Atten = (1.0 - (ExposedTime/minExposedTime)) * 100.0
                ExposedTime = minExposedTime
            else:
                Atten = 0
            pass

        else:
            pass
#        print TimeCanUse,ExposedTime,Hdose,fluxden,wave
        return Hdose,Adose,Atten,ExposedTime,Trange,Framewidth,Distance,Energy
    
    def updateDose(self,beamsize,Atten,ExposedTime,Trange,Framewidth,Distance,Energy,flux=None):
#        print self.beamlineinfo['Flux']
        # dose is Mgy, in cal should change to gy
        
        index = self.beamlineinfo["AvailableBeamSizes"].index(beamsize)
        if flux:
            pass#has flux input
        else:
            # flux = self.beamlineinfo['Flux'][str(beamsize)]
            flux = self.predict_flux(self.currentbeamsize,self.currentAtten,self.sampleFlux,beamsize,self.beamlineinfo)
        # dosefactor = self.beamlineinfo["DoseFactor"][index]
        # bestdose = self.beamlineinfo["BestDose"][index]
        # BeamFWHM = self.beamlineinfo["BeamFWHM"][index]
        dosefactor = 1
        bestdose = 10
        if beamsize == 1:
            BeamFWHM = 2*2
        else:
            BeamFWHM = beamsize*beamsize
        minExposedTime = self.beamlineinfo["minExposedTime"]
#        Dose = Dose *1e6
        fluxden=flux/BeamFWHM
        wave = 12398.0/Energy
        FullbeamExptime=Trange/Framewidth * ExposedTime * (1-Atten/100.0)
        Hdose = fluxden * FullbeamExptime *wave*wave/2000/1e6
        Adose = Hdose * dosefactor
#        print "cal========="
#        print FullbeamExptime,ExposedTime,Hdose,fluxden,wave
        return Hdose,Adose
    
    def updateDosebyTableinfo(self):
        RowCount = self.InfoTable.rowCount()
        
        for row in range(RowCount):
            beamsize = self.CorrectBeamsize(float(self.InfoTable.item(row,2).text()))
            Energy = float(self.InfoTable.item(row,11).text())
            TotalCollectRange = float(self.InfoTable.item(row,7).text())
            Distance = float(self.InfoTable.item(row,9).text())
            Delta = float(self.InfoTable.item(row,8).text())
            Atten = float(self.InfoTable.item(row,5).text())
            ExpTime = float(self.InfoTable.item(row,6).text())
            
            newHdose,newAdose=self.updateDose(beamsize,Atten,ExpTime,TotalCollectRange,Delta,Distance,Energy)
            newHdoseitem=QTableWidgetItem(str(newHdose))
            newAdoseitem=QTableWidgetItem(str(newAdose))
            self.InfoTable.setItem(row,3,newHdoseitem)
            self.InfoTable.setItem(row,4,newAdoseitem)
    # def predict_flux(self,currentBeamsize,currentAtten,sampleFlux,Targetbeamsize,par):
    #     # currentBeamsize =  float(self.bluiceData['string']['currentBeamsize'])
    #     # currentAtten = self.bluiceData['motor']['attenuation']#float
    #     # sampleFlux = float(self.bluiceData['string']['sampleFlux'])
        
    #     tr = (100-currentAtten)/100
    #     if tr <= 0:
    #         FullFlux = 0
    #     else:
    #         FullFlux = sampleFlux/tr
    #     if FullFlux == 0:
    #         #no beam or something else
    #         #using default
    #         if currentBeamsize >= 20:
    #             FullFlux=par['Flux'][100]
    #         else:
    #             FullFlux=par['Flux'][1]
    #         pass
    #     else:
    #         pass

    #     if currentBeamsize >= 20 and Targetbeamsize >= 20:
    #         # same
    #         flux = FullFlux
    #     elif currentBeamsize < 20 and Targetbeamsize >= 20:
    #         # FullFlux is smaller
    #         flux = FullFlux / par['Fluxfactor']
    #     elif currentBeamsize < 20 and Targetbeamsize < 20:
    #         flux = FullFlux
    #     elif currentBeamsize > 20 and Targetbeamsize < 20:
    #         flux = FullFlux * par['Fluxfactor']
    #     else:
    #         #shoud not got to here
    #             flux =FullFlux
    #     return flux
if __name__ == '__main__':
    # from .. import Config
    from GUI_Collectpar_tools import NormalApply,DoseApply,DoseRelateApply
    import inspect
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.insert(0, parentdir) 
    import Config
    beamlineinfo =Config.Par

    if not QtWidgets.QApplication.instance():
        print("new")
        app = QtWidgets.QApplication(sys.argv)
    else:
        print("has old")
        app = QtWidgets.QApplication.instance()

    

    
    window=collectparui(123,beamlineinfo)
    window.show()
    sys.exit(app.exec_())
    # totaltime=0.1*10/0.5
    # test.RoughDose(6e12,12400,totaltime)
    