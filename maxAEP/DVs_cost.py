# -*- coding: utf-8 -*-
"""
Created on Wed Sep 27 08:49:56 2023

@author: Rahman Khorramfar
"""

class DV:
    Xg = []; # total capacity of dispatchable generator
    Xstr = []; # storage level (MWh)
    #Xr=[];# how large is the farm
    LL=[]
    Curtail=[]
    
    # operational decisions
    prod=[]; # production from generators
    load=[]; # load
    sCh = []; sDis=[]; sLev=[]; # storage variables
    # values of the decision variables
    #Xr_val =[]
    #Zr_val=list()
    Xg_val=[];Xstr_val=[];    
    prod_val=[]; sCH_val=[]; sDis_val=[]; sLev_val=[];load_val=[];
    LL_val=[];
    Curtail_val=[];

    # costs
    total_cost=[];
    gas_inv_cost=[];
    strg_inv_cost=[];var_cost=[];fuel_cost=[];
    #lost_load_cost=[];
    curtail_cost=[];

    # cost values
    total_cost_val=[];gas_inv_cost_val=[];
    strg_inv_cost_val=[];var_cost_val=[];fuel_cost_val=[];
    #lost_load_cost_val=[];
    curtail_cost_val=[];


    
    
    
    
    
    