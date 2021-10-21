#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  2 17:22:05 2020

@author: blctl
"""

def RoughDose(flux,energy,time):
        '''
        flux for photons/sec/um^2
        energy for ev
        time for sec
        '''
        wave=12398.0/energy
        print flux,wave,time
        dose=flux*time*wave*wave/2000.0
        print dose
        return dose
    
if __name__ == '__main__':

    totaltime=0.1*10/0.5
    RoughDose(6e12,12400,totaltime)
