import asapo_consumer,logsetup,os,numpy,bitshuffle,cbf,time,subprocess,base64
import Config
def readBSLZ4( frame, shape, dtype):
    """
    unpack bitshuffle-lz4 compressed frame and return np array image data
    frame: zmq frame
    shape: image shape
    dtype: image data type
    """

    # data = frame.bytes
    data = frame
    # blob = numpy.fromstring(data[12:], dtype=numpy.uint8)
    blob = numpy.frombuffer(data[12:], dtype=numpy.uint8)
    # blocksize is big endian uint32 starting at byte 8, divided by element size
    dt = numpy.dtype(dtype)
    blocksize = numpy.ndarray(shape=(), dtype=">u4", buffer=data[8:12])/dt.itemsize
    imgData = bitshuffle.decompress_lz4(blob, shape[::-1], dt, blocksize)
    # if self.__verbose__:
    #     print("[OK] unpacked {0} bytes of bs-lz4 data".format(len(imgData)))
    return imgData


class AsapoToDozor:
    def __init__(self,tempcbffolder, server, beamtime, token, stream_id,ServerQ,meshbestjobQ,Raster_scoring_way,dozor_par,group_id=None,logger=None,par=None):
        self.server = server
        self.beamtime = beamtime
        self.token = token
        self.stream_id = stream_id
        self.tempcbffolder = tempcbffolder
        self.ServerQ = ServerQ
        self.meshbestjobQ = meshbestjobQ
        self.Raster_scoring_way = Raster_scoring_way
        self.dozor_par = dozor_par
        self.consumer = asapo_consumer.create_consumer(
            server, "auto", False, beamtime, "Eiger16M", token, 5000
        )
        self.stream_meta = self.consumer.get_stream_meta(self.stream_id)
        if par is None:
            self.Par = Config.Par
        else:
            self.Par = par
        if group_id is None:
            self.group_id = self.consumer.generate_group_id()
        else:
            self.group_id = group_id
        if logger is None:
            self.logger = logsetup.getloger2('AsapoToDozor',LOG_FILENAME='/root/log/AsapoToDozorLog.txt',level = self.Par['Debuglevel'],bypassdb=True)
        else:
            self.logger = logger
        self.pid = os.getpid()
        self.run()
            
    def run(self):
        """
        Run the consumer to receive data from Asapo.
        """
        while True:
            try:
                data, meta = self.consumer.get_next(
                    self.group_id, stream=self.stream_id, meta_only=False, ordered=False
                )
                if self.Raster_scoring_way=="Dozor":
                    t0 = time.time()
                    byte_data = data.tobytes()

                    # imageheader = json.loads(frames[0].bytes) # {”htype”:”dimage-1.0”,”series”: <series id>, ”frame”: <frame id>, ”hash”: <md5>},
                    # info #  {”htype”:”dimage_d-1.0”, ”shape”:[x,y,(z)], ”type”: <data type>, ”encoding”: <encoding>, ”size”: <size of data blob>}
                    # appendix
                    # {'user': 'yjsun', 
                    # 'directory': '/data/yjsun/20250225_07A/stafftest', 
                    # 'runIndex': 1, 
                    # 'beamsize': '50', 
                    # 'atten': '0.000000', 
                    # 'fileindex': 1, 
                    # 'filename': 'test_1_0001', 
                    # 'uid': 10009, 
                    # 'gid': 501, 
                    # 'collectype': 'Normal dataset',
                    # 'TotalFrames': 4}
                    shape =  meta['meta']['info']['shape']
                    datatype = numpy.dtype(meta['meta']['info']['type'])
                    imgdata = readBSLZ4(byte_data, shape, datatype)
                    basename = meta['meta']["appendix"]['filename']
                    frame  = meta['meta']['imageheader']['frame']
                    path = os.path.join(self.tempcbffolder, basename + "_%05d%s" %(frame+1, ".cbf"))
                    if meta['meta']['info']['type'] != "uint32" :
                        if meta['meta']['info']['type'] == "uint16":
                            maxV=65535
                        elif meta['meta']['info']['type'] == "uint8":
                            maxV=255
                        else:
                            maxV=4294967295
                        imgdata = imgdata.astype('uint32')
                        imgdata = numpy.where(imgdata==maxV,4294967295,imgdata)
                    cbf.write(path, imgdata, header = {})
                    self.logger.info(f'done for wrtie CBF file : {path}')
                    #stream_meta form zmq ot asapo self.detectconfig | self.appendix
                    dozorresult,datastr = self.dozor(path,self.stream_meta,self.dozor_par)
                    dozorresult['frame'] = frame
                    dozorresult['omega'] = self.stream_meta['omega_start']
                    dozorresult['numofX'] = self.stream_meta['raster_X']
                    dozorresult['numofY'] = self.stream_meta['raster_Y']
                    if str(meta['meta']["appendix"]['runIndex']) == '101':
                        dozorresult['view']=1
                    else:
                        dozorresult['view']=2
                            #tell gui finish job
                    self.logger.info(f'save + decode time for frame {frame},time:{time.time()-t0} sec')
                    self.meshbestjobQ.put(('updateDozor',dozorresult,datastr))
                    self.ServerQ.put(('dozor',dozorresult))
                elif self.Raster_scoring_way=="None":
                    t0 = time.time()
                    dozorresult,datastr = self.fake_dozor("",self.stream_meta,self.dozor_par)
                    dozorresult['frame'] = frame
                    dozorresult['omega'] = self.stream_meta['omega_start']
                    dozorresult['numofX'] = self.stream_meta['raster_X']
                    dozorresult['numofY'] = self.stream_meta['raster_Y']
                    # view =int(self.metadata["appendix"]['runIndex'])
                    if str(meta['meta']["appendix"]['runIndex']) == '101':
                        dozorresult['view']=1
                    else:
                        dozorresult['view']=2
                    #dezor
                    #tell gui finish job
                    self.logger.info(f'save + decode time for frame {frame},time:{time.time()-t0} sec')
                    self.meshbestjobQ.put(('updateDozor',dozorresult,datastr))
                    self.ServerQ.put(('dozor',dozorresult))
                    pass

            except asapo_consumer.AsapoEndOfStreamError as e:
                self.logger.debug(f"End of stream, {self.pid=}")
                break
            except Exception as e:
                self.logger.error(f"Error in consumer: {e}, {self.pid=}")
                # break
            #everything is ok

        pass
    def rerun_dozr(self,path,metadata,frame,dozor_par,meshbestjobQ,ServerQ):
        t0 = time.time()

        dozorresult,datastr = self.dozor(path,metadata,dozor_par)
        dozorresult['frame'] = frame
        dozorresult['omega'] = metadata['omega_start']
        dozorresult['numofX'] = metadata['appendix']['raster_X']
        dozorresult['numofY'] = metadata['appendix']['raster_Y']
        if int(metadata['appendix']['runIndex']) == 101:
            dozorresult['view']=1
        else:
            dozorresult['view']=2
        #dezor
        #tell gui finish job
        self.logger.info(f'decode time for frame {frame},time:{time.time()-t0} sec')
        meshbestjobQ.put(('updateDozor',dozorresult,datastr))
        ServerQ.put(('dozor',dozorresult))
        
        pass
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
    def fake_dozor(self,path,metadata,dozor_par):
        start_time = time.time()   
        dozorresult={}
        pid=os.getpid()
        result = ''' Program dozor /A.Popov & G.Bourenkov/
     Version 2.0.2 //  21.05.2019
     Copyright 2014 by Alexander Popov and Gleb Bourenkov
     N    |            SPOTS             |        Powder Wilson              |        Main    Spot   Visible
    image | num.of  INTaver R-factor Res.|   Scale B-fac. Res. Corr. R-factor|       Score   Score  Resolution
    --------------------------------------------------------------------------------------------------------
    1 |     1        1.   0.000  99.0| ---------no results -----------   |       1.000    0.00   99.00
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

        datastr =""
 
        
        #print "Run dozor time=",dozorresult['dozorTime']
        dozorresult['totalTime']=time.time()-start_time
        #print "Total run time=",dozorresult['totalTime']
        dozorresult['File']=path
        dozorresult['spots']=dozorspots
        dozorresult['score']=dozorscore
        dozorresult['res']=dozorres
        
        self.logger.debug("PID:%d Fake dozor result=%s",pid,dozorresult)
        
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
        data=numpy.array(-1.0)
        datastr=""
        for txt in filetxt2:
            i=i+1 
            if i>3:
                try:
                    if numpy.size(data) == 1:
                        #print "1"
                        datalist=[float(txt[0:2]),float(txt[2:10]),float(txt[10:18]),float(txt[18:30]),float(txt[30:42])]
                        #datatemp=numpy.arry(datalist)
                        #print "before=",data
                        data=numpy.append(data,float(txt[0:2]))
                        #print float(txt[0:2])
                        data=numpy.append(data,float(txt[2:10]))
                        data=numpy.append(data,float(txt[10:18]))
                        data=numpy.append(data,float(txt[18:30]))
                        data=numpy.append(data,float(txt[30:42]))
                        #print "after=",data
                        data=numpy.delete(data,0)
                    else:
                        data=numpy.append(data,float(txt[0:2]))
                        data=numpy.append(data,float(txt[2:10]))
                        data=numpy.append(data,float(txt[10:18]))
                        data=numpy.append(data,float(txt[18:30]))
                        data=numpy.append(data,float(txt[30:42]))
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