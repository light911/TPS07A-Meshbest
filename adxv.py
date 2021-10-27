
import time,signal,os
from multiprocessing import Process, Queue, Manager
import multiprocessing as mp
import math
import Config
import logsetup
import numpy as np
import subprocess
import socket
import h5py
import math

class adxv():
    def __init__(self,Par=None) :
        t0=time.time()
        signal.signal(signal.SIGINT, self.quit)
        signal.signal(signal.SIGTERM, self.quit)
        #load config
        if Par == None:
            self.m = Manager()
            self.Par = self.m.dict()
            self.Par.update(Config.Par)
        else:
            self.Par = Par
        self.logger = logsetup.getloger2('adxvlog',level = self.Par['Debuglevel'],LOG_FILENAME='./log/adxvlog.txt')

        self.port = self.get_free_port()
        self.process = Process(target=self.openadxv, args=(self.port,),name='ADXV')
        self.overload = 65535
        self.wavelength = 1
        self.distance = 140
        self.beam_centerX = 1
        self.beam_centerY = 1
        
        

        
    def showimage(self,path,N=1):
        #path should be master file
        _new=False
        with h5py.File(path,'r') as f:

            wavelength = f['/entry/instrument/beam/incident_wavelength'][()]
            orgx = f['/entry/instrument/detector/beam_center_x'][()]
            orgy = f['/entry/instrument/detector/beam_center_y'][()]
            distance = f['/entry/instrument/detector/detector_distance'][()]*1000
            overload = f['/entry/instrument/detector/saturation_value'][()]
        self.logger.warning(f'{wavelength=},{orgx=},{orgy=},{distance=},{overload=}')
        self.logger.warning(f'{self.wavelength=},{self.beam_centerX=},{self.beam_centerY=},{self.distance=},{self.overload=}')
        if self.wavelength != wavelength or self.beam_centerX != orgx or self.beam_centerY != orgy or self.distance != distance or self.overload != overload:
            #need open a new one adxv
            _new=True
            self.wavelength = wavelength 
            self.beam_centerX = orgx
            self.beam_centerY = orgy
            self.distance = distance
            self.overload = overload
            self.logger.warning('Header diffenert need new adxv')


        if self.process.is_alive() and _new:
            #has adxv running need closed and reopen
            commands =['exit']
            self.sendcommand(self.port,commands)
            time.sleep(0.1)
            self.logger.warning('process is_alive and need new process')
            self.process.terminate()
            self.port = self.get_free_port()
            self.process = Process(target=a.openadxv, args=(self.port,),name='ADXV')
            self.process.start()
            time.sleep(0.5)
            pass
        elif self.process.is_alive():
            #has adxv running no need to reopen
            pass
        else:
            #no adxv running need to open
            self.port = self.get_free_port()
            self.process = Process(target=a.openadxv, args=(self.port,),name='ADXV')
            self.process.start()
            time.sleep(0.5)
        # /data/blctl/20211027_07A/154945/collect/001_0000_master.h5
        # /data/blctl/20211027_07A/154945/collect/001_0000_data_000001.h5
        datanum = math.ceil(N/1000)
        datafile = path.replace('_master',f'_data_{datanum:06}')

        num = N - (datanum-1)*1000
        
        commands=[]
        commands.append(f'load_image {datafile}')
        commands.append(f'slab {num}')
        commands.append(f'weak_data 1')
        self.sendcommand(self.port,commands)
        # wavelength=`h5dump -d "/entry/instrument/beam/incident_wavelength" $master_file | awk '/\(0\): [0-9]/{print $2}'`
        # orgx=`h5dump -d "/entry/instrument/detector/beam_center_x" $master_file | awk '/\(0\): [0-9]/{print $2}'`
        # orgy=`h5dump -d "/entry/instrument/detector/beam_center_y" $master_file | awk '/\(0\): [0-9]/{print $2}'`
        # distance=`h5dump -d "/entry/instrument/detector/detector_distance" $master_file | awk '/\(0\): [0-9]/{print $2*1000}'`
        # data_file=${master_file/master/data_000001}
        # overload=`h5dump -d "/entry/instrument/detector/saturation_value" $master_file | awk '/\(0\): [0-9]/{print $2}'`
        
        #adxv -pixelsize 0.075 -rings -beam_center $orgx $orgy   -wavelength $wavelength -distance $distance -overload $overload $data_file 
        pass

    def openadxv(self,port=None):
        DISPLAY = os.getenv('DISPLAY') 
        HOME = os.getenv('HOME') 
        PATH = os.getenv('PATH') 
        # print(f'{DISPLAY=}, {HOME=}')
        if port:
            env={'ADXV_DISPLAY_PORT':str(port),'DISPLAY':DISPLAY,'HOME':HOME,'PATH':PATH}
        else:
            env={'ADXV_DISPLAY_PORT':'8101','DISPLAY':DISPLAY,'HOME':HOME,'PATH':PATH}
        # command = ['/data/program/ADXV/adxv','-socket']
        command = ['adxv','-pixelsize', '0.075','-rings','-beam_center',str(self.beam_centerX),str(self.beam_centerY),'-wavelength', str(self.wavelength),'-distance',str(self.distance),'-overload',str(self.overload),'-socket']
        
        # command = ['ls','-l']
        adxvProcess = subprocess.run(command,env=env)
        # adxvProcess = subprocess.Popen(command,env=env,shell=True)
        print('done')
    
    def displayimage(self,port,path):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        HOST =""
        s.connect((HOST, port))
        command = f'load_image {path}\n'
        print(command)
        s.send(command.encode())
        s.close()

    def get_free_port(self,host='127.0.0.1'):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, 0))
        port = sock.getsockname()[1]
        sock.close()
        time.sleep(0.1)
        return port 

    def slab(self,port,N):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        HOST =""
        s.connect((HOST, port))
        command = f'slab {N}\n'
        print(command)
        s.send(command.encode())
        s.close()

    def sendcommand(self,port,commands=[]):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        HOST =""
        s.connect((HOST, port))
        for command in commands:
            c = command + '\n'
            self.logger.info(f'command:{command}')
            s.send(c.encode())
        s.close()


    def quit(self,signum,frame):
        self.logger.debug(f"PID : {os.getpid()} DHS closed, Par= {self.Par} TYPE:{type(self.Par)}")
        # self.logger.info(f'PID : {os.getpid()} DHS closed') 
        self.logger.critical(f'm pid={self.m._process.ident}')
        self.m.shutdown()
        active_children = mp.active_children()
        self.logger.critical(f'active_children={active_children}')
        if len(active_children)>0:
            for item in active_children:
                self.logger.warning(f'Last try to kill {item.pid}')
                os.kill(item.pid,signal.SIGKILL)

if __name__ == '__main__':
    a=adxv()
    port = a.get_free_port()

    a.showimage('/data/blctl/20211027_07A/154945/collect/001_0000_master.h5',5)
    time.sleep(5)
    a.showimage('/data/blctl/20211027_07A/154945/RasterScanview2_0000_master.h5',10)
    time.sleep(5)
    # a.openadxv(port)
    # p = Process(target=a.openadxv, args=(port,),name='ADXV')
    # p.start()
    # time.sleep(1)
    # N=5
    # commands=[]
    # commands.append('load_image /data/blctl/20211027_07A/154945/collect/001_0000_data_000001.h5')
    # commands.append(f'slab {N}')
    # a.sendcommand(port,commands)
    # a.displayimage(port,'/data/blctl/20211027_07A/154945/collect/001_0000_data_000001.h5')
    # a.slab(port,2)
    # print(p.pid)
    # while p.is_alive():
    #     time.sleep(1)
    #     print('alive')
    # print('Closed')
    