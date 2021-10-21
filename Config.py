#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 12 09:49:13 2021

@author: blctl
"""

Par={
    "Beamline":"TPS07A",
    "Debuglevel":"INFO",#ERROR,WARNING,INFO,DEBUG
    "AvailableBeamSizes":[100,90,80,70,60,50,40,30,20,10,20,5],
    "dcsshost":"10.7.1.1",
    "dcssport":14243,
    "authhost":"10.7.1.1",
    "authport":8080,
    "foldername":"07A",
    #for default value
    "TotalRange":10,
    "Distance":200,
    "FrameWidth":0.01,
    "ExposedTime":0.01,
    "Atten":0,
    "Energy":12700,
    "Flux":{'10': 173000000000.0, '20': 1440000000000.0, '25': 766000000000.0, '30': 3470000000000.0, '5': 80400000000.0, '1': 80400000000.0},
    "DoseFactor":[2.25,2.14,1.89,1.81,1.08,1,1],
    "BestDose":[3,3.6,4.4,6,8],
    "BeamFWHM":[980,380,195,49.8,23.76],
    "minExposedTime":0.01,
    "Bestlowlimitscore":1
    }