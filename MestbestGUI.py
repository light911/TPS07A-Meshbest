#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  9 10:37:32 2021

@author: blctl
"""
import argparse,sys,os,signal,math,time,traceback,getpass,re

from functools import partial
import beamlineinfo
import logsetup
import MeshbestClient
from PyQt5 import QtWidgets,QtGui,QtCore
# from PyQt5.QtCore import QRectF
from PyQt5.QtCore import QLineF, QPointF, QRectF, Qt,QSizeF, QSize
from PyQt5.QtGui import QPixmap,QPainter,QPen,QImage
from PyQt5.QtWidgets import QApplication, QMainWindow,QGraphicsScene,QGraphicsItem,QGraphicsRectItem,QGraphicsTextItem,QWidget,QMessageBox
from PyQt5.QtCore import QObject,QThread,pyqtSignal,pyqtSlot,QMutex,QMutexLocker,QEvent,QTimer,QPoint
from PyQt5.QtGui import QPainter,QBrush,QPen,QColor,QFont,QCursor
from pathlib import Path

import colorcet as cc
import copy,base64
import numpy as np
import json
from datetime import datetime
from TPS07A_meshbestGUI import Ui_MainWindow
from multiprocessing import Process, Queue, Manager, context
import bluice
import Config
import webimage
import variables
from MestbestAPITools import genZTableMap
import multiprocessing as mp
from UI.GUI_Collectpar import collectparui
from adxv import adxv
from pathlib import Path


# import faulthandler
# faulthandler.enable()

class MainUI(QMainWindow,Ui_MainWindow):
    def __init__(self,folder,key,user,stra,beamline,info,passwd,base64passwd):
        super(MainUI,self).__init__()
        signal.signal(signal.SIGINT, self.quit)
        signal.signal(signal.SIGTERM, self.quit)
        self.setupUi(self)
        self.pid = os.getpid()
        #setup par
        self.bluicekey = key
        self.user = user
        self.uid = os.getuid()
        self.gid = os.getgid()
        self.stra = stra
        self.passwd = passwd
        self.beamline = beamline
        self.beamlineinfo = beamlineinfo
        self.base64passwd = base64passwd
        self.numofclient = 0
        self.bluiceID = -1
        self.bluiceCounter = 0
        self.m1 = Manager()
        
        self.bluiceData={}
        # self.bluiceData = self.m1.dict()
        self.bluiceData['active'] = False
        self.bluiceData['motor'] = {}
        self.bluiceData['operation'] = {}
        self.bluiceData['string'] = {}
        self.bluiceData['ionchamber']={}
        self.bluiceData['shutter']={}
        self.bluiceData['dhs']={}
        # self.bluiceData['motor'][motorname]['pos']=float(pos)
        # self.bluiceData['motor'][motorname]['moving']=True
        # self.bluiceData['motor'][motorname]['unit']= mm
        # self.bluiceData['operation']['dhs']
        # self.bluiceData['operation']['moving']
        # self.bluiceData['operation']['id']
        # self.bluiceData['operation']['txt']
        # self.bluiceData['operation']['array']
        # self.bluiceData['string'][name]['dhs'] = dhs name
        # self.bluiceData['string'][name]['txt'] = pure txt
        # self.bluiceData['string'][name]['array'] = array type
        # self.bluiceData['string'][name]['state'] = 'unkonw'or 'normal'
        # self.bluiceData['ionchamber'][name]['dhs']
        # self.bluiceData['ionchamber'][name]['array']
        # self.bluiceData['shutter'][shuttername]['dhs']
        # self.bluiceData['shutter'][shuttername]['opened']
        # self.bluiceData['dhs'][dhsname]['online']
        
        self.RasterPar={}
        self.RasterPar['View1']={}
        self.RasterPar['View2']={}
        self.RasterPar['View1']['boxRectItemarray'] = None
        self.RasterPar['View1']['Textplotarray'] = None
        self.RasterPar['View1']['pos_text_array'] = []
        self.RasterPar['View1']['pos_circle_array'] = []
        self.RasterPar['View1']['movingindex'] = -1
        self.RasterPar['View1']['movingplot'] = False

        self.RasterPar['View2']['Textplotarray'] = None
        self.RasterPar['View2']['boxRectItemarray'] = None
        self.RasterPar['View2']['pos_text_array'] = []
        self.RasterPar['View2']['pos_circle_array'] = []
        self.RasterPar['View2']['movingindex'] = -1
        self.RasterPar['View2']['movingplot'] = False
        self.RasterRunstep=0
        self.RasterRuning = False
        
        self.View1flag = False
        # self.can_move_in_rastrview_flag = True

        self.DrawinRasterView1=False
        self.DrawinRasterView2=False
        self.motorchecklist=[]
        
        self.bluiceclientlists = {}
        # self.FluxClient = FluxClient()
        # self.FluxClient.updateFlux() 
        # self.beamlineinfo['Fulx'] = self.FluxClient.Flux
        
        # self.Par = m.dict()
        self.Par = {}
        self.state = self.m1.dict() 
        self.Par.update(Config.Par)
        self.collectPause =False
        init_meshbest_data = variables.init_meshbest_data()
                
        self.Par['View1'] = init_meshbest_data
        self.Par['View2'] = init_meshbest_data
        self.Par['View3'] = init_meshbest_data#for center by viwe12
        self.Par['UI_par'] = variables.init_uipar_data()
        statectrl ={}
        statectrl['RasterDone'] = False
        statectrl['AbletoStartRaster'] = False
        statectrl['reciveserverupdate'] = True
        statectrl['AbletoCollect'] = False
        self.Par['StateCtl']=statectrl

        self.timeformessageFromMeshbest=0

        home = str(Path.home())
        LOG_FILENAME = f'{home}/log/MebestGUI_pid{self.pid}.txt'
        logfolder = Path.home().joinpath("log")
        logfolder.mkdir(parents=True, exist_ok=True)

        self.logger = logsetup.getloger2('MestbestGUI',LOG_FILENAME,level = self.Par['Debuglevel'])

        temp = self.Par['View1']['collectInfo']
        self.collectparwindows = collectparui(self.Par,view='View3')
        self.collectparwindows1 = collectparui(self.Par,view='View1')
        self.collectparwindows2 = collectparui(self.Par,view='View2')
        self.collectparwindows1.Done.connect(self.aftercollectpardone1)
        self.collectparwindows2.Done.connect(self.aftercollectpardone2)

        # self.updatelistfor1 = True
        # self.updatelistfor2 = True
        self.Drawing=False
        self.logger.info(f'GUI PID = {self.pid}')
        self.adxv=adxv(self.Par)
        self.initGUI()
        # self.initGuiEvent()
        self.setBluice()
        time.sleep(1)
        self.setSampleimage()
        self.setHutchimage()
        self.setupMeshbest(LOG_FILENAME)
        self.timer = QTimer()
        self.abort = False
        self.convertlist = variables.convertlist()
        self.initGuiEvent()
        # self.checkRootFolder()
    def initGUI(self):
        self.setWindowState(QtCore.Qt.WindowMaximized)#max windows once active
        # self.scene = graphicsScene(self)
        self.scene = QGraphicsScene()
        self.sampleQPixmap = self.scene.addPixmap(QtGui.QPixmap())
        self.corsssize = self.SampleViedo.viewport().size().width() /2
        self.corss = CrossItem(self.corsssize)
        self.scene.addItem(self.corss)
        
        # self.corss.setPen(QPen(QColor('green'),1))
        # painter = QtGui.QPainter(self.corss)
        # painter.drawline(0,corsssize/2,corsssize,corsssize/2)#draw X
        # painter.drawline(corsssize/2,0,corsssize/2,corsssize)#draw Y
        # painter.end()
        # self.scene.setFocusItem(self.sampleQPixmap)
        #get mouse pos on sample image only?
        # self.sampleQPixmap.mousePressEvent = self.sampleQPixmapClicked
        self.SampleViedo.setScene(self.scene)
                
        self.SampleViedo.setCursor(QCursor(QtCore.Qt.ForbiddenCursor))
        self.SampleViedo.setToolTip('Active is needed')  
        # self.SampleViedo.setCursor(QCursor(QtCore.Qt.CrossCursor))
        
        #htuch video
        self.hutchvideo1scene = QGraphicsScene()
        self.hutchvideoPixmap1 =self.hutchvideo1scene.addPixmap(QtGui.QPixmap())
        self.hutchvideo1.setScene(self.hutchvideo1scene)
        # self.hutchvideo1.ViewportAnchor(2)

        self.hutchvideo2scene = QGraphicsScene()
        self.hutchvideoPixmap2 =self.hutchvideo2scene.addPixmap(QtGui.QPixmap())
        self.hutchvideo2.setScene(self.hutchvideo2scene)

        self.Rasterscene1 = QGraphicsScene()
        self.Rasterscene2 = QGraphicsScene()
        self.init_scence_item_in_view12()
        self.RasterStarted = False
        #set root path
        if self.RootPath == "":
            if self.beamline == "TPS07A":
                beamline = "07A/"
            else:
                beamline = "07A/"
            path = f"/data/{self.user}/"+datetime.now().strftime("%Y%m%d_")+beamline
            self.RootPath.setText(path)
        # self.RootPathforRaster = self.RootPath.text()
        # print(self.RootPath.text())
        self.collectAllpos_1.setEnabled(False)
        self.collectAllpos_2.setEnabled(False)
        pass
    
    def initGuiEvent(self):
        #click on active
        self.Active.clicked.connect(self.changeActive)
        self.debug_motor.clicked.connect(self.debug_motorclicked)
        self.debug_string.clicked.connect(self.debug_stringclicked)
        self.debug_operation.clicked.connect(self.debug_operationclicked)
        self.debug_shutter.clicked.connect(self.debug_shutterclicked)
        self.debug_raster.clicked.connect(self.debug_rasterclicked)
        self.debug_Debug.clicked.connect(self.debug_Debugclicked)
        
        self.Raster.clicked.connect(self.Rasterclicked)
        self.StartRaster.clicked.connect(self.StartRasterclicked)
        self.Centermode.clicked.connect(self.Centermodeclicked)
        self.Transfermode.clicked.connect(self.Transfermodeclicked)
        
        self.neg_10deg.clicked.connect(self.neg_10degclicked)
        self.neg_90deg.clicked.connect(self.neg_90degclicked)
        self.pos_10deg.clicked.connect(self.pos_10degclicked)
        self.pos_90deg.clicked.connect(self.pos_90degclicked)
        self.Zoom1.clicked.connect(self.Zoom1clicked)
        self.Zoom2.clicked.connect(self.Zoom2clicked)
        self.Zoom3.clicked.connect(self.Zoom3clicked)
        self.Zoom4.clicked.connect(self.Zoom4clicked)
        #move box
        self.viwe1_move_down.clicked.connect(self.viwe1_move_down_clicked)
        self.viwe1_move_up.clicked.connect(self.viwe1_move_up_clicked)
        self.viwe1_move_left.clicked.connect(self.viwe1_move_left_clicked)
        self.viwe1_move_right.clicked.connect(self.viwe1_move_right_clicked)
        self.viwe2_move_down.clicked.connect(self.viwe2_move_down_clicked)
        self.viwe2_move_up.clicked.connect(self.viwe2_move_up_clicked)
        self.viwe2_move_left.clicked.connect(self.viwe2_move_left_clicked)
        self.viwe2_move_right.clicked.connect(self.viwe2_move_right_clicked)

        #get mouse pos on sample video view
        self.SampleViedo.mousePressEvent = self.SampleViedoClicked
        
        # self.SampleViedo.mouseMoveEvent=self.SampleViedomoved
        self.RasterView1.mouseMoveEvent = self.DrawinRasterView1Move
        self.RasterView1.mousePressEvent = self.DrawinRasterView1Press
        self.RasterView1.mouseReleaseEvent = self.DrawinRasterView1Release
        #view12 change size
        self.RasterView1.resizeEvent = self.RasterView1Resize
        
        self.RasterView2.mouseMoveEvent = self.DrawinRasterView2Move
        self.RasterView2.mousePressEvent = self.DrawinRasterView2Press
        self.RasterView2.mouseReleaseEvent = self.DrawinRasterView2Release
        
        #parchange
        self.selectGridsize.currentIndexChanged.connect(self.selectGridsize_value_change)
        self.selectBeamsize.currentIndexChanged.connect(self.selectBeamsize_value_change)
        self.Distance.valueChanged.connect(self.Distance_value_change)
        
        self.Overlap_Select_1.currentIndexChanged.connect(self.Overlap_Select_1_value_change)
        self.Overlap_Select_2.currentIndexChanged.connect(self.Overlap_Select_2_value_change)
        
        self.RotationValue.valueChanged.connect(self.info_client_update_ui)
        self.selectROI.currentIndexChanged.connect(self.info_client_update_ui)
        self.select2scan.currentIndexChanged.connect(self.info_client_update_ui)
        
        self.List_number_1.valueChanged.connect(self.List_number_1_value_change)
        self.List_number_2.valueChanged.connect(self.List_number_2_value_change)
        self.view1_opacity.valueChanged.connect(self.view1_opacity_value_change)
        self.view2_opacity.valueChanged.connect(self.view2_opacity_value_change)
        self.view1_opacity.mouseReleaseEvent = self.view1_opacity_mouseReleaseEvent
        self.view2_opacity.mouseReleaseEvent = self.view2_opacity_mouseReleaseEvent

        self.DetailInfo1.clicked.connect(self.DetailInfo1_clicked)
        self.DetailInfo2.clicked.connect(self.DetailInfo2_clicked)

        self.ClearAll_1.clicked.connect(self.ClearAll_1_clicked)
        self.ClearAll_2.clicked.connect(self.ClearAll_2_clicked)

        self.collectAllpos_1.clicked.connect(self.collectAllpos_1_clicked)
        self.collectAllpos_2.clicked.connect(self.collectAllpos_2_clicked)

        self.MovePos_1.clicked.connect(self.make_EditPos_1_uncheck)
        self.EditPos_1.clicked.connect(self.make_MovePos_1_uncheck)
        self.MovePos_2.clicked.connect(self.make_EditPos_2_uncheck)
        self.EditPos_2.clicked.connect(self.make_MovePos_2_uncheck)

        self.updatelist_1.currentIndexChanged.connect(self.updatelist_1_update)
        self.updatelist_2.currentIndexChanged.connect(self.updatelist_2_update)

        self.RootPath.textChanged.connect(self.checkRootFolder)
        self.GetDefalutFolder.clicked.connect(self.GetDefalutFolder_clicked)
        self.Abort.clicked.connect(self.Abort_clicked)

        self.Focus_neg_l.clicked.connect(self.Focus_neg_l_clicked)
        self.Focus_neg_s.clicked.connect(self.Focus_neg_s_clicked)
        self.Focus_pos_s.clicked.connect(self.Focus_pos_s_clicked)
        self.Focus_pos_l.clicked.connect(self.Focus_pos_l_clicked)
        
        
        
        pass        
    def checkRootFolder(self,updateUI=True):
        if self.bluiceData['active']:
            currenttxt = self.RootPath.text()
            if currenttxt == None:
                self.GetDefalutFolder_clicked("Default path is not set!\n")
                return
            ans = re.match("/data/(.*)/(........)_07A/(.*)",currenttxt)
            print(ans)
            if ans:
                if ans[1] != str(self.user):
                    self.logger.critical(f"The user in default path is not same with current user name!")
                    self.GetDefalutFolder_clicked("The user in default path is not same with current user name!\n")
                    return
                else:
                    pass
            else:
                self.logger.critical(f"The format of default path is not accepted!")
                self.GetDefalutFolder_clicked("The format of default path is not accepted!\n")
                return
            if updateUI:
                self.update_ui_par_to_meshbest()
            pass
    def GetDefalutFolder_clicked(self,addtext = None):
        # QtGui.QMessageBox.critical
        
        self.GetDefalutFolder.setChecked(False)
        #set root path
        if self.beamline == "TPS07A":
            beamline = "07A/"
        else:
            beamline = "07A/"
        path = f"/data/{self.user}/"+datetime.now().strftime("%Y%m%d_")+beamline
        txt = f"Program want to change default folder!\nFrom\t{self.RootPath.text()}\t\nTo\t{path}\t\n"
        if addtext:
            txt =  f"{addtext}\n"+ txt
        mesbox = QMessageBox.question(self,"Change Data Folder",txt,QMessageBox.No,QMessageBox.Yes,)
        # print(mesbox)
        if mesbox == QMessageBox.No:
            pass
        elif mesbox ==QMessageBox.Yes:
            self.RootPath.setText(path)
        self.update_ui_par_to_meshbest()

        
    def make_EditPos_1_uncheck(self):
            self.EditPos_1.setChecked(False)
    def make_MovePos_1_uncheck(self):
            self.MovePos_1.setChecked(False)
    def make_EditPos_2_uncheck(self):
            self.EditPos_2.setChecked(False)
    def make_MovePos_2_uncheck(self):
            self.MovePos_2.setChecked(False)
    def updatelist_1_update(self):
        # print(f'{self.updatelist_1.isChecked()=}')
        # if self.updatelist_1.isChecked():
        #     self.updatelistfor1 = False
        #     self.updatelist_1.setStyleSheet('background-color: red')
        # else:#default
        #     self.updatelistfor1 = True
        #     self.updatelist_1.setStyleSheet("")
        if self.bluiceData['active']:
            self.update_ui_par_to_meshbest()
    def updatelist_2_update(self):
        # print(f'{self.updatelist_2.isChecked()=}')
        # if self.updatelist_2.isChecked():
        #     self.updatelistfor2 = False
        #     self.updatelist_2.setStyleSheet('background-color: red')
        # else:#default
        #     self.updatelistfor2 = True
        #     self.updatelist_2.setStyleSheet("")
        if self.bluiceData['active']:
            self.update_ui_par_to_meshbest()

    def collectAllpos_1_clicked(self):
        self.CollectdataSeq('View1')
        pass
    def collectAllpos_2_clicked(self):
        self.CollectdataSeq('View2')
        pass

    def ClearAll_1_clicked(self):
        self.clearcollectpos('View1')
        pass
    def ClearAll_2_clicked(self):
        self.clearcollectpos('View2')
        pass

    def DetailInfo1_clicked(self):
        self.collectparwindows1.show()
        self.collectparwindows1.beamlineinfo = self.Par
        currentBeamsize =  float(self.bluiceData['string']['currentBeamsize']['txt'])
        currentAtten = self.bluiceData['motor']['attenuation']['pos']#float
        sampleFlux = float(self.bluiceData['string']['sampleFlux']['txt'])
        self.collectparwindows1.currentAtten = currentAtten
        self.collectparwindows1.currentbeamsize = currentBeamsize
        self.collectparwindows1.sampleFlux = sampleFlux
        self.collectparwindows1.update()
    def DetailInfo2_clicked(self):
        currentBeamsize =  float(self.bluiceData['string']['currentBeamsize']['txt'])
        currentAtten = self.bluiceData['motor']['attenuation']['pos']#float
        sampleFlux = float(self.bluiceData['string']['sampleFlux']['txt'])
        self.collectparwindows2.show()
        self.collectparwindows2.beamlineinfo = self.Par
        self.collectparwindows2.currentAtten = currentAtten
        self.collectparwindows2.currentbeamsize = currentBeamsize
        self.collectparwindows2.sampleFlux = sampleFlux
        self.collectparwindows2.update()
        pass

    def aftercollectpardone1(self):
        # self.plotBestpos(View="View1")
        updatestr = f'plotBestpos_View1'
        self.send_RasterInfo_to_meshbest(updatestr)
        # self.send_RasterInfo_to_meshbest()

    def aftercollectpardone2(self):
        # self.plotBestpos(View="View2")
        updatestr = f'plotBestpos_View1'
        self.send_RasterInfo_to_meshbest(updatestr)
        # self.send_RasterInfo_to_meshbest()
    def setColor(self):
        self.Active.setStyleSheet('background-color: red')
        
    def DrawinRasterView1Press(self,event):
        
        if self.RasterView1QPixmap_ori.isNull():
            self.logger.debug(f'isNull,bypass')
            pass
        elif not self.bluiceData['active']:
            self.logger.debug(f'not active,bypass')
            pass
        elif self.RasterRuning :
            self.logger.debug(f'Raster Runing ,bypass')
            pass
        elif self.Par['StateCtl']['RasterDone'] :
            iseditpos = self.EditPos_1.isChecked() or self.MovePos_1.isChecked()
            if event.button() == 1 and not iseditpos:
                #for move sample
                self.logger.info(f'Click on view1 and want to move sample')
                try:
                    if self.bluiceData['motor']['sample_x']['moving']:
                        self.logger.info(f'samplex moving')
                    elif self.bluiceData['motor']['sample_y']['moving']:
                        self.logger.info(f'sampley moving')
                    elif self.bluiceData['motor']['sample_z']['moving']:
                        self.logger.info(f'samplez moving')
                    else:
                        self.move_in_rasterview(event.pos(),'View1')
                        pass
                        
                except Exception as e:
                    traceback.print_exc()
                    self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
                    self.logger.warning(f'Error:{e}')
            elif event.button() == Qt.RightButton and not iseditpos:#=2
                position = QPoint(event.pos().x(),event.pos().y())
                mouseX=self.RasterView1.mapToScene(position).x()
                mouseY=self.RasterView1.mapToScene(position).y()
                convert_pos = QPoint(mouseX,mouseY)
                print(position,mouseX,mouseY)#semm the same?
                findx=-1
                findy=-1
                for x,items in enumerate(self.RasterPar['View1']['boxRectItemarray']):
                        for y,item in enumerate(items):
                            if item.contains(convert_pos):
                                findx=x
                                findy=y
                print(findx,findy)
                frame = self.convertXYtoFrame(findx,findy,view1=True)
                # path=f'/data/blctl/20211027_07A/154945/RasterScanview1_0000_master.h5'
                path=f'{self.RootPath_2.text()}/RasterScanview1_0000_master.h5'
                try :
                    self.adxv.showimage(path,frame)
                except Exception as e:
                    traceback.print_exc()
                    self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
                    self.logger.warning(f'Error : {e}')
                pass
            elif self.MovePos_1.isChecked():
                position = QPoint(event.pos().x(),event.pos().y())
                self.movePosinCollectinfo(event,position,view='View1')
                pass
            elif self.EditPos_1.isChecked():
                position = QPoint(event.pos().x(),event.pos().y())
                if event.button() == 1 :
                    self.addPosinCollectinfo(position,view='View1')
                elif event.button() == 2 :
                    self.delcollectpos(position,view='View1')
                pass

        else:
            self.logger.debug(f'last event,got {event.button()=}')
            if event.button() == 1:
                self.view1box.setPen(QPen(QColor('red')))
                # self.view1_start = event.pos()
                self.view1_start = self.RasterView1.mapToScene(event.pos())
                # ori_view2_start = self.view2_start
                # self.view2_start = QPointF(ori_view2_start.x(),self.RasterView1.mapToScene(event.pos()).x())
                # print('test=====')
                # print (event.pos())
                # print (self.view1_start)
                self.view2box.setPen(QPen(QColor('red')))
                self.DrawinRasterView1=True
    
    def DrawinRasterView1Move(self,event):
        # print (self.view1box.boundingRect(),self.view1_start,self.view1_end)
        # print (event.button())
        
        if self.RasterView2QPixmap_ori.isNull():
            pass
        elif not self.bluiceData['active']:
            pass
        elif self.RasterRuning:
            pass
        elif self.DrawinRasterView1:
            self.view1_end = self.RasterView1.mapToScene(event.pos())
            x = self.view1_start.x() 
            y = self.view1_start.y() 
            w = self.RasterView1.mapToScene(event.pos()).x()-self.view1_start.x() 
            h = self.RasterView1.mapToScene(event.pos()).y()-self.view1_start.y() 
            # self.view1box.setPos(event.pos())
            self.view1box.setRect(x,y,w,h)
            #update view2 in ver also
            ratio = (self.RasterView2QPixmap_ori.width()/self.RasterView2QPixmap.boundingRect().width())
            x = self.RasterPar['View2']['box'].x() / ratio
            y = self.view1box.rect().y() #using view1 Ver pos
            # y = self.view1box.boundingRect().y() #using view1 Ver pos
            w = self.RasterPar['View2']['box'].width() / ratio
            h = self.view1box.rect().height() #using view1 height
            # h = self.view1box.boundingRect().height() #using view1 height
            self.view2box.setRect(x,y,w,h)
            # print('DrawinRasterView1Move=============')
            # print(self.view1box.boundingRect(),self.view2box.boundingRect())
        elif self.RasterPar['View1']['movingplot']:
            position = QPoint(event.pos().x(),event.pos().y())
            mouseX=self.RasterView1.mapToScene(position).x()
            mouseY=self.RasterView1.mapToScene(position).y()
            i = self.RasterPar['View1']['movingindex']
            newrect = self.RasterPar['View1']['pos_circle_array'][i].rect()
            newrect.moveCenter(QPoint(mouseX,mouseY))
            self.RasterPar['View1']['pos_circle_array'][i].setRect(newrect)
        else:
            pass
            
    def DrawinRasterView1Release(self,event):    
        if self.RasterView2QPixmap_ori.isNull():
            pass
        elif not self.bluiceData['active']:
            pass
        elif self.RasterRuning:
            pass
        elif self.Par['StateCtl']['RasterDone']:
            pass
        elif self.DrawinRasterView1:
            self.view1box.setPen(QPen(QColor('yellow')))
            #need to record retive pos and size
            # print(self.RasterView1.viewport().size())
            # print(self.RasterView1QPixmap())
            ratio = (self.RasterView1QPixmap_ori.width()/self.RasterView1QPixmap.boundingRect().width())
            x = self.view1box.rect().x() * ratio
            y = self.view1box.rect().y() * ratio
            w = self.view1box.rect().width() * ratio
            h = self.view1box.rect().height() * ratio
            # ratio = self.RasterView1QPixmap.size().x() /1280 
            self.RasterPar['View1']['box'] = QRectF(x,y,w,h)
            # print('DrawinRasterView1Release=============')
            # print(self.RasterPar['View1']['box'])
            # print(self.view1_start)
            self.view2box.setPen(QPen(QColor('yellow')))
            ratio = (self.RasterView2QPixmap_ori.width()/self.RasterView2QPixmap.boundingRect().width())
            # x = self.view2box.boundingRect().x() * ratio
            # y = self.view2box.boundingRect().y() * ratio
            # w = self.view2box.boundingRect().width() * ratio
            # h = self.view2box.boundingRect().height() * ratio
            x = self.view2box.rect().x() * ratio
            y = self.view2box.rect().y() * ratio
            w = self.view2box.rect().width() * ratio
            h = self.view2box.rect().height() * ratio
            self.RasterPar['View2']['box'] = QRectF(x,y,w,h)
            # self.plotbox()
            self.DrawinRasterView1=False
            self.send_RasterInfo_to_meshbest('plotbox')

        else:
             pass
             
    def DrawinRasterView2Press(self,event):
        if self.RasterView2QPixmap_ori.isNull():
            pass
        elif not self.bluiceData['active']:
            pass
        elif self.RasterRuning:
            pass
        elif self.Par['StateCtl']['RasterDone'] :
            iseditpos = self.EditPos_2.isChecked() or self.MovePos_2.isChecked()
            if event.button() == 1 and not iseditpos:
                self.logger.info(f'Click on view1 and want to move sample')
                try:
                    if self.bluiceData['motor']['sample_x']['moving']:
                        self.logger.info(f'samplex moving')
                    elif self.bluiceData['motor']['sample_y']['moving']:
                        self.logger.info(f'sampley moving')
                    elif self.bluiceData['motor']['sample_z']['moving']:
                        self.logger.info(f'samplez moving')
                    else:
                        self.move_in_rasterview(event.pos(),'View2')
                        pass
                        
                except Exception as e:
                    traceback.print_exc()
                    self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
                    self.logger.warning(f'Error:{e}')
            elif event.button() == Qt.RightButton and not iseditpos:#=2
                position = QPoint(event.pos().x(),event.pos().y())
                mouseX=self.RasterView2.mapToScene(position).x()
                mouseY=self.RasterView2.mapToScene(position).y()
                print(position,mouseX,mouseY)#semm the same?
                convert_pos = QPoint(mouseX,mouseY)
                findx=-1
                findy=-1
                for x,items in enumerate(self.RasterPar['View2']['boxRectItemarray']):
                        for y,item in enumerate(items):
                            if item.contains(convert_pos):
                                findx=x
                                findy=y
                print(findx,findy)
                frame = self.convertXYtoFrame(findx,findy,view1=False)
                # path=f'/data/blctl/20211027_07A/154945/RasterScanview1_0000_master.h5'
                path=f'{self.RootPath_2.text()}/RasterScanview2_0000_master.h5'
                try:
                    self.adxv.showimage(path,frame)
                except Exception as e:
                    traceback.print_exc()
                    self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
                    self.logger.warning(f'Error : {e}')
                pass
            elif self.MovePos_2.isChecked():
                position = QPoint(event.pos().x(),event.pos().y())
                self.movePosinCollectinfo(event,position,view='View2')
                pass
            elif self.EditPos_2.isChecked():
                position = QPoint(event.pos().x(),event.pos().y())
                if event.button() == 1 :
                    self.addPosinCollectinfo(position,view='View2')
                elif event.button() == 2 :
                    self.delcollectpos(position,view='View2')
        else:
            if event.button() == 1:
                self.view2box.setPen(QPen(QColor('red')))
                # self.view1_start = event.pos()
                self.view2_start = self.RasterView2.mapToScene(event.pos())
                # print('test=====')
                # print (event.pos())
                # print (self.view1_start)
                self.view1box.setPen(QPen(QColor('red')))
                self.DrawinRasterView2=True
    
    def DrawinRasterView2Move(self,event):
        # print (self.view1box.boundingRect(),self.view1_start,self.view1_end)
        # print (event.button())
        
        if self.RasterView2QPixmap_ori.isNull():
            pass
        elif not self.bluiceData['active']:
            pass
        elif self.RasterRuning:
            pass
        elif self.DrawinRasterView2:
            self.view2_end = self.RasterView1.mapToScene(event.pos())
            x = self.view2_start.x() 
            y = self.view2_start.y() 
            w = self.RasterView2.mapToScene(event.pos()).x()-self.view2_start.x() 
            h = self.RasterView2.mapToScene(event.pos()).y()-self.view2_start.y() 
            # self.view1box.setPos(event.pos())
            self.view2box.setRect(x,y,w,h)
            # print('DrawinRasterView1Release=============')
            
            #update view1 in ver also
            ratio = (self.RasterView1QPixmap_ori.width()/self.RasterView1QPixmap.boundingRect().width())
            x = self.RasterPar['View1']['box'].x() / ratio
            # y = self.view2box.boundingRect().y() #using view2 Ver pos
            y = self.view2box.rect().y() #using view2 Ver pos
            w = self.RasterPar['View1']['box'].width() / ratio
            # h = self.view2box.boundingRect().height() #using view2 height
            h = self.view2box.rect().height() #using view2 height
            self.view1box.setRect(x,y,w,h)
        elif self.RasterPar['View2']['movingplot']:
            position = QPoint(event.pos().x(),event.pos().y())
            mouseX=self.RasterView2.mapToScene(position).x()
            mouseY=self.RasterView2.mapToScene(position).y()
            i = self.RasterPar['View2']['movingindex']
            newrect = self.RasterPar['View2']['pos_circle_array'][i].rect()
            newrect.moveCenter(QPoint(mouseX,mouseY))
            self.RasterPar['View2']['pos_circle_array'][i].setRect(newrect)
        else:
            pass
            
    def DrawinRasterView2Release(self,event):    
        if self.RasterView2QPixmap_ori.isNull():
            pass
        elif not self.bluiceData['active']:
            pass
        elif self.RasterRuning:
            pass
        elif self.DrawinRasterView2:
            self.view2box.setPen(QPen(QColor('yellow')))
            #need to record retive pos and size
            # print(self.RasterView1.viewport().size())
            # print(self.RasterView1QPixmap())
            ratio = (self.RasterView2QPixmap_ori.width()/self.RasterView2QPixmap.boundingRect().width())
            x = self.view2box.rect().x() * ratio
            y = self.view2box.rect().y() * ratio
            w = self.view2box.rect().width() * ratio
            h = self.view2box.rect().height() * ratio
            # ratio = self.RasterView1QPixmap.size().x() /1280 
            self.RasterPar['View2']['box'] = QRectF(x,y,w,h)
            # print('DrawinRasterView2Release=============')
            # print(self.RasterPar['View2']['box'])
            # print(self.view2_start)
            
            self.view1box.setPen(QPen(QColor('yellow')))
            ratio = (self.RasterView1QPixmap_ori.width()/self.RasterView1QPixmap.boundingRect().width())
            x = self.view1box.rect().x() * ratio
            y = self.view1box.rect().y() * ratio
            w = self.view1box.rect().width() * ratio
            h = self.view1box.rect().height() * ratio
            self.RasterPar['View1']['box'] = QRectF(x,y,w,h)
            # self.plotbox()
            self.DrawinRasterView2=False
            self.send_RasterInfo_to_meshbest('plotbox')
        else:
            pass
    def getfolderforraster(self):
        root = self.RootPath.text()
        if root[-1:]=='/':
            new_path = root + f'{datetime.now().strftime("%H%M%S")}'
        else:
            new_path = root + f'/{datetime.now().strftime("%H%M%S")}'
        
        return new_path

    def Rasterclicked(self):
        #this is get new image and has new setup
        # self.RootPathforRaster = self.getfolderforraster()
        self.RootPath_2.setText(self.getfolderforraster())
        self.clear_Raster_scence_item()

        self.logger.info(f'Rasterclicked,Current phi={self.bluiceData["motor"]["gonio_phi"]["pos"]}')
        # self.can_move_in_rastrview_flag = False
        self.Overlap_Select_1.setCurrentIndex(1)#Grid
        self.Overlap_Select_2.setCurrentIndex(1)#Grid
        self.Par['StateCtl']['RasterDone'] = False
        self.Par['StateCtl']['reciveserverupdate'] = False
        #clear old box
        self.view1box.setRect(0, 0, 0, 0)
        self.view2box.setRect(0, 0, 0, 0)
        self.RasterPar['View1']['box'] = QRectF(0,0,0,0)
        self.RasterPar['View2']['box'] = QRectF(0,0,0,0)
        self.RasterPar['View1']['Dtable'] = None
        self.RasterPar['View2']['Dtable'] = None
        self.RasterPar['View1']['Ztable'] = None
        self.RasterPar['View2']['Ztable'] = None
        self.initScoreArray('View1')
        self.initScoreArray('View2')
        self.plotbox(True)
        # take current image
        self.logger.debug('take current angle picture(view1)')
        self.RasterView1QPixmap_ori,jpg = self.SampleImageServer.gethighresimage()
        self.RasterPar['View1']['gonio_phi']=self.bluiceData['motor']['gonio_phi']['pos']
        self.RasterPar['View1']['sample_x']=self.bluiceData['motor']['sample_x']['pos']
        self.RasterPar['View1']['sample_y']=self.bluiceData['motor']['sample_y']['pos']
        self.RasterPar['View1']['sample_z']=self.bluiceData['motor']['sample_z']['pos']
        self.RasterPar['View1']['align_z']=self.bluiceData['motor']['align_z']['pos']
        self.RasterPar['View1']['zoom']=self.bluiceData['motor']['camera_zoom']['pos']
        self.RasterPar['View1']['zoom_scale_x']=self.bluiceData['motor']['zoom_scale_x']['pos']
        self.RasterPar['View1']['zoom_scale_y']=self.bluiceData['motor']['zoom_scale_y']['pos']        
        self.RasterPar['View1']['size'] = self.RasterView1QPixmap_ori.size()
        self.RasterPar['View1']['jpg'] = jpg
        Path(self.RootPath_2.text()).mkdir(parents=True, exist_ok=True)
        path = f'{self.RootPath_2.text()}/crystalimage_1.jpg'
        self.RasterView1QPixmap_ori.save(path,'jpg')
        # with open(path, 'w') as outfile:
        #     outfile.write('jpg')
        # self.logger.warning(f'self.RasterPar = {self.RasterPar["View1"]}')
        
        #rotate 90 deg
        newpos = self.bluiceData['motor']['gonio_phi']['pos'] + 90
        # gtos_start_motor_move motorName destination
        command = f'gtos_start_motor_move gonio_phi {newpos}'
        # print(command)
        self.Qinfo["sendQ"].put(command)
        self.logger.info('Send first move')
        self.logger.debug(f'command:{command}')
        # wait=waitMotorStop(self.bluiceData, 'gonio_phi')
        # wait.AllStopAt.connect(self.Rasterclicked_step2)
        # wait.start()
        # self.motorchecklist=['gonio_phi']
        # self.motorposchecklist=[newpos]
        
        # self.timer.timeout.connect(self.waitPhiInPosUpdate)
        # # self.timer.timeout.connect(self.waitMotorStopUpdate)
        # self.timer.start(100)
        # self.timeractive = True
        # self.timer.singleShot(100,self.waitPhiInPosUpdate)
        # self.timer.singleShot(100,self.waitPhiInPosUpdate)
        motorchecklist=['gonio_phi']
        motorposchecklist=[newpos]
        callback = self.Rasterclicked_step2
        self.timer.singleShot(100,partial(self.waitMotorInPosUpdate,motorchecklist,motorposchecklist,callback))
        
        pass

    def Rasterclicked_step2(self):
        # self.timer.stop()
        self.logger.debug('take current angle picture(view2)')
        self.RasterView2QPixmap_ori,jpg = self.SampleImageServer.gethighresimage()
        self.RasterPar['View2']['gonio_phi']=self.bluiceData['motor']['gonio_phi']['pos']
        self.RasterPar['View2']['sample_x']=self.bluiceData['motor']['sample_x']['pos']
        self.RasterPar['View2']['sample_y']=self.bluiceData['motor']['sample_y']['pos']
        self.RasterPar['View2']['sample_z']=self.bluiceData['motor']['sample_z']['pos']
        self.RasterPar['View2']['align_z']=self.bluiceData['motor']['align_z']['pos']
        self.RasterPar['View2']['zoom']=self.bluiceData['motor']['camera_zoom']['pos']
        self.RasterPar['View2']['zoom_scale_x']=self.bluiceData['motor']['zoom_scale_x']['pos']
        self.RasterPar['View2']['zoom_scale_y']=self.bluiceData['motor']['zoom_scale_y']['pos']
        self.RasterPar['View2']['size'] = self.RasterView2QPixmap_ori.size()
        self.RasterPar['View2']['jpg'] = jpg
        
        path = f'{self.RootPath_2.text()}/crystalimage_2.jpg'
        self.RasterView2QPixmap_ori.save(path,'jpg')
        # with open(path, 'w') as outfile:
        #     outfile.write('jpg')
        # self.logger.warning(f'self.RasterPar = {self.RasterPar["View2"]}')
        # self.meshbest.sendCommandToMeshbest(('UpdateView2jpg',jpg))
        # self.send_RasterInfo_to_meshbest()
        # self.timeractive = False
        
        self.plotView12(True)
        # self.logger.warning(f'Full RasterPar = {self.RasterPar}')
        self.send_RasterInfo_to_meshbest('passvie')
        # self.timer.timeout.connect(self.waitMotorStopUpdate)
        # self.timer.start(100)
        # self.timeractive = True
        # self.timer.singleShot(100,self.waitMotorStopUpdate)
        motorchecklist=['gonio_phi']
        callback = self.Rasterclicked_step3
        self.timer.singleShot(100, partial(self.waitMotorStopUpdate_v2,motorchecklist,callback))
        
    def Rasterclicked_step3(self):
        
        # print("poslist")
        newpos = self.bluiceData['motor']['gonio_phi']['pos'] - 90
        # gtos_start_motor_move motorName destination
        command = f'gtos_start_motor_move gonio_phi {newpos}'
        self.Qinfo["sendQ"].put(command)
        # print(command)
        self.logger.info('move back')
        self.logger.debug(f'command:{command}')
        self.StartRaster.setEnabled(True)
        self.Par['StateCtl']['AbletoStartRaster'] = True
        self.update_ui_par_to_meshbest()
        self.Par['StateCtl']['reciveserverupdate'] = True

        
    def waitMotorStopUpdate(self):
        #old code not use anymore
        
            self.logger.debug(f'Checking {self.motorchecklist} moving state')
            checkarray = []
            posarray = []
            for motor in self.motorchecklist:
                checkarray.append(not (self.bluiceData['motor'][motor]['moving']))
                posarray.append(self.bluiceData['motor'][motor]['pos'])
            if all(checkarray):
                self.logger.debug('move done')
                self.timeractive = False
                self.timer.stop()
                self.Rasterclicked_step3()
            else:
                if self.abort:
                    self.logger.debug('Got Abort,stop wait waitMotorStopUpdate!')
                else:
                    self.timer.singleShot(100,self.waitMotorStopUpdate)
                
    def waitMotorStopUpdate_v2(self,motorchecklist,callback,callbackarg=(),checktime=100):
            self.logger.debug(f'Checking {motorchecklist} moving state')
            checkarray = []
            posarray = []
            for motor in motorchecklist:
                checkarray.append(not (self.bluiceData['motor'][motor]['moving']))
                posarray.append(self.bluiceData['motor'][motor]['pos'])
            if all(checkarray):
                self.logger.debug(f'motor:{motorchecklist} move done')
                self.logger.warning(f'callback {callback} with args{callbackarg}')
                callback(*callbackarg) #go tonext function  
            else:
                if self.abort:
                    self.logger.debug('Got Abort,stop wait waitMotorStopUpdate_v2!')
                else:
                    self.timer.singleShot(checktime, partial(self.waitMotorStopUpdate_v2,motorchecklist,callback,callbackarg,checktime))
                
    def waitMotorInPosUpdate(self,motorchecklist,motorposchecklist,callback,diffvalue=0.001):
            self.logger.debug(f'Check {motorchecklist} in pos {motorposchecklist}')
            checkarray = []
            posarray = []
            for motor,pos in zip(motorchecklist,motorposchecklist):
                if motor == 'gonio_phi':
                    diff1 = self.bluiceData['motor'][motor]['pos'] - pos
                    diff = abs((diff1+180) %360 - 180)
                else:
                    diff = abs(self.bluiceData['motor'][motor]['pos'] - pos)
                self.logger.debug(f'Check {motor} newis {pos},target is {self.bluiceData["motor"][motor]["pos"]}diff pos is {diff}')
                if  diff < diffvalue:
                    checkarray.append(True)
                else:
                    checkarray.append(False)
                posarray.append(self.bluiceData['motor'][motor]['pos'])
            if all(checkarray):
                self.logger.debug('All in posotion!')
                callback()
            else:
                if self.abort:
                    self.logger.debug('Got Abort,stop wait waitMotorInPosUpdate!')
                else:
                    self.timer.singleShot(100,partial(self.waitMotorInPosUpdate,motorchecklist,motorposchecklist,callback))

    def waitPhiInPosUpdate(self):
        #old code not use anymore
        # if self.timeractive:
            self.logger.debug(f'Check {self.motorchecklist} in pos {self.motorposchecklist}')
            checkarray = []
            posarray = []
            for motor,pos in zip(self.motorchecklist,self.motorposchecklist):
                if motor == 'gonio_phi':
                    diff = abs(self.bluiceData['motor'][motor]['pos'] - pos) % 180
                else:
                    diff = abs(self.bluiceData['motor'][motor]['pos'] - pos)
                self.logger.debug(f'Check {motor} diff pos is {diff}')
                if  diff<0.001:
                    checkarray.append(True)
                else:
                    checkarray.append(False)
                posarray.append(self.bluiceData['motor'][motor]['pos'])
            if all(checkarray):
                self.logger.debug('All in posotion!')
                # self.timeractive = False
                # self.timer.stop()
                # self.logger.info('wait 100ms')
                # QTimer.singleShot(100, self.Rasterclicked_step2)
                self.Rasterclicked_step2()
            else:
                if self.abort:
                    self.logger.debug('Got Abort,stop wait waitPhiInPosUpdate!')
                else:
                    self.timer.singleShot(100,self.waitPhiInPosUpdate)
        # else:
        #      self.logger.debug('timer inactive!')
    def waitOperationDone(self,oplist,callback,callbackarg=(),checktime=100):
        '''
        

        Parameters
        ----------
        oplist : List
            the operation to check is done.
        callback : Function
            The Function to do after operation is done.
        callbackarg : args
            args for Function 

        Returns
        -------
        None.

        '''
        self.logger.debug(f'Checking {oplist} Operation state')
        checkarray = []
        for op in oplist:
            checkarray.append(not (self.bluiceData['operation'][op]['moving']))
        if all(checkarray):
            self.logger.debug(f'op:{oplist} move done')
            #go to next function
            self.logger.warning(f'callback {callback} with args{callbackarg}')
            callback(*callbackarg)
        else:
            if self.abort:
                self.logger.debug('Got Abort,stop wait waitOperationDone!')
            else:
                self.timer.singleShot(checktime, partial(self.waitOperationDone,oplist,callback,callbackarg,checktime))
        pass
    def Centermodeclicked(self):
        command = f'gtos_start_motor_move change_mode 0'
        self.Qinfo["sendQ"].put(command)
        
    def Transfermodeclicked(self):
        command = f'gtos_start_motor_move change_mode 3'
        self.Qinfo["sendQ"].put(command)
    def Zoom1clicked(self):
        command = f'gtos_start_motor_move camera_zoom 1'
        self.Qinfo["sendQ"].put(command)
    def Zoom2clicked(self):
        # print("zoom2 clicked")
        command = f'gtos_start_motor_move camera_zoom 2'
        self.Qinfo["sendQ"].put(command)    
    def Zoom3clicked(self):
        command = f'gtos_start_motor_move camera_zoom 3'
        self.Qinfo["sendQ"].put(command)
    def Zoom4clicked(self):
        command = f'gtos_start_motor_move camera_zoom 4'
        self.Qinfo["sendQ"].put(command)    
    def neg_10degclicked(self):
        newpos = self.bluiceData['motor']['gonio_phi']['pos'] - 10
        # gtos_start_motor_move motorName destination
        command = f'gtos_start_motor_move gonio_phi {newpos}'
        self.Qinfo["sendQ"].put(command)
    def neg_90degclicked(self):
        newpos = self.bluiceData['motor']['gonio_phi']['pos'] - 90
        # gtos_start_motor_move motorName destination
        command = f'gtos_start_motor_move gonio_phi {newpos}'
        self.Qinfo["sendQ"].put(command)
    def pos_10degclicked(self):
        newpos = self.bluiceData['motor']['gonio_phi']['pos'] + 10
        # gtos_start_motor_move motorName destination
        command = f'gtos_start_motor_move gonio_phi {newpos}'
        self.Qinfo["sendQ"].put(command)
    def pos_90degclicked(self):
        newpos = self.bluiceData['motor']['gonio_phi']['pos'] + 90
        # gtos_start_motor_move motorName destination
        command = f'gtos_start_motor_move gonio_phi {newpos}'
        self.Qinfo["sendQ"].put(command)
        
    def SampleViedoClicked(self,event)    :
        self.logger.info(f'Click on Image Sample Viedo')
        # print("--------SampleViedoClicked")
        # print(f'button={event.button()} ,posx={event.pos().x()},\
              # posy={event.pos().y()}')
        # print(f'SampleViedo pos={self.SampleViedo.pos()}')
        # print(f'Scene pos={self.scene.pos()}')
        try:
            if self.bluiceData['operation']['moveSample']['moving'] == False:
                movesample = False
            else:
                movesample = True
        except:
            movesample = False
        # print (movesample)
        try:
            # print (event.button(),self.bluiceData['active'],movesample)
            # print(((event.button() == 1 & self.bluiceData['active'] == True) & movesample == False))
            # print((event.button() == 1 & self.bluiceData['active'] == True))
            # print((event.button() == 1 & self.bluiceData['active'] == True))
            
            if event.button() == 1 and self.bluiceData['active'] == True and movesample == False:#right click
            
                x = self.SampleViedo.mapToScene(event.pos()).x()#ok one
                y = self.SampleViedo.mapToScene(event.pos()).y()
                # print('get pos=',x,y)
                lx = self.sampleQPixmap.boundingRect().right()
                ly = self.sampleQPixmap.boundingRect().bottom()
                # print('Full range',lx,ly)
                # print('Resized image =',self.sampleQPixmapSize)
                centerx = self.sampleQPixmap.boundingRect().center().x()
                centery = self.sampleQPixmap.boundingRect().center().y()
                
                correctX = self.correctNumber(x,0,lx)
                correctY = self.correctNumber(y,0,ly)
                # print('After coeect=',correctX,correctY)
                
                detX = correctX - centerx 
                dety = correctY - centery
                
                # print('Det to center',detX,dety)
                
                #movexy tunit = pixel
                movex = -1*self.oriImageSize.width()*detX/lx
                movey = -1*self.oriImageSize.height()*dety/ly
                # command = ('gtos_start_operation','moveSample',str(movex),str(movey))
                command = f'gtos_start_operation moveSample {self.bluiceID}.{self.bluiceCounter} {movex} {movey}'
                self.bluiceCounter += 1
                
                self.SampleViedo.setCursor(QCursor(QtCore.Qt.ForbiddenCursor))
                self.SampleViedo.setToolTip('Sample XYZ is moving')
                # print(command)
                # print(f'bluce id = {self.bluiceID}')
            
                ratio = self.oriImageSize.width()/lx
                angle = self.bluiceData['motor']['gonio_phi']['pos']
                samplex = self.bluiceData['motor']['sample_x']['pos']
                sampley = self.bluiceData['motor']['sample_y']['pos']
                samplez = self.bluiceData['motor']['sample_z']['pos']
                zoomx = self.bluiceData['motor']['zoom_scale_x']['pos']
                zoomy = self.bluiceData['motor']['zoom_scale_y']['pos']
                self.calXYZbaseonCAMCenter(x*ratio,y*ratio,angle,zoomx,zoomy,samplex,sampley,samplez)    
            
            
            
                self.Qinfo["sendQ"].put(command)
                
 
                # print(self.SampleViedo.mapFromScene(event.pos()))
                # self.sampleQPixmap.mousePressEvent(event)
                # print(f'viewport = {self.SampleViedo.viewport().size()}')
                

        except Exception as e:
            traceback.print_exc()
            self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
            self.logger.warning(f'Error : {e}')
        if  event.button() == 2:#left clieck
            #for test
            print('motor=================')
            print(self.bluiceData['motor'])
            print('string=================')
            print(self.bluiceData['string'])
            print('operation=================')
            print(self.bluiceData['operation'])
            print('ion chamber=================')
            print(self.bluiceData['ionchamber'])
            print('shutter=================')
            print(self.bluiceData['shutter'])
            print('dhs=================')
            print(self.bluiceData['dhs'])
    def correctNumber(self,num,low,high):
        # print(f'num={num},low={low},high={high}')
        if num < low:
            num = low
        elif num > high:
            num = high
        
        return num
    def move_in_rasterview(self,pos,view='View1'):
        self.logger.warning(f'{pos=}')
        if view == 'View1':
            RasterView = self.RasterView1
            RasterViewQPixmap_ori = self.RasterView1QPixmap_ori
            view2 = 'View2'
            r=1
        else:
            RasterView = self.RasterView2
            RasterViewQPixmap_ori = self.RasterView2QPixmap_ori
            view2 = 'View1'
            r=2
        # par = self.Par[view] #View1 / View2
        par = self.RasterPar[view] #View1 / View2
        par2 = self.RasterPar[view2] #90 deg apart par

        Xpix = RasterView.mapToScene(pos).x()
        Ypix = RasterView.mapToScene(pos).y()
        ratio = self.getViewRatio(r)
        Xpix = Xpix *ratio 
        Ypix = Ypix *ratio
        #using same size of original picture
        #using mark we have now
        cross = self.RasterPar[view]['CrossItem']
        offx,offy = cross.getoffset()
        # x,y = cross.pos()
        x = float(cross.x())
        y = float(cross.y())
        centerX = x + offx
        centerY = y + offy
        centerX = centerX * ratio
        centerY = centerY * ratio
        #Current motor pos
        samplex = self.bluiceData['motor']['sample_x']['pos']
        sampley = self.bluiceData['motor']['sample_y']['pos']
        samplez = self.bluiceData['motor']['sample_z']['pos']
        #current center
        # refx = par['sample_x']
        # refy = par['sample_y']
        # refz = par['sample_z']
        angle = par['gonio_phi']
        zoomx = par['zoom_scale_x']
        zoomy = par['zoom_scale_y']
        
        detX_pixel = Xpix - centerX
        detY_pixel = Ypix - centerY
        targetZ = samplez + (zoomy * detY_pixel)/1000
        targetCX = sampley + (detX_pixel*zoomx * math.sin(angle/180*math.pi))/1000 #1000 for um to mm 
        targetCY = samplex + (detX_pixel*zoomy * math.cos(angle/180*math.pi))/1000

        self.logger.info(f'')
        command = f'gtos_start_motor_move sample_x {targetCY}'
        # print(command)
        self.Qinfo["sendQ"].put(command)
        command = f'gtos_start_motor_move sample_y {targetCX}'
        # print(command)
        self.Qinfo["sendQ"].put(command)
        command = f'gtos_start_motor_move sample_z {targetZ}'
        # print(command)
        self.Qinfo["sendQ"].put(command)
        pass

    def setSampleimage(self):
        
        self.SampleImageServer = webimage.image(self.Par)
        self.SampleImageServer.updateimage.connect(self.updateimage)
        self.SampleImageServer.start()

    def setHutchimage(self):
        self.Hutchimage1_Server = webimage.image(self.Par)
        self.Hutchimage1_Server.ip = '10.7.1.105'
        self.Hutchimage1_Server.port = 80
        self.Hutchimage1_Server.path = '/snap'
        self.Hutchimage1_Server.updateimage.connect(self.updateHutchimage1)
        self.Hutchimage1_Server.start()
        self.Hutchimage2_Server = webimage.image(self.Par)
        self.Hutchimage2_Server.ip = '10.7.1.106'
        self.Hutchimage2_Server.port = 80
        self.Hutchimage2_Server.path = '/snap'
        self.Hutchimage2_Server.updateimage.connect(self.updateHutchimage2)
        self.Hutchimage2_Server.start()
    
    def updateUI(self):
       for motor in  self.bluiceData['motor']:
            if motor == 'camera_zoom':
                # self.logger.info(f'camera_zoom==={self.bluiceData["motor"][motor]["pos"]}')
                if self.bluiceData['motor'][motor]['pos'] == 1:
                    # self.logger.info(f'Zoom1')
                    self.Zoom1.setStyleSheet('background-color: lightgreen')
                    self.Zoom2.setStyleSheet('')
                    self.Zoom3.setStyleSheet('')
                    self.Zoom4.setStyleSheet('')   
                    self.Zoom1.setEnabled(False)
                    self.Zoom2.setEnabled(True)
                    self.Zoom3.setEnabled(True)
                    self.Zoom4.setEnabled(True)
                elif self.bluiceData['motor'][motor]['pos'] == 2:
                    self.Zoom1.setStyleSheet('')
                    self.Zoom2.setStyleSheet('background-color: lightgreen')
                    self.Zoom3.setStyleSheet('')
                    self.Zoom4.setStyleSheet('') 
                    self.Zoom1.setEnabled(True)
                    self.Zoom2.setEnabled(False)
                    self.Zoom3.setEnabled(True)
                    self.Zoom4.setEnabled(True)
                elif self.bluiceData['motor'][motor]['pos'] == 3:
                    self.Zoom1.setStyleSheet('')
                    self.Zoom2.setStyleSheet('')
                    self.Zoom3.setStyleSheet('background-color: lightgreen')
                    self.Zoom4.setStyleSheet('')   
                    self.Zoom1.setEnabled(True)
                    self.Zoom2.setEnabled(True)
                    self.Zoom3.setEnabled(False)
                    self.Zoom4.setEnabled(True)
                elif self.bluiceData['motor'][motor]['pos'] == 4:
                    self.Zoom1.setStyleSheet('')
                    self.Zoom2.setStyleSheet('')
                    self.Zoom3.setStyleSheet('')
                    self.Zoom4.setStyleSheet('background-color: lightgreen') 
                    self.Zoom1.setEnabled(True)
                    self.Zoom2.setEnabled(True)
                    self.Zoom3.setEnabled(True)
                    self.Zoom4.setEnabled(False)
                else:
                    pass
            if motor == 'change_mode':
                        # [ 0] Centring
                        # [ 1] BeamLocation
                        # [ 2] DataCollection
                        # [ 3] Transfer
                        # [ 4] Unknown
                if self.bluiceData['motor'][motor]['pos'] == 0 :
                    self.Centermode.setStyleSheet('background-color: lightgreen')
                    self.Transfermode.setStyleSheet('')
                    self.Centermode.setEnabled(False)
                    self.Transfermode.setEnabled(True)
                elif self.bluiceData['motor'][motor]['pos'] == 1 :
                    self.Centermode.setStyleSheet('')
                    self.Transfermode.setStyleSheet('')
                    self.Centermode.setEnabled(True)
                    self.Transfermode.setEnabled(True)
                elif self.bluiceData['motor'][motor]['pos'] == 2 :
                    self.Centermode.setStyleSheet('')
                    self.Transfermode.setStyleSheet('')
                    self.Centermode.setEnabled(True)
                    self.Transfermode.setEnabled(True)
                elif self.bluiceData['motor'][motor]['pos'] == 3 :
                    self.Centermode.setStyleSheet('')
                    self.Transfermode.setStyleSheet('background-color: lightgreen')
                    self.Centermode.setEnabled(True)
                    self.Transfermode.setEnabled(False)
                else :
                    self.Centermode.setStyleSheet('')
                    self.Transfermode.setStyleSheet('')
                    self.Centermode.setEnabled(False)
                    self.Transfermode.setEnabled(False)
            if motor == 'gonio_phi':
                setstate = not self.bluiceData['motor']['gonio_phi']['moving']
                # print(self.bluiceData['motor']['gonio_phi']['moving'])
                # print(setstate)
                self.neg_10deg.setEnabled(setstate)
                self.neg_90deg.setEnabled(setstate)
                self.pos_10deg.setEnabled(setstate)
                self.pos_90deg.setEnabled(setstate)
                # self.Focus_neg_l.setEnabled(setstate)
                # self.Focus_neg_s.setEnabled(setstate)
                # self.Focus_pos_s.setEnabled(setstate)
                # self.Focus_pos_l.setEnabled(setstate)
            elif motor == 'CentringTableFocus':
                setstate = not self.bluiceData['motor']['CentringTableFocus']['moving']
                self.Focus_neg_l.setEnabled(setstate)
                self.Focus_neg_s.setEnabled(setstate)
                self.Focus_pos_s.setEnabled(setstate)
                self.Focus_pos_l.setEnabled(setstate)
                pass
            else:
                pass
    
       if not self.bluiceData['active']:
            self.Zoom1.setEnabled(False)
            self.Zoom2.setEnabled(False)
            self.Zoom3.setEnabled(False)
            self.Zoom4.setEnabled(False)
            self.Centermode.setEnabled(False)
            self.Transfermode.setEnabled(False)
            self.neg_10deg.setEnabled(False)
            self.neg_90deg.setEnabled(False)
            self.pos_10deg.setEnabled(False)
            self.pos_90deg.setEnabled(False)
            self.Autocenter.setEnabled(False)
            self.Raster.setEnabled(False)
            self.StartRaster.setEnabled(False)
            self.Focus_neg_l.setEnabled(False)
            self.Focus_neg_s.setEnabled(False)
            self.Focus_pos_s.setEnabled(False)
            self.Focus_pos_l.setEnabled(False)
            self.DetailInfo1.setEnabled(False)
            self.DetailInfo2.setEnabled(False)

            self.ClearAll_1.setEnabled(False)
            self.EditPos_1.setEnabled(False)
            self.MovePos_1.setEnabled(False)

            self.ClearAll_2.setEnabled(False)
            self.EditPos_2.setEnabled(False)
            self.MovePos_2.setEnabled(False)
            self.GetDefalutFolder.setEnabled(False)

            uiparlists,uiindexlists,uitextlists,uicheckablelist = variables.ui_par_lists()
            for item in uiparlists:
                uiitem = getattr(self,item)
                uiitem.setEnabled(False)
            for item in uiindexlists:
                uiitem = getattr(self,item)
                uiitem.setEnabled(False)
            for item in uitextlists:
                uiitem = getattr(self,item)
                uiitem.setEnabled(False)
            for item in uicheckablelist:
                uiitem = getattr(self,item)
                uiitem.setEnabled(False)

       else:
            self.DetailInfo1.setEnabled(True)
            self.DetailInfo2.setEnabled(True)
            self.ClearAll_1.setEnabled(True)
            self.EditPos_1.setEnabled(True)
            self.MovePos_1.setEnabled(True)

            self.ClearAll_2.setEnabled(True)
            self.EditPos_2.setEnabled(True)
            self.MovePos_2.setEnabled(True)
            self.GetDefalutFolder.setEnabled(True)
           # self.Raster.setEnabled(True)
           # self.StartRaster.setEnabled(True)
            uiparlists,uiindexlists,uitextlists,uicheckablelist = variables.ui_par_lists()
            for item in uiparlists:
               uiitem = getattr(self,item)
               uiitem.setEnabled(True)
            for item in uiindexlists:
               uiitem = getattr(self,item)
               uiitem.setEnabled(True)
            for item in uitextlists:
               uiitem = getattr(self,item)
               uiitem.setEnabled(True)
            for item in uicheckablelist:
               uiitem = getattr(self,item)
               uiitem.setEnabled(True)
            pass
       self.reposition_view_cross()
                    
    def updateimage(self,image):
        self.oriImageSize=image.size()
        TargetImageSize = self.SampleViedo.viewport().size()
        newimage = image.scaled(TargetImageSize,QtCore.Qt.KeepAspectRatio)
        # newimage = image.scaled(TargetImageSize,QtCore.Qt.KeepAspectRatioByExpanding)
        # newimage = image.scaled(TargetImageSize,QtCore.Qt.IgnoreAspectRatio)
        
        self.sampleQPixmapSize = newimage.size()
        self.sampleQPixmap.setPixmap(newimage)
        # self.sampleQPixmap.setPixmap(image)
        # newscale = image.size().width()/TargetImageSize.width() 
        # print(newscale)
        # self.sampleQPixmap.setScale(1/newscale)
        
        #move cross to center
        centerx =  self.sampleQPixmap.boundingRect().center().x()
        centery =  self.sampleQPixmap.boundingRect().center().y()
        # centerx = self.sampleQPixmapSize.height()/2
        # centery = self.sampleQPixmapSize.width()/2
        # print(f"newpos{centerx},{centery}")
        offx,offy = self.corss.getoffset()
        self.corss.setPos(centerx-offx, centery-offy)
        
        
        # cal_CAMpos_baseon_XYZ
        #
        # print(f'original image size = {image.size()}\n viewportsize = {TargetImageSize}\n')
        
        # print(f'framesize = {self.SampleViedo.frameSize()}')
        # print(f'Totalsize = {self.SampleViedo.size()}')
        
        #For Raster view
        # if self.RasterView2QPixmap_ori.isNull():
        #     pass
        # else:
        #     TargetImageSize = self.RasterView1.viewport().size()
        #     newimage = self.RasterView1QPixmap_ori.scaled(TargetImageSize,QtCore.Qt.KeepAspectRatio)
        #     self.RasterView1QPixmap.setPixmap(newimage)
        #     ratio =  (self.RasterView1QPixmap_ori.width()/self.RasterView1QPixmap.boundingRect().width())
        #     x = (self.RasterPar['View1']['box'].x() / ratio)
        #     y = (self.RasterPar['View1']['box'].y() / ratio)
        #     w = (self.RasterPar['View1']['box'].width() / ratio)
        #     h = (self.RasterPar['View1']['box'].height() / ratio)
        #     # self.view1box.setRect(x,y,w,h)
        #     TargetImageSize = self.RasterView2.viewport().size()
        #     newimage = self.RasterView2QPixmap_ori.scaled(TargetImageSize,QtCore.Qt.KeepAspectRatio)
        #     self.RasterView2QPixmap.setPixmap(newimage)
        # pass
    def updateHutchimage1(self,image):
        # oriImageSize=image.size()
        TargetImageSize = self.hutchvideo1.viewport().size()
        # old size?
        
        scale = image.size().width()/TargetImageSize.width()
        # if self.hutchvideo1_scale.value() == 0:
        #     newscale = 1
        # else:
        newscale = 1+ self.hutchvideo1_scale.value()/100*scale

        newimage = image.scaled(TargetImageSize*newscale,QtCore.Qt.KeepAspectRatio)
        if self.hutchvideoPixmap1.pixmap().size().width() != newimage.size().width():
            self.hutchvideo1scene.setSceneRect(0,0,newimage.size().width(),newimage.size().height())
        # newimage = image
        
        # newimage = image.scaled(TargetImageSize,QtCore.Qt.KeepAspectRatioByExpanding)
        # newimage = image.scaled(TargetImageSize,QtCore.Qt.IgnoreAspectRatio)
        
        # self.sampleQPixmapSize = newimage.size()
        self.hutchvideoPixmap1.setPixmap(newimage)
        # print(self.hutchvideo1scene.sceneRect())

    def updateHutchimage2(self,image):
        # oriImageSize=image.size()
        
        TargetImageSize = self.hutchvideo2.viewport().size()
        scale = image.size().width()/TargetImageSize.width()
        newscale = 1+ self.hutchvideo2_scale.value()/100*scale
        newimage = image.scaled(TargetImageSize*newscale,QtCore.Qt.KeepAspectRatio)
        # newimage = image.scaled(TargetImageSize,QtCore.Qt.KeepAspectRatioByExpanding)
        # newimage = image.scaled(TargetImageSize,QtCore.Qt.IgnoreAspectRatio)
        if self.hutchvideoPixmap2.pixmap().size().width() != newimage.size().width():
            self.hutchvideo2scene.setSceneRect(0,0,newimage.size().width(),newimage.size().height())
        else:
            pass
            # print(self.hutchvideo2.geometry())
        # self.sampleQPixmapSize = newimage.size()
        self.hutchvideoPixmap2.setPixmap(newimage)

    def RasterView1Resize(self,event):
        # print('****************')
        # print(event.oldSize())
        # print(event.size())
        self.plotView12(False)
        self.plot_overlap_image('View1')                     
        self.plot_overlap_image('View2')
        self.reposition_view_cross() 

    def plotView12(self,Newone=True):
        if self.RasterView2QPixmap_ori.isNull():
            pass
        else:
            TargetImageSize = self.RasterView1.viewport().size()
            newimage = self.RasterView1QPixmap_ori.scaled(TargetImageSize,QtCore.Qt.KeepAspectRatio)
            self.RasterView1QPixmap.setPixmap(newimage)
            ratio =  (self.RasterView1QPixmap_ori.width()/self.RasterView1QPixmap.boundingRect().width())
            x = (self.RasterPar['View1']['box'].x() / ratio)
            y = (self.RasterPar['View1']['box'].y() / ratio)
            w = (self.RasterPar['View1']['box'].width() / ratio)
            h = (self.RasterPar['View1']['box'].height() / ratio)
            # print('full scle=',self.RasterPar['View1']['box'])
            # print('New Qrect=',QRectF(x,y,w,h))
            self.view1box.setPen(QPen(QColor('yellow')))
            self.view1box.setRect(x,y,w,h)
            
            TargetImageSize = self.RasterView2.viewport().size()
            newimage = self.RasterView2QPixmap_ori.scaled(TargetImageSize,QtCore.Qt.KeepAspectRatio)
            self.RasterView2QPixmap.setPixmap(newimage)
            ratio =  (self.RasterView2QPixmap_ori.width()/self.RasterView2QPixmap.boundingRect().width())
            x = (self.RasterPar['View2']['box'].x() / ratio)
            y = (self.RasterPar['View2']['box'].y() / ratio)
            w = (self.RasterPar['View2']['box'].width() / ratio)
            h = (self.RasterPar['View2']['box'].height() / ratio)
            # print('full scle=',self.RasterPar['View2']['box'])
            # print('New Qrect=',QRectF(x,y,w,h))
            self.view2box.setPen(QPen(QColor('yellow')))
            self.view2box.setRect(x,y,w,h)
            self.plotbox(Newone)
            if Newone:
                pass
            else:
                # self.plotdozor(True,'score','View1')
                # self.plotdozor(True,'score','View2')
                self.plot_overlap_image('View1')                     
                self.plot_overlap_image('View2') 
                pass
        pass
        # print((self.RasterView1QPixmap_ori.width()/self.RasterView1QPixmap.boundingRect().width()))
    def getViewRatio(self,view=1)    :
        if view == 1 or view == 'View1':
            try:
                ratio = (self.RasterView1QPixmap_ori.width()/self.RasterView1QPixmap.boundingRect().width())
            except:
                ratio = 1
        else:
            try:
                ratio = (self.RasterView2QPixmap_ori.width()/self.RasterView2QPixmap.boundingRect().width())
            except:
                ratio = 1
        return ratio    
    def selectGridsize_value_change(self):
        #only replot if @active
        if self.bluiceData['active']:
            self.plotbox()
            gridsize = float(self.selectGridsize.currentText())
            defaultselectbeamsize = self.gridsizetobeamsize(gridsize)
            index = self.selectBeamsize.findText(str(defaultselectbeamsize))
            self.selectBeamsize.setCurrentIndex(index)
            self.update_ui_par_to_meshbest()
        self.CalRasterDose()
    def selectBeamsize_value_change(self):
        if self.bluiceData['active']:
            self.update_ui_par_to_meshbest()
            
        self.CalRasterDose()
    def Distance_value_change(self):
        if self.bluiceData['active']:
            self.update_ui_par_to_meshbest()
        
    def plotbox(self,Newone=True):
            self.logger.debug(f'plotbox at Gridsize {float(self.selectGridsize.currentText())}')
            # print('plotbox is called!')
            # print(self.selectGridsize.currentText())
            # beamsizeX = float(self.selectGridsize.currentText())
            gridsizeX = float(self.selectGridsize.currentText())
            gridsizeY = float(self.selectGridsize.currentText())
            
            try:
                # camscaleX = self.bluiceData['motor']['zoom_scale_x']['pos']#um/pix
                # camscaleY = self.bluiceData['motor']['zoom_scale_y']['pos']
                camscaleX = self.RasterPar['View1']['zoom_scale_x']
                camscaleY = self.RasterPar['View1']['zoom_scale_y']
            except:
                #maybe in new raster creat
                camscaleX = self.bluiceData['motor']['zoom_scale_x']['pos']#um/pix
                camscaleY = self.bluiceData['motor']['zoom_scale_y']['pos']
                # camscaleX = self.RasterPar['View1']['zoom_scale_x']
                # camscaleY = self.RasterPar['View1']['zoom_scale_y']
            try:    
                # numofXbox1 = math.ceil(self.RasterPar['View1']['box'].width()*camscaleX/beamsizeX)
                # numofYbox1 = math.ceil(self.RasterPar['View1']['box'].height()*camscaleY/beamsizeY)
                numofXbox1 = round(self.RasterPar['View1']['box'].width()*camscaleX/gridsizeX)
                numofYbox1 = round(self.RasterPar['View1']['box'].height()*camscaleY/gridsizeY)
                if numofXbox1 == 1:
                    numofXbox1 = 2#unable to raster wiht x num =1
            except Exception as e:
                numofXbox1 = 2 
                numofYbox1 = 2 

            if camscaleX:
                pass
            else:
                camscaleX = self.bluiceData['motor']['zoom_scale_x']['pos']

            if camscaleY:
                pass
            else:
                camscaleY = self.bluiceData['motor']['zoom_scale_y']['pos']

            self.RasterPar['View1']['numofX']=numofXbox1
            self.RasterPar['View1']['numofY']=numofYbox1
            self.RasterPar['View1']['gridsizeX']=gridsizeX
            self.RasterPar['View1']['gridsizeY']=gridsizeY
            bigbox = self.RasterPar['View1']['box']

            # ratio = (self.RasterView1QPixmap_ori.width()/self.RasterView1QPixmap.boundingRect().width())
            ratio = self.getViewRatio(1)
            
            startx = bigbox.x() / ratio
            starty = bigbox.y() / ratio
            
            
            # print("scene.items()",self.Rasterscene1.items())

            try:
                # print("the scene i remember",self.RasterPar['View1']['boxRectItemarray'])
                # for a in self.RasterPar['View1']['boxitemarray']:
                for a in self.RasterPar['View1']['boxRectItemarray'] :
                    for b in a :
                        self.Rasterscene1.removeItem(b)
            except:
                pass
                
            
                
            #plot on scene
            
            self.RasterPar['View1']['boxRectItemarray']=[[0]*numofYbox1 for i in range(numofXbox1)]
            if Newone:
                self.clear_dozor_plot()
                self.initScoreArray('View1')
                #clear txt item
                # try:
                #     for a in self.RasterPar['View1']['Textplotarray'] :
                #         for b in a :
                #             self.RasterPar['View1'].removeItem(b)                       
                # except:
                #     pass
                #creat empty txt item in view?
                array = self.RasterPar['View1']['scoreArray']
                txtformat = '1.0f'
                myfont = QFont()
                myfont.setBold(False)
                myfont.setPointSize(10)
                self.RasterPar['View1']['Textplotarray']=[[0]*numofYbox1 for i in range(numofXbox1)]
                for x,item in enumerate(array):
                    for y,item2 in enumerate(item):
                        x0,y0,xc,yc=self.plottool_getpixel(x,y,ratio,True)
                        temp = self.Rasterscene1.addText(f'{item2:{txtformat}}',myfont)
                        temp.setPos(xc-temp.boundingRect().width()/2,yc-temp.boundingRect().height()/2)
                        # temp.setDefaultTextColor(QColor(0, 0, 0, 0))                
                        temp.setDefaultTextColor(QColor('white'))
                        temp.setVisible(False)
                        temp.setZValue(99)
                        self.RasterPar['View1']['Textplotarray'][x][y] = temp

            # print(f'{beamsizeX=},{camscaleX=},{ratio=}')
            w = gridsizeX / camscaleX / ratio
            h = gridsizeY / camscaleY / ratio
            
            # print(f'number={numofXbox1},{numofYbox1}, size={w},{h}')
            for y in range(numofYbox1):
                for x in range(numofXbox1):
                    x0 = startx + x*w
                    y0 = starty + y*h
                    # print(f'current={x},{y}')
                    temp = self.Rasterscene1.addRect(x0,y0,w,h)
                    temp.setPen(QPen(QColor('yellow')))
                    self.RasterPar['View1']['boxRectItemarray'][x][y] = temp
                    # print(f'current={x},{y},{temp},{temp.rect()}')
                    # self.Rasterscene1.addItem(self.RasterPar['View1']['boxRectItemarray'][x][y])
                    
            # print(self.RasterPar['View1']['boxRectItemarray'])        
            # self.view1gridsgroup = self.Rasterscene1.createItemGroup(tempitemlist)
            
            #replot view1 box
            w = w * (numofXbox1) 
            h = h * (numofYbox1) 
            # print("old:",self.RasterPar['View1']['box'])
            self.RasterPar['View1']['box']= QRectF( bigbox.x(), bigbox.y(),w*ratio,h*ratio)
            self.view1box.setRect(startx, starty, w, h)
            # print("new:",self.RasterPar['View1']['box'])
            
            
            try:    
                
                numofXbox2 = round(self.RasterPar['View2']['box'].width()*camscaleX/gridsizeX)
                numofYbox2 = round(self.RasterPar['View2']['box'].height()*camscaleY/gridsizeY)
                if numofXbox2 == 1:
                    numofXbox2 = 2#unable to raster wiht x num =1
            except Exception as e:
                numofXbox2 = 2 
                numofYbox2 = 1 

            self.RasterPar['View2']['numofX']=numofXbox2
            self.RasterPar['View2']['numofY']=numofYbox2
            self.RasterPar['View2']['gridsizeX']=gridsizeX
            self.RasterPar['View2']['gridsizeY']=gridsizeY
            
            bigbox = self.RasterPar['View2']['box']
            ratio = self.getViewRatio(2)
            
            startx = bigbox.x() / ratio
            starty = bigbox.y() / ratio
            
            
            # print("scene.items()",self.Rasterscene1.items())

            try:
                # print("the scene i remember",self.RasterPar['View1']['boxRectItemarray'])
                # for a in self.RasterPar['View1']['boxitemarray']:
                for a in self.RasterPar['View2']['boxRectItemarray'] :
                    for b in a :
                        self.Rasterscene2.removeItem(b)
            except:
                pass
                
            
                
            #plot on scene
            
            self.RasterPar['View2']['boxRectItemarray']=[[0]*numofYbox2 for i in range(numofXbox2)]
            if Newone:
                self.initScoreArray('View2')
                # try:
                #     for a in self.RasterPar['View2']['Textplotarray'] :
                #         for b in a :
                #             self.RasterPar['View2'].removeItem(b)                       
                # except:
                #     pass
                #creat empty txt item in view?
                array = self.RasterPar['View2']['scoreArray']
                txtformat = '1.0f'
                myfont = QFont()
                myfont.setBold(False)
                myfont.setPointSize(10)
                self.RasterPar['View2']['Textplotarray']=[[0]*numofYbox2 for i in range(numofXbox2)]
                for x,item in enumerate(array):
                    for y,item2 in enumerate(item):
                        x0,y0,xc,yc=self.plottool_getpixel(x,y,ratio,True)
                        temp = self.Rasterscene2.addText(f'{item2:{txtformat}}',myfont)
                        temp.setPos(xc-temp.boundingRect().width()/2,yc-temp.boundingRect().height()/2)
                        # temp.setDefaultTextColor(QColor(0, 0, 0, 0))
                        temp.setDefaultTextColor(QColor('white'))
                        temp.setVisible(False)
                        temp.setZValue(99)
                        self.RasterPar['View2']['Textplotarray'][x][y] = temp

            # self.RasterPar['View1']['boxitemsize'] = [[0]*numofXbox1]*numofYbox1
            
            w = gridsizeX / camscaleX / ratio
            h = gridsizeY / camscaleY / ratio
            
            # print(f'number={numofXbox1},{numofYbox1}, size={w},{h}')
            for y in range(numofYbox2):
                for x in range(numofXbox2):
                    x0 = startx + x*w
                    y0 = starty + y*h
                    # print(f'current={x},{y}')
                    temp = self.Rasterscene2.addRect(x0,y0,w,h)
                    temp.setPen(QPen(QColor('yellow')))
                    self.RasterPar['View2']['boxRectItemarray'][x][y] = temp
                    # print(f'current={x},{y},{temp},{temp.rect()}')
                    # self.Rasterscene1.addItem(self.RasterPar['View1']['boxRectItemarray'][x][y])
                    
            # print(self.RasterPar['View1']['boxRectItemarray'])        
            # self.view1gridsgroup = self.Rasterscene1.createItemGroup(tempitemlist)
            
            #replot view1 box
            w = w * (numofXbox2) 
            h = h * (numofYbox2) 
            self.RasterPar['View2']['box']= QRectF( bigbox.x(), bigbox.y(),w*ratio,h*ratio)
            self.view2box.setRect(startx, starty, w, h)
            
            
            

    def setBluice(self):
        # manager = Manager()
        self.bluiceinfo=self.m1.dict()
        self.Qinfo=self.m1.dict()
        self.MotorMoving=self.m1.dict()
        self.opCompleted=self.m1.dict()
        
        self.bluice = bluice.BluiceClient(self.Par)
        self.bluice.info = self.bluiceinfo
        self.bluice.Qinfo = self.Qinfo
        self.bluice.MotorMoving = self.MotorMoving
        self.bluice.opCompleted = self.opCompleted
        self.bluice.info['run1']={'beam_stop':'42'}
        self.bluice.passwd = self.passwd
        self.bluice.base64passwd = self.base64passwd
        self.bluice.key = self.bluicekey 
        self.bluice.user = self.user
        self.bluice.bluicemessage.connect(self.messageFromBluice)
        
        #Qthread
        self.bluice.start()
        
        #mp using, no use now
        # self.p = Process(target=self.bluice.initconnection, args=())
        # self.p.start()
        pass
    def setupMeshbest(self,LOG_FILENAME):
        self.meshbest = MeshbestClient.MestbestClient(LOG_FILENAME)
        # self.meshbest.Par=self.Par
        self.meshbest.Mestbestemessage.connect(self.messageFromMeshbest)
        #Qthread
        self.meshbest.start()
        

    def test(self):
        pass
    def StartRasterclicked(self):
        self.logger.info(f'Button Start Raster clicked')
        path=f'{self.RootPath_2.text()}/StartRasterclickedPar.txt'
        with open(path,'w') as f:
            f.write(f"UI_par:{self.Par['UI_par']}\n")
            writeitem = ['box','collectInfo','GridX','GridY','gonio_phi','sample_x','sample_y',\
                'sample_z','align_z','zoom','zoom_scale_x','zoom_scale_y','numofX','numofY',\
                'gridsizeX','gridsizeY']
            for view in ['View1','View2']:
                f.write(f"{view}:===\n")
                for key, value in self.Par[view].items(): 
                    if str(key) in writeitem: 
                        f.write(f'{key}:{value}\n')
            

        self.Qinfo["sendQ"].put('gtos_set_string system_status {Start Rastering...} black #d0d000')
        self.Par['StateCtl']['AbletoStartRaster'] = False
        self.Overlap_Select_1.setCurrentIndex(2)
        self.Overlap_Select_2.setCurrentIndex(2)
        # self.initScoreArray('View1')
        # self.initScoreArray('View2')
        self.plotView12(True)
        
        self.StartRaster.setEnabled(False)
        self.Raster.setEnabled(False)
        # self.clear_dozor_plot()
        self.RasterRuning = True
        self.RasterRunstep=0
        self.Par['StateCtl']['RasterDone'] = False
        self.update_ui_par_to_meshbest()
        self.ArmDetectorandMeshbest()
      
        # self.meshbest.sendCommandToMeshbest(('Hi',self.RasterPar))
    def StartRasterclicked_done(self):
        self.logger.info(f'Job done for two raster')
        self.RasterRuning = False
        # self.StartRaster.setEnabled(True)
        self.Raster.setEnabled(True)
        # self.can_move_in_rastrview_flag = True
        self.Par['StateCtl']['RasterDone'] = True
        self.update_ui_par_to_meshbest()
        self.Qinfo["sendQ"].put('gtos_set_string system_status Ready black #00a040')
        pass
    
    def ArmDetectorandMeshbest(self):
        # this not work
        self.logger.info(f'{self.RasterPar["View2"]["box"]}, so .....{self.RasterPar["View2"]["box"] == QRectF(0,0,0,0)}')
        self.Qinfo["sendQ"].put('gtos_set_string system_status {Wait for Detector setup(Raster)} black #d0d000')
        if self.RasterRunstep ==0:
            view=1
            if self.RasterPar['View1']['box'] == QRectF(0,0,0,0):
                self.skipview = True
            else:
                self.skipview = False
            parlist = self.calRasterParDetector(view1=True)
            arm='armview'
        else:
            view=2
            if self.RasterPar['View2']['box'] == QRectF(0,0,0,0):
                self.skipview = True
            else:
                self.skipview = False
            if self.select2scan.currentText() == "Disable":
                self.skipview = True

            parlist = self.calRasterParDetector(view1=False)
            arm='armview'
            # self.skipview = True
        
        if self.skipview:
            self.logger.info(f'skip view{view}')
            # self.TriMD3RasterEx()
            self.Raster_move_xyzphi()
        else:
            #move pos phi
            # self.Raster_move_xyzphi()
            #arm detector and meshbesst
            
            self.logger.debug(f'patlist = {parlist}')
            command = f"gtos_start_operation detector_ratser_setup {self.bluiceID}.{self.bluiceCounter} "
            self.bluiceCounter += self.bluiceCounter
            
            for item in parlist:
                command = command + str(item) + " "
            
            #arm meshbetserver and detector
            self.meshbest.sendCommandToMeshbest((arm,parlist))
            self.opCompleted['detector_ratser_setup'] = False
            self.Qinfo["sendQ"].put(command)
            
            #wait detectorop
            self.logger.debug(f'op state list = {self.opCompleted}')
            self.logger.info(f'Wait for setup detctor done')
            oplist=['detector_ratser_setup']


            
            # # callback = self.TriMD3RasterEx
            callback = self.Raster_move_xyzphi
            while True:
                checkarray = []
                self.logger.debug(f'check op:{oplist} job')
                for op in oplist:
                    checkarray.append(self.opCompleted[op])
                if all(checkarray):
                    self.logger.debug(f'op:{oplist} move done')
                    break
                QApplication.processEvents()
                time.sleep(0.1)
            callback()
            # self.bluiceData['operation']['detector_ratser_setup']['moving'] = True
            # self.timer.singleShot(100, partial(self.waitOperationDone
            #                                    ,oplist,callback))
            
    def Raster_move_xyzphi(self):
        if self.RasterRunstep == 0:
            parlist = self.calstartRasterScanPar(view1=True)
            self.RasterRunstep = 1
            callback = self.TriMD3Raster
            par = self.RasterPar['View1']
        else:
            #self.RasterRunstep = 2
            parlist = self.calstartRasterScanPar(view1=False)
            callback = self.TriMD3Raster
            par = self.RasterPar['View2']
        
        #make sure motor stop before we move
        motorchecklist=['gonio_phi','sample_x','sample_y','sample_z','attenuation']
        self.logger.debug(f'Moving list = {self.MotorMoving}')
        while True:
            self.logger.debug(f'Checking online {motorchecklist} moving state')
            checkarray = []
            posarray = []
            for motor in motorchecklist:
                checkarray.append(not (self.MotorMoving[motor]))
            if all(checkarray):
                self.logger.debug(f'motor:{motorchecklist} move done')
                break
            QApplication.processEvents()
            time.sleep(0.2)
            
        if self.select2scan.currentText() == "Disable" and self.RasterRunstep == 2:
            #skip view2 move
            self.StartRasterclicked_done()
        else:
            attenuation = self.Attenuation.value()
            samplex = par['sample_x']
            sampley = par['sample_y']
            samplez = par['sample_z']
            angle = par['gonio_phi']
            zoomx = par['zoom_scale_x']
            zoomy = par['zoom_scale_y']
            centerX = par['box'].center().x()
            CenterY = par['box'].center().y()
            samplez,sampley,samplex = self.calXYZbaseonCAMCenter(centerX,CenterY,angle,zoomx,zoomy,samplex,sampley,samplez)    
        
            command = f'gtos_start_motor_move gonio_phi {angle}'
            # print(command)
            self.Qinfo["sendQ"].put(command)
            command = f'gtos_start_motor_move sample_x {samplex}'
            # print(command)
            self.Qinfo["sendQ"].put(command)
            command = f'gtos_start_motor_move sample_y {sampley}'
            # print(command)
            self.Qinfo["sendQ"].put(command)
            command = f'gtos_start_motor_move sample_z {samplez}'
            # print(command)
            self.Qinfo["sendQ"].put(command)
            command = f'gtos_start_motor_move attenuation {attenuation}'
            # print(command)
            self.Qinfo["sendQ"].put(command)

            motorchecklist=['gonio_phi','sample_x','sample_y','sample_z','attenuation']
            motorposchecklist=[angle,samplex,sampley,samplez,attenuation]
            # motorchecklist=['sample_x','sample_y','sample_z']
            # motorposchecklist=[samplex,sampley,samplez]
            self.logger.info(f'wait {motorchecklist} goto {motorposchecklist}')
            # self.timer.singleShot(100,partial(self.waitMotorInPosUpdate,motorchecklist,motorposchecklist,callback))
            self.timer.singleShot(200, partial(self.waitMotorStopUpdate_v2,motorchecklist,callback))
        
    def TriMD3Raster(self):
        
        self.logger.info(f'Ready for Tri. MD3')
        self.Qinfo["sendQ"].put('gtos_set_string system_status {Wait for MD3 scan (Raster)} black #d0d000')
        if self.RasterRunstep == 1:
            parlist = self.calstartRasterScanPar(view1=True)
            self.RasterRunstep = 2
            callback = self.ArmDetectorandMeshbest
            par = self.RasterPar['View1']
        else:
            #self.RasterRunstep = 2
            parlist = self.calstartRasterScanPar(view1=False)
            callback = self.StartRasterclicked_done
            par = self.RasterPar['View2']

        if self.skipview:
            callback()
        else:
            
            command = f"gtos_start_operation startRasterScan {self.bluiceID}.{self.bluiceCounter} "
            self.bluiceCounter += self.bluiceCounter
            for item in parlist:
                command = command + str(item) + " "
            self.logger.debug(f"send command to dcss:{command}")
        
        
        
        
            self.Qinfo["sendQ"].put(command)
            #wait operation done
            self.logger.info(f'Wait for MD3 operation')
            oplist=['startRasterScan']
            self.bluiceData['operation']['startRasterScan']['moving'] = True
            self.timer.singleShot(100, partial(self.waitOperationDone
                                               ,oplist,callback))
        
    def TriMD3RasterEx(self):
        
        self.logger.info(f'Ready for Tri. MD3')
        if self.RasterRunstep == 0:
            parlist = self.calRasterPar(view1=True)
            self.RasterRunstep = 1
            callback = self.ArmDetectorandMeshbest
        else:
            parlist = self.calRasterPar(view1=False)
            callback = self.StartRasterclicked_done

        if self.skipview:
            callback()
        else:
            
            command = f"gtos_start_operation startRasterScanEx {self.bluiceID}.{self.bluiceCounter} "
            self.bluiceCounter += self.bluiceCounter
            for item in parlist:
                command = command + str(item) + " "
            self.logger.debug(f"send command to dcss:{command}")
        
        
        
        
            self.Qinfo["sendQ"].put(command)
            #wait operation done
            self.logger.info(f'Wait for MD3 operation')
            oplist=['startRasterScanEx']
            self.bluiceData['operation']['startRasterScanEx']['moving'] = True
            self.timer.singleShot(100, partial(self.waitOperationDone
                                               ,oplist,callback))
            
    def StartRasterclicked_3(self):
        self.logger.info('scan Raster done')
        pass
    def calMutiPosPar(self,info):
        # self.operationHandle = command[1]
        # self.runIndex = int(command[2])
        # self.filename = command[3]
        # self.directory = command[4]
        # self.userName = command[5]
        # self.axisName = command[6]
        # self.exposureTime = float(command[7])
        # self.oscillationStart = float(command[8])
        
        # self.detosc =  float(command[9])
        # self.TotalFrames = int(command[10]) #1
        # self.distance = float(command[11])
        # self.wavelength = float(command[12])
        # self.detectoroffX = float(command[13])
        # self.detectoroffY = float(command[14])
        
        # self.sessionId = command[17]
        # self.fileindex = int(command[18])
        # self.unknow = int(command[19]) #1
        # self.beamsize = command[20] # 50
        # self.atten = command[21] #0
        
        # self.bluice.job = 'collect'
        # self.bluice.file_root = str(info['FileName'])
        # self.bluice.directory = str(info['FolderName'])
        # self.bluice.start_angle = str(info['StartPhi'])
        # self.bluice.end_angle = str(info['EndPhi'])
        # self.bluice.delta = str(info['Delta'])
        # self.bluice.exposure_time = str(info['ExpTime'])
        # self.bluice.distance = str(info['Distance'])
        # self.bluice.attenuation = str(info['Atten'])
        # self.bluice.beamsize = str(info['BeamSize'])
        # self.bluice.energy1 = str(info['Energy'])
        runIndex = int(1)
        
        filename = str(info['FileName'])
        directory = str(info['FolderName'])
        # directory = self.RootPathforRaster
        userName = self.user
        axisName = "gonio_phi"
        exposureTime = str(info['ExpTime'])
        oscillationStart = str(info['StartPhi'])
        
        detosc =  str(info['Delta'])
        TotalFrames =  str(math.ceil(abs(float(info['EndPhi'])-float(info['StartPhi']))/float(info['Delta'])))#1
        # distance = self.bluiceData['motor']['detector_z']['pos']
        distance = str(info['Distance'])
        wavelength = 1/self.bluiceData['motor']['energy']['pos']*12398
        detectoroffX = self.bluiceData['motor']['detector_vert']['pos']
        detectoroffY = self.bluiceData['motor']['detector_horz']['pos']
        
        sessionId = "no"
        fileindex = 0
        unknow = int(1) #1
        #for beam size , gird size =1000 using beamsize 90
        #par['gridsizeY'] is grid size, so we need change it
        # beamsize = self.gridsizetobeamsize(par['gridsizeY'])
        # new! change beam size only in EPIS DHS
        beamsize = str(info['BeamSize']) # 50
        
        atten = self.bluiceData['motor']['attenuation']['pos'] #or str(info['Atten'])

        
        ans =  [runIndex,filename,directory,userName,axisName,exposureTime,oscillationStart,detosc,TotalFrames,distance,wavelength,detectoroffX,detectoroffY,sessionId,fileindex,unknow,beamsize,atten]
        self.logger.info(f'{ans}')
        return ans

    def calRasterParDetector(self,view1=True):
        # self.operationHandle = command[1]
        # self.runIndex = int(command[2])
        # self.filename = command[3]
        # self.directory = command[4]
        # self.userName = command[5]
        # self.axisName = command[6]
        # self.exposureTime = float(command[7])
        # self.oscillationStart = float(command[8])
        
        # self.detosc =  float(command[9])
        # self.TotalFrames = int(command[10]) #1
        # self.distance = float(command[11])
        # self.wavelength = float(command[12])
        # self.detectoroffX = float(command[13])
        # self.detectoroffY = float(command[14])
        
        # self.sessionId = command[17]
        # self.fileindex = int(command[18])
        # self.unknow = int(command[19]) #1
        # self.beamsize = command[20] # 50
        # self.atten = command[21] #0
        if view1:
            par = self.RasterPar['View1']
            filename = 'RasterScanview1'
            runIndex = int(101)
        else:
            filename = 'RasterScanview2'
            par = self.RasterPar['View2']
            runIndex = int(102)
            
        # runIndex =view1 =101 view2 =102
        filename = filename
        directory = self.RootPath_2.text()
        # directory = self.RootPathforRaster
        userName = self.user
        axisName = "gonio_phi"
        exposureTime = self.ExpouseValue.value()
        oscillationStart = par['gonio_phi']
        
        detosc =  float(self.RotationValue.value())
        TotalFrames = int(par['numofX']*par['numofY'] ) #1
        # distance = self.bluiceData['motor']['detector_z']['pos']
        distance = self.Distance.value()
        wavelength = 1/self.bluiceData['motor']['energy']['pos']*12398
        detectoroffX = self.bluiceData['motor']['detector_vert']['pos']
        detectoroffY = self.bluiceData['motor']['detector_horz']['pos']
        
        sessionId = "no"
        fileindex = 0
        unknow = int(1) #1
        #for beam size , gird size =100 using beamsize 90
        #par['gridsizeY'] is grid size, so we need change it
        # beamsize = self.gridsizetobeamsize(par['gridsizeY'])
        # new! change beam size only in EPICS DHS
        # beamsize = par['gridsizeY'] # 50
        beamsize = self.selectBeamsize.currentText() # 50
        
        atten = self.bluiceData['motor']['attenuation']['pos'] #0
        if self.selectROI.currentText() == "Enable":
            roi = 1
        else:
            roi = 0
        numofX = par['numofX']
        numofY = par['numofY'] 
        #  sscanf(commandBuffer.textInBuffe
        # self.logger.info(f'Default action for {command[0]}:{command[1:]}')
        uid = self.uid
        gid = self.gid
        gridsizex = par['gridsizeX']
        gridsizey = par['gridsizeY']
        ans =  [runIndex,filename,directory,userName,axisName,exposureTime,oscillationStart,detosc,TotalFrames,distance,wavelength,detectoroffX,detectoroffY,sessionId,fileindex,unknow,beamsize,atten,roi,numofX,numofY,uid,gid,gridsizex,gridsizey]
        self.logger.debug(f'{ans}')
        return ans
    def gridsizetobeamsize(self,gridsize):
        table={100:80,90:70,80:60,70:50,60:40,50:30,40:20,30:10,20:5,10:1,5:1}
        return table[gridsize]
    def calRasterPar(self,view1=True):
        #current not  use
        # startRasterScanEx
        # double omega_range,
        # double line_range, ver?
        # double total_uturn_range, hor?
        # double start_omega,
        # double start_y,
        # double start_z,
        # double start_cx,
        # double start_cy,
        # int number_of_lines,
        # int frames_per_lines,
        # double exposure_time,
        # boolean invert_direction,
        # boolean use_centring_table,
        # boolean shutterless
        if view1:
            par = self.RasterPar['View1']
        else:
            par = self.RasterPar['View2']
        # https://doc.qt.io/qt-5/qrect.html
        
        angle = par['gonio_phi']
        zoomx = par['zoom_scale_x']
        zoomy = par['zoom_scale_y']
        samplex = par['sample_x']
        sampley = par['sample_y']
        samplez = par['sample_z']
        
        start_pointX_pixel = par['box'].right() - par['gridsizeX']/2/zoomx
        start_pointY_pixel = par['box'].bottom() - par['gridsizeY']/2/zoomy
        # centerX = self.oriImageSize.width()/2
        # centerY = self.oriImageSize.height()/2
        # detX_pixel = start_pointX_pixel - centerX
        # detY_pixel = start_pointY_pixel - centerY
        
        start_y,start_cx,start_cy = self.calXYZbaseonCAMCenter(start_pointX_pixel,start_pointY_pixel,angle,zoomx,zoomy,samplex,sampley,samplez)    
        #
        
        #todo
        # self.RotationValue.value()
        omega_range = self.RotationValue.value()*par['numofY'] 
        
        line_range = (par['numofY']* par['gridsizeY'])/1000*-1
        total_uturn_range = ((par['numofX']-1) * par['gridsizeX'])/1000
        start_omega = par['gonio_phi'] - omega_range/2
        # start_y = par['sample_z'] + (par['zoom_scale_y']*detY_pixel)/1000
        start_z = par['align_z']
        # start_cx = par['sample_y'] + (detX_pixel*par['zoom_scale_x'] * math.sin(par['gonio_phi']/180*math.pi))/1000 #1000 for um to mm 
        # start_cy = par['sample_x'] + (detX_pixel*par['zoom_scale_x'] * math.cos(par['gonio_phi']/180*math.pi))/1000
        number_of_lines = par['numofX']
        frames_per_lines = par['numofY'] 
        
        
        
        
        if self.ExpousetimeType.currentText() == "Exposure time":
            exposure_time = self.ExpouseValue.value()
        elif self.ExpousetimeType.currentText() == "Rate":
            exposure_time = 1 / self.ExpouseValue.value()
        else:
            self.logger.warning(f"Undefine name {self.ExpousetimeType.currentText()} in ExpousetimeType")
        #par is a line(exptime)
        exposure_time = exposure_time * frames_per_lines
        
        self.logger.info(f'cal raster par : omega_range:{omega_range},line_range:{line_range},total_uturn_range:{total_uturn_range},start_omega:{start_omega},number_of_lines:{number_of_lines},frames_per_lines:{frames_per_lines}')
        self.logger.info(f'cal raster par : start_y:{start_y},start_z:{start_z},start_cx:{start_cx},start_cy:{start_cy}')
        return [omega_range,line_range,total_uturn_range,start_omega,start_y,start_z,start_cx,start_cy,number_of_lines,frames_per_lines,exposure_time,1,1,1]
    def calstartRasterScanPar(self,view1=True):
        #  startRasterScan
        # vertical_range (double): vertical range of the grid      should be X
        # horizontal_range (double): horizontal range of the grid  should be Y
        # number_of_lines (int) : number of horizontal lines of scan
        # number_of_frames (int): number of frame trigger issued for the detector
        # invert_direction (Boolean): flag to enable passes in the reverse direction


        # ScanStartAngle,
        # ScanExposureTime, (a line)
        # ScanRange

        if view1:
            par = self.RasterPar['View1']
        else:
            par = self.RasterPar['View2']
        # https://doc.qt.io/qt-5/qrect.html
        
        angle = par['gonio_phi']
        zoomx = par['zoom_scale_x']
        zoomy = par['zoom_scale_y']
        samplex = par['sample_x']
        sampley = par['sample_y']
        samplez = par['sample_z']
       
       


        
        #todo
        ScanRange = self.RotationValue.value()*par['numofY']
        #start ar edge of y box
        y_range = abs((par['numofY']* par['gridsizeY'])/1000)
        #start at center of x box
        x_range = abs(((par['numofX']-1) * par['gridsizeX'])/1000)
        ScanStartAngle = par['gonio_phi']
  
        number_of_lines = par['numofX']
        frames_per_lines = par['numofY'] 
        
        
        
        
        if self.ExpousetimeType.currentText() == "Exposed time":
            exposure_time = self.ExpouseValue.value()
        elif self.ExpousetimeType.currentText() == "Rate":
            exposure_time = 1 / self.ExpouseValue.value()
        else:
            self.logger.warning(f"Undefine name {self.ExpousetimeType.currentText()} in ExpousetimeType")
        #par is a line(exptime)
        ScanExposureTime = exposure_time * frames_per_lines
        
        self.logger.info(f'cal raster par : x_range:{x_range},y_range:{y_range},number_of_lines:{number_of_lines},frames_per_lines:{frames_per_lines}')
        self.logger.info(f'cal raster par : ScanStartAngle:{ScanStartAngle},ScanExposureTime:{ScanExposureTime},ScanRange:{ScanRange}')
        return [x_range,y_range,number_of_lines,frames_per_lines,1,ScanStartAngle,ScanExposureTime,ScanRange]
    def calXYZbaseonCAMCenter(self,Xpix,Ypix,angle,zoomx,zoomy,samplex,sampley,samplez):
        #samplxyz for center pos
        # self.logger.warning(f'input:X:{Xpix},Y:{Ypix},phi:{angle},zx:{zoomx},zy:{zoomy},samplex:{samplex},sampley:{sampley},samplez:{samplez}')
        centerX = self.oriImageSize.width()/2
        centerY = self.oriImageSize.height()/2
        detX_pixel = Xpix - centerX
        detY_pixel = Ypix - centerY
        self.logger.debug(f'detY_pixel={detY_pixel}, detX_pixel={detX_pixel}')
        targetZ = samplez + (zoomy * detY_pixel)/1000
        targetCX = sampley + (detX_pixel*zoomx * math.sin(angle/180*math.pi))/1000 #1000 for um to mm 
        targetCY = samplex + (detX_pixel*zoomy * math.cos(angle/180*math.pi))/1000
        
        self.logger.debug(f'cal targetZ={targetZ}, targetCX={targetCX},targetCY={targetCY}')
        return targetZ,targetCX,targetCY
    
    def cal_CAMpos_baseon_XYZ(self,angle,samplex,sampley,samplez,refx,refy,refz,zoomx,zoomy):
        try :

            detver_mm = samplez - refz
            detver_pixel = detver_mm /zoomy*1000
            dethor_pixel_x = ( samplex - refx )/zoomx * math.cos(angle/180*math.pi)*1000
            dethor_pixel_y = ( sampley - refy )/zoomy * math.sin(angle/180*math.pi)*1000
            # print(f'{samplex=},{refx=},{sampley=},{refy=}')
            # ref_hor = 
            # current_hor = 
            # dethor_mm = current_hor - ref_hor
            # dethor_pixel = dethor_mm / zoomx*1000
            dethor_pixel = dethor_pixel_x + dethor_pixel_y
            # print(f'{angle=},{math.cos(angle/180*math.pi)=}')
            # print(f'{detver_pixel=},{dethor_pixel=},{dethor_pixel_x=},{dethor_pixel_y=},{zoomx=},{zoomy=}')
            pos_ver = detver_pixel
            pos_hor = dethor_pixel
        except:
            pos_ver = 0
            pos_hor = 0
        return pos_hor,pos_ver

    def reposition_view_cross(self):
        for view in ['View1','View2']:
                cross = self.RasterPar[view]['CrossItem']
                try:
                    samplex = self.bluiceData['motor']['sample_x']['pos']
                    sampley = self.bluiceData['motor']['sample_y']['pos']
                    samplez = self.bluiceData['motor']['sample_z']['pos']
                    
                    refx = self.RasterPar[view]['sample_x']
                    refy = self.RasterPar[view]['sample_y']
                    refz = self.RasterPar[view]['sample_z']
                    angle = self.RasterPar[view]['gonio_phi']
                    zoomx = self.RasterPar[view]['zoom_scale_x']
                    zoomy = self.RasterPar[view]['zoom_scale_y']
                except:
                    pass
                else:
                    x,y = self.cal_CAMpos_baseon_XYZ(angle,samplex,sampley,samplez,refx,refy,refz,zoomx,zoomy)
                    if view == 'View1':
                        ratio = self.getViewRatio(1)
                        centerx = self.RasterView1QPixmap.boundingRect().center().x()
                        centery = self.RasterView1QPixmap.boundingRect().center().y()
                        scence = self.RasterView1
                        lx = self.RasterView1QPixmap.boundingRect().right()
                        ly = self.RasterView1QPixmap.boundingRect().bottom()
                    else:
                        ratio = self.getViewRatio(2)
                        centerx = self.RasterView2QPixmap.boundingRect().center().x()
                        centery = self.RasterView2QPixmap.boundingRect().center().y()
                        scence = self.RasterView2
                        lx = self.RasterView2QPixmap.boundingRect().right()
                        ly = self.RasterView2QPixmap.boundingRect().bottom()
                    x = centerx + (x / ratio)
                    y = centery + (y / ratio)
                    # self.logger.warning(f'{centerx=},{centery=},{x=},{y=},{ratio=}')
                    # newpos = scence.mapFromScene(x,y)
                    # self.logger.warning(f'after map {newpos=}')
                    # do not make cross over the screen
                    
                    correctX = self.correctNumber(x,0,lx)
                    correctY = self.correctNumber(y,0,ly)

                    offx,offy = cross.getoffset()
                    target = QPointF(correctX-offx,correctY-offy)
                    cross.setPos(target)

    def messageFromMeshbest(self,command):
        self.logger.debug(f'Meshbest Emit : {command}')
        if command[0] == "imagewrited":
            self.logger.info(f'Frame {command[1]} is done!')
            pass
        elif command[0] == 'dozor':
            #[dozor,dozorresult]
            # dozorresult['totalTime']=time.time()-start_time       
            # dozorresult['File']=path
            # dozorresult['spots']=dozorspots
            # dozorresult['score']=dozorscore
            # dozorresult['res']=dozorres
            # dozorresult['frame']=frame
            # self.logger.debug(f'dozor result {json.dumps(command[1], indent=4)}')
            if command[1]['view'] == 1:
                view1=True
                view = 'View1'
            else:
                view1=False
                view = 'View2'
                
            x,y=self.convertFrametoXY(command[1]['frame']+1,view1)#frame start from 0 
            
            # self.logger.warning(f'X,Y = {x},{y}, Target array shape:{self.RasterPar[view]["scoreArray"].shape}')
            self.RasterPar[view]['scoreArray'][x][y] = float(command[1]['score'])
            self.RasterPar[view]['resArray'][x][y] = float(command[1]['res'])
            self.RasterPar[view]['spotsArray'][x][y] = float(command[1]['spots'])
            self.Par[view]['scoreArray'][x][y] = float(command[1]['score'])
            self.Par[view]['resArray'][x][y] = float(command[1]['res'])
            self.Par[view]['spotsArray'][x][y] = float(command[1]['spots'])
            
            if (time.time()-self.timeformessageFromMeshbest)>0.1:
                self.timeformessageFromMeshbest=time.time()
                self.plotdozor_update(x,y,True,'score',view)
                #try full update?not work....
                # self.plotdozor(True,'score',view,1)
                
                #will not update all point
            else:
                # self.plotdozor_update(x,y,True,'score',view)
                #not update gui
                #may lack last one?
                #put in temp update list?
                pass
            # self.logger.warning(f'data:{self.RasterPar[view]["scoreArray"]}')
            
        elif command[0] == 'updatePar':
            # try:
            #     self.logger.warning(f"test: {command[1]['View1'].keys()}")
            #     self.logger.warning(f"test: {command[1]['View1']['jpg'][:5]}")
            # except:
            #     pass
            #server tell client to update, maybe come from active clinet or server itself
            

            #from here will updated all par

            # temp = copy.deepcopy(command[1])
            
            # temp['View1'].pop('jpg', None)
            # temp['View2'].pop('jpg', None)
            # self.logger.info(f'got updatePar :{temp}======')
            try:
                if self.Par['StateCtl']['reciveserverupdate'] == False and self.bluiceData['active']:
                    self.logger.warning('Do not update!I am doing my job')
                    return
            except Exception as e:
                traceback.print_exc()
                self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
                self.logger.warning(f'Error:{e}')
            if self.bluiceData['active']:
                self.logger.debug(f'I am active client,update Dtable only and XY')
                #active only update Dtable
                view1_data = self.Par['View1']
                view2_data = self.Par['View2']

                view1_data['Dtable'] = command[1]['View1']['Dtable']
                view1_data['Ztable'] = command[1]['View1']['Ztable']
                view1_data['BestPositions'] = command[1]['View1']['BestPositions']
                view1_data['numofX'] = command[1]['View1']['numofX']
                view1_data['numofY'] = command[1]['View1']['numofY']
                view2_data['Dtable'] = command[1]['View2']['Dtable']
                view2_data['Ztable'] = command[1]['View2']['Ztable']
                view2_data['BestPositions'] = command[1]['View2']['BestPositions']
                view2_data['numofX'] = command[1]['View2']['numofX']
                view2_data['numofY'] = command[1]['View2']['numofY']
                ui_par_data = self.Par['UI_par']
                StateCtl_data = self.Par['StateCtl']
                # view1_collectInfo = 
                # self.logger.info(f'Test: view1_data Ztable {view1_data["Ztable"]}')
            else:
                self.logger.info(f'I am inactive client,update all')
                view1_data = command[1]['View1']
                view2_data = command[1]['View2']
                ui_par_data = command[1]['UI_par']
                StateCtl_data = command[1]['StateCtl']
                
            
            self.Par['View1'] = view1_data
            self.Par['View2'] = view2_data
            self.Par['UI_par'] = ui_par_data
            self.Par['StateCtl'] = StateCtl_data
            # self.logger.info(f'got view1 dtable = {command[1]["View1"]["Dtable"]}')
            # self.logger.info(f'got view2 dtable = {command[1]["View2"]["Dtable"]}')
            #update and decode Dtable to Raster
            Dtable,Ztable,BestPositions = self.decodeTable(self.Par['View1'])
            self.RasterPar['View1']['Dtable'] = Dtable
            self.RasterPar['View1']['Ztable'] = Ztable
            #filter bad pos
            filterBestPositions = self.filter_BestPositions(BestPositions)

            self.RasterPar['View1']['BestPositions'] = filterBestPositions
            
            Dtable,Ztable,BestPositions = self.decodeTable(self.Par['View2'])
            self.RasterPar['View2']['Dtable'] = Dtable
            self.RasterPar['View2']['Ztable'] = Ztable
            filterBestPositions = self.filter_BestPositions(BestPositions)


            self.RasterPar['View2']['BestPositions'] = filterBestPositions
            
            self.RasterPar['View1']['scoreArray'] = view1_data['scoreArray']
            self.RasterPar['View1']['resArray'] = view1_data['resArray']
            self.RasterPar['View1']['spotsArray'] = view1_data['spotsArray']
            self.RasterPar['View2']['scoreArray'] = view2_data['scoreArray']
            self.RasterPar['View2']['resArray'] = view2_data['resArray']
            self.RasterPar['View2']['spotsArray'] = view2_data['spotsArray']
            # self.logger.info(f'after update Par :{self.Par}')
            # self.logger.info(f'after view1 decode = {self.RasterPar["View1"]["Dtable"]}')
            # self.logger.info(f'after view2 decode = {self.RasterPar["View2"]["Dtable"]}')
            if self.bluiceData['active']:
                if len(self.Par['View1']['collectInfo'])>0:
                    self.collectAllpos_1.setEnabled(True)
                if len(self.Par['View2']['collectInfo'])>0:
                    self.collectAllpos_2.setEnabled(True)
                        
            else:
                # self.logger.debug(f'view1_data update Par :{self.RasterPar["View1"]["scoreArray"]}')
                # self.logger.debug(f'after update Par :{self.RasterPar}')
                self.collectAllpos_1.setEnabled(False)
                self.collectAllpos_2.setEnabled(False)
                pass

            # full update
            # self.logger.warning(f'{self.Par=}')
            self.full_update(self.Par)
            #replot
            try:
                #this area define special update
                if len(command) >= 3:
                    self.logger.warning(f'updatetype : {command[2]=}')
                    if command[2] == 'passvie' and self.bluiceData['active']:
                        #server only ask update passive one
                        return
                    elif command[2] == "plotBestpos_View1":
                        self.plotBestpos('View1')
                        return
                    elif command[2] == "plotBestpos_View2":
                        self.plotBestpos('View2')
                        return
                    elif command[2] == "plotbox":
                        self.plotbox()
                        return
                    elif command[2] == "plotView12":
                        self.plotView12()
                        return
                    else:
                        self.plotView12(False)#false not clear sozor array  
                else:
                    self.plotView12(False)#false not clear sozor array
            except Exception as e:
                traceback.print_exc()
                self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
                self.logger.warning(f'Error : {e}')
                self.plotView12(False)#false not clear sozor array  
                pass
            
        elif command[0] == 'notify_ui_update':
            if command[1] == 'meshbetjob':
                sid = command[2]
                if sid == 101:
                    if self.updatelist_1.currentIndex() == 0:#meshbest
                        #view1 update
                        self.Overlap_Select_1.setCurrentIndex(6)#Crystal Map with Dozor score
                        self.plot_overlap_image('View1') #make sure it update
                        listnum1=len(self.RasterPar['View1']['BestPositions'])      
                        self.List_number_1.setValue(listnum1)
                        #creat collect info
                        self.create_collectinfo('View1')
                        #plot position
                        self.plotBestpos('View1')
                        pass
                else:
                    if self.updatelist_2.currentIndex() == 0:
                        #view2 update
                        self.Overlap_Select_2.setCurrentIndex(6)#Crystal Map with Dozor score
                        self.plot_overlap_image('View2') #make sure it update
                        listnum2=len(self.RasterPar['View2']['BestPositions'])
                        self.List_number_2.setValue(listnum2)    
                        #creat collect info
                        self.create_collectinfo('View2')
                        #plot position
                        self.plotBestpos('View2')

                    pass
                
            else:
                pass
        else:
            pass
        #    self.logger.debug(f'Meshbest Emit : {command}')
        
    def decodeTable(self,par):
        try:
            # self.logger.warning(f'Decode ori  Datble:{par["Dtable"]}')
            # row, col = par['GridY'], par['GridX']         
            if par['Dtable'] == None:
                return None,None,None
            row, col = par['numofY'], par['numofX']
            Dtable = np.frombuffer(base64.b64decode(par['Dtable']))
            Dtable = np.reshape(Dtable, (row, col))
            Ztable = np.frombuffer(base64.b64decode(par['Ztable']))
            Ztable = np.reshape(Ztable, (row, col))
            BestPositions = np.frombuffer(base64.b64decode(par['BestPositions']))
            BestPositions = np.reshape(BestPositions, (int(np.size(BestPositions)/4),4))
        except Exception as e:
            traceback.print_exc()
            self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
            self.logger.warning(f'Has error when decodeTable {e}')
            Dtable = None
            Ztable = None
            BestPositions = None
            # self.logger.warning(f'After decode Datble:{Dtable}')
        return Dtable,Ztable,BestPositions

    def plot_overlap_image(self,view='View1'):
        # self.Overlap_Select_1.setItemText(0, _translate("MainWindow", "None"))
        # self.Overlap_Select_1.setItemText(1, _translate("MainWindow", "Grid"))
        # self.Overlap_Select_1.setItemText(2, _translate("MainWindow", "Dozor score"))
        # self.Overlap_Select_1.setItemText(3, _translate("MainWindow", "Number of Peaks"))
        # self.Overlap_Select_1.setItemText(4, _translate("MainWindow", "Visible resolution"))
        # self.Overlap_Select_1.setItemText(5, _translate("MainWindow", "Crystal Map"))
        # self.Overlap_Select_1.setItemText(6, _translate("MainWindow", "Crystal Map with Dozor score"))
        if view =='View1':
            select =  self.Overlap_Select_1
            Opacity = self.view1_opacity.value()/100
        else:
            select =  self.Overlap_Select_2
            Opacity = self.view2_opacity.value()/100
        self.logger.debug(f'Opacity={Opacity}')
        self.plotBestpos(view)#always plot bestpos
        if select.currentIndex() == 0:
            self.setOpacity_dozor_plot(0,view,showGrid=False,ClearFill=True,ClearText=True)
            self.RasterPar[view]['overlap_QPixmap'].setOpacity(0)
            pass
        elif select.currentIndex() == 1:#grid
            self.setOpacity_dozor_plot(Opacity,view,showGrid=True,ClearFill=True,ClearText=True)
            self.RasterPar[view]['overlap_QPixmap'].setOpacity(0)
            pass
        elif select.currentIndex() == 2:#Dozor score
            self.plotdozor(True,'score',view,Opacity)
            self.RasterPar[view]['overlap_QPixmap'].setOpacity(0)
        elif select.currentIndex() == 3:#Number of Peaks
            self.plotdozor(True,'spots',view,Opacity)
            self.RasterPar[view]['overlap_QPixmap'].setOpacity(0)
        elif select.currentIndex() == 4:#Visible resolution
            self.plotdozor(True,'res',view,Opacity)
            self.RasterPar[view]['overlap_QPixmap'].setOpacity(0)
        elif select.currentIndex() == 5:#Crystal Map
            #clear dozor plot
            self.setOpacity_dozor_plot(0,view,showGrid=False,ClearFill=True,ClearText=True)
            
            self.plot_meshbet("",view,overlapDozor=False)
            self.RasterPar[view]['overlap_QPixmap'].setOpacity(Opacity)
        elif select.currentIndex() == 6:#Crystal Map with Dozor score
            self.setOpacity_dozor_plot(0,view,showGrid=False,ClearFill=True,ClearText=True)
            
            self.plot_meshbet("",view,overlapDozor=True)
            self.RasterPar[view]['overlap_QPixmap'].setOpacity(Opacity)
        pass
    def plot_meshbet(self,Type="",view='View1',overlapDozor=True):
        # print(self.Raster[view])
        Dtable = self.RasterPar[view]['Dtable']
        Ztable = self.RasterPar[view]['Ztable']
        BestPositions = self.RasterPar[view]['BestPositions']
        
        try:
            if len(Ztable) < 1:
                return
        except:
                return
        if view =='View1':
            listnum = self.List_number_1.value()
        else:
            listnum = self.List_number_2.value()
        tempimage = genZTableMap(Ztable,Dtable,BestPositions,cmap='hot_with_alpha',
                                 addPositions=False,listnum=listnum,
                                 addText=False,Textsize=12,txtcolor='white',
                                 Circle_color='orange',overlapDozor=overlapDozor)
        
        # scanarea = self.RasterPar[view]['box']#this is full size
        scanarea = self.RasterPar[view]['viewRect'].boundingRect()
        TargetImageSize = QSize(int(scanarea.width()),int(scanarea.height()))
        # self.logger.warning(f'TargetImageSize={TargetImageSize}')
        newimage = tempimage.scaled(TargetImageSize,QtCore.Qt.KeepAspectRatio)
        self.RasterPar[view]['overlap_QPixmap'].setPixmap(newimage)
        self.RasterPar[view]['overlap_QPixmap'].setPos(scanarea.x(),scanarea.y())
        self.plotBestpos(view)
        pass
    
    def setOpacity_dozor_plot(self,opacity,view='View1',showGrid = True,ClearFill=False,ClearText=False):
        try :
            if type(self.RasterPar[view]['boxRectItemarray'][0][0]) == type(QGraphicsRectItem()):
                hasitem = True
            else:
                hasitem = False
        except:
            hasitem = False
        if hasitem:
            self.logger.debug(f'setOpacity_dozor_plot to {opacity}')
            for x,item in enumerate(self.RasterPar[view]['boxRectItemarray']):
                for y,item2 in enumerate(item):
                    item2.setOpacity(opacity)
                    if showGrid :
                        item2.setPen(QPen(QColor('yellow')))
                    else:
                        item2.setPen(QPen(QColor(0, 0, 0, 0)))
                    if ClearFill:
                        item2.setBrush(QColor(0, 0, 0, 0))
                    
        else:
            self.logger.debug(f'no QGraphicsRectItem in boxRectItemarray,bypass setting')
        try :
            if type(self.RasterPar[view]['Textplotarray'][0][0]) == type(QGraphicsTextItem()):
                hasitem2 = True
            else:
                hasitem2 = False
        except:
            hasitem2 = False
        # self.logger.warning(f'{hasitem2=}')
        try:
            if hasitem2:
                for x,item in enumerate(self.RasterPar[view]['Textplotarray']):
                        for y,item2 in enumerate(item):
                            # self.logger.warning(f'{ClearText=}')
                            if ClearText:
                                # item2.setDefaultTextColor(QColor(0,0,0,0))
                                item2.setVisible(False)
                                pass
                            else:
                                # item2.setDefaultTextColor(QColor('white'))
                                item2.setVisible(True)
                                pass
        except Exception as e:
            traceback.print_exc()
            self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
            self.logger.warning(f'Error:{e}')


        
    def plotdozor_update(self,x,y,text,Type,view='View1',Opacity=100):
        
        if Type == "spots":
            array = self.RasterPar[view]['spotsArray']
            data = array[x][y]
            datatext = f'{data:1.0f}'
        elif Type == "res":
            array = self.RasterPar[view]['resArray']
            data = array[x][y]
            datatext = f'{data:1.1f}'
        elif Type == "score":
            array = self.RasterPar[view]['scoreArray']
            data = array[x][y]
            datatext = f'{data:1.1f}'
            self.logger.debug(f'scoreArray = {array}')
        else:
            self.logger.info("Unkonw plot type")
            return
        if view == 'View1':
            Rasterscene= self.Rasterscene1
            r=1
            view1 = True
            par = self.RasterPar['View1']
        else:
            Rasterscene= self.Rasterscene2
            r=2
            view1 =False
            par = self.RasterPar['View2']
        
            
        # try:
        #     for a in self.RasterPar[view]['Textplotarray'] :
        #         for b in a :
        #             Rasterscene.removeItem(b)
                    
                    
        # except:
        #     pass
        numofXbox = par['numofX']
        numofYbox = par['numofY']
        smallbox = par['boxRectItemarray'][0][0]
        if smallbox.boundingRect().width() <= 1:
            # box too small(small than xx)
            #not plot text
            print(f'{smallbox.boundingRect().width()=}')
            pass
        else:
            # print('here')
            # qpen = QPen()
            # qpen.setColor(QColor('white'))
            # qp=QPainter.setPen(qpen)
            
            myfont = QFont()
            myfont.setBold(False)
            myfont.setPointSize(10)
            
            ratio = self.getViewRatio(r)
            x0,y0,xc,yc=self.plottool_getpixel(x,y,ratio,view1)
            # temp = Rasterscene.addText(datatext)
            temp = self.RasterPar[view]['Textplotarray'][x][y]
            # temp.paint(qp)
            temp.setPlainText(datatext)
            temp.setFont(myfont)
            
            if temp.boundingRect().width()>smallbox.boundingRect().width():
                resizeR = smallbox.boundingRect().width()/temp.boundingRect().width()
                myfont.setPointSize(int(10*resizeR))
                temp.setFont(myfont)
            
            temp.setPos(xc-temp.boundingRect().width()/2,yc-temp.boundingRect().height()/2)
            # if text:
            #     # temp.setDefaultTextColor(QColor('white'))
            #     # qpen = QPen()
            #     # qpen.setColor(QColor('white'))
            #     # qp=QPainter()
            #     # qp.setPen(qpen)
            #     # temp.paint(qp,QtWidgets.QStyleOptionGraphicsItem(),QWidget())
            #     # temp.update(temp.boundingRect())
            #     pass
            # else:
                # temp.setDefaultTextColor(QColor(0,0,0,0))
            
            pos = (xc-temp.boundingRect().width()/2,yc-temp.boundingRect().height()/2)
            # self.logger.debug(f'x={x},y={y},pos={pos}')                
            # self.RasterPar[view]['Textplotarray'][x][y] = temp
            temp.setVisible(True)
            temp.setOpacity(Opacity)
            
        self.DrawColoronBox(array,view,Opacity)
            
            # self.RasterPar[view]['boxRectItemarray'][x][y].setBrush(QColor(Color))
    def DrawColoronBox(self,array,view='View1',Opacity=100):                
        maxi = np.nanmax(array)
        if maxi==0 :
            maxi=255
        for x,item in enumerate(self.RasterPar[view]['boxRectItemarray']):
            for y,item2 in enumerate(item):
                value = array[x][y]
                if np.isnan(value):
                    Color=cc.cwr[0]
                    QQColor = QColor(Color)
                    QQColor.setAlpha(0)
                else:
                    Cindex = int(value/maxi*255)
                    Color=cc.cwr[Cindex]
                    QQColor = QColor(Color)
                    if Cindex < 1:
                        QQColor.setAlpha(0)
                    elif Cindex < 12:
                        QQColor.setAlpha(125)
                    else:
                        QQColor.setAlpha(230)
                item2.setBrush(QQColor)
                item2.setOpacity(Opacity)
                    
    def clear_dozor_plot(self):
        try:
            for a in self.RasterPar['View1']['Textplotarray'] :
                for b in a :
                    self.Rasterscene1.removeItem(b)
        except:
                pass
        try:
            for a in self.RasterPar['View2']['Textplotarray'] :
                for b in a :
                    self.Rasterscene2.removeItem(b)
        except:
                pass
    def plotdozor(self,text,Type,view='View1',Opacity=1):
        if view =='View1':
            select =  self.Overlap_Select_1
        else:
            select =  self.Overlap_Select_2
        if not select.currentIndex() in [2,3,4,5]:
            return
        try:
            numofXbox =self.RasterPar[view]['numofX']
            numofYbox =self.RasterPar[view]['numofY']
            if numofXbox == 0 or  numofYbox== 0:
                return
            # self.logger.warning(f'plt:{self.RasterPar[view]["scoreArray"]}')
            if Type == "spots":
                array = self.RasterPar[view]['spotsArray']
                
                testarray = np.zeros((numofXbox, numofYbox))
                testarray[:] = np.nan
                if np.array_equal(array, testarray, equal_nan=True):
                    return
                txtformat = '1.0f'
            elif Type == "res":
                array = self.RasterPar[view]['resArray']
                testarray = np.zeros((numofXbox, numofYbox))
                testarray[:] = 50
                if np.array_equal(array, testarray, equal_nan=True):
                    return
                txtformat = '1.1f'
            elif Type == "score":
                array = self.RasterPar[view]['scoreArray']
                testarray = np.zeros((numofXbox, numofYbox))
                testarray[:] = np.nan
                # self.logger.warning(f'testarray={testarray},array={array},{np.array_equal(array, testarray, equal_nan=True)}')
                if np.array_equal(array, testarray, equal_nan=True):
                    return
                txtformat = '1.1f'
            else:
                self.logger.info("Unkonw plot type")
                return
            if view == 'View1':
                Rasterscene= self.Rasterscene1
                r=1
                view1 = True
                par = self.RasterPar['View1']
            else:
                Rasterscene= self.Rasterscene2
                r=2
                view1 =False
                par = self.RasterPar['View2']
            
            
                
            try:
                for a in self.RasterPar[view]['Textplotarray'] :
                    for b in a :
                        Rasterscene.removeItem(b)                       
            except:
                pass
            # numofXbox = par['numofX']
            # numofYbox = par['numofY']
            self.logger.info(f'{view=}, {numofXbox=},{numofYbox=}')
            myfont = QFont()
            myfont.setBold(False)
            myfont.setPointSize(10)
            self.RasterPar[view]['Textplotarray']=[[0]*numofYbox for i in range(numofXbox)]
            # self.logger.warning(f'numofXbox={numofXbox},numofYbox={numofYbox}')     
            ratio = self.getViewRatio(r)
            try:
                smallbox = par['boxRectItemarray'][0][0]
            except IndexError:
                # smallbox = QGraphicsRectItem()
                print('error here')
                return
            
                
            for x,item in enumerate(array):
                for y,item2 in enumerate(item):
                    
                    x0,y0,xc,yc=self.plottool_getpixel(x,y,ratio,view1)
                    
                    temp = Rasterscene.addText(f'{item2:{txtformat}}',myfont)
            
                    if temp.boundingRect().width()>smallbox.boundingRect().width():
                        resizeR = smallbox.boundingRect().width()/temp.boundingRect().width()
                        myfont.setPointSize(int(10*resizeR))
                        temp.setFont(myfont)
                        
                    # temp.setPen(QPen(QColor('yellow')))
                    # temp.setFont(myfont)
                    temp.setPos(xc-temp.boundingRect().width()/2,yc-temp.boundingRect().height()/2)
                    if text:
                        temp.setDefaultTextColor(QColor('white'))
                    else:
                        temp.setDefaultTextColor(QColor(0, 0, 0, 0))
                    pos = (xc-temp.boundingRect().width()/2,yc-temp.boundingRect().height()/2)
                    # self.logger.info(f'x={x},y={y},pos={pos}')                
                    temp.setOpacity(Opacity)
                    # try:
                    self.RasterPar[view]['Textplotarray'][x][y] = temp
                    # except Exception as e:
                    #     traceback.print_exc()
                    #     self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
                    #     self.logger.warning(f'Error:{e}')
            self.DrawColoronBox(array,view,Opacity)   
        except Exception as e:
            traceback.print_exc()
            self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
            self.logger.warning(f'Error:{e}')
            
        
    def plottool_getpixel(self,indexX,indexY,ratio,view1=True):
        if view1:
            par = self.RasterPar['View1']
        else:
            par = self.RasterPar['View2']
            
        gridsizeX = par['gridsizeX']
        gridsizeY = par['gridsizeY']
        camscaleX = par['zoom_scale_x']
        camscaleY = par['zoom_scale_y']
        numofXbox = par['numofX']
        numofYbox = par['numofY']
        bigbox = par['box']
        startx = bigbox.x() / ratio
        starty = bigbox.y() / ratio
        # print(f'{gridsizeX=},{camscaleX=},{ratio=}')
        if not camscaleX:#no old par
            camscaleX=1
            camscaleY=1
        w = gridsizeX / camscaleX / ratio
        h = gridsizeY / camscaleY / ratio
        
        x0 = startx + indexX*w
        y0 = starty + indexY*h
        centerX = startx + (indexX+0.5)*w
        centerY = starty + (indexY+0.5)*w
        
        return x0,y0,centerX,centerY
        
    def convertFrametoXY(self,number,view1=True):
        #1 = right left conor
        if view1:
            par = self.RasterPar['View1']
        else:
            par = self.RasterPar['View2']
            
        numofX = par['numofX']
        numofY = par['numofY']
        if number%numofY == 0:
            #in last row
            offset = 0
            
        else:
            offset = 1
            
        
        col = numofX - int(number/numofY)-offset #ver line
        
        revseCol = numofX - col
        
        if (revseCol%2) == 1:
            #even line0,2,4,6,8.....
            # maxinline=(revseCol+1)*numofY
            row = number % numofY -1
            if row == -1:
                row = numofY - 1
            
        else:
            #odd 1,3,5...
            row = numofY - (number % numofY)
            if row == numofY:
                row = 0
        self.logger.debug(f'Frame={number} ,numofX={numofX},numofY={numofY},offset={offset},col={col},row={row}')
        return col,row#X,Y

    def convertXYtoFrame(self,x,y,view1=True):
        if view1:
            par = self.RasterPar['View1']
        else:
            par = self.RasterPar['View2']
            
        numofX = par['numofX']
        numofY = par['numofY']
        reversedx=numofX-x-1
        reversedy=numofY-y-1
        if reversedx%2 ==0:
            #even
            frame = reversedx*numofY+y+1
            
        else:
            #odd
            
            frame = reversedx*numofY+reversedy+1
        print(f'{reversedx=},{reversedy=},{frame=}')
        return frame
    def messageFromBluice(self,command):
        
        if command[0] == "stog_login_complete":
            self.bluiceID = int(command[1])
            self.logger.info(f'My bluice ID is {self.bluiceID}')
            self.setToPassive()
        elif command[0] == "stog_become_master":
            pass#has bug??
            self.setToActive()
            # self.logger.warning(command)
        elif command[0] == "stog_become_slave":
            self.setToPassive()
            # self.logger.warning(command)
                            
        elif command[0] == "stog_update_client_list":
            self.bluiceclientlists = {}
            self.numofclient  = int(command[1])
        elif command[0] == "stog_update_client":
            #update bluiceclientlists
            #['stog_update_client', '77', 'blctl', '{Beamline', 'Control}', '{REMOTE}', '{Beamline', 'Scientist}', '1', '1', 'gui07a1.nsrrc.org.tw', '{}', '1', '0'
            oldstr=""
            for item in command:
                oldstr = oldstr + item + " "
            
            
            temp ={}
            temp['id'] = command[1]
            temp['user'] = command[2]
            index = 0
            temp['fullname'] , index2 = self.dealClientlist(oldstr,index) 
            temp['location'] , index3 = self.dealClientlist(oldstr,index2) 
            temp['title'] , index4 = self.dealClientlist(oldstr,index3) 
            a = oldstr[index4:].split(" ")
            # print("aaa=",a)
            temp['active'] = bool(int(a[5]))
            # self.logger.info(f'update :{temp}')
            self.bluiceclientlists[str(command[1])] = temp
            # self.updateActiveState() #not used any more
            # self.logger.info(f'update client list : {self.bluiceclientlists}')
        elif command[0] == "stog_configure_pseudo_motor":
            # stoh_configure_real_motor motoName position upperLimit lowerLimit scaleFactor speed acceleration backlash lowerLimitOn upperLimitOn motorLockOn backlashOn reverseOn 
            # [u'stog_configure_pseudo_motor', u'fluxmode', u'idhs', u'fluxmode', u'1.000000', u'2.000000', u'-2.000000', u'0', u'0', u'0', u'']
            motorname=command[1]
            pos=command[4]
            self.bluiceData['motor'][motorname] ={}
            self.bluiceData['motor'][motorname]['pos']=float(pos)
            self.bluiceData['motor'][motorname]['moving'] = False
            self.update_motorpos_to_ui(motorname,pos,False)
        elif command[0] == "stog_configure_real_motor":
            # stoh_configure_real_motor motoName position upperLimit lowerLimit scaleFactor speed acceleration backlash lowerLimitOn upperLimitOn motorLockOn backlashOn reverseOn 
            #[u'stog_configure_real_motor', u'detector_z', u'idhs', u'detector_z', u'400.000000', u'910.000000', u'100.900000', u'78.740000', u'1000', u'350', u'-238', u'1', u'1', u'0', u'1', u'1', u'']
            motorname=command[1]
            pos=command[4]
            self.bluiceData['motor'][motorname] ={}
            self.bluiceData['motor'][motorname]['pos']=float(pos)
            self.bluiceData['motor'][motorname]['moving'] = False
            self.update_motorpos_to_ui(motorname,pos,False)
        elif command[0] == "stog_configure_string":
            # ['stog_configure_string', 'beamlineOpenState', 'idhs', 'Closed', '3654660363']
            # ['stog_configure_string', 'madScanStatus', 'self', '0', '{DCSS', 'was', 'reset}', 'TPP', '/data/TPP/20190815_05A/afa/acidob_bac/Zn_MAD/TPP0402/A9/Zn_scan', 'A9', 'Zn-K', '{9659.000', 'eV}', '{8638.9', 'eV}', '{1.000', 's}', '{9664.497070', '-7.906010', '2.686792', '9677.975586', '-5.964602', '4.724238', '10000.000000', '-2.600000', '3.600000', 'NULL/A9scan', 'A9smooth_exp.bip', 'A9smooth_norm.bip', 'A9fp_fpp.bip}', '/data/blctl/currentExcitationScan/BL7-1.bip']
            name = command[1]
            dhs = command[2]
            a = command
            del a[0:3]
            string=""
            for item in a:
                string = string + item + " "
            
            self.bluiceData['string'][name] ={}
            self.bluiceData['string'][name]['state'] = 'unkonw'
            self.bluiceData['string'][name]['dhs'] = dhs
            self.bluiceData['string'][name]['txt'] = string.rstrip()

            self.update_string_to_ui(name,a)
            # self.bluiceData['string'][name]['array'] = a
        elif command[0] =="stog_set_string_completed":
            # ['stog_set_string_completed', 'screeningActionList', 'normal', '0', '-1', '0', '{1', '1', '1', '1', '1', '1', '1', '1', '0', '0', '0', '0', '0', '0', '0', '1}']
            # ['stog_set_string_completed', 'madScanStatus', 'normal', '0', '{DCSS', 'was', 'reset}', 'TPP', '/data/TPP/20190815_05A/afa/acidob_bac/Zn_MAD/TPP0402/A9/Zn_scan', 'A9', 'Zn-K', '{9659.000', 'eV}', '{8638.9', 'eV}', '{1.000', 's}', '{9664.497070', '-7.906010', '2.686792', '9677.975586', '-5.964602', '4.724238', '10000.000000', '-2.600000', '3.600000', 'NULL/A9scan', 'A9smooth_exp.bip', 'A9smooth_norm.bip', 'A9fp_fpp.bip}', '/data/blctl/currentExcitationScan/BL7-1.bip']
            # ['stog_set_string_completed', 'system_status', 'normal', '{EPICS', 'offline}', 'black', 'red']
            name = command[1]
            state = command[2]
            a = command
            del a[0:3]
            string=""
            for item in a:
                string = string + item + " "
            self.bluiceData['string'][name]['state'] = state
            self.bluiceData['string'][name]['txt'] = string.rstrip()
            self.bluiceData['string'][name]['array'] = a
            self.update_string_to_ui(name,a)
            #todo update system_status to state bar?
        elif command[0] == "stog_set_motor_base_units":
            # ['stog_set_motor_base_units', 'maxOscTime', 's']
            motorname = command[1]
            unit = command[2]
            self.bluiceData['motor'][motorname]['unit'] = unit
        elif command[0] == "stog_configure_ion_chamber":
            # ['stog_configure_ion_chamber', 'i0', 'simdhs', 'daqIon', '0', 'rtc1', 'standardVirtualIonChamber']
            name=command[1]
            dhs = command[2]
            self.bluiceData['ionchamber'][name] = {}
            self.bluiceData['ionchamber'][name]['dhs'] = dhs
            self.bluiceData['ionchamber'][name]['array'] = dhs
        elif command[0] == "stog_configure_shutter":
            # ['stog_configure_shutter', 'Al_1', 'simdhs', 'open']
            shuttername = command[1]
            dhs = command[2]
            if command[3] == 'open':
                opened = True
            else:
                opened = False
            self.bluiceData['shutter'][shuttername] = {}
            self.bluiceData['shutter'][shuttername]['dhs'] = dhs
            self.bluiceData['shutter'][shuttername]['opened'] = opened
        elif command[0] == "stog_report_shutter_state":
            # ['stog_report_shutter_state', 'shutter', 'closed', 'no_hw_host_EPICS']
            shuttername = command[1]
            
            if command[2] == 'open':
                opened = True
            else:
                opened = False
            # state = command[3]
            self.bluiceData['shutter'][shuttername]['opened'] = opened
            
        elif command[0] == 'stog_configure_hardware_host' :
            # ['stog_configure_hardware_host', 'EPICS', 'self', 'online']
            dhsname = command[1]
            if command[3] == 'online':
                online = True
            else:
                online = False
            self.bluiceData['dhs'][dhsname] = {}
            self.bluiceData['dhs'][dhsname]['online'] = online
            
        elif command[0] == "stog_motor_move_started":
            #"stoh_start_motor_move motorName destination
            motorname=command[1]
            self.bluiceData['motor'][motorname]['moving']=True
            pos = self.bluiceData['motor'][motorname]['pos']
            self.update_motorpos_to_ui(motorname,pos,True)
            # print(command,self.bluiceData['motor'][motorname]['moving'])
        elif command[0] == "stog_update_motor_position":
            # ['stog_update_motor_position', 'cam_horz', '-0.539248', 'normal']
            motorname=command[1]
            pos = command[2]
            self.bluiceData['motor'][motorname]['pos']=float(pos)
            moving = self.bluiceData['motor'][motorname]['moving']
            self.update_motorpos_to_ui(motorname,pos,moving)
        elif command[0] == "stog_motor_move_completed":
            #[u'stog_motor_move_completed', u'change_mode', u'4.000000', u'normal']
            motorname=command[1]
            pos=command[2]
            if motorname == 'centerLoop':
                #todo maybe need change epics dhs
                #Traceback (most recent call last):
                # File "/NAS/Eddie/TPS07A/MeshbestServer/MestbestGUI.py", line 2473, in messageFromBluice
                #     self.bluiceData['motor'][motorname]['pos']=float(pos)
                # KeyError: 'centerLoop'
                pass
            else:
                self.bluiceData['motor'][motorname]['pos']=float(pos)
                self.bluiceData['motor'][motorname]['moving'] = False
            self.update_motorpos_to_ui(motorname,pos,False)
            # print(command,self.bluiceData['motor'][motorname]['moving'])
        elif command[0] == "stog_configure_operation":
            # ['stog_configure_operation', 'collectShutterless', 'self']
            # self.logger.warning(f'Bluice Emit : {command}')
            opname=command[1]
            dhs = command[2]
            # a = command
            # del a[0:3]
            # string=""
            # for item in a:
                # string = string + item + " "
            self.bluiceData['operation'][opname]={}
            self.bluiceData['operation'][opname]['moving'] = False
            self.bluiceData['operation'][opname]['dhs'] = dhs
            # self.bluiceData['operation'][opname]['txt'] = string
            # self.bluiceData['operation'][opname]['array'] = a
           
            pass    
        elif command[0] == "stog_start_operation":
            #stoh_start_operation operationName operationHandle [arg1 [arg2 [arg3 [...]]]]
            #operationName is the name of the operation to be started.
            #operationHandle is a unique handle currently constructed by calling the create_operation_handle procedure in BLU-ICE. This currently creates a handle in the following format:
            #clientNumber.operationCounter
            #where clientNumber is the number provided to the BLU-ICE by DCSS via the stog_login_complete message. DCSS will reject an operation message if the clientNumber does not match the client. The operationCounter is a number that the client should increment with each new operation that is started.
            #arg1 [arg2 [arg3 [...]]] is the list of arguments that should be passed to the operation. It is recommended that the list of arguments continue to follow the general format of the DCS message structure (space separated tokens). However, this requirement can only be enforced by the writer of the operation handlers.
            #[u'stog_start_operation', u'getMD2Motor', u'1.24970', u'camera_zoom']
            #[u'stog_start_operation', u'moveSample', u'122.327', u'-303.00686378', u'-91.6692524683']
            # ['stog_start_operation', 'moveSample', '2.5', '229.313358302', '103.03900156']
            # set x [expr 1280 * [$itk_component(canvas) canvasx $x] / $m_imageWidth]
            # set y [expr 1024 * [$itk_component(canvas) canvasy $y] / $m_imageHeight]
            #[u'stog_start_operation', u'collectRun', u'122.332', u'0', u'che', u'0', u'PRIVATEXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX']
            opname=command[1]
            opid = command[2]
            a = command
            del a[0:3]
            string=""
            for item in a:
                string = string + item + " "
            self.bluiceData['operation'][opname]['moving'] = True
            self.bluiceData['operation'][opname]['id'] = opid
            self.bluiceData['operation'][opname]['txt'] = string
            self.bluiceData['operation'][opname]['array'] = a
            pass
        elif command[0] == "stog_operation_completed":
            # ['stog_operation_completed', 'moveSample', '64.5', 'error', 'sample_x_no_hw_host_EPICS']
            # ['stog_operation_completed', 'getMD2Motor', '1.75', 'normal', 'camera_zoom']
            opname=command[1]
            opid = command[2]
            a = command
            del a[0:3]
            string=""
            for item in a:
                string = string + item + " "
            self.bluiceData['operation'][opname]['moving'] = False
            self.bluiceData['operation'][opname]['id'] = opid
            self.bluiceData['operation'][opname]['txt'] = string
            self.bluiceData['operation'][opname]['array'] = a
            if opname == 'moveSample':
                self.SampleViedo.setCursor(QCursor(QtCore.Qt.CrossCursor))
                self.SampleViedo.setToolTip('Click will move the pos. to center')
        elif command[0] == "stog_device_permission_bit":
            #['stog_device_permission_bit', 'injectState', '{0', '1', '1', '1', '1}', '{0', '1', '1', '1', '1}'] 
            pass
        elif command[0] == "stoh_abort_all":#gui will not recive this
            self.abort = True
            self.collectPause = True
            self.timer.singleShot(500,self.restAbort)
        elif command[0] == "stog_note":
            # ['stog_note', 'Warning', 'Raster', 'Scan', 'has', 'problem:', "'Raster", "Scan',", "'8',", "'2022-05-05", "08:47:16.995',", "'2022-05-05", "08:47:26.98',", "'null',", "'Cannot", 'move', 'to', 'position:', "Omega=220.9999',", "'-1'", ''] 
            if command[1] == 'Warning' and command[2] == 'Raster':
                txtlist = command[3:]
                txt =command[2]#start with raster and add space in rest str
                for item in txtlist:
                    txt = f'{txt} {item}'
                txt += f'\n\nmaybe need to increase Exposure time'
                mesbox = QMessageBox.warning(self,"Warning from DCSS",txt,QMessageBox.Ok)
                #move md3 make state to ready
                pos =self.bluiceData['motor']['gonio_phi']['pos']
                command = f'gtos_start_motor_move gonio_phi {pos}'
                self.Qinfo["sendQ"].put(command)
                self.StartRaster.setEnabled(True)
                self.Par['StateCtl']['AbletoStartRaster'] = True
                self.update_ui_par_to_meshbest()
                self.Par['StateCtl']['reciveserverupdate'] = True
            else:
                self.logger.info(f'Bluice Emit : {command}')
            pass
        else:
            self.logger.info(f'Bluice Emit : {command}')
        self.updateUI()

    def update_string_to_ui(self,name,value):
            if name == "tps_current":
                self.Current.setValue(float(value[0]))
            elif name == 'sampleFlux':
                try:
                    sampleFlux =  float(value[0]) 
                    if sampleFlux == 0:
                        flux = 0
                    else:
                        currentBeamsize = float(self.bluiceData['string']['currentBeamsize']['txt'])
                        BeamSize = float(self.bluiceData['string']['currentBeamsize']['txt'])
                        currentAtten = self.bluiceData['motor']['attenuation']['pos']#float
                        
                        flux = self.predict_flux(currentBeamsize,currentAtten,sampleFlux,BeamSize,self.Par)
                        
                except:
                    flux =0
                self.beamlineflux.setText(f'{flux:.3e} phs/sec')
                self.CalRasterDose()
            elif name == 'tps_state':
                if value[0]=='Beams':
                    self.TPSStateText.setText('Open')
                else:
                    self.TPSStateText.setText('Closed')
            elif name == "system_status":
                
                data =self.bluiceData['string']['system_status']['txt']
                if data.find('{') != -1:
                    end = data.find('}')
                    state=data[1:end]
                    ans = data[end+1:].split()
                    textc = ans[0]
                    bagc =  ans[1]

                    
                else:
                    ans = data.split()
                    state = ans[0]
                    textc = ans[1]
                    bagc =  ans[2]
                self.LastInfo.setText(state)
                self.LastInfo.setStyleSheet(f'color: {textc};background-color: {bagc}')
                if state == "Abort!":
                    self.abort=True
                    self.collectPause = True
                    self.timer.singleShot(500,self.restAbort)
                # print(f'state = {state},color for text ={textc}, color for background = {bagc}')

            # print(name,value)


    def update_motorpos_to_ui(self,motor,pos,moving=False):
        if motor == "energy":
            self.Energy.setValue(float(pos))

    def restAbort(self):
        self.abort = False
    def dealClientlist(self,oldstr,startindex=0):
        index1 = oldstr.find("{",startindex)
        index2 = oldstr.find("}",startindex)
        matchstr = oldstr[index1+1:index2]
        return matchstr,index2+1
    
    def updateActiveState(self):
        # self.logger.info(f'update client list : {self.bluiceclientlists}')
        if len(self.bluiceclientlists) == self.numofclient:
            # print('my active state=',self.bluiceclientlists[str(self.bluiceID)]['active'])
            if self.bluiceclientlists[str(self.bluiceID)]['active'] :
                #active
                self.setToActive()
            else:
                self.setToPassive()
                
    def setToActive(self):
        self.bluiceData['active'] = True
        self.Active.setText("Active")
        self.Active.setChecked(True)
        self.Active.setStyleSheet('background-color: lightgreen')
        self.logger.info(f'Client become active')
        self.SampleViedo.setCursor(QCursor(QtCore.Qt.CrossCursor))
        self.SampleViedo.setToolTip('Click will move the pos. to center')
        # self.StartRaster.setEnabled(True)
        self.Raster.setEnabled(True)
        if self.Par['StateCtl']['AbletoStartRaster']:
            self.StartRaster.setEnabled(True)

        if len(self.Par['View1']['collectInfo'])>0:        
            self.collectAllpos_1.setEnabled(True)
        if len(self.Par['View2']['collectInfo'])>0:        
            self.collectAllpos_2.setEnabled(True)

        self.viwe1_move_down.setEnabled(True)
        self.viwe1_move_up.setEnabled(True)
        self.viwe1_move_left.setEnabled(True)
        self.viwe1_move_right.setEnabled(True)
        self.viwe2_move_down.setEnabled(True)
        self.viwe2_move_up.setEnabled(True)
        self.viwe2_move_left.setEnabled(True)
        self.viwe2_move_right.setEnabled(True)
        self.checkRootFolder()
                    
    def setToPassive(self):
        self.Active.setText("Passive")
        self.bluiceData['active'] = False
        self.Active.setChecked(False)
        self.Active.setStyleSheet('background-color: yellow')
        self.logger.info(f'Client become passive')
        self.SampleViedo.setCursor(QCursor(QtCore.Qt.ForbiddenCursor))
        self.SampleViedo.setToolTip('Active is needed')
        self.collectAllpos_1.setEnabled(False)
        self.collectAllpos_2.setEnabled(False)
        self.viwe1_move_down.setEnabled(False)
        self.viwe1_move_up.setEnabled(False)
        self.viwe1_move_left.setEnabled(False)
        self.viwe1_move_right.setEnabled(False)
        self.viwe2_move_down.setEnabled(False)
        self.viwe2_move_up.setEnabled(False)
        self.viwe2_move_left.setEnabled(False)
        self.viwe2_move_right.setEnabled(False)
    
    def changeActive(self):
        # print(self.bluiceclientlists,self.bluiceID)
        # if self.bluiceclientlists[str(self.bluiceID)]['active'] :
        #     #original is active
        #     #gtos_become_slave
        #     self.Qinfo["sendQ"].put("gtos_become_slave")
        # else:
        #     self.Qinfo["sendQ"].put("gtos_become_master force")
        #     #gtos_become_master force
        
        if self.bluiceData['active'] :
            #original is active
            #gtos_become_slave
            self.Qinfo["sendQ"].put("gtos_become_slave")
        else:
            self.Qinfo["sendQ"].put("gtos_become_master force")
        # self.update_ui_par_to_meshbest()#for renew restart meshserver    
            
    def full_update(self,par):
        # self.logger.warning(f'full_update')
        uiparlists, uiindexlists, uitextlists,uicheckablelists = variables.ui_par_lists()
        # self.logger.warning(f"update UI_par current setting ={self.Par['UI_par']}")
        for item in uiparlists:
            newitem = getattr(self,item)
            if self.Par['UI_par'][item] is not None:
                newitem.setValue(self.Par['UI_par'][item])
                self.logger.info(f"update uiparlists {item} with value {self.Par['UI_par'][item]}")
                
        for item in uiindexlists:
            newitem = getattr(self,item)
            
            if self.Par['UI_par'][item] is not None:
                newitem.setCurrentIndex(self.Par['UI_par'][item])
                self.logger.info(f"update uiindexlists {item} with value {self.Par['UI_par'][item]}")
        for item in uitextlists:
            if self.bluiceData['active'] and item == 'RootPath':
                #id active do not update rootpath avoid update loop
                pass
            else:#update item
                newitem = getattr(self,item)
                if self.Par['UI_par'][item] is not None:
                    newitem.setText(self.Par['UI_par'][item])
                    self.logger.info(f"update uitextlists {item} with value {self.Par['UI_par'][item]}")
        
        for item in uicheckablelists:
            newitem = getattr(self,item)
            if self.Par['UI_par'][item] is not None:
                newitem.setChecked(self.Par['UI_par'][item])
                self.logger.info(f"update uicheckablelists {item} with value {self.Par['UI_par'][item]}")
        
        #update checkedable button color
        # if not self.bluiceData['active']:
        #     self.updatelist_1_update()
        #     self.updatelist_2_update()

        #update par to RasterPar
        try :
            for view in ["View1","View2"]:
                for name in self.convertlist:
                    self.RasterPar[view][name] =  self.Par[view][name]
                x,y,w,h =self.Par[view]['box']
                self.RasterPar[view]['box'] = QRectF(x,y,w,h)
        except Exception as e:
            traceback.print_exc()
            self.logger.warning(f'Catch Unexpected error:{sys.exc_info()[0]}')
            self.logger.warning(f'Error : {e}')
            
            pass
        # self.logger.warning(f'{self.Par}')
        
        try :
            
            if self.Par['View1']['jpg']:
                jpg = self.Par['View1']['jpg']
                tempq = QPixmap()
                tempq.loadFromData(jpg,format='jpg')
                self.RasterView1QPixmap_ori = tempq
        except Exception as e:
            traceback.print_exc()
            self.logger.warning(f'Catch Unexpected error:{sys.exc_info()[0]}')
            self.logger.warning(f'Error : {e}')
            pass
        
        try:
            if self.Par['View2']['jpg']:
                jpg = self.Par['View2']['jpg']
                tempq = QPixmap()
                tempq.loadFromData(jpg,format='jpg')
                self.RasterView2QPixmap_ori = tempq
        except Exception as e:
            traceback.print_exc()
            self.logger.warning(f'Catch Unexpected error:{sys.exc_info()[0]}')
            self.logger.warning(f'Error : {e}')
            pass
        
        # self.plot_overlap_image('View1')                     
        # self.plot_overlap_image('View2')
    def Focus_neg_l_clicked(self):
        newpos = self.bluiceData['motor']['CentringTableFocus']['pos'] - 0.05
        # gtos_start_motor_move motorName destination
        command = f'gtos_start_motor_move CentringTableFocus {newpos}'
        self.Qinfo["sendQ"].put(command)
        pass
    def Focus_neg_s_clicked(self):
        newpos = self.bluiceData['motor']['CentringTableFocus']['pos'] - 0.005
        # gtos_start_motor_move motorName destination
        command = f'gtos_start_motor_move CentringTableFocus {newpos}'
        self.Qinfo["sendQ"].put(command)
        pass
    def Focus_pos_s_clicked(self):
        newpos = self.bluiceData['motor']['CentringTableFocus']['pos'] + 0.005
        # gtos_start_motor_move motorName destination
        command = f'gtos_start_motor_move CentringTableFocus {newpos}'
        self.Qinfo["sendQ"].put(command)
        pass
    def Focus_pos_l_clicked(self):
        newpos = self.bluiceData['motor']['CentringTableFocus']['pos'] + 0.05
        # gtos_start_motor_move motorName destination
        command = f'gtos_start_motor_move CentringTableFocus {newpos}'
        self.Qinfo["sendQ"].put(command)
        pass

    def Abort_clicked(self):
        command = f'gtos_abort_all soft'
        self.Qinfo["sendQ"].put(command)
        pass
    def Overlap_Select_1_value_change (self):
        if self.bluiceData['active']:
            self.plot_overlap_image("View1")
            self.update_ui_par_to_meshbest()
    def Overlap_Select_2_value_change (self):
        if self.bluiceData['active']:
            self.plot_overlap_image("View2")
            self.update_ui_par_to_meshbest()
    
    def List_number_1_value_change (self):
        if self.bluiceData['active']:
            self.create_collectinfo('View1')
            # self.plot_overlap_image("View1")
            self.update_ui_par_to_meshbest()
            
    def List_number_2_value_change (self):
        if self.bluiceData['active']:
            self.create_collectinfo('View2')
            # self.plot_overlap_image("View2")
            self.update_ui_par_to_meshbest()
            
    def view1_opacity_value_change (self):
        if self.bluiceData['active']:
            self.plot_overlap_image("View1")
            # self.update_ui_par_to_meshbest()
    def view2_opacity_value_change (self):
        if self.bluiceData['active']:
            self.plot_overlap_image("View2")
            # self.update_ui_par_to_meshbest()
            
    def view1_opacity_mouseReleaseEvent(self,event):
         if self.bluiceData['active']:
            self.plot_overlap_image("View1")
            self.update_ui_par_to_meshbest()
    def view2_opacity_mouseReleaseEvent(self,event):
         if self.bluiceData['active']:
            self.plot_overlap_image("View2")
            self.update_ui_par_to_meshbest()       
    def info_client_update_ui(self) :
        if self.bluiceData['active']:
            self.update_ui_par_to_meshbest()
    def debug_Debugclicked(self): 
        print('Par=================Start')
        # print(self.bluiceData['motor'])
        # print(json.dumps(self.RasterPar, indent=4))
        # print(self.RasterPar)
        # print("\n")
        # a = self.calRasterPar()
        # print(a)
        # print(self.RasterPar['View1']['spotsArray'])
        # print(self.RasterPar['View2']['spotsArray'])
        temp = copy.deepcopy(self.Par)
        temp['View1'].pop('jpg', None)
        temp['View2'].pop('jpg', None)
        print(temp)
        
        # print(json.dumps(self.Par, indent=4))
        print('Par=================END')    
    def debug_motorclicked(self):
        print('motor=================Start')
        # print(self.bluiceData['motor'])
        print(json.dumps(self.bluiceData['motor'], indent=4))
        print('motor=================END')
    def debug_stringclicked(self):
        print('string=================Start')
        # print(self.bluiceData['string'])
        print(json.dumps(self.bluiceData['string'], indent=4))
        print('string=================END')
    def debug_operationclicked(self):
        print('operation=================Start')
        # print(self.bluiceData['operation'])
        print(json.dumps(self.bluiceData['operation'], indent=4))
        print('operation=================END')
    def debug_shutterclicked(self):
        print('shutter=================Start')
        # print(self.bluiceData['shutter'])
        print(json.dumps(self.bluiceData['shutter'], indent=4))
        print('shutter=================END')
    def debug_rasterclicked(self):
        print('raster=================Start')
        # print(self.bluiceData['shutter'])
        # print(f'{self.RasterPar}')
        templists = self.RasterPar.keys()
        for key in templists:
            #view1
            templistslevel2 = self.RasterPar[key].keys()
            for k2 in templistslevel2:
                if k2 == "jpg" or k2 == "boxRectItemarray" or k2 == "Textplotarray":
                    print(f'{key} bypass')
                else:
                    print(f'[{key}] [{k2}] : { self.RasterPar[key][k2]}')
        print('raster=================END')    
            #gtos_become_master force
    def clear_Raster_scence_item(self):
        items = self.Rasterscene1.items()
        if len(items):
            for item in items:
                try :
                    self.Rasterscene1.removeItem(item)
                except:
                    pass
        items = self.Rasterscene2.items()
        if len(items):
            for item in items:
                try :
                    self.Rasterscene2.removeItem(item)
                except:
                    pass
        #recover some setup
        self.init_scence_item_in_view12()
    def init_scence_item_in_view12(self):
        #this usr for reinit scence_item in viwe12
        self.RasterView1QPixmap_ori = QtGui.QPixmap()
        self.RasterView2QPixmap_ori = QtGui.QPixmap()
        
        self.RasterView1QPixmap = self.Rasterscene1.addPixmap(QtGui.QPixmap())
        self.RasterView2QPixmap = self.Rasterscene2.addPixmap(QtGui.QPixmap())
        
        self.RasterPar['View1']['QPixmap'] = self.RasterView1QPixmap
        self.RasterPar['View2']['QPixmap'] = self.RasterView2QPixmap
        
        self.RasterPar['View1']['overlap_QPixmap'] = self.Rasterscene1.addPixmap(QtGui.QPixmap())
        self.RasterPar['View2']['overlap_QPixmap'] = self.Rasterscene2.addPixmap(QtGui.QPixmap())
        
        self.RasterView1.setScene(self.Rasterscene1)
        self.RasterView2.setScene(self.Rasterscene2)
        
        self.view1box = self.Rasterscene1.addRect(0, 0, 0, 0)
        self.view1box.setZValue(100)
        self.view1_start = QPointF()
        self.view1_end = QPointF()
        self.RasterPar['View1']['box'] = QRectF(0,0,0,0)
        self.RasterPar['View1']['viewRect'] = self.view1box
        self.view1gridsgroup = None
        
        self.view2box = self.Rasterscene2.addRect(0, 0, 0, 0)
        self.view2box.setZValue(100)
        self.view2_start = QPointF()
        self.view2_end = QPointF()
        self.RasterPar['View2']['box'] = QRectF(0,0,0,0)
        self.RasterPar['View2']['viewRect'] = self.view2box

        self.RasterPar['View1']['CrossItem'] = CrossItem(self.corsssize,color=Qt.red,pensize=3)
        self.RasterPar['View2']['CrossItem'] = CrossItem(self.corsssize,color=Qt.red,pensize=3)

        self.Rasterscene1.addItem(self.RasterPar['View1']['CrossItem'])
        self.Rasterscene2.addItem(self.RasterPar['View2']['CrossItem'])

        self.RasterPar['View1']['CrossItem'].setZValue(100)
        self.RasterPar['View2']['CrossItem'].setZValue(100)
    def initScoreArray(self,view='View1'):
        self.logger.warning(f'initScoreArray for {view=}')
        try:
            numofXbox = self.RasterPar[view]['numofX']
            numofYbox = self.RasterPar[view]['numofY']
        except:
            numofXbox = self.Par[view]['numofX']
            numofYbox = self.Par[view]['numofY']
        try:
            self.RasterPar[view]['Textplotarray']=[[0]*numofYbox for i in range(numofXbox)]
            self.RasterPar[view]['scoreArray'] = np.zeros((numofXbox, numofYbox))
            self.RasterPar[view]['scoreArray'][:] = np.nan
            self.RasterPar[view]['resArray']=np.zeros((numofXbox, numofYbox))
            self.RasterPar[view]['resArray'][:]=50#set all value to 50
            self.RasterPar[view]['spotsArray']=np.zeros((numofXbox, numofYbox))
            self.RasterPar[view]['spotsArray'][:] = np.nan
            
            self.Par[view]['scoreArray'] = np.zeros((numofXbox, numofYbox))
            self.Par[view]['scoreArray'][:] = np.nan
            self.Par[view]['resArray']=np.zeros((numofXbox, numofYbox))
            self.Par[view]['resArray'][:]=50#set all value to 50
            self.Par[view]['spotsArray']=np.zeros((numofXbox, numofYbox))
            self.Par[view]['spotsArray'][:] = np.nan
        except:
            pass
        self.Par[view]['collectInfo'] = []
        self.meshbest.sendCommandToMeshbest(('Clear_scoreArray'))

    def movefactor(self):
        return 1
    def viwe1_move_down_clicked(self):
        self.move_button_clicked("View1",'down')
    def viwe1_move_up_clicked(self):
        self.move_button_clicked("View1",'up')
    def viwe1_move_left_clicked(self):
        self.move_button_clicked("View1",'left')
    def viwe1_move_right_clicked(self):
        self.move_button_clicked("View1",'right')
    def viwe2_move_down_clicked(self):
        self.move_button_clicked("View2",'down')
    def viwe2_move_up_clicked(self):
        self.move_button_clicked("View2",'up')
    def viwe2_move_left_clicked(self):
        self.move_button_clicked("View2",'left')
    def viwe2_move_right_clicked(self):
        self.move_button_clicked("View2",'right')

    def move_button_clicked(self,view,direction):
        x1=self.RasterPar['View1']['box'].x()
        y1=self.RasterPar['View1']['box'].y()
        w1=self.RasterPar['View1']['box'].width()
        h1=self.RasterPar['View1']['box'].height()
        
        x2=self.RasterPar['View2']['box'].x()
        y2=self.RasterPar['View2']['box'].y()
        w2=self.RasterPar['View2']['box'].width()
        h2=self.RasterPar['View2']['box'].height()
        if direction == 'down':
            y1=y1+self.movefactor()
            y2=y2+self.movefactor()
        elif direction == 'up':
            y1=y1-self.movefactor()
            y2=y2-self.movefactor()
        elif direction == 'left':
            if view == 'View1':
                x1=x1-self.movefactor()
            else:
                x2=x2-self.movefactor()
        elif direction == 'right':
            if view == 'View1':
                x1=x1+self.movefactor()
            else:
                x2=x2+self.movefactor()

        self.RasterPar['View1']['box'] = QRectF(x1,y1,w1,h1)
        self.RasterPar['View2']['box'] = QRectF(x2,y2,w2,h2)
        # self.plotView12()
        # self.send_RasterInfo_to_meshbest()
        self.send_RasterInfo_to_meshbest('plotView12')
    def clearcollectpos(self,view):
        self.Par[view]['collectInfo']=[]
        # self.send_RasterInfo_to_meshbest()
        # self.plot_overlap_image(view)
        updatestr = f'plotBestpos_{view}'
        self.send_RasterInfo_to_meshbest(updatestr)#ask client plot plotBestpos_View1 or 2
        pass

    def delcollectpos(self,position,view):
        mouseX=self.RasterView1.mapToScene(position).x()
        mouseY=self.RasterView1.mapToScene(position).y()
        convert_pos = QPoint(mouseX,mouseY)
        findindex = -1
        for i,item in enumerate(self.RasterPar[view]['pos_circle_array']):
            if item.contains(convert_pos):
                findindex = i
        print(i)
        if findindex == -1:
            pass
        else:
            del self.Par[view]['collectInfo'][findindex]
            self.send_RasterInfo_to_meshbest()
            self.plot_overlap_image(view)
            self.logger.info(f'Del pos:{findindex} in {view}')
        pass
    def MousePos_Mapto_Raster(self,position,view='View1'):
        RasterPar =  self.RasterPar[view]
        if view =='View1':
            ratio = self.getViewRatio(1)
        else:
            ratio = self.getViewRatio(2)
        if view == 'View1':
            RasterView = self.RasterView1
        else:
            RasterView = self.RasterView2
        mouseX = RasterView.mapToScene(position).x()
        mouseY = RasterView.mapToScene(position).y()
        #position at full view
        convert_posX = mouseX*ratio
        convert_posY = mouseY*ratio
        
        #get box pos
        boxX = RasterPar['box'].x()
        boxY = RasterPar['box'].y()
        
        zoomx = RasterPar['zoom_scale_x']
        zoomy = RasterPar['zoom_scale_y']

        #diffpos
        diffx = convert_posX - boxX + RasterPar['gridsizeX']/2/zoomx
        diffy = convert_posY - boxY + RasterPar['gridsizeX']/2/zoomy


        rasterX = diffx * zoomx 
        rasterY = diffy * zoomy 
        viewX = rasterX / RasterPar['gridsizeX'] 
        viewY = rasterY / RasterPar['gridsizeY']

        # self.logger.warning(f'{viewX=},{rasterX=},{diffx=},{convert_posX=},{boxX=},{ratio=},{zoomx=},{RasterPar["gridsizeX"]=}')
        return viewX,viewY
    def movePosinCollectinfo(self,event,position,view='View1'):
        raster = self.RasterPar[view]
        if view == 'View1':
            RasterView = self.RasterView1
        else:
            RasterView = self.RasterView2
        mouseX=RasterView.mapToScene(position).x()
        mouseY=RasterView.mapToScene(position).y()
        convert_pos = QPoint(mouseX,mouseY)
        if event.button() == 1 :
            if not raster['movingplot']:
                findindex = -1
                for i,item in enumerate(self.RasterPar[view]['pos_circle_array']):
                    if item.contains(convert_pos):
                        findindex = i
                if findindex == -1:
                    pass
                else:
                    raster['pos_circle_array'][findindex].setPen(QPen(QtCore.Qt.red))
                    raster['movingindex'] = findindex
                    raster['movingplot'] = True
            else:
                #end of move
                raster['movingplot'] = False
                i = raster['movingindex']
                viewX ,viewY = self.MousePos_Mapto_Raster(position,view)
                currentCollectlist = self.Par[view]['collectInfo']
                currentCollectlist[i]['ViewX'] = viewX
                currentCollectlist[i]['ViewY'] = viewY
                self.Par[view]['collectInfo'] = currentCollectlist
                self.logger.info(f'Set {i} new pos')
                # self.send_RasterInfo_to_meshbest(False)
                # # self.plot_overlap_image(view)
                # self.plotBestpos(view)
                updatestr = f'plotBestpos_{view}'
                self.send_RasterInfo_to_meshbest(updatestr)
        else:
            #cancel
            raster['movingplot'] = False
            # self.plot_overlap_image(view)
            self.plotBestpos(view)


    def addPosinCollectinfo(self,position,view='View1'):
        currentCollectlist = self.Par[view]['collectInfo']
        i = len(currentCollectlist)
        RasterPar =  self.RasterPar[view]
        posdata={}
        #,x,y,beamsize,socre
        viewX ,viewY = self.MousePos_Mapto_Raster(position,view)

       

        posdata['ViewX'] = viewX
        posdata['ViewY'] = viewY
        BeamSize = self.CorrectBeamsize(1 * RasterPar['gridsizeY'])

        CollectOrder = int(i+1)
        CollectType = 0#todo collec
        CollectDone = False
        FileName = f'{i+1:03d}'
        
        FolderName = f'{self.RootPath_2.text()}/collect'
        Distance = self.Distance.value()
        Energy = self.bluiceData['motor']['energy']['pos']
        TotalCollectRange = 10 #todo set a input?
        StartPhi = RasterPar['gonio_phi'] - (TotalCollectRange /2)
        EndPhi = RasterPar['gonio_phi'] + (TotalCollectRange /2)
        Delta = 0.1 #todo set a input?
        Atten = 0
        ExpTime = 0.01
        displaytext = "Atten-Time"
        DoseSelect = 0
        dose = 10
        RoughtDose = 10
        EstimateDose = 10
        #get flux
        currentBeamsize =  float(self.bluiceData['string']['currentBeamsize']['txt'])
        currentAtten = self.bluiceData['motor']['attenuation']['pos']#float
        sampleFlux = float(self.bluiceData['string']['sampleFlux']['txt'])
        flux = self.collectparwindows.predict_flux(currentBeamsize,currentAtten,sampleFlux,BeamSize,self.Par)
        
        newHdose,newAdose,newAtten,newExptime,newTrange,newDelta,NewDistance,NewEnergy=\
        self.collectparwindows.calDosePar(displaytext,DoseSelect,BeamSize,dose,RoughtDose,EstimateDose,Atten,ExpTime,TotalCollectRange,Delta,Distance,Energy,flux)
        posdata['BeamSize'] = BeamSize
        posdata['CollectOrder'] = CollectOrder
        posdata['CollectType'] = CollectType
        posdata['CollectDone'] = CollectDone
        posdata['FileName'] = FileName
        posdata['FolderName'] = FolderName
        posdata['Distance'] = Distance
        posdata['Energy'] = Energy
        posdata['StartPhi'] = RasterPar['gonio_phi'] - (newTrange /2)
        posdata['EndPhi'] = RasterPar['gonio_phi'] + (newTrange /2)
        posdata['TotalCollectRange'] = newTrange
        posdata['Delta'] = newDelta
        posdata['ExpTime'] = newExptime
        posdata['Atten'] = newAtten
        posdata['RoughtDose']=newHdose
        posdata['EstimateDose'] = newAdose
        currentCollectlist.append(posdata)
        self.Par[view]['collectInfo'] = currentCollectlist
        if len(self.Par[view]['collectInfo'])>0:
            if view=='View1':
                self.collectAllpos_1.setEnabled(True)
            else:
                self.collectAllpos_2.setEnabled(True)
        self.logger.info(f'Add pos:({viewX}),({viewY}) in {view}')
        updatestr = f'plotBestpos_{view}'
        self.send_RasterInfo_to_meshbest(updatestr)#ask client plot plotBestpos_View1 or 2
        # self.plot_overlap_image(view)#too heavy
        # self.plotBestpos(view)#will replot by after send message to server
        
    def create_collectinfo(self,view='View1'):
        
        RasterPar = self.RasterPar[view]
        par = self.Par[view]
        if view=='View1':
            numlist = self.List_number_1.value()    
            updatetype = self.updatelist_1.currentIndex()
        elif view == 'View2':
            numlist = self.List_number_2.value()
            updatetype = self.updatelist_2.currentIndex()
        elif view == 'View3':#todo for viwe12
            numlist = self.List_number_1.value()
            updatetype = self.updatelist_1.currentIndex()    
            pass
        if updatetype == 0:
            collectlist=list()           
            for i,item in enumerate(RasterPar['BestPositions']):
                posdata={}
                #,x,y,beamsize,socre
                posdata['ViewX'] = item[0]
                posdata['ViewY'] = item[1]
                BeamSize = self.CorrectBeamsize(item[2] * RasterPar['gridsizeY'])

                CollectOrder = int(i+1)
                CollectType = 0#todo collec
                CollectDone = False
                FileName = f'{i+1:03d}'
                
                FolderName = f'{self.RootPath_2.text()}/collect'
                Distance = self.Distance.value()
                Energy = self.bluiceData['motor']['energy']['pos']
                TotalCollectRange = 10 #todo set a input?
                StartPhi = RasterPar['gonio_phi'] - (TotalCollectRange /2)
                EndPhi = RasterPar['gonio_phi'] + (TotalCollectRange /2)
                Delta = 0.1 #todo set a input?
                Atten = 0
                ExpTime = 0.01
                displaytext = "Atten-Time"
                DoseSelect = 0
                dose = 10
                RoughtDose = 10
                EstimateDose = 10
                #get flux
                currentBeamsize =  float(self.bluiceData['string']['currentBeamsize']['txt'])
                currentAtten = self.bluiceData['motor']['attenuation']['pos']#float
                sampleFlux = float(self.bluiceData['string']['sampleFlux']['txt'])
                flux = self.collectparwindows.predict_flux(currentBeamsize,currentAtten,sampleFlux,BeamSize,self.Par)
                
                newHdose,newAdose,newAtten,newExptime,newTrange,newDelta,NewDistance,NewEnergy=\
                self.collectparwindows.calDosePar(displaytext,DoseSelect,BeamSize,dose,RoughtDose,EstimateDose,Atten,ExpTime,TotalCollectRange,Delta,Distance,Energy,flux)
                posdata['BeamSize'] = BeamSize
                posdata['CollectOrder'] = CollectOrder
                posdata['CollectType'] = CollectType
                posdata['CollectDone'] = CollectDone
                posdata['FileName'] = FileName
                posdata['FolderName'] = FolderName
                posdata['Distance'] = Distance
                posdata['Energy'] = Energy
                posdata['StartPhi'] = RasterPar['gonio_phi'] - (newTrange /2)
                posdata['EndPhi'] = RasterPar['gonio_phi'] + (newTrange /2)
                posdata['TotalCollectRange'] = newTrange
                posdata['Delta'] = newDelta
                posdata['ExpTime'] = newExptime
                posdata['Atten'] = newAtten
                posdata['RoughtDose']=newHdose
                posdata['EstimateDose'] = newAdose
                # self.logger.warning(f'{posdata["StartPhi"]},{posdata["EndPhi"]},{newTrange}')
                if i >=numlist:
                    pass
                else:
                    collectlist.append(posdata)
            self.logger.warning(f'View = {view}, len collectlist={len(collectlist)}')
            self.Par[view]['collectInfo'] = collectlist
            if len(self.Par[view]['collectInfo'])>0:
                if view=='View1':
                    self.collectAllpos_1.setEnabled(True)
                else:
                    self.collectAllpos_2.setEnabled(True)
            # self.send_RasterInfo_to_meshbest(False)#also send par[view][collectInfo]
            updatestr = f'plotBestpos_{view}'
            self.send_RasterInfo_to_meshbest(updatestr)
            # self.plotBestpos(view)
        elif updatetype == 1:#manual
            pass    
        elif updatetype == 2:#peak
            #todo
            pass
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
        # if currentBeamsize >= 30 and Targetbeamsize >= 30:
        #     # same
        #     flux = FullFlux
        # elif currentBeamsize >= 30 and Targetbeamsize <= 20:
        #     # FullFlux is smaller
        #     flux = FullFlux / par['Fluxfactor']
        # elif currentBeamsize < 20 and Targetbeamsize < 20:
        #     flux = FullFlux
        # elif currentBeamsize > 20 and Targetbeamsize < 20:
        #     flux = FullFlux * par['Fluxfactor']
        # else:
        #     #shoud not got to here
        #         flux =FullFlux
        return flux
    
    def CalRasterDose(self):
        try:
            currentBeamsize =  float(self.bluiceData['string']['currentBeamsize']['txt'])
            currentAtten = self.bluiceData['motor']['attenuation']['pos']#float
            sampleFlux = float(self.bluiceData['string']['sampleFlux']['txt'])
            TargetBeamSize = float(self.selectBeamsize.currentText())
            flux = self.collectparwindows.predict_flux(currentBeamsize,currentAtten,sampleFlux,TargetBeamSize,self.Par)
            if self.ExpousetimeType.currentText() == "Exposed time":
                exposure_time = self.ExpouseValue.value()
            elif self.ExpousetimeType.currentText() == "Rate":
                exposure_time = 1 / self.ExpouseValue.value()
            else:
                self.logger.warning(f"Undefine name {self.ExpousetimeType.currentText()} in ExpousetimeType")
                exposure_time = self.ExpouseValue.value()
            setatten=self.Attenuation.value()
            wave = 12398.0/self.bluiceData['motor']['energy']['pos']
            # if TargetBeamSize == 1:
            #     beamXsize = 5#beam size in hor direct,fwhm=2
            # elif TargetBeamSize == 5:
            #     beamXsize = TargetBeamSize/2.35*6# 6 sigma
            # elif TargetBeamSize == 10:
            #     beamXsize = TargetBeamSize/2.35*6# 6 sigma
            # else:
            #     beamXsize = TargetBeamSize+10#10umbigger
            if TargetBeamSize == 1:
                beamXsize = 2#beam size in hor direct,fwhm=2
            else:
                beamXsize = TargetBeamSize

            beamYsize = float(self.selectGridsize.currentText())#gridsize in ver
            beamarea = beamXsize *beamYsize
            dose=flux*(1-setatten/100)*exposure_time*wave*wave/beamarea/2000.0/1e6#MGy
            # print(setatten,dose,flux,exposure_time,self.bluiceData['motor']['energy']['pos'])
            self.rasterdose.setValue(dose)
        except Exception as e:
            self.logger.info(f'Catch Error:{e}')
            self.logger.info(traceback.format_exc())

    def CorrectBeamsize(self,beamsize):
        AvailableBeamSizes = self.Par['AvailableBeamSizes']
        newbeamsize=min(AvailableBeamSizes, key=lambda x:abs(x-beamsize))
        return newbeamsize
    def plotBestpos(self,View='View1'):
        par = self.Par[View]#todo
        RasterInfo = self.RasterPar[View]
        circleItems = self.RasterPar[View]['pos_circle_array']
        textItems = self.RasterPar[View]['pos_text_array']
        if View=="View1":
            Viewscene=self.Rasterscene1
            
        elif View=="View2":
            Viewscene=self.Rasterscene2
        else:
            #should not got here
            Viewscene=self.Rasterscene1
        try:
            # self.logger.warning(f'View = {View}, len circleItems={len(circleItems)},items={circleItems}')
            if len(circleItems)==0:
                pass
            else:
                for a in circleItems:
                    Viewscene.removeItem(a)
                circleItems =[]
                for b in textItems:
                    Viewscene.removeItem(b)
                textItems = []
        except Exception as e:
            self.logger.warning(f'Error on {e}')
        
        ratio =  self.getViewRatio(View)
        try:
            FactorPixUmX = 1/par['zoom_scale_x']
            FactorPixUmY = 1/par['zoom_scale_y']
        except:
            FactorPixUmX = 1
            FactorPixUmY = 1
        gridsizeX = par['gridsizeX']
        gridsizeY = par['gridsizeY']
        try:
            halfoffsetX = FactorPixUmX*gridsizeX/2
            halfoffsetY = FactorPixUmY*gridsizeY/2
        except:
            halfoffsetX = 0
            halfoffsetY = 0
        offsetx = RasterInfo['box'].x() - halfoffsetX
        offsety = RasterInfo['box'].y() - halfoffsetY
        for i,posdata in enumerate(par['collectInfo']): 
            BeamSize = posdata['BeamSize']
        
            x= (offsetx + posdata['ViewX']*FactorPixUmX*gridsizeX)/ ratio
            y= (offsety + posdata['ViewY']*FactorPixUmY*gridsizeY)/ ratio
            
            width = BeamSize*FactorPixUmX / ratio
            height = BeamSize*FactorPixUmY / ratio
            newCircle,newText=self.CircleItem(x,y,width,height,Text=str(i+1),Ccolor="goldenrod",Tcolor="white")
            
            if posdata['CollectDone'] == True :
                newCircle.setBrush(QColor('green'))
                newCircle.setPen(QPen(QColor('green'),1))
                newCircle.setOpacity(0.7)
            elif posdata['CollectDone'] == None :
                newCircle.setBrush(QColor('red'))
                newCircle.setPen(QPen(QColor('red'),1))
                newCircle.setOpacity(0.7)
            # newCircle,newText=self.CircleItem(x,y,width,height,Text=str(i+1),Ccolor="goldenrod",Tcolor="white")
            Viewscene.addItem(newCircle)
            Viewscene.addItem(newText)
            circleItems.append(newCircle)
            textItems.append(newText)
        #write back
        self.RasterPar[View]['pos_circle_array'] = circleItems
        self.RasterPar[View]['pos_text_array'] = textItems
        

        
    def CircleItem(self,x,y,width,height,Ccolor="goldenrod",Tcolor="white",Text=""):
        pos=QRectF(0,0,width,height)
        pos.moveCenter(QPointF(x,y))
        newCircle = QtWidgets.QGraphicsEllipseItem(pos)
#        ans.setBrush(QBrush(QtCore.Qt.red, style = QtCore.Qt.NoBrush))#this for fill
        newCircle.setPen(QPen(QColor(Ccolor),2))
        newText = QtWidgets.QGraphicsTextItem(Text)
#        print "text width",newText.boundingRect().width()
        
        newText.setDefaultTextColor(QColor(Tcolor))
        myfont = QFont()
        myfont.setBold(False)
        myfont.setPointSize(10)
        newText.setFont(myfont)
        newText.setPos(x-newText.boundingRect().width()/2,y-newText.boundingRect().height()/2)
        newCircle.setZValue(101)#max,higher than grid
        newText.setZValue(101)#max
        return newCircle,newText

    def filter_BestPositions(self,BestPositions):
        try:
            ans =[]
            for item in BestPositions:
                # if item[3] > 10:
                if item[3] > 0.1:
                    ans.append(item)
        except:
            ans = []
        return ans
        # [[6.00000000e+000 2.00000000e+000 3.33333333e+000 4.58015813e+007]
        # [8.50000000e+000 2.00000000e+000 3.33333333e+000 3.38387528e+007]
        # [6.50000000e+000 4.50000000e+000 2.33333333e+000 2.32227241e+007]
        # [1.50000000e+000 9.40000000e+000 2.33333333e+000 2.17526962e+007]
        # [2.50000000e+000 3.40000000e+000 2.33333333e+000 1.06971968e+007]
        # [3.60000000e+000 2.10000000e+000 1.66666667e+000 2.37521285e+006]
        # [3.60000000e+000 1.00000000e+001 1.33333333e+000 1.77364432e+006]
        # [9.00000000e-001 7.40000000e+000 1.33333333e+000 1.20858045e+006]
        # [3.90000000e+000 6.00000000e+000 3.33333333e+000 1.13546131e+006]
        # [4.90000000e+000 1.00000000e+001 1.33333333e+000 7.20559120e+005]
        # [6.00000000e+000 7.90000000e+000 3.33333333e+000 4.17105580e+005]
        # [9.00000000e-001 6.20000000e+000 1.33333333e+000 4.08333472e+005]
        # [9.00000000e-001 4.80000000e+000 1.33333333e+000 3.22684960e+005]
        # [3.40000000e+000 8.60000000e+000 2.00000000e+000 1.07309991e+005]
        # [7.60000000e+000 6.00000000e+000 3.00000000e+000 9.79957991e+004]
        # [8.00000000e+000 8.10000000e+000 1.33333333e+000 9.57338560e+004]
        # [5.90000000e+000 9.90000000e+000 1.00000000e+000 5.60388330e+004]
        # [9.00000000e+000 6.00000000e+000 1.00000000e+000 4.62811230e+004]
        # [6.90000000e+000 1.00000000e+001 1.33333333e+000 3.90628960e+004]
        # [4.90000000e+000 4.00000000e+000 1.33333333e+000 2.40274112e+004]
        # [2.00000000e+000 6.90000000e+000 1.33333333e+000 1.48011485e+004]
        # [8.70000000e+000 4.70000000e+000 1.66666667e+000 8.15170150e+003]
        # [6.00000000e+000 1.90000000e+000 1.00000000e+000 3.78520047e+003]
        # [7.90000000e+000 9.10000000e+000 1.00000000e+000 3.44736000e+002]
        # [6.92921936e-310 6.92921936e-310 4.65418559e-310 6.92949311e-310]
        # [6.92921921e-310 6.92921966e-310 4.65418559e-310 6.92949310e-310]
    # self.viwe1_move_down.clicked.connect(self.viwe1_move_down_clicked)
    #     self.viwe1_move_up.clicked.connect(self.viwe1_move_up_clicked)
    #     self.viwe1_move_left.clicked.connect(self.viwe1_move_left_clicked)
    #     self.viwe1_move_right.clicked.connect(self.viwe1_move_right_clicked)


    def closeEvent(self, event):
        self.quit("","")
    def send_RasterInfo_to_meshbest(self,updatetype='all')  :
        par = variables.Raster_to_Meshbest_par(self.RasterPar, self.Par)
        # par =  copy.deepcopy(self.Par)
        # for view in ["View1","View2"]:
        #     for name in self.convertlist:
        #         par[view][name] = self.RasterPar[view][name]            

        #     x = self.RasterPar[view]['box'].x()
        #     y = self.RasterPar[view]['box'].y()
        #     w = self.RasterPar[view]['box'].width()
        #     h = self.RasterPar[view]['box'].height()
        #     par[view]['box'] = [x,y,w,h]
        
        # self.logger.warning(f'Send to meshbest server:{par}')
        self.Par.update(par)
        #if updatetype == all
        # try:
        #     self.logger.critical(f"Send par out : {par['View1'].keys()}")
        #     self.logger.critical(f"Send par out : {par['View1']['jpg'][:5]}")
        # except:
        #     pass
        self.meshbest.sendCommandToMeshbest(('Update_par',par,updatetype))
        
    def update_ui_par_to_meshbest(self):
        uiparlists,uiindexlists,uitextlists,uicheckablelists= variables.ui_par_lists()
        
        for item in uiparlists:
            newitem = getattr(self,item)
            # print(f'Name:{item}, value={newitem.value()}')
            self.Par['UI_par'][item] = newitem.value()
            
        for item in uiindexlists:
            newitem = getattr(self,item)
            # print(f'Name:{item}, value={newitem.currentIndex()}')
            self.Par['UI_par'][item] = newitem.currentIndex()

        for item in uitextlists:
            newitem = getattr(self,item)
            # print(f'Name:{item}, value={newitem.currentIndex()}')
            self.Par['UI_par'][item] = newitem.text()
        
        for item in uicheckablelists:
            newitem = getattr(self,item)
            # print(f'Name:{item}, value={newitem.currentIndex()}')
            self.Par['UI_par'][item] = newitem.isChecked()

        # par = copy.deepcopy(self.Par)
        par = variables.Raster_to_Meshbest_par(self.RasterPar, self.Par)
        self.meshbest.sendCommandToMeshbest(('Update_par',par))
    def update_All_par_to_meshbest(self):
        # TODO
        uiparlists,uiindexlists,uitextlists ,uicheckablelists= variables.ui_par_lists()
        
        for item in uiparlists:
            newitem = getattr(self,item)
            # print(f'Name:{item}, value={newitem.value()}')
            self.Par['UI_par'][item] = newitem.value()
            
        for item in uiindexlists:
            newitem = getattr(self,item)
            # print(f'Name:{item}, value={newitem.currentIndex()}')
            self.Par['UI_par'][item] = newitem.currentIndex()
            
        for item in uitextlists:
            newitem = getattr(self,item)
            self.Par['UI_par'][item] = newitem.text()

        for item in uicheckablelists:
            newitem = getattr(self,item)
            self.Par['UI_par'][item] = newitem.isChecked()
        # par = copy.deepcopy(self.Par)
        par = variables.Raster_to_Meshbest_par(self.RasterPar, self.Par)
        self.meshbest.sendCommandToMeshbest(('Update_par',par))
    #collect bolck

    def CollectdataSeq(self,view):
        self.saveImageforCollect()
        self.collectPause = False##todo
        self.showforreadycollect(False)
        self.CollectAction(view)

    def CollectAction(self,view):
        par =self.Par[view]
        CollectInfo = self.Par[view]['collectInfo']
        #check pause?
        if len(CollectInfo) > 0:
           
            CurrentCollectindex, CurrentCollectinfo = self.findNeedCollectInfo(view)
            if CurrentCollectindex == -1:
                #collect done
                self.showforreadycollect(True)
                return False

            self.logger.warning(f'{CurrentCollectindex=}')
            
            
            RasterInfo = self.RasterPar[view]
            
            try:
                FactorPixUmX = 1/par['zoom_scale_x']
                FactorPixUmY = 1/par['zoom_scale_y']
            except:
                FactorPixUmX = 1
                FactorPixUmY = 1
            gridsizeX = par['gridsizeX']
            gridsizeY = par['gridsizeY']
            try:
                halfoffsetX = FactorPixUmX*gridsizeX/2
                halfoffsetY = FactorPixUmY*gridsizeY/2
            except:
                halfoffsetX = 0
                halfoffsetY = 0
            offsetx = RasterInfo['box'].x() - halfoffsetX
            offsety = RasterInfo['box'].y()  - halfoffsetY
            x= (offsetx + CurrentCollectinfo['ViewX']*FactorPixUmX*gridsizeX)
            y= (offsety + CurrentCollectinfo['ViewY']*FactorPixUmY*gridsizeY)

            #move sample
            self.makecollectred(CurrentCollectindex,view)
            samplex = RasterInfo['sample_x']
            sampley = RasterInfo['sample_y']
            samplez = RasterInfo['sample_z']
            angle = RasterInfo['gonio_phi']
            zoomx = RasterInfo['zoom_scale_x']
            zoomy = RasterInfo['zoom_scale_y']

            
            samplez,sampley,samplex = self.calXYZbaseonCAMCenter(x,y,angle,zoomx,zoomy,samplex,sampley,samplez)

            start_angle = CurrentCollectinfo['StartPhi']

            attenuation = CurrentCollectinfo['Atten']
            motorchecklist=['gonio_phi','sample_x','sample_y','sample_z','attenuation']
            self.logger.debug(f'Checking {motorchecklist} moving state')
            checkarray = []
            posarray = []
            _check=True
            while _check:
                for motor in motorchecklist:
                    checkarray.append(not (self.bluiceData['motor'][motor]['moving']))
                    posarray.append(self.bluiceData['motor'][motor]['pos'])
                if all(checkarray):
                    self.logger.debug('move done')
                    _check=False
                QApplication.processEvents()
                time.sleep(0.2)
                

            command = f'gtos_start_motor_move gonio_phi {start_angle}'
            # print(command)
            self.Qinfo["sendQ"].put(command)
            command = f'gtos_start_motor_move sample_x {samplex}'
            # print(command)
            self.Qinfo["sendQ"].put(command)
            command = f'gtos_start_motor_move sample_y {sampley}'
            # print(command)
            self.Qinfo["sendQ"].put(command)
            command = f'gtos_start_motor_move sample_z {samplez}'
            # print(command)
            self.Qinfo["sendQ"].put(command)
            command = f'gtos_start_motor_move attenuation {attenuation}'
             # print(command)
            self.Qinfo["sendQ"].put(command)


            motorchecklist=['gonio_phi','sample_x','sample_y','sample_z','attenuation']
            motorposchecklist=[start_angle,samplex,sampley,samplez,attenuation]
            
            callback = self.CollectAction_collect#next job
            callbackarg = (view,CurrentCollectinfo,CurrentCollectindex)
            self.logger.warning(f'wating {motorchecklist} ')
            self.timer.singleShot(200, partial(self.waitMotorStopUpdate_v2,motorchecklist,callback,callbackarg))           
            
            return True

    def CollectAction_collect(self,view,CurrentCollectinfo,CurrentCollectindex):
#            setupRun(self,file_root,directory,start_angle,end_angle,delta,exposure_time,distance,attenuation,beamsize,energy1=-1,shuttered="1"):
        energy = str(self.Energy.value())    
        info=CurrentCollectinfo
        parlist = self.calMutiPosPar(CurrentCollectinfo)
        self.logger.debug(f'patlist = {parlist}')
        command = f"gtos_start_operation mutiPosCollect {self.bluiceID}.{self.bluiceCounter} "
        self.bluiceCounter += self.bluiceCounter
            
        for item in parlist:
            command = command + str(item) + " "
        self.opCompleted['mutiPosCollect'] = False
        self.Qinfo["sendQ"].put(command)

        #wait collect done(operation)
        self.logger.info(f'Wait for Collect operation')
        oplist=['mutiPosCollect']
        callback = self.after_collectdone
        callbackarg = (view,CurrentCollectindex)
        self.timer.singleShot(100, partial(self.waitOperationDone
                                            ,oplist,callback,callbackarg))
        self.makecollectred(CurrentCollectindex,view)
        
    def after_collectdone(self,view,CurrentCollectindex):
        #make something to do after collect one run
        #replace one item
        self.makecollectgreen(CurrentCollectindex,view)
        temp=self.Par[view]['collectInfo'].pop(CurrentCollectindex)
        temp['CollectDone']=True
        self.Par[view]['collectInfo'].insert(CurrentCollectindex,temp)
        #update display
        #todo update GUI_collecrpar.py
        #update to meshbest server
        self.update_All_par_to_meshbest()
        #go for next check pause? or check abort?
        if not self.collectPause:
            self.CollectAction(view)

    def findNeedCollectInfo(self,view) :
        CollectInfo = self.Par[view]['collectInfo']
        index=-1
        i=0
        for item in CollectInfo:
            if item['CollectDone'] == False:
                index = i
                return index,item
            i = i + 1 
        return -1,{}
    def makecollectgreen(self,CurrentCollectindex,view):
        if CurrentCollectindex == -1:
            pass
        else:
            Circle = self.RasterPar[view]['pos_circle_array'][CurrentCollectindex]
            Circle.setBrush(QColor('green'))
            Circle.setPen(QPen(QColor('green'),1))
            Circle.setOpacity(0.7)

    def makecollectred(self,CurrentCollectindex,view):
        if CurrentCollectindex == -1:
            pass
        else:
            Circle = self.RasterPar[view]['pos_circle_array'][CurrentCollectindex]
            Circle.setBrush(QColor('red'))
            Circle.setPen(QPen(QColor('red'),1))
            Circle.setOpacity(0.7)

    def saveImageforCollect(self):
        #save par self.RasterView1QPixmap_ori.save(path,'jpg')
        path=f'{self.RootPath_2.text()}/RasterPar.txt'
        with open(path,'w') as f:
            f.write(str(self.Par))

        path=f'{self.RootPath_2.text()}/UI_collectPar.txt'
        with open(path,'w') as f:
            f.write(f"UI_par:{self.Par['UI_par']}\n")
            writeitem = ['box','collectInfo','GridX','GridY','gonio_phi','sample_x','sample_y',\
                'sample_z','align_z','zoom','zoom_scale_x','zoom_scale_y','numofX','numofY',\
                'gridsizeX','gridsizeY']
            for view in ['View1','View2']:
                f.write(f"{view}:===\n")
                for key, value in self.Par[view].items(): 
                    if str(key) in writeitem: 
                        f.write(f'{key}:{value}\n')
            
        
        self._save_current_image('collectview')
        # sys.exit()    
        #todo
        pass
    def _save_current_image(self,filename):
        path=f'{self.RootPath_2.text()}/{filename}1.jpg'
        rect = self.RasterView1.sceneRect()
        rectf=QRectF(rect)        
        image = QImage(rectf.width(),rectf.height(), QImage.Format_ARGB32_Premultiplied)
        
        painter = QPainter(image)
        self.Rasterscene1.render(painter, QRectF(image.rect()),rectf)
        image.save(path)
        path=f'{self.RootPath_2.text()}/{filename}2.jpg'
        self.Rasterscene2.render(painter, QRectF(image.rect()),rectf)
        image.save(path)
        painter.end()
    def showforreadycollect(self,show):
        #todo
        if self.bluiceData['active']:
            pass
        else:
            show = False
        self.Raster.setEnabled(show)
        self.StartRaster.setEnabled(show)
        self.viwe1_move_down.setEnabled(show)
        self.viwe1_move_up.setEnabled(show)
        self.viwe1_move_left.setEnabled(show)
        self.viwe1_move_right.setEnabled(show)
        self.viwe2_move_down.setEnabled(show)
        self.viwe2_move_up.setEnabled(show)
        self.viwe2_move_left.setEnabled(show)
        self.viwe2_move_right.setEnabled(show)
        #show true=wait for collect
        #show False= collecting
        # self.Collectdata.setEnabled(show)
        # self.Abort.setEnabled(True)
        # self.Pause.setEnabled(not show)
        pass







    def quit(self,signum,frame):
        self.logger.critical(f'Main GUi exit')
        self.logger.critical(f'Call bluice closed')
        try:
            self.bluice.quit(signal.SIGINT, "exit_gracefully")
        except Exception as e:
            traceback.print_exc()
            self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
            self.logger.warning(f'Error:{e}')

        self.logger.critical(f'Call MeshbestClinet closed')
        try:
            self.meshbest.quit(signal.SIGINT, "exit_gracefully")
        except Exception as e:
            traceback.print_exc()
            self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
            self.logger.warning(f'Error:{e}')
        self.logger.critical(f'Call SampleImageServer closed')
        self.SampleImageServer.stop()
        for handler in self.logger.handlers:
            handler.close()
        # time.sleep(1)
        # sys.exit()
        self.close()
        # sys.exit(1)
        self.logger.critical(f'm1 pid={self.m1._process.ident}')
        self.m1.shutdown()
        active_children = mp.active_children()
        self.logger.critical(f'active_children={active_children}')
        if len(active_children)>0:
            for item in active_children:
                self.logger.warning(f'Last try to kill {item.pid}')
                os.kill(item.pid,signal.SIGKILL)
        self.logger.critical(f'All closed')
class graphicsScene(QGraphicsScene):
    def __init__ (self, parent=None):
        super(graphicsScene, self).__init__ (parent)

    def mousePressEvent(self, event):
        super(graphicsScene, self).mousePressEvent(event)
        item = QtGui.QGraphicsItem()
        position = QtCore.QPointF(event.scenePos()) - item.rectF.center()
        item.setPos(position.x() , position.y())
        self.addItem(item)
        
class CrossItem(QGraphicsItem):
    
    def __init__(self,sizex,sizey=None,color=Qt.red,pensize=1):
        super(CrossItem,self).__init__()
        if sizey == None:
            self.sizey = float(sizex)
        else:
            self.sizey = float(sizey)
        self.sizex = float(sizex)
        self.color = color
        self.pensize = pensize
        # print(self.sizex,self.sizey,type(self.sizex),type(self.sizey))
    def paint(self, painter, option, widget):
        # painter = QPainter()
        # painter.setPen(Qt.red)
        painter.setPen(QPen(self.color,self.pensize))
        # painter.begin(self)
        painter.drawLine(0,int(self.sizey/2),int(self.sizex),int(self.sizey/2))#Hor line
        painter.drawLine(int(self.sizex/2),0,int(self.sizex/2),int(self.sizey))#ver line
        # print("paint")
        # painter.end(self)
    # def paintEvent(self, arg__0):
    #     painter = QPainter(self)
    #     painter.setPen(QColor.blue)
    #     painter.begin(self)
    #     painter.drawLine(0,self.sizey/2,self.sizex,self.sizey)#Hor line
    #     painter.drawLine(self.sizex/2,0,self.sizex/2,self.sizey)#ver line
    #     painter.end(self)
    def boundingRect(self):
        # print(self.sizex,self.sizey,type(self.sizex),type(self.sizey))
        
        # a = QRectF()
        # a.setTop(0)
        # a.setBottom(0)
        # a.setHeight(self.sizey)
        # a.setWidth(self.sizex)
        # print("update")
        return QRectF(0,0,self.sizex,self.sizey)
    # def center(self):
    #     return (self.sizex/2,self.sizey/2)
    def getoffset(self):
        return (self.sizex/2,self.sizey/2)

# class changefolderbox(QMessageBox):
#     def __init__(self, parent=None):
#         super().__init__(parent)

#         self.setWindowTitle("HELLO!")

#         QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

#         self.buttonBox = QDialogButtonBox(QBtn)
#         self.buttonBox.accepted.connect(self.accept)
#         self.buttonBox.rejected.connect(self.reject)

#         self.layout = QVBoxLayout()
#         message = QLabel("Something happened, is that OK?")
#         self.layout.addWidget(message)
#         self.layout.addWidget(self.buttonBox)
#         self.setLayout(self.layout)        
# class waitMotorStop(QThread):
#     AllStopAt = pyqtSignal(list)
#     def __init__(self,bluiceData,*args):
#         super(waitMotorStop,self).__init__()
#         self.motorlist=[]
#         for arg in args:
#             self.motorlist.append(arg)
#         self.bluiceData=bluiceData
#         self.updatewait=100

#     def run(self):
#         self.timer = QTimer() 
#         self.timer.timeout.connect(self.update)
#         self.timer.start(self.updatewait)
#         pass
#     def update(self):
#         print('check')
#         checkarray = []
#         posarray = []
#         for motor in self.motorlist:
#             checkarray.append(self.bluiceData['motor'][motor]['moving'])
#             posarray.append(self.bluiceData['motor'][motor]['pos'])
#         if all(checkarray):
#             self.timer.stop()
#             self.AllStopAt.emit(posarray)
#             print('check stop')
            
        
if __name__ == "__main__":
    def run_app():         
        '''
        run main screen
        '''
        par = argparse.ArgumentParser()

        par.add_argument("-folder",type=str,help="Raw data folder")
        par.add_argument("-key",type=str,help="The string to  login bluice")
        par.add_argument("-user",type=str,help="Current user name")
        par.add_argument("-stra",type=str,help="The strategy for determine collect par.")
        par.add_argument("-beamline",type=str,help="Beamline")
        par.add_argument("-passwd",type=str,help="The string to  login bluice")
        par.add_argument("-base64passwd",type=str,help="The string to  login bluice")
        args=par.parse_args()
#        print args.folder
       #app = QtWidgets.QApplication(sys.argv)
        if not QtWidgets.QApplication.instance():
            print("new")
            app = QtWidgets.QApplication(sys.argv)
        else:
            print("has old")
            app = QtWidgets.QApplication.instance()
        #print "go"%tb
        if args.folder:
            folder = args.folder
        else:
            folder = os.getcwd()
        if args.key:
            key = args.key
        else:
            #try to find seesion keey
            home = Path.home()
            print(home)
            seesionfile = home.joinpath('.bluice/session')
            print(f'{seesionfile=},{seesionfile.exists()=}')
            if seesionfile.exists():
                with open(seesionfile,'r') as f:
                    context= f.readline()#line one only
                    key = context.rstrip() 
            else:
                key = ""
        if args.user :
            user = args.user
        else:
            user = getpass.getuser()
        if args.stra :
            stra = args.stra    
        else:
            stra = "Auto"
        if args.beamline :
            beamline = args.beamline    
        else:
            beamline = "TPS07A"
        if args.passwd :
            passwd = args.passwd    
        else:
            passwd = ""
        if args.base64passwd :
            base64passwd = args.base64passwd    
        else:
            pwdpath = Path(__file__).parent.joinpath("pass.txt")
            with open(pwdpath,'r') as f:
                context= f.readline()#line one only
                base64passwd = context.rstrip() 
                # print(context)
        #reading setup
        info = beamlineinfo.BeamlineInfo[beamline]
        print(user)    
        window = MainUI(folder,key,user,stra,beamline,info,passwd,base64passwd)
        window.show()
        sys.exit(app.exec_())
        
        
        
        
    run_app()
