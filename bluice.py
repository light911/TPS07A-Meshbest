#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 15:19:15 2020

@author: blctl
"""
import signal,sys,os
# import logging.handlers
#import coloredlogs
import http.client,base64,re,time,socket
import multiprocessing as mp
from multiprocessing import Process, Queue, Manager
from PyQt5.QtCore import QObject,QThread,pyqtSignal,pyqtSlot,QMutex,QMutexLocker
import copy
import logsetup

class BluiceClient(QThread):
    Done = pyqtSignal(str)
    updateGUI = pyqtSignal(dict)
    bluicemessage =  pyqtSignal(list)
    def __init__(self,par,parent=None):
        # super(self.__class__,self).__init__(parent)
#        super(self.__class__,self).__init__(parent)
        # super().__init__()
        super(BluiceClient,self).__init__()
        signal.signal(signal.SIGINT, self.quit)
        signal.signal(signal.SIGTERM, self.quit)
        self.closedbluice = False
        self.host="10.7.1.1"
        self.port=14243
        self.authhost="10.7.1.1"
        self.autport=8080
        self.dhsname="ringstatus"
        self.user="blctl"
        self.passwd=""
        self.hostname="gui07a1.nsrrc.org.tw :0.0"
        self.base64passwd=""
        self.key=""
        # self.client = socket._socketobject
        self.client = ""
        self.tcptimeout=0.05
        
        self.Par = par
        par = {}
        par['Debuglevel'] = "DEBUG"
        # self.Par.update(par)
        self.logger = logsetup.getloger2('Bluice',
                                         LOG_FILENAME='./log/BluiceLog.txt',
                                         level = self.Par['Debuglevel'])
        
#        manager = Manager()

        self.info={}
        self.Qinfo={}
#        self.MotorMoving=manager.dict()
#        self.opCompleted=manager.dict()
        self.MotorMoving={}#
        self.opCompleted={}
        self.job='initconnection'
        self.rasterNum=int(0)
        self.view=int(0)
        self.verpos=float(0)
        self.horpos=float(0)
        self.file_root=''
        self.directory=''
        self.start_angle=''
        self.end_angle=''
        self.delta=''
        self.exposure_time=''
        self.distance=''
        self.attenuation=''
        self.beamsize=''
        self.energy1=''
        self.shuttered="0"
        print("dcsdhs init")  
        self.test=False
    def run(self):
        #for QThread
#        print "Bluice job=", self.job
        if self.job == 'initconnection':
            self.initconnection()
        elif self.job == 'moveSample':
            self.moveSample_mp(self.rasterNum,self.view,self.verpos,self.horpos)
        elif self.job == 'collect':            
            self.collect_mp(self.file_root,self.directory,self.start_angle,\
                         self.end_angle,self.delta,self.exposure_time,\
                         self.distance,self.attenuation,self.beamsize,\
                         self.energy1,self.shuttered)
        elif self.job == 'abort':
            self.abort()
           
    def initconnection(self):
#        print "Bluice job (init)=", self.job
#        loginID = self.get_login_str()
        if self.key =="":
            if self.passwd =="":
                pass
            else:
                self.base64passwd = base64.b64encode(self.user+":"+self.passwd)              
            loginID = self.get_login_str_2()
        else:
            self.logger.info("Have session key")
            loginID = self.key
        self.info['sid']=loginID
        self.info['counter']=1
        loginsrt = "gtos_client_is_gui "+ self.user+ " " + loginID + " " + self.hostname
        # self.logger.info(loginsrt)
        '''
        gtos_client_is_gui blctl F1EA013BCAB10598F440A3ADC76EC37E gui05a1-local.nsrrc.org.tw :0
        '''
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(self.tcptimeout)
        self.logger.info("try to connect")
        trytime=0
        while True:
            try:
                self.client.connect((self.host, self.port))
                self.logger.info("try to Connect to %s:%d" % (self.host, self.port))
                
            except:
                if trytime == 0:
#                    self.logger.debug(f'fail connect to {self.host} {self.port}')
                    self.logger.critical("connection to DCSS fail, I wait 1 sec then try again until sucess...")
                    trytime =1
                else:
                    self.logger.debug("connection fail wait 1 sec then try again")
                    
                time.sleep(1)
                continue
            break
        
        self.logger.info("connection success")
        time.sleep(0.5)
        ans = self.client.recv(4096)
        self.logger.info(f"ans:{ans}")
#        index = ans.decode().find('\x00')
        index = ans.decode().find('\x00')

#        print (f'DCSS answer:{ans}')
#        print (f'len:{len(ans)}')
        if ans[0:index].decode() == "stoc_send_client_type" :
            self.logger.debug("dcss ans correct!")
            echo=loginsrt
        else:
            self.logger.debug("dcss ans NOT correct!")
            echo=loginsrt
        self.logger.info ("Answer to DCSS:%s" % (echo))
        command = self.ansDHS(echo)
#        self.client.sendall(command.encode())
        self.logger.info(f"toDCSS:{command}")
        self.client.sendall(command.encode())
        self.run2()

    def run2(self) :
#        print("RUN")
        #creat reciver, sender ,PV process
        m = Manager()
        reciveQ = m.Queue() 
        sendQ = m.Queue()
        MainQ = m.Queue()
        self.Qinfo["sendQ"]=sendQ
        self.Qinfo["reciveQ"]=reciveQ
        self.Qinfo["MainQ"] = MainQ

        
        
        reciver_ = Process(target=self.reciver, args=(reciveQ,sendQ,MainQ,self.client,))
        sender_ = Process(target=self.sender, args=(reciveQ,sendQ,MainQ,self.client,))
#        test_ = Process(target=self.test, args=(reciveQ,sendQ,epicsQ,self.client,))
#        epcisPV_ = Process(target=self.epicsPV, args=(reciveQ,sendQ,epicsQ,self.client,))
        reciver_.start()
        sender_.start()
#        test_.start()
#        epcisPV_.start()
        
        while True:
            try:
                command = MainQ.get(block=True)
                if isinstance(command,str):
                    if command == "exit" :
                        break
                elif isinstance(command,list) :
                    #send to GUI
                    self.bluicemessage.emit(command)
                else:
                    pass
            except:
                pass
        
        
        
        reciver_.join()
        sender_.join()
#        epcisPV_.join()

        if self.closedbluice:
            pass
        else:
            self.initconnection()
        
    def reciver(self,reciveQ,sendQ,MainQ,tcpclient) :
        msg = ""
        while True:
            time.sleep(0.01)
            #check command
            try:
                command = reciveQ.get(block=False)
                if isinstance(command,str):
                    if command == "exit" :
                        break
                else:
                    pass
            except:
                pass
            #recive data
            try:
                data = self.client.recv(4096)
#                print(f'data:{data}')
#                print data
            except socket.timeout:
                pass

            except socket.error:
                # Something else happened, handle error, exit, etc.
                self.logger.critical ("Error for socket error")
                sendQ.put("exit")
                MainQ.put("exit")
                break
            else:
                if len(data) == 0:
                    self.logger.critical ("orderly shutdown on DCSS server end")
                    sendQ.put("exit")
                    MainQ.put("exit")
                    break
                else:
                    # got a message do something :)
                    msg = msg + data.decode()
                    index = msg.find('\x00')
                    while index != -1:
                        
#                        print(f'msg:{msg.encode()}')
#                        print(f'index:{index}')
                        processdata=msg[0:index]
                        
                        msg = msg [index+1:]
#                        print(f'new msg:{msg}')

                        command = self.processrecvice(processdata).split(" ")
                        MainQ.put(command)
                        if command[0] == "stoh_abort_all":
                            self.logger.debug(command)
                            #refesh UI?
                            pass
                        elif command[0] == "stoh_start_motor_move":
                            self.logger.debug(command)
                            #"stoh_start_motor_move motorName destination
                            motor=command[1]
                            self.MotorMoving[motor]=True
                            #refesh UI?
                            pass
                        elif command[0] == "stoh_set_shutter_state":
                            self.logger.debug(command)
                            #stoh_set_shutter_state shutterName state (state is open or closed.)
                            pass
                        elif command[0] == "stoh_start_oscillation":
                            #stoh_start_oscillation motorName shutter deltaMotor deltaTime
                            self.logger.debug(command)
                            pass
                        elif command[0] == "stoh_start_operation":
                            #stoh_start_operation operationName operationHandle [arg1 [arg2 [arg3 [...]]]]
                            #operationName is the name of the operation to be started.
                            #operationHandle is a unique handle currently constructed by calling the create_operation_handle procedure in BLU-ICE. This currently creates a handle in the following format:
                            #clientNumber.operationCounter
                            #where clientNumber is the number provided to the BLU-ICE by DCSS via the stog_login_complete message. DCSS will reject an operation message if the clientNumber does not match the client. The operationCounter is a number that the client should increment with each new operation that is started.
                            #arg1 [arg2 [arg3 [...]]] is the list of arguments that should be passed to the operation. It is recommended that the list of arguments continue to follow the general format of the DCS message structure (space separated tokens). However, this requirement can only be enforced by the writer of the operation handlers.
                            self.logger.debug(command)
                            pass
                        elif command[0] == "stoh_read_ion_chambers":
                            #stoh_read_ion_chambers time repeat ch1 [ch2 [ch3 [...]]]
                            self.logger.debug(command)
                            pass
                        elif command[0] == "stoh_register_string":
                            pass
                        elif command[0] == "stog_update_client":
                            self.logger.debug(command)
                            pass                        
                        elif command[0] == "stog_update_client_list":
                            self.logger.debug(command)
                            pass                        
                        elif command[0] == "stog_set_permission_level":
                            self.logger.debug(command)
                            pass                        
                        elif command[0] == "stog_configure_hardware_host":
#                            print command
                            self.logger.debug(command)
                            pass                        
                        elif command[0] == "stog_set_motor_base_units":
                            self.logger.debug(command)
                            pass                        
                        elif command[0] == "stog_configure_string":
                            self.logger.debug(command)
                            self.updaterun(command)
                            pass                                   
                        elif command[0] == "stog_configure_ion_chamber":
                            self.logger.debug(command)
                            pass                                
                        elif command[0] == "stog_dcss_end_update_all_device":
                            self.logger.debug(command)
                            pass     
                        elif command[0] == "stog_configure_operation":
                            self.logger.debug(command)
                            pass     
                        elif command[0] == "stog_note":
                            self.logger.debug(command)
                            pass     
                        elif command[0] == "stog_start_operation":
                            #[u'stog_start_operation', u'getMD2Motor', u'1.24970', u'camera_zoom']
                            #[u'stog_start_operation', u'moveSample', u'122.327', u'-303.00686378', u'-91.6692524683']
                            #[u'stog_start_operation', u'collectRun', u'122.332', u'0', u'che', u'0', u'PRIVATEXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX']
#                            print command
                            op=command[1]
                            self.opCompleted[op]=False
                            self.logger.debug(command)
                            pass  
                        elif command[0] == "stog_operation_update":
                            #[u'stog_operation_update', u'prepare_mount_next_crystal', u'1.25103', u'OK', u'to', u'prepare']
#                            print command
                            self.logger.debug(command)
                            pass     
                        elif command[0] == "stog_operation_completed":
                            self.logger.debug(command)
                            #[u'stog_operation_completed', u'changeMode', u'1.24909', u'normal', u'']
                            op=command[1]
                            self.opCompleted[op]=True
                        elif command[0] == "stog_log":
                            #[u'stog_operation_completed', u'changeMode', u'1.24909', u'normal', u'']
                            self.logger.debug(command)
                            pass     
                        elif command[0] == "stog_motor_move_started":
                            #[u'stog_motor_move_started', u'detector_z', u'400.000000']
                            self.logger.debug(command)
                            motor=command[1]
                            self.MotorMoving[motor]=True
                            pass     
                        
                        elif command[0] == "stog_configure_shutter":
                            #stog_configure_shutter shutter md2 closed
                            #stog_configure_shutter Al_128 alfilter open
                            motor=command[1]
                            pos=command[3]
                            self.info[motor]=pos 
                            self.logger.debug(command)
                            pass   
                        elif command[0] == "stog_report_shutter_state":
                            #[u'stog_report_shutter_state', u'Al_1', u'open']
                            try:
                                motor=command[1]
                                pos=command[2]
                                self.info[motor]=pos                          
                            except:
                                self.logger.info(f"error:motor={command[1]} pos={command[2]}")
                                self.logger.info(command)
                            self.logger.debug(command)
                            
                        elif command[0] == "stog_configure_real_motor":
                            # stoh_configure_real_motor motoName position upperLimit lowerLimit scaleFactor speed acceleration backlash lowerLimitOn upperLimitOn motorLockOn backlashOn reverseOn 
                            #[u'stog_configure_real_motor', u'detector_z', u'idhs', u'detector_z', u'400.000000', u'910.000000', u'100.900000', u'78.740000', u'1000', u'350', u'-238', u'1', u'1', u'0', u'1', u'1', u'']
                            motor=command[1]
                            pos=command[4]
                            self.info[motor]=float(pos)
#                            print command
#                            print command
                            self.logger.debug(command)
                        elif command[0] == "stog_configure_pseudo_motor":
                            # stoh_configure_real_motor motoName position upperLimit lowerLimit scaleFactor speed acceleration backlash lowerLimitOn upperLimitOn motorLockOn backlashOn reverseOn 
                            # [u'stog_configure_pseudo_motor', u'fluxmode', u'idhs', u'fluxmode', u'1.000000', u'2.000000', u'-2.000000', u'0', u'0', u'0', u'']
                            motor=command[1]
                            pos=command[4]
                            self.info[motor]=float(pos)
#                            print command
                            self.logger.debug(command)
                        elif command[0] == "stog_motor_move_completed":
                            #[u'stog_motor_move_completed', u'change_mode', u'4.000000', u'normal']
                            motor=command[1]
                            pos=command[2]
                            self.info[motor]=float(pos)
                            self.MotorMoving[motor]=False
#                            print command
                            self.logger.debug(command)
                        elif command[0] == "stog_update_motor_position":
                            #[u'stog_update_motor_position', u'attenuation', u'75.756615', u'normal']
                            motor=command[1]
                            pos=command[2]
                            self.info[motor]=float(pos)
#                            print command
                            self.logger.debug(command)
                        elif command[0] == "stog_device_permission_bit" :
                            #stog_device_permission_bit slit_2_spear {0 1 1 1 1} {0 0 0 0 0}
                            self.logger.debug(command)
                        elif command[0] == "stog_set_string_completed" :
                            self.updaterun(command)
                            if command[1] == "tps_current" or command[1] == "tls_current" or command[1] == "beamlineOpenState" or command[1] == "tps_state":
                                pass
                            else :
                                self.logger.debug(command)
                            #stog_set_string_completed beamlineOpenState normal Closed 3666394636
                            #stog_set_string_completed tps_current normal 404.0531
                            
                        elif command[0] == "stog_set_motor_base_units":
                            #[u'stog_set_motor_base_units', u'hs1l', u'm']
                            self.logger.debug(command)
                        elif command[0] == "stog_set_motor_dependency":
                            self.logger.debug(command)
                        elif command[0] == "stog_set_motor_children":
                            self.logger.debug(command)
                        elif command[0] == "stog_report_ion_chambers":
                            self.logger.debug(command)
                        elif command[0] == "":
                            self.logger.debug(command)
                            pass
                        elif command[0] == "stog_become_master":
                            self.logger.debug(command)
                        elif command[0] == "stog_become_slave":
                            self.logger.debug(command)
                        elif command[0] == "stog_login_complete":
                            self.info['loginindex']=command[1]
                            self.logger.debug(command)
                        else:
#                            print(f'Unknown command:{command[0]}')
                            self.logger.info(f"Unknown command:{command}")
                        
                        index = msg.find('\x00')
                        
    def processrecvice(self,string):
        '''
        ex"           46            0 stoh_register_string tps_current tps_current\n\x00"
        ex"          20            0 stoh_abort_all soft"
        '''
        # print (f'process str:{string}')
        index = string.find("0")
        if index != -1:
            length = int(string[0:13])
            zeroindex = string.find("0",13)
            ans = string[zeroindex+2:zeroindex+length+1]
            # print (f'0 index@{index} length:{length}')
            # print (f'after process str:{ans} length:{len(ans)}')
            # print (ans.encode())
        else:
            ans=""
            # print(ans)
        return ans

                            
    def sender(self,reciveQ,sendQ,MainQ,tcpclient) :
        starttime=time.time()
        oldinfo={}
        
        while True:
            time.sleep(0.01)
            if time.time()-starttime > 0.05:
                
                newinfo = copy.deepcopy(self.info)
                for item in newinfo :
                    try:
                        if newinfo[item] != oldinfo[item]:
#                            print item,newinfo[item]
                            pass
                    except:
                        pass
                
                oldinfo = newinfo
                starttime = time.time()
                
            #check command
            try:
                command = sendQ.get(block=False)
                if isinstance(command,str):
                    if command == "exit" :
                        break
                    elif command == "hi" :
                        print("sender recive hi")
                    else:
#                        tcpclient.sendall(command.encode())
                        # print(command)
                        todcss = self.toDCSScommand(command).encode()
                        tcpclient.sendall(todcss)
                        self.logger.debug(todcss)
                elif isinstance(command,tuple) :
                    #command 0:command 1:motorname 2:position 3:type 4:state
                    echo = ""
                    if command[0] == "updatevalue" :
                        if command[3] == "motor":
                            #htos_update_motor_position motorname postion status
                            echo = "htos_update_motor_position " + str(command[1]) + " " +str(command[2]) + " " + str(command[4])
                        elif command[3]  == "shutter" :
                            #htos_report_shutter_state shutterName state
                            echo = "htos_report_shutter_state " + str(command[1])+ " " +str(command[2]) + " " + str(command[4])
                        elif command[3]  == "ioncchamber" :
                            #htos_report_ion_chambers time ch1 counts1 [ch2 counts2 [ch3 counts3 [chN countsN]]]
                            echo = "htos_report_ion_chambers " + str(command[1]) + " " + str(command[2])  
                        elif command[3]  == "operation_update" :
                            #htos_operation_update operationName operationHandle arguments
                            echo = "htos_operation_update " + str(command[1]) + " " + str(command[2])
                        elif command[3] == "operation_completed" :   
                            #htos_operation_completed operationName operationHandle status arguments
                            echo = "htos_operation_completed " + str(command[1]) + " " + str(command[4])+ " " + str(command[2])
                        elif command[3] == "string" :
                            #htos_set_string_completed strname status arguments
                            echo = "htos_set_string_completed " + str(command[1]) + " " + str(command[4]) + " " + str(command[2])
                            if str(command[1]) == "TPSstate":
                                print(echo)
                        
                        else :
                            self.logger.info ("unkonw command type:%s" % command)
                            pass
                            
                    elif command[0] == "startmove" :
                        #htos_motor_move_started motorName position
                        echo = "htos_motor_move_started " + str(command[1]) + " " +str(command[2])
                        
                    elif command[0] == "endmove" :
                        #htos_motor_move_completed motorName position completionStatus
                        #Normal indicates that the motor finished its commanded move successfully.
                        #aborted indicates that the motor move was aborted.
                        #moving indicates that the motor was already moving.
                        #cw_hw_limit indicates that the motor hit the clockwise hardware limit.
                        #ccw_hw_limit indicates that the motor hit the counter-clockwise hardware limit.
                        #both_hw_limits indicates that the motor cable may be disconnected.
                        #unknown indicates that the motor completed abnormally, but the DHS software or the hardware controller does not know why.
                        echo = "htos_motor_move_completed " + str(command[1]) + " " +str(command[2]) + " " +str(command[3])
                    elif command[0] == "gtos_start_operation" :
                        if command[1] == 'moveSample':
                            echo = f'gtos_start_operation moveSample {self.info["loginindex"]}.{self.info["counter"]} {command[2]} {command[3]}'
                            self.info["counter"] = self.info["counter"] + 1
                    else:
                        self.logger.info ("unkonw command type:%s" % command)
                        pass
                    #send to dcss    
                    
                    todcss = self.toDCSScommand(echo)
                    #print(f'todcss:{todcss.encode()}')
                    #print(len(todcss.encode()))
                    tcpclient.sendall(todcss.encode()) 
                    self.logger.warning(todcss)
                    
                else:
                    self.logger.info ("unkonw command type:%s" % command)
                    pass
            except:
                pass
        pass

    def test(self,reciveQ,sendQ,epicsQ,tcpclient) :
        oldfilno=sys.stdin.fileno()
        print(oldfilno)
        sys.stdin = os.fdopen(0)
        while True:
            text=input("Test command:")
            if text == "1" :
                self.setupRun("test","/data/blctl/test123","1","6","0.5","0.1","600","50","12400")
#                self.setupRun(file_root,directory,start_angle,end_angle,delta,exposure_time,distance,attenuation,energy1)
            elif text == "quit" :
#                sendQ.put("exit")
                reciveQ.put("exit")
                break
            elif text[:3] == "op_" :
                print((text[3:]))
                self.SendOprationtoDcss(text[3:])
            elif text == "collect" :
                self.info['loginindex']
                sendQ.put("gtos_become_master force")
                command = "gtos_start_operation collectRuns %s.%s 1 %s" % (self.info['loginindex'],self.info['counter'],self.info['sid'])
                sendQ.put(str(command))
                self.info['counter'] = self.info['counter'] + 1
                
            else:
                pass
    def moveSample(self,rasterNum,view,ver,hor):
        msp=Process(target=self.moveSample_mp, args=(rasterNum,view,ver,hor,))
        msp.start()
        
    def moveSample_mp(self,rasterNum,view,ver,hor):
        '''
        gtos_start_operation rasterRunsConfig 6.127 move_view_to_beam 0 1 -0.151162790698 0.13483146067 
                                                              rasterNum  view_index ver_box hor_box
                                                              0 0 for center 
                                                              
                                                             -1,-1
                                                              0,-1  0,0  0,1 
                                                              0, 1       1,1
        '''
        if self.test:
            print("Start moving")
            time.sleep(1)
            self.opCompleted['rasterRunsConfig']=True
            print("End of moving")
        else:
            
            command = 'rasterRunsConfig move_view_to_beam ' + str(rasterNum) + ' ' + str(view) + ' ' + str(ver) + ' ' + str(hor)
            print("Start moving")
            self.SendOprationtoDcss(command)
            self.opCompleted['rasterRunsConfig'] = False
            time.sleep(0.05)
            
            while not self.opCompleted['rasterRunsConfig']:
                time.sleep(0.05)
            
            print("End of moving")
#        self.Done.emit('moveSample')
        #make sure move completed
    def collect(self,file_root,directory,start_angle,end_angle,delta,exposure_time,distance,attenuation,beamsize,energy1,shuttered="0"):
        collp=Process(target=self.collect_mp, args=(file_root,directory,start_angle,end_angle,delta,exposure_time,distance,attenuation,beamsize,energy1,shuttered,))
        collp.start()
        
    def collect_mp(self,file_root,directory,start_angle,end_angle,delta,exposure_time,distance,attenuation,beamsize,energy1,shuttered="0"):
#        print self.info
#        if energy1 == -1.0:
#            energy1 = 12400
#        print self.info['run1']
#            energy = str(self.info['energy'])
        if self.test:    
            print("Start collect")
            time.sleep(1)
            self.opCompleted['collectRuns']=True
            print("End of collect")
        else:
            
            self.setupRun(file_root,directory,start_angle,end_angle,delta,exposure_time,distance,attenuation,str(energy1),shuttered)
            command = "gtos_start_motor_move beamSize %s" % (beamsize)
            print(command)
            sendQ=self.Qinfo["sendQ"]
            sendQ.put(str(command))
            self.MotorMoving['beamSize'] = True
            while self.MotorMoving['beamSize']:
                time.sleep(0.05)
            print("End of moveing beamsize")
            
            command = "gtos_start_operation collectRuns %s.%s 1 %s" % (self.info['loginindex'],self.info['counter'],self.info['sid'])
            sendQ.put(str(command))
            self.opCompleted['collectRuns']=False
            while not self.opCompleted['collectRuns']:
                time.sleep(0.05)
#            command = "gtos_start_operation collectRun %s.%s 1 %s" % (self.info['loginindex'],self.info['counter'],self.info['sid'])
#            sendQ.put(str(command))
#            self.opCompleted['collectRun']=False
#            while not self.opCompleted['collectRun']:
#                time.sleep(0.05)
            
#        self.Done.emit('Collect')
    def abort(self):
        command= 'gtos_abort_all soft'
        sendQ=self.Qinfo["sendQ"]
        sendQ.put(str(command))
#        self.Done.emit('Abort')
        
    def get_login_str(self):
        conn=http.client.HTTPConnection(self.authhost+":"+str(self.autport))
        page='/gateway/servlet/APPLOGIN?userid=XXXX&passwd=YYY&AppName=BluIce'
        page=page.replace('XXXX',self.user)
        tobase64=base64.b64encode(self.user+":"+self.passwd)
        page=page.replace('YYY',tobase64)
#        print page
        conn.request("GET",page)
        r1 = conn.getresponse()
        if r1.status == 200:
            txt=r1.read()
#            print txt
            '''
            Auth.SessionKey=SMBSessionID
            Auth.SMBSessionID=23D0BB51B1B2B1C59DAA06C8A3175200
            Auth.SessionValid=TRUE
            Auth.SessionCreation=1583483773030
            Auth.SessionAccessed=1583483773030
            Auth.UserID=blctl
            Auth.Method=smb_pam
            Auth.AllBeamlines=BL-13B1;BL-13C1;BL-15A1;BL-05A;BL-sim
            Auth.UserType=
            Auth.RemoteAccess=Y
            Auth.Enabled=Y
            Auth.UserPriv=4
            Auth.UserName=Beamline Control
            Auth.Beamlines=ALL
            Auth.JobTitle=Beamline Scientist
            Auth.OfficePhone=3127
            Auth.UserStaff=Y
            '''
            txt2=txt.splitlines()
            for line in txt2:
                if bool(re.search("Auth.SMBSessionID=",line)):
                    loginstr=line[18:]
        else:
            print((r1.reason))
        
        

        
        conn.close()
        print("login str=",loginstr)
        return loginstr

    def get_login_str_2(self):
        conn=http.client.HTTPConnection(self.authhost+":"+str(self.autport))
        page='/gateway/servlet/APPLOGIN?userid=XXXX&passwd=YYY&AppName=BluIce'
        page=page.replace('XXXX',self.user)
#        tobase64=base64.b64encode(self.user+":"+self.passwd)
        page=page.replace('YYY',self.base64passwd)
#        print page
        conn.request("GET",page)
        r1 = conn.getresponse()
        if r1.status == 200:
            txt=r1.read().decode()
#            print txt
            '''
            Auth.SessionKey=SMBSessionID
            Auth.SMBSessionID=23D0BB51B1B2B1C59DAA06C8A3175200
            Auth.SessionValid=TRUE
            Auth.SessionCreation=1583483773030
            Auth.SessionAccessed=1583483773030
            Auth.UserID=blctl
            Auth.Method=smb_pam
            Auth.AllBeamlines=BL-13B1;BL-13C1;BL-15A1;BL-05A;BL-sim
            Auth.UserType=
            Auth.RemoteAccess=Y
            Auth.Enabled=Y
            Auth.UserPriv=4
            Auth.UserName=Beamline Control
            Auth.Beamlines=ALL
            Auth.JobTitle=Beamline Scientist
            Auth.OfficePhone=3127
            Auth.UserStaff=Y
            '''
            txt2=txt.splitlines()
            for line in txt2:
                if bool(re.search("Auth.SMBSessionID=",line)):
                    loginstr=line[18:]
        else:
            print((r1.reason))
        
        

        
        conn.close()
        print("login str=",loginstr)
        return loginstr    
    
    #some Tools        
    def ansDHS(self,command):
        addNumber = 200 - len(command)
        addText=""
        for i in range(addNumber):
            addText = addText + '\x00'
        returnANS = command + addText
    #    print(len(command))
    #    print(addNumber)
    #    print(returnANS)
    #    print(len(returnANS))
        return returnANS
        
        
    def toDCSScommand(self,command):
        index = len(command)+1
        command = self.addspace(index)+"            0 "+ command +"\x00"
        return command
    
    def addspace(self,number):
        addspaceN=0
        addspaceN = 12-len(str(number))
        ans=""
        for x in range(addspaceN):
            ans = ans + " "
        ans = ans + str(number)
        return ans
#        conn.request(/gatw)
    def updaterun(self,command):
        
        if command[1][:8] == "runExtra":
            pass
        elif command[1][:4] == "runs": 
            pass
        elif command[1][:3] == "run": 
            self.info[command[1]] = {"dhs":command[2],\
                     "status":command[3],\
                     "next_frame":command[4],\
                     "run_label":command[5],\
                     "file_root":command[6],\
                     "directory":command[7],\
                     "start_frame":command[8],\
                     "axis_motor":command[9],\
                     "start_angle":command[10],\
                     "end_angle":command[11],\
                     "delta":command[12],\
                     "wedge_size":command[13],\
                     "exposure_time":command[14],\
                     "distance":command[15],\
                     "beam_stop":command[16],\
                     "attenuation":command[17],\
                     "num_energy":command[18],\
                     "energy1":command[19],\
                     "energy2":command[20],\
                     "energy3":command[21],\
                     "energy4":command[22],\
                     "energy5":command[23],\
                     "detector_mode":command[24],\
                     "inverse_on":command[25],\
                     "shuttered":command[26]}
                
#        print 'updateinfo:',self.info
    def setupRun(self,file_root,directory,start_angle,end_angle,delta,exposure_time,distance,attenuation,energy1,shuttered="0"):
#        wedge_size = (float(end_angle)-float(start_angle))/float(delta)
        command=[]
        command.append("gtos_become_master force")
        #for normal collect,
        command.append("gtos_set_string collect_mode normal")
        for i in range(15,-1,-1):
            j=i+1
            command.append("gtos_start_operation runsConfig %s.%s %s deleteRun %s" % (self.info['loginindex'],self.info['counter'],self.user,j))
            self.info['counter'] = self.info['counter'] + 1
        command.append("gtos_start_operation runsConfig %s.%s %s addNewRun" % (self.info['loginindex'],self.info['counter'],self.user))
        self.info['counter'] = self.info['counter'] + 1

            #gtos_start_operation runsConfig 6.10 blctl deleteRun 3
            
        wedge_size="36000"
        command.append("gtos_set_string run1 inactive " + "0 1 " + file_root + " " + directory + " 1 phi "\
                + start_angle + " " + end_angle + " " + delta + " " + wedge_size + " " + exposure_time\
                + " " + distance +" "+ self.info["run1"]["beam_stop"] + " " + attenuation + " 1 " + energy1\
                + " 0 0 0 0 2 0 " + shuttered)
                
        sendQ=self.Qinfo["sendQ"]
        for items in command:

            sendQ.put(str(items))
            time.sleep(0.1)  
            
    def SendOprationtoDcss(self,opstr):      
        command=[]
        command.append("gtos_become_master force")
        indexstr=str(self.info['loginindex']) + "." + str(self.info['counter'])
        self.info['counter'] = self.info['counter'] + 1    
        fulltxt=opstr.split(" ")
        i=0
        for txt in fulltxt:
            if i == 0:
                abc = "gtos_start_operation " + txt
                i=i+1
            elif i == 1:
                abc = abc + " " + indexstr + " " + txt
                i = i + 1
            else:
                abc = abc + " " + txt
        command.append(abc)
        sendQ=self.Qinfo["sendQ"]
        for items in command:
            sendQ.put(str(items))
            time.sleep(0.1)       
        #gtos_start_operation rasterRunsConfig 6.127 move_view_to_beam 0 1 -0.151162790698 0.13483146067 

                                               #next_frame run_label
        #gtos_set_string run1 inactive 0 1 test /data/blctl/test 1 Phi 0.00 6.0 1.0 180.0 0.1 600.000000 42.005334 50 1 12400.000000 0.0 0.0 0.0 0.0 2 0 1
    def quit(self,signum,frame):
        self.logger.critical(f'Quit Bluice Client')
        self.closedbluice = True
        self.Qinfo["MainQ"].put("exit")
        self.Qinfo["sendQ"].put("exit")
        self.Qinfo["reciveQ"].put("exit")
        self.client.close()
        pass
    
def quit(signum,frame):
    print("Bluice client program STOP")
    print(f'give info at break= {info}')
    print(f'info2={abc},{info}')
    
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, quit)
    signal.signal(signal.SIGTERM, quit)
    print((sys.stdin.fileno()))
    manager = Manager()
    info=manager.dict()
    Qinfo=manager.dict()
    MotorMoving=manager.dict()
#    manager.shutdown
#    print type(info)
    abc=BluiceClient()
    abc.info=info
    abc.Qinfo=Qinfo
    abc.MotorMoving=MotorMoving
    abc.initconnection()