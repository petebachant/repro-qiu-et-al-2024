# -*- coding: utf-8 -*-
"""
Created on Wed Sep 27 08:49:56 2023

@author: Rahman Khorramfar
"""

class DV:
    #Xr=[];# how large is the farm
    LL=[]
    Curtail=[]
    
    # operational decisions
    prod=[]; # production from generators
    sCh = []; sDis=[]; sLev=[]; # storage charge, discharge, and level

    prod_val=[]; sCh_val=[]; sDis_val=[];sLev=[]; load_val=[];
    LL_val=[];
    Curtail_val=[];

    # costs
    total_cost=[];
    var_cost=[];fuel_cost=[];
    #lost_load_cost=[];
    curtail_cost=[];

    
    # cost values
    total_cost_val=[];
    var_cost_val=[];fuel_cost_val=[];
    #lost_load_cost_val=[];
    curtail_cost_val=[];


    
    
    
    
    
    