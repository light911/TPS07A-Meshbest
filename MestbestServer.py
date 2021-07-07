# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import logsetup
import time,signal,sys,os
from multiprocessing.managers import BaseManager
from multiprocessing import Process, Queue , Manager
from multiprocessing.managers import BaseProxy
from multiprocessing import process


#https://stackoverflow.com/questions/29788809/python-how-to-pass-an-autoproxy-object


class QueueManager(BaseManager): pass

class MestbestSever():
    def __init__(self,Par):
        self.Par = Par
        self.MangerPort = 6534
        self.logger = logsetup.getloger2('MestbestServer',level = self.Par['Debuglevel'])
        self.ServerQ = Queue()
        m = Manager()
        self.clientsinfo = m.list()
        self.clientsQ = []
        self.clientidlist = []
        # self.clientsQ = []
        
        self.clientid = 1
        # print(type(self.clientsQ))
        pass
    def start(self):
        #start ManagerServer
        p1 = Process(target=self.ManagerServer,args=(self.MangerPort,))
        p1.start()
        #start monitor
        p2 = Process(target=self.Monitor,args=(self.ServerQ,))
        p2.start()
        
        p3 = Process(target=self.test,args=())
        p3.start()
        p3.join()
        
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
        # print(f'reportID {self.clientid}')
        
        # d = self.clientsQ[0]
        
        data = {}
        data['info'] = message
        data['id'] =  self.clientid
        self.clientid =  self.clientid+1
        # print(data,type(self.clientsQ),self.clientsQ)
        # templlist = []
        # templlist.append(data)
        # print(f'templist={templlist}')
        self.clientsinfo.append(data)
        self.logger.info(f'Add new client,id = {data["id"]}')

        # print(f'END---Type {type(self.clientsinfo)},Len {len(self.clientsinfo)}')
        
    def sendtoAllClient(self,message):
        if len(self.clientsQ) != len(self.clientsinfo):
            self.clientsQ = []
            self.clientidlist = []
            # print(self.clientsQ,self.clientsinfo)
            for item in self.clientsinfo:
                ip = item['info']['ip']
                port = item['info']['port']
        
                QueueManager.register('ClientQ')
                mm = QueueManager(address=(ip,port), authkey=b'tps07a')
                mm.connect()
                ClientQ = mm.ClientQ()
                self.clientidlist.append(item['id'])
                self.clientsQ.append(ClientQ)
        # print(len(self.clientsQ))
        # print(type(self.clientsQ))
        removelist=[]
        for Q,cid in zip(self.clientsQ,self.clientidlist):
            # pass
            try:
                # message = message + ()
                Q.put(message)
            except EOFError:
                removelist.append(cid)
                self.logger.warning(f'sending Queue has EOFError,id = {cid}')
            except BrokenPipeError:
                removelist.append(cid)
                self.logger.warning(f'sending Queue has BrokenPipeErrorid = {cid}')
            except:
                self.logger.warning(f'Unexpected error:{sys.exc_info()[0]}')
        if removelist:
            for cid in removelist:
                self.removeIDinClientsInfo(cid)
                
                pass
    def removeIDinClientsInfo(self,cid):
        try:
            removeitem = next(item for item in  self.clientsinfo if item["id"] == cid)
        except:
            self.logger.warning(f'Unable find id :{cid} in {self.clientsinfo}')
            removeitem = ''
        # print(removeitem)
        if removeitem:
            self.logger.debug(f'remove find {removeitem} in {self.clientsinfo}')
            self.clientsinfo.remove(removeitem)
        else:
            self.logger.debug(f'removeIDinClientsInfo is requested,but no action due to not find match cid')
            pass
            
            
        
    def Monitor(self,ServerQ):       
        self.logger.info(f'Start Monitor')
        while True:
            #check command
            try:
                command = ServerQ.get(block=True)
                self.logger.info(f'Get Q: {command}')
                if isinstance(command,str):
                    
                    if command == "exit" :
                        sys.exit()
                        break
                elif isinstance(command,tuple) :
                     if command[0] == "regID" :
                         self.logger.info(f'New client ask for register: {command[1]}')
                         self.addManagerClient(command[1])
                         pass
                else:
                    pass
            except:
                pass
    
        
def quit(signum,frame):
    print("Main cloesd")
    sys.exit()
    pass       
        
if __name__ == "__main__":
    signal.signal(signal.SIGINT, quit)
    signal.signal(signal.SIGTERM, quit)
    # logger=logsetup.getloger2('MestbestServer')
    par={}
    par['Debuglevel'] = "DEBUG"
    m=MestbestSever(par)
    m.start()
    