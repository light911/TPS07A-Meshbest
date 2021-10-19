#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 11 19:34:31 2021

@author: blctl
"""
from __future__ import print_function
from flask import Flask,jsonify,request
from multiprocessing import Pool, Manager,Process
from algorithms import meshandcollect_directData
import json,traceback

p = Pool()
m = Manager()
data = m.dict()
datalist = m.list()
test = {'sessionid':-1,'State':'Finished','data':{
    "MeshBest": {
        "Dtable": "",
        "Ztable": "",
        "difminpar": 0.02,
        "positionReference": ""
    },
    "beamlineInfo": {
        "beamlineApertures": [
            50,
            30,
            20,
            10,
            5
        ],
        "detectorPixelSize": 0.0782
    },
    "grid_info": {
        "beam_height": 0.01,
        "beam_width": 0.01,
        "steps_x": 25,
        "steps_y": 16
    },
    "inputDozor": {
        "detectorDistance": 120.0,
        "orgx": 1440,
        "orgy": 1920,
        "wavelength": 0.99984
    }}}

datalist.append(test)
startid =1

app = Flask('MeshbestwebServer')

@app.route('/', methods=['GET', 'POST'])
def welcome():
    return "Hello World!"

@app.route('/job', methods=['POST'])
def jobPOST():
    getdata = request.data #give you strig
    # print(request.data)
    print('Header: ',request.headers)
    if request.is_json:
        jsondata = request.get_json()
        sessionid = jsondata['sessionid']
        
        #check id
        sameid = False
        for i,item in enumerate(datalist):
            if item['sessionid'] == sessionid:
                # print('checkin {}=={}!'.format( item['sessionid'],sessionid))
                sameid = True
                j=i
                current = item
            else:
                # print('checkin {}!={}!'.format( item['sessionid'],sessionid))
                pass
        # print(sameid)
        if sameid:
            
            if current['State'] == "End" or current['State'] == "Fail" :
                datalist[j]=jsondata
                p1 = Process(target=runmeshandcollect,args=(datalist,sessionid,))
                p1.start()
                ans ="Got same session id = {}, update job".format(sessionid)
                # print("send session id=",sessionid)
            else:
                ans ="Got same session id,job still running"
        else:
            datalist.append(jsondata)
            # print("send session id=",sessionid)
            p1 = Process(target=runmeshandcollect,args=(datalist,sessionid,))
            p1.start()
            ans = "session {} startd".format(sessionid)
        # print('got data: ',request.get_json())
        # print('after append: ',datalist)
    else:
        
        print('not json')
        # print('Try covert data: ',request.get_json(True))
        ans = "Got : " + str(getdata)
    print("job ans = ",ans)
    return ans

@app.route('/job', methods=['GET'])
def jobGET():
    ans = {}
    for i,a in enumerate(datalist):
        ans[i]=a
        
    return  jsonify(ans)


def runmeshandcollect(datalist1,session):
    for i,item in enumerate(datalist1):
        if item['sessionid'] == session:
            mydictdata = item
            j=i
    mydictdata['State'] ='Start'
    
    
    data = mydictdata['data']
    mydictdata.pop('data',None)
    datalist1[j]=mydictdata
    
    try:
        backdata = meshandcollect_directData(data)
    except Exception as e:
        traceback.print_exc()
        # print('Unexpected error:',sys.exc_info()[0])
        print('Error',e)
        mydictdata['State'] ='Fail'
         # mydictdata['data'] = backdata
    else:
        mydictdata['State'] ='End'
        mydictdata['data'] = backdata
    datalist1[j]=mydictdata

if __name__ == '__main__':       
    app.run(host='0.0.0.0', port=8082)

