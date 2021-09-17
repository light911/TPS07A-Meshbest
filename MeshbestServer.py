#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logsetup
import time,signal,sys,os,copy
from multiprocessing.managers import BaseManager
from multiprocessing import Process, Queue , Manager
from multiprocessing.managers import BaseProxy
from MestbestAPITools import convert_data
import requests,json

import numpy,base64
import Config
from Eiger.DEigerStream import ZMQStream
from Eiger.fileWriter import stream2cbf
import variables
#https://stackoverflow.com/questions/29788809/python-how-to-pass-an-autoproxy-object


class QueueManager(BaseManager): pass

class MestbestSever():
    def __init__(self):
        signal.signal(signal.SIGINT, self.quit)
        signal.signal(signal.SIGTERM, self.quit)
        m = Manager()
        # par={}
        # par['Debuglevel'] = "DEBUG"
        self.Par = m.dict()
        self.state = m.dict() 
        self.Par.update(Config.Par)
        self.state.update(Config.Par)
        init_meshbest_data = variables.init_meshbest_data()
        
        self.Par['View1'] = init_meshbest_data
        self.Par['View2'] = init_meshbest_data
        self.Par['UI_par'] = variables.init_uipar_data()
        
        self.MangerPort = 6534
        self.logger = logsetup.getloger2('MestbestServer',LOG_FILENAME='./log/MesrbestServerLog.txt',level = self.Par['Debuglevel'])
        self.ServerQ = m.Queue()
        # self.processQ = m.Queue()
        self.ZMQQ = m.Queue()
        self.meshbestjobQ = m.Queue()
        self.clientsinfo = m.list()
        self.clientsQ = []
        self.clientidlist = []
        # self.clientsQ = []
        
        self.clientid = 1
        # print(type(self.clientsQ))
        #ZMQ setup
        self.eigerhost = '10.7.1.98'
        self.eigerzmqport = 9999
        self.meshPositionsdata_1 = []
        self.meshPositionsdata_2 = []
        self.checkingViwe1 =False
        self.checkingViwe2 =False
        self.numofdataView1 = 0
        self.numofdataView2 = 0
        self.meshbesturl ='http://10.7.1.107:8082/job'
        #
        self.convertlist = variables.convertlist()
        pass
        self.logger.debug(f'Init Par {self.Par}')

        self.processnum=100
        self.job_queue = m.Queue()
        # for i in range(self.processnum):#number of cpu
        #     Process(target=self.worker, args=(self.job_queue,)).start()

    def worker(self,job_queue):
        os.nice(19)
        while True:
            command = job_queue.get(block=True)
            if isinstance(command,str):
                if command == "exit" :
                    break
            elif isinstance(command,tuple) :
                frames = command[0]
                ServerQ = command[1]
                metadata = command[2]
                meshbestjobQ = command[3]
                stream2cbf.__decodeImage2__(frames,ServerQ,metadata,meshbestjobQ)
            else:
                pass    
    
    def start(self):
        #start ManagerServer
        p1 = Process(target=self.ManagerServer,args=(self.MangerPort,))
        p1.start()
        #start monitor
        p2 = Process(target=self.Monitor,args=(self.ServerQ,self.ZMQQ,))
        p2.start()
        
        
        p3 = Process(target=self.ZMQ_monitor,args=(self.ZMQQ,self.ServerQ,self.meshbestjobQ,self.job_queue,))
        p3.start()
        
        p4 = Process(target=self.meshbetjob,args=(self.ServerQ,self.meshbestjobQ,))
        p4.start()        
        # p4 = Process(target=self.writetoCBF,args=(self.ServerQ,self.processQ,self.ZMQQ,))
        # p4.start()
        # p3 = Process(target=self.test,args=())
        # p3.start()
        self.logger.info(f'All process started')
        self.logger.info(f'ManagerServer PID ={p1.pid}')
        self.logger.info(f'Monitor       PID ={p2.pid}')
        self.logger.info(f'ZMQ_monitor   PID ={p3.pid}')
        self.logger.info(f'Meshbetjob    PID ={p4.pid}')
        # p1.join()
        p2.join()
        p3.join()
        p4.join()
        # p2.kill()
        self.logger.critical(f'All process Stoped')
        
    def test(self):
        while True:
            self.sendtoAllClient(('Test','Hi~'))
            time.sleep(1)
        
    def ManagerServer(self,port=6544):
        # self.ServerQ = Queue()
        QueueManager.register('ServerQ', callable=lambda:self.ServerQ)
        m = QueueManager(address=('', port), authkey=b'tps07a')
        s = m.get_server()
        self.logger.info(f'Start Queue Manager server')
        s.serve_forever()
        
    def addManagerClient(self,message):
        # print(f'addManagerClient,message={message}')
        # print(f'Start--Type {type(self.clientsinfo)},Len {len(self.clientsinfo)}')
        ip = message['ip']
        port = message['port']

        QueueManager.register('ClientQ')
        mm = QueueManager(address=(ip,port), authkey=b'tps07a')
        mm.connect()
        ClientQ = mm.ClientQ()
        
        # print(ClientQ,type(ClientQ))
        
        ClientQ.put(('YourID',self.clientid))
        par = copy.deepcopy(self.Par)
        self.logger.info(f'send par to new client,id = {self.clientid}')
        ClientQ.put(('updatePar',par))
        # print(f'reportID {self.clientid}')
        
        
        
        # d = self.clientsQ[0]
        
        data = {}
        data['info'] = message
        data['id'] =  self.clientid
        # data['Q'] = ClientQ
        # self.clientsQ.append(ClientQ)
        
        self.clientid =  self.clientid+1
        # print(data,type(self.clientsQ),self.clientsQ)
        # templlist = []
        # templlist.append(data)
        # print(f'templist={templlist}')
        self.clientsinfo.append(data)
        # self.clientsQ.append(ClientQ)
        # self.clientidlist.append(data['id'])
        self.logger.info(f'Add new client,id = {data["id"]}')
        self.logger.warning(f'Current number of client : {len(self.clientsinfo)}')
        self.sendtoAllClient(('newclient',data["id"]))
        # print(f'END---Type {type(self.clientsinfo)},Len {len(self.clientsinfo)}')
        
    def sendtoAllClient(self,message):
        # will send to Mestbestemessage in MestUI in the End
        # self.logger.warning(f' clientsQ {len(self.clientsQ)}, clientsinfo {len(self.clientsinfo)}')
        # self.logger.warning(f' clientsinfo:{self.clientsinfo}')
        removelist=[]
        if len(self.clientsQ) != len(self.clientsinfo):
            self.logger.debug(f' clientsQ {len(self.clientsQ)} =! clientsinfo {len(self.clientsinfo)}')
            self.clientsQ = []
            self.clientidlist = []
            # print(self.clientsQ,self.clientsinfo)
            for item in self.clientsinfo:
                ip = item['info']['ip']
                port = item['info']['port']
                # self.logger.warning(f'reupdate client {item["id"]}:{item["info"]} ')
                try:
                    QueueManager.register('ClientQ')
                    mm = QueueManager(address=(ip,port), authkey=b'tps07a')
    
                    mm.connect()
                    ClientQ = mm.ClientQ()
                except ConnectionRefusedError:
                    removelist.append(item["id"])
                    # self.removeIDinClientsInfo(item["id"])
                else:
                    self.logger.warning(f'client ok = {item["id"]}:{item["info"]} ')
                    self.clientidlist.append(item['id'])
                    self.clientsQ.append(ClientQ)
                # self.clientsQ.append(item['Q'])
        # print(len(self.clientsQ))
        # print(type(self.clientsQ))
        if removelist:
            self.logger.warning(f'remove client {removelist} ')
            for cid in removelist:
                self.removeIDinClientsInfo(cid)
        
        self.logger.debug(f'send message to {len(self.clientsQ)} client : ')
        for Q,cid in zip(self.clientsQ,self.clientidlist):
            # pass
            try:
                # message = message + ()
                Q.put(message)
                if message[0] == 'updatePar':
                    self.logger.debug(f'send message {message }to ID {cid} client')
                else:
                    self.logger.warning(f'send message {message }to ID {cid} client')
            except EOFError:
                removelist.append(cid)
                self.logger.warning(f'sending Queue has EOFError,id = {cid}')
            except BrokenPipeError:
                removelist.append(cid)
                self.logger.warning(f'sending Queue has BrokenPipeErrorid = {cid}')
            except:
                removelist.append(cid)
                self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
        if removelist:
            self.logger.warning(f'remove client {removelist} ')
            for cid in removelist:
                self.removeIDinClientsInfo(cid)
                
                pass
    def removeIDinClientsInfo(self,cid):
        self.logger.warning(f'try to remove clinet id :{cid}')
        try:
            removeitem = next(item for item in  self.clientsinfo if item["id"] == cid)
        except:
            self.logger.warning(f'Unable find id :{cid} in {self.clientsinfo}')
            removeitem = ''
        # print(removeitem)
        if removeitem:
            self.logger.debug(f'remove client {removeitem} in {self.clientsinfo}')
            self.clientsinfo.remove(removeitem)
        else:
            self.logger.debug(f'removeIDinClientsInfo is requested,but no action due to not find match cid')
            pass
            
            
    def RasterInfo_to_meshbest(self,rasterpar):
         # self.logger.info(f'DEBUG from GUI box = {rasterpar["View1"]["box"]}')
         View1_data =  rasterpar['View1']
         View2_data =  rasterpar['View2']
         # View1_data = copy.deepcopy(self.Par['View1'])
         # View2_data = copy.deepcopy(self.Par['View2'])
         # # self.logger.info(f'View1_data = {View1_data}')
         # # self.logger.info(f'View2_data = {View2_data}')
         # for name in self.convertlist:
         #     self.logger.info(f'update for = {name}')
         #     View1_data[name] = rasterpar['View1'][name]
         #     View2_data[name] = rasterpar['View2'][name]
         # View1_data['box'] = rasterpar['View1']['box']
         # View2_data['box'] = rasterpar['View2']['box']
         
         #No not update scoreArray,resArray,spotsArray,Dable,Ztable
         scoreArray_1 = copy.deepcopy(self.Par['View1']['spotsArray'])
         resArray_1 = copy.deepcopy(self.Par['View1']['resArray'])
         scoreArray_1 = copy.deepcopy(self.Par['View1']['scoreArray'])
         Dtable_1 = copy.deepcopy(self.Par['View1']['Dtable'])
         Ztable_1 = copy.deepcopy(self.Par['View1']['Ztable'])
         
         scoreArray_2 = copy.deepcopy(self.Par['View2']['spotsArray'])
         resArray_2 = copy.deepcopy(self.Par['View2']['resArray'])
         scoreArray_2 = copy.deepcopy(self.Par['View2']['scoreArray'])
         Dtable_2 = copy.deepcopy(self.Par['View2']['Dtable'])
         Ztable_2 = copy.deepcopy(self.Par['View2']['Ztable'])
         
         View1_data['spotsArray'] = scoreArray_1
         View1_data['resArray'] = resArray_1
         View1_data['scoreArray'] = scoreArray_1
         View1_data['Dtable'] = Dtable_1
         View1_data['Ztable'] = Ztable_1
         
         View2_data['spotsArray'] = scoreArray_2
         View2_data['resArray'] = resArray_2
         View2_data['scoreArray'] = scoreArray_2
         View2_data['Dtable'] = Dtable_2
         View2_data['Ztable'] = Ztable_2
         
         #update rest thing
         self.Par['View1'] = View1_data
         self.Par['View2'] = View2_data
         self.Par['UI_par'] = rasterpar['UI_par']
         self.logger.debug(f'after update par from Client: {self.Par}')
         return 
    
    def Monitor(self,ServerQ,ZMQQ):       
        self.logger.info(f'Start Monitor')
        while True:
            #check command
            try:
                command = ServerQ.get(block=True)
                self.logger.info(f'Get Q: {command}')
                if isinstance(command,str):
                    # self.logger.info(f'command is srt')
                    if command == "exit" :
                        # ServerQ.close()
                        # sys.exit()
                        break
                elif isinstance(command,tuple) :
                     # self.logger.info(f'command is tuple')
                     if command[0] == "regID" :
                         self.logger.info(f'New client ask for register: {command[1]}')
                         self.addManagerClient(command[1])
                         pass
                     elif command[0] == "armview":
                         # 'armview',[runIndex,filename,directory,userName,axisName,exposureTime,oscillationStart,detosc,TotalFrames,distance,wavelength,detectoroffX,detectoroffY,sessionId,fileindex,unknow,beamsize,atten,roi,numofX,numofY]]
                         self.logger.info(f'Got Arm Veiw 1: {command[1]}')
                         #sholud clear old data and has new array for resArray/spotsArray/scoreArray
                         if command[1][1] == "RasterScanview1":
                             view='View1'
                         else:
                             view='View2'
                         numofXbox = int(command[1][19])
                         numofYbox = int(command[1][20])
                         self.logger.debug(f'got armview numofXbox={numofXbox},numofYbox={numofYbox}')
                         self.initScoreArray(numofXbox,numofYbox,view)
                         ZMQQ.put(command)
                     elif command[0] == "Update_par":
                         
                         self.logger.debug(f'Update_par form client:{command[1]}')
                         self.RasterInfo_to_meshbest(command[1])
                         par = copy.deepcopy(self.Par)
                         self.sendtoAllClient(('updatePar',par))
                     elif command[0] == "Direct_Update_par":
                         
                         self.logger.info(f'Direct_Update_par')
                         par = copy.deepcopy(self.Par)
                         self.sendtoAllClient(('updatePar',par))
                             
                     
                     elif command[0] == "notify_ui_update":
                         self.sendtoAllClient(command)
                         
                     elif command[0] == "sendtoClient":
                         temp = list(command)
                         temp.pop(0)
                         self.sendtoAllClient(tuple(temp))
                     elif command[0] == "dozor":
                         # ('dozor',dozorresult)
                         self.sendtoAllClient(command)
                         #update myself info?
                         if command[1]['view'] == 1:
                             view = 'View1'
                         else:
                             view = 'View2'
                         frame = int(command[1]['frame']) + 1
                         numofX = self.Par[view]['numofX']
                         numofY = self.Par[view]['numofY']
                         temp = copy.deepcopy(self.Par[view])
                         x,y=self.convertFrametoXY(frame,numofX,numofY)#frame start from 0 
                         temp['scoreArray'][x][y] = float(command[1]['score'])
                         temp['resArray'][x][y] = float(command[1]['res'])
                         temp['spotsArray'][x][y] = float(command[1]['spots'])
                         self.Par[view] = temp
                         self.logger.debug(f'after update index ={frame} x={x} y ={y}, pararray = {self.Par[view]["scoreArray"]}')
                     elif command[0] == "EndOfSeries":
                         # All job done
                         # self.sendtoAllClient(tuple(temp))
                         pass
                else:
                    pass
            except Exception as e:
                self.logger.warning(f'Error : {e}')
    def ZMQ_monitor(self,ZMQQ,ServerQ,meshbestjobQ,job_queue):
         os.nice(-19)#high priority
         fw = stream2cbf.Stream2Cbf("temp", "/home/meshbesttemp")
         fw.register_observer(self)
         # folder = fw.path
         self.logger.info(f'CBF file will write to  {fw.path} with filename {fw.basename}')
         stream = ZMQStream(self.eigerhost,  self.eigerzmqport)
         while True:
            frames = stream.receive() # get ZMQ frames
            if frames: # decode frames using the filewriter
                   fw.decodeFrames(frames,ServerQ,meshbestjobQ,job_queue)
                
            try:
                command = ZMQQ.get(block=False)
                if isinstance(command,str):
                    self.logger.info(f'command is srt')
                    if command == "exit" :
                        self.logger.critical(f'close ZMQ stream')
                        stream.close()
                        # ZMQQ.close()
                        # sys.exit()
                        break
                elif isinstance(command,tuple) :
                     self.logger.info(f'command is tuple')
                     if command[0] == "armview" :
                         # [17, 'RasterScanViwe1', '/data/blctl/20210727_07A/', 'blctl', 'gonio_phi', 0.1, 119.999802, 0.0, 15, 625.99884, 7.874044121870488e-05, 0.0, -0.997409, 'no', 0, 1, 50.0, 0.0, 1, 3, 5]
                         # [runIndex,filename,directory,userName,axisName,exposureTime,oscillationStart,detosc,TotalFrames,distance,wavelength,detectoroffX,detectoroffY,sessionId,fileindex,unknow,beamsize,atten,roi,numofX,numofY]
                         self.logger.info(f'update filename to {command[1][1]}')
                         fw.basename = command[1][1]
                         self.logger.info(f'CBF file will write to  {fw.path} with filename {fw.basename}')
                         #reload dozor par
                         import DozorPar
                         fw.dozor_par=DozorPar.DozorPar
                         pass
                else:
                    pass
            except:
                pass

    def notify(self, observable, *args, **kwargs):          
        
        if args[0] == "EndOfSeries":
            self.logger.info(f'Frame {args[1]} is done!')
            self.ServerQ.put(('sendtoClient','imagewrited',args[1],args[2]))
        elif args[0] == "newthread":
            self.logger.info(f'newthread start {args[1]}')
            pass
        else:
            pass
        
        
    def meshbetjob(self,ServerQ,meshbestjobQ):       
        self.logger.info(f'Start meshbetjob Monitor')
        while True:
            #check command
            try:
                command = meshbestjobQ.get(block=True)
                # self.logger.info(f'Get Q: {command}')
                if isinstance(command,str):
                    # self.logger.info(f'command is srt')
                    if command == "exit" :
                        # ServerQ.close()
                        # sys.exit()
                        break
                elif isinstance(command,tuple) :
                     # self.logger.info(f'command is tuple')
                     if command[0] == "regID" :
                         pass
                     elif command[0] == "BeginOfSeries":
                         if command[1] == 101:
                             self.logger.debug(f'view1 header get')
                             self.logger.info(f'Clear temp data for view1')
                             self.meshPositionsdata_1 =[]
                             self.checkingViwe1 = True
                         elif command[1] == 102:
                             self.logger.debug(f'view2 header get')
                             self.meshPositionsdata_2 =[]
                             self.logger.info(f'Clear temp data for view2')
                             self.checkingViwe2 = True
                         else:
                             self.logger.debug(f'normal data collect')
                         # self.meshPositionsdata = []
                         pass
                     elif command[0] == "updateDozor":   
                         # meshbestjobQ.put(('updateDozor',dozorresult,datastr))
                         # dozorresult is  dict have ,view,frame,totalTime,File,spots,score,res
                         # datastr is str encode by b64,has spot pos info
                         
                         dozorresult = command[1]
                         datastr = command[2]
                         index = int(dozorresult['frame'])
                         numofX = int(dozorresult['numofX'])
                         numofY = int(dozorresult['numofY'])
                         signleframedata = {}
                         signleframedata['index'] = index
                         X,Y = self.convertFrametoXY(index+1,numofX,numofY)
                         signleframedata['indexZ'] = Y #ver
                         signleframedata['indexY'] = X #hor
                         signleframedata['omega'] = dozorresult['omega']
                         signleframedata['dozor_score'] = dozorresult['score']
                         signleframedata['Filename'] =  dozorresult['File']
                         signleframedata['dozorSpotList'] = datastr

                         if dozorresult['view']==1:
                             self.meshPositionsdata_1.append(signleframedata)
                         else:
                             self.meshPositionsdata_2.append(signleframedata)
                         
                         self.logger.debug(f'update view:{dozorresult["view"]} frame:{index}')
                     elif command[0] == "EndOfSeries":
                         # All job done
                         # self.sendtoAllClient(tuple(temp))
                         self.logger.info(f'Raster collect done! wait all result and perpare meshbest')
                         header = command[1]
                         
                         
                         
                         # url = 'http://10.7.1.107:8082/job'
                        
                         # headers = {"Content-Type": "application/json"}
                         # alldata ={}
                         # alldata['data'] = jsondata
                         self.logger.debug(f'collect done for {header["appendix"]["runIndex"]}')
                         if int(header['appendix']['runIndex']) == 101:
                             sid = 101#view1
                         else:
                             sid = 102#view2
                        
                         # response = requests.post(self.meshbesturl , json=alldata) 
                         meshbestjobQ.put(('check_data',sid,header))
                         pass
                     elif command[0] == "check_data":
                         sid = command[1]
                         header = command[2]
                         if command[1] == 101:
                             checkingViwe = self.checkingViwe1
                             meshPositionsdata = self.meshPositionsdata_1
                             
                         else:
                             checkingViwe = self.checkingViwe2
                             meshPositionsdata = self.meshPositionsdata_2
                             
                         currentnum = len(meshPositionsdata)
                         
                         exceptNum = int(header['appendix']['raster_X']) * int(header['appendix']['raster_Y'])
                         if currentnum == exceptNum:
                             self.logger.info(f'job done! we got {currentnum} data')
                             
                             meshbestjobQ.put(('startjob',sid,header))
                             
                         else:
                             # time.sleep(0.02)
                             meshbestjobQ.put(('check_data',sid,header))
                             if command[1] == 101:
                                 if self.numofdataView1 != currentnum:
                                     a=[]
                                     for i in self.meshPositionsdata_1:
                                         a.append(i['index'])
                                     b = [x for x in range(exceptNum)]
                                     miss = set(a) ^ set(b)
                                     self.logger.info(f'SID ={sid} we got {currentnum} data,except {exceptNum}, we miss {miss}')
                                 self.numofdataView1 = currentnum
                             else:
                                 if self.numofdataView2 != currentnum:
                                     a=[]
                                     for i in self.meshPositionsdata_2:
                                         a.append(i['index'])
                                     b = [x for x in range(exceptNum)]
                                     miss = set(a) ^ set(b)
                                     self.logger.info(f'SID ={sid} we got {currentnum} data,except {exceptNum}, we miss {miss}')
                                 self.numofdataView2 = currentnum
                     elif command[0] == "startjob":
                         self.logger.info(f'startjob {sid}')
                         sid = command[1]
                         header = command[2]
                         if sid == 101:
                             checkingViwe = self.checkingViwe1
                             meshPositionsdata = self.meshPositionsdata_1
                             self.logger.info(f'set to view1')
                             path='/tmp/meshbest/viwe_1.json'
                         else:
                             checkingViwe = self.checkingViwe2
                             meshPositionsdata = self.meshPositionsdata_2
                             self.logger.info(f'set to view2')
                             path='/tmp/meshbest/viwe_2.json'
                             
                         jsondata = self.PreparejasonData(header,meshPositionsdata)
                         
                         self.logger.info(f'got jsondata try to write to {path}')
                
                         
                         # txt = json.dumps(alldata)
                         # self.logger.info(f'jsondata = {jsondata}')
                         with open(path, 'w') as outfile:
                             json.dump(jsondata, outfile, sort_keys=True, indent=4, ensure_ascii=False)
                         
                         self.logger.info(f'write to flie {path}')
                         
                         
                         alldata ={}
                         alldata['data'] = jsondata
                         alldata['sessionid'] = sid
                         self.logger.info(f'startjob to {self.meshbesturl},by data{alldata["data"]["beamlineInfo"]}')
                         response = requests.post(self.meshbesturl , json=alldata) 
                         # headers = {"Content-Type": "application/json"}
                         # url = 'http://10.7.1.107:8082/job'
                         self.logger.info(f'send job id {sid},response= {response.content}')
                         #Check for job become start
                         time.sleep(0.5)
                         # self.wait_job_state(sid,self.meshbesturl,"Start")
                         meshbestjobQ.put(('check_jsondata',sid))
                         
                     elif command[0] == "check_jsondata":
                        # self.logger.info(f'check_jsondata sid = {command[1]}')
                        sid = command[1]
                        response = requests.get(self.meshbesturl)
                        ans = response.json()
                        # print(len(ans))
                        # print(ans)
                        
                        for item in ans:
                            # a = json.loads(item)
                            # print(a)
                            if ans[item]['sessionid'] == sid:
                                my_sid_ans = ans[item]
                        # self.logger.info(f'my sid and = {my_sid_ans}')
                        if my_sid_ans['State'] == 'End':
                            self.logger.info(f'Get data for sid {sid} ')
                            # Dtable,Ztable,BestPositions = convert_data(my_sid_ans['data'],self.logger)
                            
                            if sid == 101:
                                Par = copy.deepcopy(self.Par['View1'])
                                # self.logger.info(f'debug:{my_sid_ans["data"]["MeshBest"]}')
                                Par['GridX'] = int(my_sid_ans['data']['grid_info']['steps_x'])
                                Par['GridY'] = int(my_sid_ans['data']['grid_info']['steps_y'])
                                Par['Dtable'] = my_sid_ans['data']['MeshBest']['Dtable']
                                Par['Ztable'] = my_sid_ans['data']['MeshBest']['Ztable']
                                Par['BestPositions'] = my_sid_ans['data']['MeshBest']['BestPositions']
                                self.Par['View1'] = Par
                                
                            else:
                                Par = copy.deepcopy(self.Par['View2'])
                                Par['GridX'] = int(my_sid_ans['data']['grid_info']['steps_x'])
                                Par['GridY'] = int(my_sid_ans['data']['grid_info']['steps_y'])
                                Par['Dtable'] =  my_sid_ans['data']['MeshBest']['Dtable']
                                Par['Ztable'] = my_sid_ans['data']['MeshBest']['Ztable']
                                Par['BestPositions'] = my_sid_ans['data']['MeshBest']['BestPositions']
                                self.Par['View2'] = Par
                            
                            self.logger.info(f'Gready to updatepar self.Par=  {self.Par} ')
                            # self.logger.info(f'Dtable={Dtable},Ztable={Ztable},BestPositions={BestPositions}')    
                            ServerQ.put(('Direct_Update_par','meshbetjob',sid))
                            ServerQ.put(('notify_ui_update','meshbetjob',sid))
                        elif my_sid_ans['State'] == 'Fail':
                            pass
                        else:
                            time.sleep(0.05)
                            meshbestjobQ.put(('check_jsondata',sid))
                     elif command[0] == "check_state":
                         response = requests.get(self.meshbesturl) 
                         ans = response.json()
                         
                         if ans['state'] == 'Start':
                             pass
                             # meshbestjobQ.put(('check_state',alldata['sessionid']))
                else:
                    pass
            except:
                pass
        
    def wait_job_state(self,sid,url,TargetState="Start",timeout=60):
        t0=time.time()
        check = True
        while check:
            response = requests.get(url)
            ans = response.json()
            for item in ans:
                # a = json.loads(item)
                # print(a)
                if ans[item]['sessionid'] == sid:
                    my_sid_ans = ans[item]
            if my_sid_ans['State'] == TargetState:
                self.logger.debug(f'sid = {sid},Job state = {TargetState} Check Done,url={url},take time={time.time()-t0}')
                check = False
            else:
                pass
            if time.time() - t0 > timeout:
                self.logger.debug(f'Leave check job state due to timeout ={time.time() - t0}')
                check = False
        self.logger.debug(f'wait_job_state Done!')
        
    def PreparejasonData(self,header,meshPositionsdata):
        # jsondata = {}
        # jsondata['beamlineInfo'] = {}
        # jsondata['beamlineInfo']['beamlineApertures'] = [50, 30, 20, 10, 5]
        jsondata = self.defaultinput()
        self.logger.info(f'current json data = {jsondata}')
        jsondata['grid_info']['steps_x'] = int(header['appendix']['raster_X'])
        
        jsondata['grid_info']['steps_y'] = int(header['appendix']['raster_Y'])
        
        jsondata['inputDozor']['detectorDistance'] = float(header['detector_distance'])*1000
        
        jsondata['beamlineInfo']['detectorPixelSize'] = float(header['x_pixel_size'])*1000
        jsondata['inputDozor']['wavelength'] = float(header['wavelength'])
        jsondata['inputDozor']['orgx'] = float(header['beam_center_x'])
        jsondata['inputDozor']['orgy'] = float(header['beam_center_y'])
        
        jsondata['grid_info']['beam_width'] = float(header['appendix']['beamsize'])/1000
        jsondata['grid_info']['beam_height']= float(header['appendix']['beamsize'])/1000
        self.logger.info(f'json data before meshPositions = {jsondata}')
        jsondata['meshPositions'] = meshPositionsdata
        self.logger.info(f'done for PreparejasonData ')
        return jsondata
         # header
         # {"auto_summation": true,
         #  "beam_center_x": 1034.0,
         #  "beam_center_y": 1081.0,
         #  "bit_depth_image": 16,
         #  "bit_depth_readout": 16,
         #  "chi_increment": 0.0,
         #  "chi_start": 0.0, 
         #  "compression": "bslz4", 
         #  "count_time": 0.0099999,
         #  "countrate_correction_applied": true,
         #  "countrate_correction_count_cutoff": 115122,
         #  "data_collection_date": "2021-08-10T16:25:34.236+08:00", 
         #  "description": "Dectris EIGER2 Si 16M",
         #  "detector_distance": 0.1500011,
         #  "detector_number": "E-32-0122",
         #  "detector_readout_time": 1e-07,
         #  "detector_translation": [0.0, 0.0, -0.1500011],
         #  "eiger_fw_version": "release-2020.2.1",
         #  "element": "",
         #  "flatfield_correction_applied": true,
         #  "frame_count_time": 36400.0,
         #  "frame_period": 36400.0,
         #  "frame_time": 0.01,
         #  "kappa_increment": 0.0, 
         #  "kappa_start": 0.0,
         #  "nimages": 16, 
         #  "ntrigger": 14,
         #  "omega_increment": 0.0,
         #  "omega_start": 101.285893, 
         #  "phi_increment": 0.0, 
         #  "phi_start": 0.0,
         #  "photon_energy": 12700.094887059258,
         #  "pixel_mask_applied": true,
         #  "roi_mode": "4M", 
         #  "sensor_material": "Si",
         #  "sensor_thickness": 0.00045,
         #  "software_version": "1.8.0", 
         #  "trigger_mode": "exts", 
         #  "two_theta_increment": 0.0,
         #  "two_theta_start": 0.0, 
         #  "virtual_pixel_correction_applied": true, 
         #  "wavelength": 0.9762462370224789,
         #  "x_pixel_size": 7.5e-05,
         #  "x_pixels_in_detector": 2068,
         #  "y_pixel_size": 7.5e-05,
         #  "y_pixels_in_detector": 2162,
         #  "appendix": {"user": "blctl", 
         #               "directory": "/data/blctl/20210810_07A/",
         #               "runIndex": "100", 
         #               "beamsize": "50.0", 
         #               "atten": "0.0",
         #               "fileindex": 0,
         #               "filename": "RasterScanViwe1_0000", 
         #               "uid": 1000, 
         #               "gid": 1001, 
         #               "raster_X": 14, 
         #               "raster_Y": 16}}

    def convertFrametoXY(self,number,numofX,numofY):
        #1 = right left conor
        
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
    
    def defaultinput(self):
       self.logger.info(f'got defaultinput')
       ans ={
            	"grid_info": 
            		{
            			"steps_x":25,
            			"steps_y":1,
            			"beam_width":0.03,
            			"beam_height":0.03
            		},
            
            	"inputDozor":
            		{
            			"detectorDistance":150,
            			"wavelength":0.998,
            			"orgx":1440,
            			"orgy":1920
            		},
            	"beamlineInfo":
            		{
            			"detectorPixelSize":0.0783,
            			        "beamlineApertures": [
                        			   50,
                        			   30,
              		                   10,
                                        5
            			         ]
            		},
            
                    "MeshBest":
                            {
                                    "difminpar":0.02,
                                    "Ztable":"",
                                    "Dtable":"",
                                    "positionReference":""
                            }
            }

       self.logger.info(f'got defaultinput {ans}')
       return ans

    def initScoreArray(self,numofXbox,numofYbox,view='View1'):
        # numofXbox = self.Par[view]['numofX']
        # numofYbox = self.Par[view]['numofY']
        temp = copy.deepcopy(self.Par[view])
        temp['numofX'] = numofXbox
        temp['numofY'] = numofYbox
        temp['Textplotarray']=[[0]*numofYbox for i in range(numofXbox)]
        temp['scoreArray'] = numpy.zeros((numofXbox, numofYbox))
        temp['scoreArray'][:] = numpy.nan
        temp['resArray']=numpy.zeros((numofXbox, numofYbox))
        temp['resArray'][:]=50#set all value to 50
        temp['spotsArray']=numpy.zeros((numofXbox, numofYbox))
        temp['spotsArray'][:] = numpy.nan
        self.Par[view] = temp
        self.logger.debug(f' init array {numofXbox},{numofYbox}')
        self.logger.debug(f'After init should :{view}={temp}')
    def quit(self,signum,frame):
        self.logger.critical(f'Start Quit Meshbest Server PID:{os.getpid()}')
        try:
            self.ServerQ.put("exit")
            # self.clientsQ.put("exit")
            self.ZMQQ.put("exit")
            self.meshbestjobQ.put('exit')
            self.processQ.close()
        except:
            pass
        self.logger.critical(f'Quit Meshbest Server PID:{os.getpid()}')
        sys.exit()
   
                         
def quit(signum,frame):
    print("Main cloesd")
    # sys.exit()
    pass       
        
if __name__ == "__main__":
    # signal.signal(signal.SIGINT, quit)
    # signal.signal(signal.SIGTERM, quit)
    # logger=logsetup.getloger2('MestbestServer')
    
    m=MestbestSever()
    m.start()
    