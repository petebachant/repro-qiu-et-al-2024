# -*- coding: utf-8 -*-
"""
Created on Mon Sep 11 15:18:12 2023

@author: Rahman Khorramfar
"""
import numpy as np
import pandas as pd
import sys
import xarray as xr
import NCDataCost as NCDataCost
import Modules_cost as Modules
import os
import itertools
import time
import gurobipy as gp
import gurobipy as gp
from gurobipy import GRB


class Setting:
    demandfile = str()
    RE_cell_size = dict()  # degree
    RE_plant_types = list()  # set of RE plant types considered
    REfile = dict()
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
    csvdir = str()
    test_years = list()
    landusefile = dict()


# Setting parameters
Setting.wall_clock_time_lim = 10000  # seconds
Setting.demandfile = '../Demand/ISONE_grossload_metdata_spliced_22yr_UTC0.csv'
Setting.solver_gap = 0.001  # x100 percent
Setting.wall_clock_time_lim = 10000  # seconds
Setting.RE_plant_types = ['solar-UPV', 'wind-onshore']
Setting.gas_plant_types = ['ng', 'CCGT']
Setting.plant_types = Setting.RE_plant_types + Setting.gas_plant_types
Setting.print_results_header = 1
Setting.print_detailed_results = 1

Setting.WACC = 0.071

Setting.val_lost_load = 10*1000;
Setting.gas_price = 5.45
Setting.storage_types = ['Li-ion']

Setting.test_name = 'onshoresolar'
Setting.datadir = '../CF_Data/'
Setting.test_name = "onshoresolar"
Setting.year_list = [2007, 2008, 2009, 2010, 2011, 2012, 2013]


def runmodel(Setting, mdl, wake, landr, onwindsize, solarsize, cap_ng, cap_cc, evalist, ens_id,case):
    Setting.case = case
    Setting.eva_years = evalist
    Setting.test_year = Setting.year_list.copy()

    for year in Setting.eva_years:
        Setting.test_year.remove(year)
        
    print(Setting.test_year)

    Setting.num_y = len(Setting.test_year)
    Setting.eva_num_y = len(evalist)

    Setting.ens_id = ens_id

    # GW to MW # currently the ISO-NE cap is 31 GW
    Setting.UB_dispatchable_cap['ng'] = cap_ng
    Setting.UB_dispatchable_cap['CCGT'] = cap_cc  # GW to MW
    Setting.weather_model = mdl
    Setting.wake = wake
    Setting.landr = landr
    Setting.RE_cell_size['wind-onshore'] = onwindsize
    Setting.RE_cell_size['solar-UPV'] = solarsize

    if Setting.wake == 1:
        if Setting.weather_model == "WRHigh":
            Setting.REfile['wind-onshore'] = '%s/%s/Wind/wakecf/WTK_wakecf64_IEA_3.4MW_130_onshore_%.2fdeg_' % (Setting.datadir, mdl, onwindsize)
        elif Setting.weather_model == "WRLow":
            Setting.REfile['wind-onshore'] = '%s/%s/Wind/wakecf/ERA5_wakecf16_IEA_3.4MW_130_onshore_%.2fdeg_' % (Setting.datadir, mdl, onwindsize)
    else:
        if Setting.weather_model == "WRHigh":
            Setting.REfile['wind-onshore'] = '%s/%s/Wind/simplecf/WTK_simplecf_IEA_3.4MW_130_onshore_%.2fdeg_' % (Setting.datadir, mdl, onwindsize)
        elif Setting.weather_model == "WRLow":
            Setting.REfile['wind-onshore'] = '%s/%s/Wind/simplecf/ERA5_simplecf_IEA_3.4MW_130_onshore_%.2fdeg_' % (Setting.datadir, mdl, onwindsize)

    if Setting.weather_model == "WRHigh":
        Setting.REfile['solar-UPV'] = '%s/%s/Solar/NSRDB_SAM_UTC_%.2f_cf_' % (Setting.datadir, mdl,solarsize)
    else:
        Setting.REfile['solar-UPV'] = '%s/%s/Solar/ERA5_SAM_UTC_%.2f_cf_' % (Setting.datadir, mdl, solarsize)

    Setting.landusefile['solar-UPV'] = '../Landuse_data/wind_coe_composite_50_ISNE_%.2fmean.nc' % (solarsize)
    Setting.landusefile['wind-onshore'] = '../Landuse_data/wind_coe_composite_50_ISNE_%.2fmean.nc' % (onwindsize)

    stime = time.time()
    dat = NCDataCost.Data(Setting)
    print(dat.demand)
    Model = gp.Model()
    Modules.define_DVs(dat, Setting, Model)
    Modules.add_constraints(dat, Setting, Model)
    obj = Modules.add_obj_func(dat, Setting, Model)
    Model.modelSense = GRB.MINIMIZE
    Model.setObjective(obj)
    Model.setParam('OutputFlag', 1)
    Model.setParam('MIPGap', Setting.solver_gap)
    Model.setParam('Timelimit', Setting.wall_clock_time_lim)
    Model.setParam('Presolve', 2)  # -1 to 2
    Model.optimize()
    Modules.get_DV_vals(Model, Setting)
    Modules.print_results(dat, Setting, stime, Model)
    Model.reset()
    del (Model)


mdl = str(sys.argv[1])  # WR
wake = int(sys.argv[2])  # if wake=1, then wake effect is considered
landr = int(sys.argv[3])  # if landr=1, then land restriction is considered
onwindsize = float(sys.argv[4])  # OR wind
solarsize = float(sys.argv[5])  # OR solar
cap_ng = float(sys.argv[6])  # maximum capacity of natural gas (0-1)
cap_cc = float(sys.argv[7])  # maximum capacity of CCGT (0-1)
num_y = int(sys.argv[8])
ensid = int(sys.argv[9])  # 0 means runs all
case= str(sys.argv[10])  # 0 means runs all
Setting.csvdir = f'../Result_{case}/'
year_lists = list(itertools.combinations(Setting.year_list, num_y))

suffix = 'ng_%d_cc_%d_wake_%d_landr_%d_wind-onshore%.2f_solar-UPV%.2f_%s_Load.csv' % (
    cap_ng*100, cap_cc*100, wake, landr, onwindsize, solarsize, mdl)

if ensid != 0:
    csvfilename = '%s/Results/%s_sub%dyrs_ens%d_%s' % (os.getcwd(), Setting.test_name, num_y, ensid, suffix)
    print(csvfilename)
    if not os.path.exists(csvfilename):
        runmodel(Setting, mdl, wake, landr, onwindsize,
                 solarsize, cap_ng, cap_cc, year_lists[ensid-1], ensid, case)
else:
    for en in range(len(year_lists)):
        sub_year_list = year_lists[en]
        csvfilename = '%s/Results/%s_sub%dyrs_ens%d_%s' % (
            os.getcwd(), Setting.test_name, num_y, en+1, suffix)
        print(csvfilename)
        if not os.path.exists(csvfilename):
            print(csvfilename)
            runmodel(Setting, mdl, wake, landr, onwindsize,
                     solarsize, cap_ng, cap_cc, sub_year_list, en+1, case)
