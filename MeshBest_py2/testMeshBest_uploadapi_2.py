#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 12 11:45:33 2021

@author: blctl
"""
from __future__ import print_function
import json
import requests,time

#jsonFilePath = "/NAS/Eddie/TPS07A/MeshBest_py2/data_1.json" 
#jsonFilePath = "/NAS/Eddie/TPS07A/MeshbestServer/MeshBest_py2/viwe_1.json"
jsonFilePath = "/NAS/Eddie/TPS07A/MeshbestServer/MeshBest_py2/viwe_2.json"


with open(jsonFilePath, 'r') as json_file:
        jsondata = json.load(json_file)



url = 'http://10.7.1.107:8082/job'

headers = {"Content-Type": "application/json"}
alldata ={}
alldata['data'] = jsondata
alldata['sessionid'] = 102


response = requests.post(url, json=alldata)
print(response.content)
time.sleep(4)
response = requests.get(url) 
ans = response.json()
# print(len(ans))
# print(ans)

for item in ans:
    # a = json.loads(item)
    # print(a)
    if ans[item]['sessionid'] == 102:
        ans2 = ans[item]
print(ans2)    
# time.sleep(2)
# response = requests.get(url) 
# ans = response.json()
# print(ans)
# time.sleep(2)
# response = requests.get(url) 
# ans = response.json()
# print(ans)
