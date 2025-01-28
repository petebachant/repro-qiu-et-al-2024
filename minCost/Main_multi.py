# -*- coding: utf-8 -*-
"""
@author: Liying Qiu & Rahman Khorramfar 
Last modified on 2024-02-09
"""
import run_model as run
import sys
import itertools
import numpy as np
import pandas as pd
import xarray as xr
import os

class Setting:
    RE_capacity_density = dict()  # MW/km2
    RE_cell_size = dict()  # degree
    RE_plant_types = list()  # set of RE plant types considered
    REfile = dict()
    landusefile = dict()
    solver_gap = float()
    wall_clock_time_lim = int()
    weather_model = str()
    print_results_header = bool()
    print_detailed_results = bool()
    test_name = str()
    datadir = str()
    UB_dispatchable_cap = dict()
    lost_load_thres = float()
    gas_price = float()
    storage_types = list()
    plant_types = list()
    wake = int()
    gas_plant_types = list()
    val_lost_load = float()
    val_curtail = float()
    demandfile = str()
    num_y = int()
    sub_year_list = list()
    ens_id = int()
    year_list=list()

# Optimization configuration
Setting.wall_clock_time_lim = 10000  # seconds
Setting.solver_gap = 0.001  # x100 percent
Setting.wall_clock_time_lim = 100000  # seconds
Setting.print_results_header = 1
Setting.print_detailed_results = 1

###############Input data and parameters######################################
Setting.demandfile = '../Demand/ISONE_grossload_metdata_spliced_22yr_UTC0.csv'
Setting.RE_plant_types = ['solar-UPV', 'wind-onshore']
Setting.gas_plant_types = ['ng', 'CCGT']
Setting.plant_types = Setting.RE_plant_types + Setting.gas_plant_types
######################
Setting.WACC = 0.071
Setting.lost_load_thres = 0.0
Setting.RE_capacity_density['wind-onshore'] = 3.1158
Setting.RE_capacity_density['solar-UPV'] = 24
Setting.gas_price = 5.45
#Setting.gas_price = 3
Setting.storage_types = ['Li-ion']
Setting.test_name = "onshoresolar"
Setting.datadir = '../CF_Data/'
Setting.year_list = [2007, 2008, 2009, 2010, 2011, 2012, 2013]
#######################################################################################
####input from command line
mdl = str(sys.argv[1]) #WR
wake = int(sys.argv[2]) # if wake=1, then wake effect is considered
landr = int(sys.argv[3]) # if landr=1, then land restriction is considered
onwindsize = float(sys.argv[4]) # OR wind
solarsize = float(sys.argv[5]) # OR solar
cap_ng = float(sys.argv[6]) #maximum capacity of natural gas (0-1)
cap_cc = float(sys.argv[7])  # maximum capacity of CCGT (0-1)
num_y = int(sys.argv[8])
ensid = int(sys.argv[9]) # 0 means runs all

# mdl = 'WTK'
# wake = 0
# landr = 0
# onwindsize = 0.06
# solarsize = 0.14
# cap_ng =0
# cap_cc = 0.05
# num_y = 7
# ensid=1

year_lists = list(itertools.combinations(Setting.year_list, num_y))
suffix='ng_%d_cc_%d_wake_%d_landr_%d_wind-onshore%.2f_solar-UPV%.2f_%s_Load.csv' % (cap_ng*100,cap_cc*100, wake, landr, onwindsize, solarsize, mdl)
if ensid != 0:
    csvfilename = '%s/Results/%s_sub%dyrs_ens%d_%s' % (os.getcwd(), Setting.test_name, num_y, ensid, suffix)
    print(csvfilename)
    if not os.path.exists(csvfilename):
        run.runmodel(Setting, mdl, wake, landr, onwindsize,solarsize, cap_ng, cap_cc, year_lists[ensid-1], ensid)
else:
    for en in range(len(year_lists)):
        sub_year_list = year_lists[en]
        csvfilename = '%s/Results/%s_sub%dyrs_ens%d_%s' % (os.getcwd(), Setting.test_name, num_y, en+1, suffix)
        print(csvfilename)
        if not os.path.exists(csvfilename):
            print(csvfilename)
            run.runmodel(Setting, mdl, wake, landr, onwindsize,solarsize, cap_ng, cap_cc, sub_year_list, en+1)