"""
FileWriter class is a dummy object which decodes the EIGER zmq
stream frames from header, images, and end of series meassages.
Inherite from this class and modify following functions in order
to create a FileWriter which actually saves files:
__decodeHeader__(self, frames)
__decodeImage__(self, frames)
__decodeEndOfSeries__(self, frames)
"""

import lz4.block
import bitshuffle
import numpy as np
import json
import os
import struct
# from .... import logsetup,Config
import logsetup,Config
import time
from multiprocessing import Process,Pool

__author__ = "SasG"
__date__ = "16/11/22"
__version__ = "0.0.3"
__reviewer__ = ""

class FileWriter():
    """
    dummy class to decode zmq frames from EIGER ZMQ stream
    """
    def __init__(self, basename="eigerStream", path=".", ftype="", verbose=False, roi=False):

        self.basename = basename
        self.ftype = ftype
        self.path = path
        self.timer=0
        # self.Par = Config.Par
        # self.logger = logsetup.getloger2('FileWriter',LOG_FILENAME='./log/FileWriter.txt',level = self.Par['Debuglevel'])
        if not os.path.isdir(self.path):
            raise IOError("[ERR] path %s does not exist" %self.path)

        if roi: self.roi = ROI(*roi,verbose=verbose)
        else: self.roi = ROI(verbose=verbose)

        self.__verbose__ = verbose
        if self.__verbose__:
            self.logger.info("[OK] initialized %s FileWriter" %self.ftype)
        # self.process = Pool(processes=100)

    def decodeFrames(self, frames,ServerQ,meshbestjobQ,job_queue):
        """
        decode and proces EIGER ZMQ stream frames
        ServerQ for send message to GUI
        """
        try:
            header = json.loads(frames[0].bytes)
        except Exception as e:
            print(e)

        if header["htype"].startswith("dheader-"):
            self.__decodeHeader__(frames,ServerQ,meshbestjobQ,job_queue)
        elif header["htype"].startswith("dimage-"):
            self.__decodeImage__(frames,ServerQ,meshbestjobQ,job_queue)
            
        elif header["htype"].startswith("dseries_end"):
            self.__decodeEndOfSeries__(frames,ServerQ,meshbestjobQ,job_queue)
        else:
            self.logger.warning("[ERR] not an EIGER ZMQ message")
            return False
        return True

    def __decodeImage__(self, frames,ServerQ,meshbestjobQ,info,header,job_queue):
        """
        decode ZMQ image frames
        """
        if self.__verbose__:
            print("[*] decode image")

        # header = json.loads(frames[0].bytes) # header dict
        # info = json.loads(frames[1].bytes) # info dict

        if info["encoding"] == "lz4<": #TODO: soft code flag
            data = self.readLZ4(frames[2], info["shape"], info["type"])
        elif info["encoding"] == "bs32-lz4<": #TODO: soft code flag
            data = self.readBSLZ4(frames[2], info["shape"], info["type"])
        elif info["encoding"] =="bs16-lz4<":
            data = self.readBSLZ4(frames[2], info["shape"], info["type"])
        elif info["encoding"] =="<":
            data = self.readUncompressed(frames[2], info["shape"], info["type"])
        else:
            raise IOError("[ERR] encoding %s is not implemented" %info["encoding"])

        return data

    def __decodeEndOfSeries__(self, frames,ServerQ,meshbestjobQ,job_queue):
        if self.__verbose__:
            print("[OK] received end of series ", json.loads(frames[0].bytes))
            return True

    def __decodeHeader__(self, frames,ServerQ,meshbestjobQ,job_queue):
        """
        decode and process ZMQ header frames
        """
        if self.__verbose__:
            print("[*] decode header")
        header = json.loads(frames[0].bytes)
        if header["header_detail"]:
            if self.__verbose__:
                print(header)
        if header["header_detail"] is not "none":
            if self.__verbose__:
                print("detector config")
                for key, value in json.loads(frames[1].bytes).items():
                    print(key, value)
        if header["header_detail"] == "all":
            if json.loads(frames[2].bytes)["htype"].startswith("dflatfield"):
                if self.__verbose__:
                    print("writing flatfield")
            if json.loads(frames[4].bytes)["htype"].startswith("dpixelmask"):
                if self.__verbose__:
                    print("writing pixel mask")
            if json.loads(frames[6].bytes)["htype"].startswith("dcountrate"):
                if self.__verbose__:
                    print("writing LUT")
        if len(frames) == 9:
            if self.__verbose__:
                print("[*] appendix: ", json.loads(frames[8].bytes))

    def readBSLZ4(self, frame, shape, dtype):
        """
        unpack bitshuffle-lz4 compressed frame and return np array image data
        frame: zmq frame
        shape: image shape
        dtype: image data type
        """

        data = frame.bytes
        blob = np.fromstring(data[12:], dtype=np.uint8)
        # blocksize is big endian uint32 starting at byte 8, divided by element size
        dt = np.dtype(dtype)
        blocksize = np.ndarray(shape=(), dtype=">u4", buffer=data[8:12])/dt.itemsize
        imgData = bitshuffle.decompress_lz4(blob, shape[::-1], dt, blocksize)
        # if self.__verbose__:
        #     print("[OK] unpacked {0} bytes of bs-lz4 data".format(len(imgData)))
        return imgData

    def readLZ4(self, frame, shape, dtype):
        """
        unpack lz4 compressed frame and return np array image data
        frame: zmq frame
        dataSize: data size of single value
        """

        dtype = np.dtype(dtype)
        dataSize = dtype.itemsize*shape[0]*shape[1] # bytes * image size

        imgData = lz4.block.decompress(struct.pack('<I', dataSize) + frame.bytes)
        # if self.__verbose__:
        #     print("[OK] unpacked {0} bytes of lz4 data".format(len(imgData)))

        return np.reshape(np.fromstring(imgData, dtype=dtype), shape[::-1])

    def readUncompressed(self, frame, shape, dtype):
        """
        unpack uncompressed frame and return np array image data
        frame: zmq frame
        dataSize: data size of single value
        """

        dtype = np.dtype(dtype)
        dataSize = dtype.itemsize*shape[0]*shape[1] # bytes * image size

        imgData = frame.bytes
        if self.__verbose__:
            print("[OK] unpacked {0} bytes of uncompressed data".format(len(imgData)))

        return np.reshape(np.fromstring(imgData, dtype=dtype), shape[::-1])

class ROI():
    """
    NOT IMPLEMENTED YET
    software ROI
    class ROI returns region of interest of a numpy array
    """
    def __init__(self, start=[False,False], end=[False,False], verbose=False):

        self.xstart, self.ystart = start[0],start[1]
        self.xend, self.yend = end[0],end[1]
        self.active = all([self.xstart, self.ystart, self.xend, self.yend])
        self.__verbose__ = verbose

        if self.__verbose__:
            if self.active:
                print("ROI active, start: %s, end: %s (ROI not yet implemented)" %(start, end))
            else:
                print("[INFO] software ROI inactive (ROI not yet implemented)")

    def __str__(self):
        if active:
            return "ROI start: %s end: %s" %(self.start, self.end)
        else:
            return "none"

    def roi(data):
        if self.active:
            return data[self.ystart:self.yend+1, self.xstart:self.xend+1]
        else:
            return data
