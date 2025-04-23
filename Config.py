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
    "Flux":{100:8.8E12, 1: 9e+11, 5:1.97e12, 10:3.81e12, 20:6.71e12},
    "PV_dbpm3fluxlist":'07a-ES:Table:DBPM3Fluxlist',
    "PV_beamsizelist":'07a-ES:Table:Beamsize',
    "Beamsizelist":[1,5,10,20,30,40,50,60,70,80,90,100],
    "Fluxfactor":[1,2.213,4.28,7.2896,10.1737],#useless now,factor bewtween s3op =1 and =0.003,[1,5,10,20,30]
    "DoseFactor":[2.25,2.14,1.89,1.81,1.08,1,1],
    "BestDose":[3,3.6,4.4,6,8],
    "BeamFWHM":[980,380,195,49.8,23.76],
    "minExposedTime":7.8e-3,
    "Bestlowlimitscore":1
    }