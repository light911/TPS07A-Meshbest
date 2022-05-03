"""
TODO:
-comment and clean up
-flatfield not as integer!!!
-header data not stored
"""

from .fileWriter import FileWriter
import threading
import cbf
import lz4, bitshuffle
import numpy as np
import json,base64
import os
import logsetup,Config
import time
from multiprocessing import Process,Pool,Queue
import subprocess,shutil,sys

try:
    from dectris import albula
    print("[INFO] using ALBULA API to handle images")
except:
    albula = None
    print("[INFO] using PSI cbf module to handle images")


__author__ = "SasG"
__date__ = "16/11/22"
__version__ = "0.0.2"
__reviewer__ = ""

class Stream2Cbf(FileWriter):
    def __init__(self, basename, path, verbose=False):
        self.basename = basename
        self.path = path
        self.__verbose__ = verbose
        self.ftype = ".cbf"
        self.series = 0
        self.metadata = {}
        self.currentframe = -1

        FileWriter().__init__(basename, path, self.ftype, verbose)
        self.Par = Config.Par
        self.logger = logsetup.getloger2('FileWriter',LOG_FILENAME='./log/FileWriter.txt',level = self.Par['Debuglevel'])
        self._observers=[]
        self.timer=0
        self.dozor_par={"spot_level":5.5,"spot_size":3}
        # self.process = Pool(100)
        # self.header = {}
        # self.temp=True

    

    def saveConfig(self, frames):
        """
        save detector config as plain text
        """
        pass
        # print(f'LEN={len(frames)}')
        if len(frames) == 9:#oringal 9-2
            appendix = frames[8]#8-2
            # print('has appendix')
        else:
            appendix = None
            # print('no appendix')
        self.series = json.loads(frames[0].bytes)["series"]
        
        data = json.loads(frames[1].bytes)
        if appendix:
            data["appendix"] = json.loads(appendix.bytes)
            # print(f'appenidx={data["appendix"]}')
        self.metadata = data
        # print(data)
        # print(type(data))
        if self.metadata["appendix"]['runIndex'] == '101' or self.metadata["appendix"]['runIndex'] =='102':
            path = os.path.join(self.path, self.basename + "_%05d_config.json" %(self.series))
            
        else:
            
            path = os.path.join(self.path,self.metadata["appendix"]['filename'] + "_%05d_config.json" %(self.series))
        with open(path,"w") as f:
            json.dump(data,f)
            f.close
        print("[OK] wrote %s" %path)

    def saveTable(self, frames, name="", ftype=".dat"):
        """
        save pixel mask, flatfield or LUT
        """
        pass
        # path = os.path.join(self.path, self.basename+"_%05d_%s%s" %(self.series,name,ftype))

        # header = json.loads(frames[0].bytes)
 
        # dtype = np.dtype(header["type"])
       
        # data = np.reshape(np.fromstring(frames[1].bytes, dtype=dtype), header["shape"][::-1])

        # if ftype == ".dat":
        #     np.savetxt(path, data)
        # elif ftype == ".cbf":
        #     cbf.write(path, data, self.__getHeader__())
        # else:
        #     raise IOError("file type %s not known. Allowed are .cbf|.dat" %ftype)

        # print("[OK] wrote %s" %path)

    def saveImage(self, data, series, frame,metadata):
        """
        save image data as cbf
        """
        # path = os.path.join(self.path, self.basename + "_%05d_%05d%s" %(series, frame+1, self.ftype))
        
        # path = os.path.join(self.path, self.basename + "_%05d%s" %(frame+1, self.ftype))
        basename = metadata["appendix"]['filename']
        path = os.path.join(self.path, basename + "_%05d%s" %(frame+1, self.ftype))
        # if albula:
        #     albula.DImageWriter.write(albula.DImage().fromData(data), path)
        # else:
        #     cbf.write(path, data, header = self.__getHeader__())
        # print("[OK] wrote %s" %path)
        # print(f'Header={self.__getHeader__()}')
        cbf.write(path, data, header = self.__getHeader__())
        return path

    def __getHeader__(self):
        """
        return cbf header string from meta data
        """
        header = ""
        for key, value in self.metadata.items():
            header += "# %s: %s\n" %(key, value)
        return header

    def __decodeHeader__(self, frames,ServerQ,meshbestjobQ,job_queue):
        """
        decode and process ZMQ header frames
        """
        self.timer = time.time()
        #new dataset clear temp meshPositionsdata
        
        self.logger.info(f"Get frame Header!")
        header = json.loads(frames[0].bytes)
        if header["header_detail"]:
            if self.__verbose__:
                print("[OK] decode header ", header)
        if header["header_detail"] is not "none":
            if len(frames) == 9 and self.__verbose__:
                # print("[*] Appendix:", frames[8].bytes)
                pass
            
            self.saveConfig(frames)
            if self.__verbose__:
                print("[OK] detector config:")
                for key, value in json.loads(frames[1].bytes).items():
                    # print("[*] ", key, value)
                    pass
        view = int(self.metadata["appendix"]['runIndex'])
        meshbestjobQ.put(('BeginOfSeries',view))
        # if header["header_detail"] == "all":
        #     if json.loads(frames[2].bytes)["htype"].startswith("dflatfield"):
        #         threading.Thread(target=self.saveTable,args=(frames[2:4],"flatfield",".cbf")).start()
        #     if json.loads(frames[4].bytes)["htype"].startswith("dpixelmask"):
        #         threading.Thread(target=self.saveTable,args=(frames[4:6],"pixelmask",".cbf")).start()
        #     if json.loads(frames[6].bytes)["htype"].startswith("dcountrate"):
        #         threading.Thread(target=self.saveTable,args=(frames[6:8],"countrate",".dat")).start()

    def __decodeImage__(self, frames,ServerQ,meshbestjobQ,job_queue):
        """
        decode ZMQ image frames and save as .cbf
        """
        # t0 = time.time()
        # data = FileWriter().__decodeImage__(frames) # read back image data
        
        # info = json.loads(frames[1].bytes)
        # header = json.loads(frames[0].bytes)
        # self.logger.debug(f'decode time for frame {header["frame"]},time:{time.time()-t0} sec')
        # if len(frames)==5:
        #     self.metadata["appendix"] = frames[4].bytes
        # self.metadata["real_time"] = json.loads(frames[3].bytes)["real_time"]
        # self.currentframe = int(header["frame"])
        # self.logger.info(f'Starting writing frame {header["frame"]},time pass:{time.time()-self.timer} sec')
        # threading.Thread(target=self.saveImage,args=(data, header["series"], header["frame"])).start()
        # p1 = threading.Thread(target=self.__decodeImage2__,args=(frames,))
        
        
        
        info = json.loads(frames[1].bytes)
        header = json.loads(frames[0].bytes)
        
        if len(frames)==5:
            self.metadata["appendix"] = frames[4].bytes
        self.metadata["real_time"] = json.loads(frames[3].bytes)["real_time"]
        try:
            if self.metadata["appendix"]['runIndex'] == '101' or self.metadata["appendix"]['runIndex'] =='102':
                
            
                # info = json.loads(frames[1].bytes)
                # header = json.loads(frames[0].bytes)
                # data = frames[2]
                series = header["series"]
                frame = header["frame"]
                # data = FileWriter().__decodeImage__(frames,ServerQ,meshbestjobQ,info,header,job_queue)
                # r = self.process.apply_async(self.__decodeImage2__,args=(data,ServerQ,self.metadata,meshbestjobQ,info,header,job_queue,))
                #to using 
                # r.get()
                # job_queue.put((frames,ServerQ,self.metadata,meshbestjobQ))
                dozor_par = self.dozor_par
                p1 = Process(target=self.__decodeImage2__,args=(frames,ServerQ,self.metadata,meshbestjobQ,info,header,job_queue,dozor_par,))
                p1.start()
            else:
                self.logger.debug(f'Run index {self.metadata["appendix"]["runIndex"]} not a raster scan,frame= {header["frame"]}')
        except Exception as e:
            self.logger.warning(f'Has error on {e}')
        
        self.currentframe = int(header["frame"])
        
        # self.notify_observers("newthread",p1)
        # return data
    #this two function make pool work    
    # def __getstate__(self):
    #     self_dict = self.__dict__.copy()
    #     del self_dict['process']
    #     return self_dict

    # def __setstate__(self, state):
    #     self.__dict__.update(state)

    
    def __decodeImage2__(self,frames,ServerQ,metadata,meshbestjobQ,info,header,job_queue,dozor_par):
        t0 =time.time()
        os.nice(34)
        # data = FileWriter().__decodeImage__(frames,ServerQ,meshbestjobQ,job_queue) # read back image data
        data = FileWriter().__decodeImage__(frames,ServerQ,meshbestjobQ,info,header,job_queue)
        # data = frames
        # np.save("/data/blctl/test",data)
        # self.logger.warning(f'Data type = {data.dtype}')
        if data.dtype != "uint32" :
            if data.dtype == "uint16":
                maxV=65535
            elif data.dtype == "uint8":
                maxV=255
            else:
                maxV=4294967295
            data = data.astype('uint32')
            data = np.where(data==maxV,4294967295,data)
            # self.logger.warning(f'New Data type = {data.dtype}')
        # info = json.loads(frames[1].bytes)
        # header = json.loads(frames[0].bytes)
        series = header["series"]
        frame = header["frame"]
        view =int(metadata["appendix"]['runIndex'])
        # self.logger.debug(f'decode time for frame {header["frame"]},time:{time.time()-t0} sec')
        path = self.saveImage(data, series, frame,metadata)
        
        dozorresult,datastr = self.dozor(path,metadata,dozor_par)
        dozorresult['frame'] = frame
        dozorresult['omega'] = metadata['omega_start']
        dozorresult['numofX'] = metadata['appendix']['raster_X']
        dozorresult['numofY'] = metadata['appendix']['raster_Y']
        if view == 101:
            dozorresult['view']=1
        else:
            dozorresult['view']=2
        #dezor
        #tell gui finish job
        self.logger.info(f'save + decode time for frame {frame},time:{time.time()-t0} sec')
        ServerQ.put(('dozor',dozorresult))
        meshbestjobQ.put(('updateDozor',dozorresult,datastr))
        pass
    def __decodeEndOfSeries__(self, frames,ServerQ,meshbestjobQ,job_queue):
        self.logger.info(f"End of Series: {self.currentframe}")
        self.logger.info(f"Time for whole Series = {time.time()-self.timer} sec")
        # self.notify_observers('EndOfSeries',self.basename,self.currentframe+1)
        ServerQ.put(('EndOfSeries'))
        try:
            if self.metadata["appendix"]['runIndex'] == '101' or self.metadata["appendix"]['runIndex'] =='102':
                meshbestjobQ.put(('EndOfSeries',self.metadata))
            if self.__verbose__:
                print("[OK] received end of series ", json.loads(frames[0].bytes))
        except Exception as e:
            self.logger.warning(f'Has error on {e}')
        return True
    
    #man dhs need register after active calss
    # in here
    # self.epics = epicsdev(EpicsConfig.epicslist,self.Par)
    # self.epics.register_observer(self)
    # for event use self.notify_observers send it
    # self.notify_observers('ChangeMD3BS',value)
    
    # in upper dhs need has a 
    # def notify
    def dozor(self,path,metadata,dozor_par):
        spot_level=f'spot_level {dozor_par["spot_level"]}'
        spot_size=f'spot_size {dozor_par["spot_size"]}'
        dozorresult={}
        #path = /tmp/meshbest/temp_00279.cbf
        pid=os.getpid()
        extwithpt = os.path.splitext(path)[1]#.cbf
        tempproc=path.replace(extwithpt,"_proc")#/tmp/meshbest/temp_0027_proc
        filename = os.path.basename(path)#temp_00279.cbf
        outputpath = os.path.dirname(path)#tmp/meshbest
        
        if os.path.isdir(tempproc):
            self.logger.debug("PID:%s _proc folder exist not need to creat",pid)
            pass
        else:
            self.logger.debug("PID:%s Creat folder=%s",pid,tempproc)
            os.mkdir(tempproc)
        os.chdir(tempproc)
        start_time = time.time()   
        txt=""
        txt = txt + "nx " + str(metadata['x_pixels_in_detector']) +"\n"
        txt = txt + "ny " + str(metadata['y_pixels_in_detector']) +"\n"
        txt = txt + "orgx " + str(metadata['beam_center_x']) + "\n"
        txt = txt + "orgy " + str(metadata['beam_center_y']) + "\n"
        txt = txt + "detector_distance " + str(metadata['detector_distance']*1000) + "\n"
        txt = txt + "X-ray_wavelength " + str(metadata['wavelength']) + "\n"
        txt = txt + "starting_angle " + str(metadata['omega_start']) + "\n"
        txt = txt + "oscillation_range " + str(metadata['omega_increment']) + "\n"
        txt = txt + "exposure " + str(metadata['frame_time']) + "\n"
        txt = txt + "first_image_number " + "1" + "\n"
        txt = txt + "number_images " + "1" + "\n"
        txt = txt + "name_template_image " + str(path) + "\n"
        txt = txt + "pixel " + str(metadata['x_pixel_size']*1000) + "\n"
        txt = txt + "pixel_min 1\n"
        txt = txt + "pixel_max " + str(metadata['countrate_correction_count_cutoff']) +"\n"
        txt = txt + f"{spot_level}\n"#higher less spot default 5.5
        txt = txt + "fraction_polarization 0.99\n"
        txt = txt + f"{spot_size}\n"
        txt = txt + "wedge_number 1\n"
        txt = txt + "end\n"
        newfilename = filename.replace(extwithpt, "_dozor.txt")
        dozor_filepath=os.path.join(tempproc,newfilename)
        # print(f'extwithpt={extwithpt},newfilename={newfilename},dozor_filepath={dozor_filepath}')
        # path.replace(".cbf","_dozor.txt")
        #num_q=filename.count("?")
        #replacestr = "?"*num_q
        #filename=filename.replace(replacestr,"dozor")
        #print filename
        with open(dozor_filepath, 'w') as outfile:
            outfile.write(txt)
        command = "/data/program/MeshbestServer/dozor -p -pall " + dozor_filepath
        
        
        #os.system(command)
        try :
            result = subprocess.check_output(command, shell=True).decode('utf-8')
        except:
            
            self.logger.debug("PID:%d fail to  run dozor for file %s",pid,filename)
            result = ''' Program dozor /A.Popov & G.Bourenkov/
     Version 2.0.2 //  21.05.2019
     Copyright 2014 by Alexander Popov and Gleb Bourenkov
     N    |            SPOTS             |        Powder Wilson              |        Main    Spot   Visible
    image | num.of  INTaver R-factor Res.|   Scale B-fac. Res. Corr. R-factor|       Score   Score  Resolution
    --------------------------------------------------------------------------------------------------------
        1 |     0        0.   0.000  99.0| ---------no results -----------   |       0.000    0.00   99.00
    --------------------------------------------------------------------------------------------------------
    '''
        # print(result)
        # print(type(result))
        result2 = result.split("\n")
        i=0
        for temp in result2:
           i=i+1 
           
           if i==7:
               #only take line 7
              #print temp
              dozorspots=int(temp[7:13])
              dozorscore=float(temp[74:86])
              dozorres=float(temp[31:37])
              #print "score=",dozorscore
              #print "spots=",dozorspots
              #print "res.=",dozorres
           else:
              pass
              #dozorscore.append(float(temp[13:23]))
              #dozorspots.append(int(temp[7:13]))
              
        spotfile=tempproc+"/00001.spot"
        
        if os.path.isfile(spotfile):
            datastr = self.readspot(spotfile)
            self.logger.debug("PID:%d rename 00001.spot file to %s",pid,filename.replace("_dozor.txt",".spot"))
            #logger.debug(os.getcwd())
            #mv spot to a folder, here filename is in cbf folder,so next we need copy to mccd folder
            os.rename(spotfile,newfilename.replace("_dozor.txt",".spot"))
            
                
            os.chdir(outputpath)
        else:
            datastr =""
            self.logger.debug("PID:%d spotfile not found,maybe due to no spot found here",pid)
            #print os.getcwd()
            os.chdir(outputpath)
            pass
        #for test
        dozor_result = os.path.join(tempproc,filename.replace(extwithpt, "_dozorResult.txt"))
        
        with open(dozor_result, 'w') as outfile:
            outfile.write(result)
        
        #time.sleep(0.1)
        # try:
        #     self.logger.debug("PID:%d try to remove %s",pid,tempproc)
        #     shutil.rmtree(tempproc, ignore_errors=True)
        #     os.remove(filename)#_dozor.txt on ram disk
        #     # os.remove(filecbfpath)#cbf file on ram disk
        #     if os.path.isfile(filename.replace("_dozor.txt",".spot")):
        #         os.remove(filename.replace("_dozor.txt",".spot"))#.spot file on ram disk
        #     else:
        #         pass
        # except:
        #     self.logger.warn("PID:%d fail to remove folder\n%s",pid,sys.exc_info())
            
            
    #    with open("dozor_sum_int.dat", 'r') as readfile:
    #        filetxt=readfile.read()
    #    #print filetxt
    #    filetxt2=filetxt.split("\n")
        
        #print "Run dozor time=",dozorresult['dozorTime']
        dozorresult['totalTime']=time.time()-start_time
        #print "Total run time=",dozorresult['totalTime']
        dozorresult['File']=path
        dozorresult['spots']=dozorspots
        dozorresult['score']=dozorscore
        dozorresult['res']=dozorres
        
        self.logger.debug("PID:%d dozor result=%s",pid,dozorresult)
        
        txt=""
        txt=txt+str(dozorresult['score'])+"\n"
        txt=txt+str(dozorresult['spots'])+"\n"
        txt=txt+str(dozorresult['res'])+"\n"
        txt=txt+str(dozorresult['File'])+"\n"
        txt=txt+"score\tspots\tres\tFile name"
    # #    with open(filemccdpath.replace(".mccd",".score"), 'w') as outfile:
    #     with open(filemccdpath.replace(extwithpt,".score"), 'w') as outfile:
    #         outfile.write(txt)
    # #    os.chown(filemccdpath.replace(".mccd",".score"), os.stat(filemccdpath).st_uid, os.stat(filemccdpath).st_gid)    
    #     os.chown(filemccdpath.replace(extwithpt,".score"), os.stat(filemccdpath).st_uid, os.stat(filemccdpath).st_gid)    
        
        return dozorresult,datastr
    
    def readspot(self,path):
        """
        read xxxx.spot file
        /data/blctl/meshbest/testdata/BL-05A_raster0_0_VIEW1_10_00019.cbf
        N_of_spots=     3
        omega=   262.26
        1  1222.0  1850.0       440.8        37.0
        1  1239.0  1985.0       359.1        35.8
        1  1222.0  1986.0       389.1        36.2
    
        meshbest require all info,but only using posX posY I Sigma(index1,2,3,4?)
        
        """
        
        #print "read file=",path    
        with open(path, 'r') as readfile:
            filetxt=readfile.read()
        #print filetxt
        filetxt2=filetxt.split("\n")
        i=0
        data=np.array(-1.0)
        datastr=""
        for txt in filetxt2:
            i=i+1 
            if i>3:
                try:
                    if np.size(data) == 1:
                        #print "1"
                        datalist=[float(txt[0:2]),float(txt[2:10]),float(txt[10:18]),float(txt[18:30]),float(txt[30:42])]
                        #datatemp=np.arry(datalist)
                        #print "before=",data
                        data=np.append(data,float(txt[0:2]))
                        #print float(txt[0:2])
                        data=np.append(data,float(txt[2:10]))
                        data=np.append(data,float(txt[10:18]))
                        data=np.append(data,float(txt[18:30]))
                        data=np.append(data,float(txt[30:42]))
                        #print "after=",data
                        data=np.delete(data,0)
                    else:
                        data=np.append(data,float(txt[0:2]))
                        data=np.append(data,float(txt[2:10]))
                        data=np.append(data,float(txt[10:18]))
                        data=np.append(data,float(txt[18:30]))
                        data=np.append(data,float(txt[30:42]))
                except ValueError:
                    #print ValueError
                    #print txt
                    pass
            else:
               pass 
        #print posx
        #print "data=",data
        datastr=base64.b64encode(data)
        #print datastr
        return datastr.decode("utf-8")
    
    def register_observer(self, observer):
        self._observers.append(observer)
        self.logger.debug("Stream2Cbf register PID:%d",os.getpid())
        # self.logger.debug("Register",observer)
        
    def notify_observers(self, *args, **kwargs):
        for observer in self._observers:
            observer.notify(self, *args, **kwargs)
        self.logger.debug(f"Stream2Cbf notify_observers PID:{os.getpid()} {args},{kwargs}",)