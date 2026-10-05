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
    #emit QImage (QPixmap is not thread safe outside GUI thread)
    updateimage = pyqtSignal(QImage)
    #emit error reason when image source can not be reached/decoded
    imageerror = pyqtSignal(str)
    def __init__(self,par):
        super(image,self).__init__()
       
        self.Par = par
        # self.Par.update(par)
        self.logger = logsetup.getloger2('getimage',
                                         level = self.Par['Debuglevel'])
        self._stop = False
        self.ip = '10.7.1.4'
        self.port = 6001
        # self.path = '/jpg.cgi?stream=MD3Image'
        self.path = '/image1.cgi?stream=MD3Image'
        self.highrespath = '/image1.cgi?stream=MD3Image'
        self.updateinterval = 0.1 #sec
        self.timeout = 3 #sec, http connect/read timeout
        self.retryinterval = 1 #sec, wait before reconnect after error
        
    def run(self):
        self.logger.info(f'webimaage PID = {os.getpid()}')
        connected = True
        while not self._stop:
            try:
                jpg = self.getimg()
                tempq = QImage.fromData(jpg,'jpg')
                if tempq.isNull():
                    raise ValueError(f'can not decode image ({len(jpg)} bytes)')
            except Exception as e:
                reason = f'{type(e).__name__}: {e}'
                if connected:
                    self.logger.warning(f'image source {self.ip}:{self.port}{self.path} lost, {reason}')
                    connected = False
                self.imageerror.emit(reason)
                time.sleep(self.retryinterval)
                continue
            if not connected:
                self.logger.warning(f'image source {self.ip}:{self.port}{self.path} reconnected')
                connected = True
            self.updateimage.emit(tempq)
            time.sleep(self.updateinterval)
            
        pass
    def _get(self,path):
        conn = http.client.HTTPConnection(self.ip,port=self.port,timeout=self.timeout)
        try:
            conn.request("GET", path)
            r1 = conn.getresponse()
            jpg = r1.read()  # This will return entire content.
            if r1.status != 200:
                raise IOError(f'HTTP {r1.status} {r1.reason}')
        finally:
            conn.close()
        return jpg
    def getimg(self):
        return self._get(self.path)
    def gethighresimage(self):
        #raise exception if image source is not available
        jpg = self._get(self.highrespath)
        tempq = QPixmap()
        if not tempq.loadFromData(jpg,format='jpg'):
            raise ValueError(f'can not decode image ({len(jpg)} bytes)')
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