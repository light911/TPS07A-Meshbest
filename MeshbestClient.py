#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  6 15:31:18 2021

@author: blctl
"""

import logsetup
import time,signal,sys,os,socket
from multiprocessing.managers import BaseManager
from multiprocessing import Process, Queue , Manager
import traceback
from queue import Empty
# import queue as _queue
from PyQt5.QtCore import QThread,pyqtSignal,pyqtSlot

class QueueManager(BaseManager): pass

class MestbestClient(QThread):
    Mestbestemessage =  pyqtSignal(tuple)
    def __init__(self,LOG_FILENAME='./log/log.txt'):
        super(MestbestClient,self).__init__()
        signal.signal(signal.SIGINT, self.quit)
        signal.signal(signal.SIGTERM, self.quit)
        self.m = Manager()
        
        self.localIP='10.7.1.2'
        self.localPort = self.get_free_port(self.localIP)
        self.Par = self.m.dict()
        par = {}
        par['Debuglevel'] = "INFO"
        self.Par.update(par)
        self.logger = logsetup.getloger2('MestbestClient',LOG_FILENAME,level = self.Par['Debuglevel'])
        self.ServerQIP = '10.7.1.107'
        self.ServerQPort = 6534
        
        self.ClientQ = Queue()
        self.MainQ = Queue()
        self.ClientID = -1
        pass
    def run(self):
        self.start2()
    def start2(self):
        #This start a process to send command to server
        p1 = Process(name='meshbestclient_ManagerServer',target=self.ManagerServer,args=(self.localPort,))
        p1.start()
        
        #start monitor
        #this recvice the data from Server
        p2 = Process(name='meshbestclient_Monitor',target=self.Monitor,args=(self.ClientQ,self.MainQ,))
        p2.start()
        
        self.ManagerClient(self.ServerQIP,port=self.ServerQPort)
        self.MonitorPID = p1.pid
        self.logger.info(f'ManagerServer PID ={p1.pid}')
        self.logger.info(f'Monitor       PID ={p2.pid}')
        while True:
            try:
                command = self.MainQ.get(block=True)
                if isinstance(command,str):
                    if command == "exit" :
                        break
                elif isinstance(command,list) :
                    #send to GUI
                    self.Mestbestemessage.emit(tuple(command))
                elif isinstance(command,tuple) :
                    #send to GUI
                    self.Mestbestemessage.emit(command)
                else:
                    pass
            except:
                pass
        
        
        # p1.join()
        p2.join()
        self.logger.critical(f'Exit ManagerClient Main Thread')

    def sendCommandToMeshbest(self,command):
        self.ServerQ.put(command)
        
    def Monitor(self,ClientQ,MainQ):       
        self.logger.info(f'Start Monitor:{ClientQ}')
        #ClientQ message from server
        #MainQ is this client send message to GUI(by EMIT)
        while True:
            #check command
            try:
                command = ClientQ.get(block=True,timeout=1)
                
                if isinstance(command,str):
                    
                    if command == "exit" :
                        # sys.exit()
                        break
                elif isinstance(command,tuple) :
                    #get command from GUI and send it to server?                    
                    MainQ.put(command)
                    self.logger.debug(f'Get Q: {command[0]}')
                    if command[0] == "YourID" and self.ClientID == -1:
                        self.ClientID = command[1]
                        self.logger.info(f'Assigned ID : {command[1]}')
                        pass
                    elif command[0] == "Test":
                        self.logger.info(f'message : {command}')
                    elif command[0] == "updatePar":
                        # self.logger.debug(f'before update Par : {self.Par}')
                        # self.logger.debug(f'command : {command[1]},{type(command[1])}')
                        self.Par.update(command[1])
                        # self.logger.debug(f'after update Par : {self.Par}')
                else:
                    self.logger.debug(f'got unknow command {command}')
                    pass
            except Empty:
                # self.logger.warning(f'here')
                pass
            except:
                traceback.print_exc()
                self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
                pass
        
    def ManagerClient(self,ip,port=6534):
        try:
            print(ip)
            QueueManager.register('ServerQ')
            m = QueueManager(address=(ip,port), authkey=b'tps07a')
            m.connect()
            self.ServerQ = m.ServerQ()

        except ConnectionRefusedError:
            self.logger.warning(f'Meshbest Server ConnectionRefused,try 1sec later')
            time.sleep(1)
            self.ManagerClient(self.ServerQIP,port=self.ServerQPort)
        else:
            self.ServerQ.put('hello')
            test = {}
            test['abc'] = 'cdef'
            test['jgh'] = 1
            test['list'] = [1,23,45,6]
            self.ServerQ.put(test)
            # mm = Manager()
            # q = mm.Queue()
            clientinfo={}
            clientinfo['ip'] = self.localIP
            clientinfo['port'] = self.localPort
            self.ServerQ.put(('regID',clientinfo))    
        
        
    
    def ManagerServer(self,port=6544):
        QueueManager.register('ClientQ', callable=lambda:self.ClientQ)
        m = QueueManager(address=('', port), authkey=b'tps07a')
        s = m.get_server()
        
        self.logger.info(f'Start Queue Manager server at port :{port}')
        # self.logger.info(f'Start Queue Manager server PID at {m._process.ident}')
        s.serve_forever()
    
    def get_free_port(self,host='127.0.0.1'):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, 0))
        port = sock.getsockname()[1]
        sock.close()
        time.sleep(0.1)
        return port 
    def quit(self,signum,frame):
        self.logger.critical(f'Quit Meshbest Client')
        self.closedmeshbest = True
        self.MainQ.put("exit")
        self.ClientQ.put("exit")
        self.logger.critical(f'meshbest client m pid={self.m._process.ident}')
        
        
        try:
            self.logger.info(f'try to kill MonitorPID = {self.MonitorPID}')
            os.kill(self.MonitorPID,signal.SIGKILL)
        except:
            pass
        # time.sleep(1)
        self.m.shutdown()
        # sys.exit()
def quit(signum,frame):
    print("Client cloesd")
    sys.exit()
    pass          
    
if __name__ == "__main__":
    signal.signal(signal.SIGINT, quit)
    signal.signal(signal.SIGTERM, quit)
    # par={}
    # par['Debuglevel'] = "DEBUG"
    m = MestbestClient()
    m.start2()