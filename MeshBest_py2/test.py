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
jsonFilePath = "/NAS/Eddie/TPS07A/MeshBest_py2/hi.json"

with open(jsonFilePath, 'r') as afile:
        testdata = json.load(afile)

print(testdata)
jsondata = json.load(testdata)
