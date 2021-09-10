#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  2 09:20:47 2019

@author: blctl
"""

import sys,signal,time,os,traceback
import socket
#import threading
import multiprocessing as mp
from multiprocessing import Process, Queue, Manager
from multiprocessing.managers import BaseManager
# from MeshBest.dozor import convtocbfandrundozor
#from MeshBest.color import formatter_message,ColoredFormatter
import logging
import logging.handlers
import coloredlogs
import shutil

logfile='TcpServer.log'
#formatter2 = '%(asctime)s -- %(thread)d - %(name)s - %(levelname)s - %(message)s'
#formatter2 = '%(asctime)s -- %(thread)d - %(funcName)s - %(levelname)s - %(message)s'
formatter2 = '%(asctime)s -- %(funcName)s - %(levelname)s - %(message)s'
#for file
logging.basicConfig(
        filename=logfile,
        filemode='w',
        level=logging.DEBUG,format=formatter2,        
        )


#logging.handlers.RotatingFileHandler(logfile,mode='a',maxBytes=10240,backupCount=10)


loglevel=logging.INFO

# create logger
logger = logging.getLogger("TCPServer")
logger.setLevel(logging.DEBUG)



ch = logging.StreamHandler()
ch.setLevel(logging.INFO)


# create formatter
formatter = logging.Formatter(formatter2)
# add formatter to ch
ch.setFormatter(formatter)
#ch.setFormatter(color_formatter)

# add ch to logger
#logger.addHandler(ch)
coloredlogs.install(fmt=formatter2,level=logging.INFO)
#coloredlogs.DEFAULT_LOG_FORMAT = formatter2

#filehandler = logging.FileHandler('test.log',mode='w')
#filehandler.setLevel(logging.DEBUG)
#filehandler.setFormatter(formatter)
#logger.addHandler(filehandler)

#filehandler = logging.handlers.RotatingFileHandler('dozor.log',mode='w',maxBytes=102400,backupCount=10)
#filehandler.setLevel(logging.DEBUG)
#filehandler.setFormatter(formatter)
#logger.addHandler(filehandler)




#logger.debug('Server Started-debug')
#logger.debug('debug message')
#logger.info('info message')
#logger.warn('warn message')
#logger.error('error message')
#logger.critical('critical message')



def serverTCP(port):
    logger.info('Server Started')
    bind_ip="10.5.1.107"
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    serversocket.bind(('0.0.0.0', port))
    serversocket.listen(100)
    logger.info("Listening on %s:%d" % (bind_ip, port))
    return serversocket

#server= socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#server.bind((bind_ip,bind_port))
#server.listen(100)
#
#print "Listening on %s:%d" % (bind_ip, bind_port)




def handle_client(client,status):
    #global loglevel,logger
    start_time=time.time()
    timeout=3
    read_buff = ""
    client.settimeout(1)
    #client_id=threading.current_thread().ident
    #header="handle_client:"+str(client_id)
    #clientlog = logging.getLogger(header)
    #clientlog.setLevel(loglevel)
    #logger = logging.getLogger("handle_client")
    pid=os.getpid()
    result={}
    
    while True:
        try:
            read_a_char = client.recv(10000).decode('utf-8')
        except socket.error as socketerror:
            logger.warn("Error: %s", socketerror)
        except socket.timeout:
            logger.warn("Socket NO RESPONSE")
            
        if time.time()-start_time > timeout:
            logger.warn("Socket didn't recive \n within %d sec",timeout)
            logger.warn("Get %s",read_a_char)
            break
        
        
        if read_a_char != '\n':
            read_buff += read_a_char
            '''
            fotmat1
            online dozor
            image path:/filespath
            
            format2
            offline dozor
            Rundozor:/folder:view
            
            offline meshbest
            RunMeshBest:/folder:view
            
            offline dozor&meshbest
            RunAll:/folder:view
            '''
        else:
            logger.debug("command= %s",read_buff)
            data = read_buff.split(":")
            if data[0]== "image path":
                #print "got! ",data[1]
                outputfolder="/tmp/ramdisk/"
                info={}
                info[0]=data[1]
                info[1]=outputfolder
                #result=dozor.convtocbfandrundozor(info)
                # result=convtocbfandrundozor(info,status)
                #logger = logging.getLogger("handle_client")
                answer= str(result['File']) + " " + str(result['spots']) + " " + str(result['score']) + " " + str(result['res'])
            
            elif data[0]== "Rundozor":
                folder = data[1]
                view = int(data[2])
                # PrepareData(folder,status,view)
                
                
                result['File']=folder
                result['totalTime']=time.time()-start_time
                
                answer = "Rundozor "+ str(result['totalTime']) + " done"
                
            elif data[0]== "RunMeshBest":
                
                folder = data[1]
                view = int(data[2])
#                outputname="data_"+str(view)+".json"
#                outputjsonFolder = folder + "/meshbest_" + str(view) + "/" 
#                outputjsonpath=outputjsonFolder + outputname
                status['monjob']=True
                # outputjsonpath,outputjsonFolder = PreparejasonData(folder,status,view)
                client.sendall(('Finish PrepareData\r\n').encode('utf-8'))
                
                # MeshBest.algorithms.meshandcollect(outputjsonpath,status,outputjsonFolder)             
                # ChangeOwninFolder(outputjsonFolder,outputjsonpath)
                status['monjob']=False
                result['File']=folder
                result['totalTime']=time.time()-start_time
                
                answer = "RunMeshBest "+ str(result['totalTime']) + " done"
                
            elif data[0]== "RunAll":
                try:
                    
                    folder = data[1]
                    view = int(data[2])
                    status['monjob']=True
                    client.sendall(('Start PrepareData\r\n').encode('utf-8'))
                    # PrepareData(folder,status,view)
                    client.sendall(('Finish PrepareData\r\n').encode('utf-8'))
                    
                    client.sendall(('Start PreparejasonData\r\n').encode('utf-8'))
                    # outputjsonpath,outputjsonFolder = PreparejasonData(folder,status,view)
                    client.sendall(('Start Meshbest\r\n').encode('utf-8'))
                    # MeshBest.algorithms.meshandcollect(outputjsonpath,status,outputjsonFolder)             
                    # ChangeOwninFolder(outputjsonFolder,outputjsonpath)
                    status['monjob']=False
                    result['File']=folder
                    result['totalTime']=time.time()-start_time
                    answer = "RunAll "+ str(result['totalTime']) + " done"
                except Exception as e:
                    answer ="Error"
                    error_class = e.__class__.__name__ #取得錯誤類型
                    detail = e.args[0] #取得詳細內容
                    cl, exc, tb = sys.exc_info() #取得Call Stack
                    lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
                    fileName = lastCallStack[0] #取得發生的檔案名稱
                    lineNum = lastCallStack[1] #取得發生的行號
                    funcName = lastCallStack[2] #取得發生的函數名稱
                    errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(fileName, lineNum, funcName, error_class, detail)
                    logger.warn("Error:%s",errMsg)
                
            else:
                logger.warn("worng format")
                logger.warn("%s",read_buff)
                
            try:
                client.sendall(('server_echo ' + answer + '\r\n').encode('utf-8'))
                logger.debug("answer=%s",answer)
                #maybe need remove?
                client.sendall(('Done\r\n').encode('utf-8'))
            except:
                logger.warn("Error on send data back")
            read_buff = ''
            client.close()
            try:     
                logger.info("Tread closed -- PID:%d File:%s, take %f sec",pid,result['File'],result['totalTime'])
            except Exception as e:
#                print result
                logger.warn("PID:%d Result:%s",pid,result)
                logger.warn("Error:%s",e)
            break
            
def quit(signum,frame):
    global server
    timestr = time.strftime("%Y%m%d_%H%M%S",time.localtime())
    timef = "_" + timestr + ".log"
    #print timef
    logfilewithtime=logfile.replace(".log",timef)
    #print logfilewithtime
    shutil.copy2(logfile,logfilewithtime)
    logger.info("try to close TCP port and end program")
    server.close()
    sys.exit()

def statusreport():
#    global status
#    
#    print status['Jobname']
#    print status['doneJob']
#    print status['totalJob']
    ans={}
    ans['monjob'] = False
    ans['Jobname'] = ""
    ans['doneJob'] = 1
    ans['totalJob'] = 1
    return ans
#    return status
# def statusreport2(status,port):
#     # manager_client = RemoteDict.ManagerClient('',port+1,'tps05a')
#     # num = manager_client.get_num()
#     # status_remote = manager_client.get_dict()
# #    getlist = manager_client.get_list
# #    m = BaseManager('',port+1,'tps05a')
# #    m.connect()
# #    num=m.num()
# #    print status
#     while True:
# #        print status
#         time.sleep(0.1)
#         if status['monjob']:
# #            print status
# #            print float(float(status['doneJob'])/float(status['totalJob']))
# #            status_remote = status
#             # status_remote.put('monjob',status['monjob'])
#             # status_remote.put('process',float(float(status['doneJob'])/float(status['totalJob']))*100)
#             # status_remote.put('Jobname',status['Jobname'])
#             # num.put(float(float(status['doneJob'])/float(status['totalJob'])))
# #            print num.get()
            
            
# # class statusManager(BaseManager): pass
# # class f(float):pass

# def ManagerServer(port):
#     #set up for remote share manager
# #    statusManager.register('num', lambda: f)
# #
# #    m = statusManager(address=('',port+1), authkey='tps05a')
# #
# #    s = m.get_server()
# ##    print "Manager ip:",s.address
# #    s.serve_forever()
#     manager_server = RemoteDict.ManagerServer('0.0.0.0',port+1,'tps05a')
#     manager_server.run()
    
def dhsServer(port):   
#    global status
    
    #start manaer server
    # p1 = mp.Process(target=ManagerServer,args=(port,))
    # p1.start()
    
    #start clinet

#    BaseManager.register('Status')
#    m = BaseManager(address=('',port+1), authkey='tps05a')
#    m.connect()
#    status = m.Status()
#    print status
    
            



    
    manager = Manager()
    status=manager.dict()
    status['monjob']= False
    status['Jobname']=False
    status['doneJob']=1
    status['totalJob']=1
    # p2 = mp.Process(target=statusreport2,args=(status,port,))
    # p2.start()
    
#    p = mp.Process(target=statusreport,args=(status,))
#    p.start()
    while True:
    
        client, addr = server.accept()
        #print "test"
        header="TCPserver"
        logger = logging.getLogger("TCPServer")
        logger.info("Acepted connection from: %s:%d" % (addr[0],addr[1]))
        #using MP 
        p = mp.Process(target=handle_client,args=(client,status,))
        p.start()
        logger.info("Start Thread PID:%d",p.pid)
        #client.close()
        #using threading
#        client_handler = threading.Thread(target=handle_client,args=(client,))
#        client_handler.setDaemon(True)
#        client_handler.start()
        #time.sleep(0.01)
   
if __name__ == '__main__':
    signal.signal(signal.SIGINT, quit)
    signal.signal(signal.SIGTERM, quit)
    server = serverTCP(int(sys.argv[1]))
    dhsServer(int(sys.argv[1]))
