#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 17 17:03:45 2021

@author: blctl
"""
import logsetup
import requests,time
import Config
import base64
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.patches import Circle
from PyQt5.QtGui import QPixmap, QImage
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy 

def poll_result(logger,sid=101,url = 'http://10.7.1.107:8082/job',timeout=100):
    while True:
        
        response = requests.get(url)
        ans = response.json()
        # print(len(ans))
        # print(ans)
        
        for item in ans:
            # a = json.loads(item)
            # print(a)
            if ans[item]['sessionid'] == sid:
                my_sid_ans = ans[item]
        if my_sid_ans['State'] == 'End':
            logger.info(f'Get data for sid {sid}')
            return my_sid_ans['data'],my_sid_ans['State']
        elif my_sid_ans['State'] == 'Start':
            #job still ruuning
            time.sleep(0.5)
        elif my_sid_ans['State'] == 'Fail':
            
            return None,my_sid_ans['State']
        else:
            logger.info(f'Unknow state {my_sid_ans["State"]}')
            return None,'Fail'

def convert_data(jsondata,logger):
    try:
        row, col = jsondata['grid_info']['steps_y'], jsondata['grid_info']['steps_x']
        # difminpar = jsondata['MeshBest']['difminpar']
    except KeyError:
        logger.error('Experiment parameters are not communicated in the JSON')
           
    try:
        Dtable = numpy.frombuffer(base64.b64decode(jsondata['MeshBest']['Dtable']))
        Dtable = numpy.reshape(Dtable, (row, col))
        Ztable = numpy.frombuffer(base64.b64decode(jsondata['MeshBest']['Ztable']))
        Ztable = numpy.reshape(Ztable, (row, col))
        BestPositions = numpy.frombuffer(base64.b64decode(jsondata['MeshBest']['BestPositions']))
        BestPositions = numpy.reshape(BestPositions, (int(numpy.size(BestPositions)/4),4))
    except KeyError:
        logger.error('Plotting: No data to work with in the JSON')
    return Dtable,Ztable,BestPositions

def defCmap():
    #get colormap
    ncolors = 256
    #color_array = plt.get_cmap('gist_rainbow')(range(ncolors))
    color_array = plt.get_cmap('hot')(range(ncolors))
#    print color_array
#    print "--------"
    #change alpha values
    #color_array[:,-1] =np.linspace(0,1,ncolors)
#    for i in xrange(10):#make last 10 value T
#        color_array[i,-1] =0
    color_array[0,-1] = 0 #make last one T
    #print np.linspace(1.0,0.0,ncolors)       
    #create a colormap object
    map_object = LinearSegmentedColormap.from_list(name='hot_with_alpha',colors=color_array)

    # register this new colormap with matplotlib
    plt.register_cmap(cmap=map_object)
#    f,ax = plt.subplots()
#    h = ax.imshow(np.random.rand(100,100),cmap='rainbow_alpha')
#    plt.colorbar(mappable=h)
    
def genDTableMapv2(Dtable,cmap='hot_with_alpha'):
    defCmap()
   
    #print Dtable
    row=len(Dtable)
    col=len(Dtable[0])
    #print row,col
    fig = Figure(tight_layout=True,frameon=False,figsize=(col/10.0,row/10.0))
    
    fig.set_size_inches(col/10.0,row/10.0,forward=True)
    # fig.set_size_inches(col/10.0,row/10.0,forward=True)
    #fig.patch.set_facecolor((1,0.47,0.42))
    #ax=fig.add_subplot(111)
    ax = fig.add_axes([0,0,1,1])
    
    ax.axis('off')
    #fig.tight_layout(pad=0)
    #fig.subplots_adjust(left=0.0,right=1.0,top=1.0,bottom=0.0)
    
    ax.imshow(Dtable, cmap=cmap, interpolation='nearest', origin='upper',extent=[0, col, row, 0])
    #hot
    
    # fig.savefig("test.png")
    canvas = FigureCanvas(fig)
    canvas.draw()
    size = canvas.size()
    #print "canvas size=",size
    width, height = size.width(), size.height()
    #print width, height
    #image = QImage(canvas.buffer_rgba(),width,height,QImage.Format_ARGB32)
    image = QImage(canvas.buffer_rgba(),width,height,QImage.Format_RGBA8888)
    # plt.show()
    #plt.close()
    
    #print image
    #print canvas
    
    return QPixmap(image)
    # plt.imshow(Dtable, cmap='hot', interpolation='nearest', origin='upper', extent=[0.5, (col + 0.5), (row + 0.5), 0.5])
def genZTableMap(Ztable,Dtable,BestPositions,cmap='hot_with_alpha',addPositions=True,listnum=10,addText=True,Textsize=12,txtcolor='white',Circle_color='orange',overlapDozor=True):
    defCmap()
    
    cmap2 = colors.LinearSegmentedColormap.from_list('my_cmap2', [(0, 0, 0), (0, 0, 0.001)], 256)
    cmap2._init()
    alphas = numpy.linspace(-0.01, -1, cmap2.N + 3)
    cmap2._lut[:, -1] = alphas
#    
#    f,ax = plt.subplots()
#    h = ax.imshow(np.random.rand(100,100),cmap=cmap2)
#    plt.colorbar(mappable=h)
    
    
    if numpy.all(Ztable==-1):
        overlapDozor = False
    #print Dtable
    row=len(Ztable)
    col=len(Ztable[0])
    #print row,col
    fig = Figure(tight_layout=True,frameon=False,figsize=(col/5.0,row/5.0))
    
    #fig.set_size_inches(col/5,row/5,forward=True)
    #fig.patch.set_facecolor((1,0.47,0.42))
    #ax=fig.add_subplot(111)
    ax = fig.add_axes([0,0,1,1])
    
    ax.axis('off')
    #fig.tight_layout(pad=0)
    #fig.subplots_adjust(left=0.0,right=1.0,top=1.0,bottom=0.0)
    difminpar=0.2
    CrystImage=ax.imshow(Ztable, cmap=cmap, interpolation='nearest', origin='upper',extent=[0, col, row, 0],vmin=-1)
    if overlapDozor:
        OpacityImage=ax.imshow(Dtable, cmap=cmap2, interpolation='nearest', origin='upper', vmin=difminpar, \
                              vmax=numpy.percentile(Dtable[Dtable>difminpar], 99), extent=[0, col, row, 0])
    
    if addPositions:
        #ax=fig.add_subplot(111)
        # BestPositions = np.loadtxt(inuptfile.replace("Ztable","Result_BestPositions"))
        # print (BestPositions)
        # print(len(BestPositions))
        if listnum < len(BestPositions):
            for i in range(listnum):
                position = BestPositions[i]
                # print(i)
                # print(position)
                ax.add_artist(Circle((position[0], position[1]), position[2]/2.0, zorder=5, clip_on=False,linewidth=1, edgecolor=Circle_color, fill=False))
                if addText:
                    ax.text(position[0], position[1],i+1,color=txtcolor,size=Textsize,ha='center', va='center')
        else: #plot all  
            i=0
            for position in BestPositions:
                ax.add_artist(Circle((position[0], position[1]), position[2]/2.0, zorder=5, clip_on=False,
                                     linewidth=1, edgecolor=Circle_color, fill=False))
                if addText:
                    ax.text(position[0], position[1],i+1,color=txtcolor,size=Textsize,ha='center', va='center')
                i=i+1
    
    
    #hot
    
    fig.savefig("test.png")
    canvas = FigureCanvas(fig)
    canvas.draw()
    size = canvas.size()
    #print "canvas size=",size
    width, height = size.width(), size.height()
    #print width, height
    #image = QImage(canvas.buffer_rgba(),width,height,QImage.Format_ARGB32)
    image = QImage(canvas.buffer_rgba(),width,height,QImage.Format_RGBA8888)
    #plt.close()
    
    #print image
    #print canvas
    return QPixmap(image)
    #plt.imshow(Dtable, cmap='hot', interpolation='nearest', origin='upper', extent=[0.5, (col + 0.5), (row + 0.5), 0.5])


if __name__ == "__main__":
    # signal.signal(signal.SIGINT, quit)
    # signal.signal(signal.SIGTERM, quit)
    # logger=logsetup.getloger2('MestbestServer')
    Par=(Config.Par)
    
    logger = logsetup.getloger2('TestMestbestServer',LOG_FILENAME='./log/TestMesrbestServerLog.txt',level = Par['Debuglevel'])
    jsondata,state = poll_result(logger,sid=101)
    if jsondata:
        Dtable,Ztable,BestPositions = convert_data(jsondata,logger)
        # genDTableMapv2(Dtable)
        genZTableMap(Ztable,Dtable,BestPositions,overlapDozor=True)
        print(Ztable)