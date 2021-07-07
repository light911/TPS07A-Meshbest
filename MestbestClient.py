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

class QueueManager(BaseManager): pass

class MestbestClient():
    def __init__(self,par):
        self.localIP='10.7.1.4'
        self.localPort = self.get_free_port(self.localIP)
        self.Par =par
        self.logger = logsetup.getloger2('MestbestClient',level = self.Par['Debuglevel'])
        self.ServerQIP = '10.7.1.4'
        self.ServerQPort = 6534
        
        self.ClientQ = Queue()
        self.ClientID = -1
        pass
    
    def start(self):
        p1 = Process(target=self.ManagerServer,args=(self.localPort,))
        p1.start()
        #start monitor
        p2 = Process(target=self.Monitor,args=(self.ClientQ,))
        p2.start()
        
        self.ManagerClient(self.ServerQIP,port=self.ServerQPort)
        
    def Monitor(self,ClientQ):       
        self.logger.info(f'Start Monitor:{ClientQ}')
        while True:
            #check command
            try:
                command = ClientQ.get(block=True,timeout=1)
                self.logger.info(f'Get Q: {command}')
                if isinstance(command,str):
                    
                    if command == "exit" :
                        sys.exit()
                        break
                elif isinstance(command,tuple) :
                     if command[0] == "YourID" :
                         self.ClientID = command[1]
                         self.logger.info(f'Assigned ID : {command[1]}')
                         pass
                     elif command[0] == "Test":
                         self.logger.info(f'message : {command}')
                else:
                    pass
            except Empty:
                # self.logger.warning(f'here')
                pass
            except:
                traceback.print_exc()
                self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
                pass
        
    def ManagerClient(self,ip,port=6544):
        try:
            QueueManager.register('ServerQ')
            m = QueueManager(address=(ip,port), authkey=b'tps07a')
            m.connect()
            self.ServerQ = m.ServerQ()

        except ConnectionRefusedError:
            self.logger.warning(f'Mesgbest Server ConnectionRefused,try 1sec later')
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
        self.logger.info(f'Start Queue Manager server:{s}')
        s.serve_forever()
    
    def get_free_port(self,host='127.0.0.1'):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, 0))
        port = sock.getsockname()[1]
        sock.close()
        return port 
   
def quit(signum,frame):
    print("Client cloesd")
    sys.exit()
    pass          
    
if __name__ == "__main__":
    signal.signal(signal.SIGINT, quit)
    signal.signal(signal.SIGTERM, quit)
    par={}
    par['Debuglevel'] = "DEBUG"
    m = MestbestClient(par)
    m.start()