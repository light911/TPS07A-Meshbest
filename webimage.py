#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 12 13:27:59 2021

@author: blctl
"""
from PyQt5.QtCore import QThread,pyqtSignal,pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
import logsetup
import http.client
import time,os

# import io

class image(QThread):
    updateimage = pyqtSignal(QPixmap)
    def __init__(self,par):
        super(image,self).__init__()
       
        self.Par = par
        # self.Par.update(par)
        self.logger = logsetup.getloger2('getimage',
                                         level = self.Par['Debuglevel'])
        self._stop = False
        self.ip = '10.7.1.4'
        self.port = 6001
        self.path = '/jpg.cgi?stream=MD3Image'
        self.highrespath = '/jpg.cgi?stream=MD3Image'
        self.updateinterval = 0.1 #sec
        
    def run(self):
        self.logger.info(f'webimaage PID = {os.getpid()}')
        while not self._stop:
            jpg = self.getimg()
            # f = io.BytesIO(jpg)
            # print("IMAGE type == ",type(jpg))
            tempq = QPixmap()
            tempq.loadFromData(jpg,format='jpg')
            self.updateimage.emit(tempq)
            time.sleep(self.updateinterval)
            # f.close()
            
        pass
    def getimg(self):
        conn = http.client.HTTPConnection(self.ip,port=self.port)
        conn.request("GET", self.path)
        r1 = conn.getresponse()
        # print(r1.status, r1.reason)
        jpg = r1.read()  # This will return entire content.
        # print("Get IMAGE type == ",type(jpg))
        conn.close()
        return jpg
    def gethighresimage(self):
        conn = http.client.HTTPConnection(self.ip,port=self.port)
        conn.request("GET", self.highrespath)
        r1 = conn.getresponse()
        jpg = r1.read()
        conn.close()
        tempq = QPixmap()
        tempq.loadFromData(jpg,format='jpg')
        return tempq,jpg
    def stop(self):
        self._stop = True

if __name__ == '__main__':
    import Config
    test = image(Config.Par)
    a=test.getimg()
    # print(type(a))
    # b = QPixmap()
    # b.loadFromData(a)
    # print(b)